import os
import subprocess
import requests
from config import Config

# ---------------------------------------------------------
# Helper: cari study dari Accession Number dari PACS
# ---------------------------------------------------------
def find_dicom_by_accession(acc_num):
    url = f"{Config.DCM4CHEE_URL}/rs/studies?AccessionNumber={acc_num}"

    resp = requests.get(url, timeout=10)

    if resp.status_code != 200:
        return None, "Study tidak ditemukan"

    studies = resp.json()
    if not studies:
        return None, "Study tidak ditemukan"

    study_uid = studies[0]["0020000D"]["Value"][0]
    return study_uid, None


# ---------------------------------------------------------
# Helper: Ambil metadata dari PACS
# ---------------------------------------------------------
def get_dicom_metadata(study_uid):
    url = f"{Config.DCM4CHEE_URL}/rs/studies/{study_uid}/metadata"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    return {
        "series": data[0]["0020000E"]["Value"][0],
        "sop": data[0]["00080018"]["Value"][0],
    }


def get_all_instances(study_uid):
    url = f"{Config.DCM4CHEE_URL}/rs/studies/{study_uid}/metadata"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    instances = []
    for item in data:
        instances.append({
            "series": item["0020000E"]["Value"][0],
            "sop": item["00080018"]["Value"][0],
        })

    return instances

# ---------------------------------------------------------
# Helper: Download WADO
# ---------------------------------------------------------
def download_wado(study_uid, meta, target_path):
    params = {
        "requestType": "WADO",
        "studyUID": study_uid,
        "seriesUID": meta["series"],
        "objectUID": meta["sop"],
        "contentType": "application/dicom",
    }

    with requests.get(f"{Config.DCM4CHEE_URL}/wado", params=params, stream=True) as r:
        r.raise_for_status()
        with open(target_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

# ---------------------------------------------------------
# Helper: Modify DICOM tags
# ---------------------------------------------------------
def modify_dicom(file_path, patient_id=None, acc_num=None):
    cmd = ["dcmodify", "--ignore-errors"]

    if patient_id:
        cmd.extend(["-i", f"(0010,0020)={patient_id}"])

    if acc_num:
        cmd.extend(["-i", f"(0008,0050)={acc_num}"])

    cmd.append(file_path)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception(f"dcmodify error: {result.stderr}")

    # Hapus file .bak
    bak = f"{file_path}.bak"
    if os.path.exists(bak):
        os.remove(bak)


# ---------------------------------------------------------
# Helper: Send to Router (storescu)
# ---------------------------------------------------------
def send_to_router(file_path):
    cmd = [
        "storescu",
        "-v",
        "--propose-lossless",
        "-aec",
        Config.ROUTER_AET,
        Config.ROUTER_IP,
        Config.ROUTER_PORT,
        file_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if "Received Store Response (Success)" not in (result.stdout + result.stderr):
        raise Exception(f"StoreSCU Failed: {result.stderr}")

def process_dicom(data):
    study_uid = data.get("study")
    patient_id = data.get("patientid")
    accession = data.get("accesionnum")

    try:
        # =====================================================
        # 1 & 2. Tentukan Study UID
        # =====================================================
        if study_uid:
            # validasi study ada / tidak
            try:
                instances = get_all_instances(study_uid)
                if not instances:
                    return {
                        "status": "error",
                        "message": "Study UID tidak memiliki instance"
                    }, 404
            except Exception:
                return {
                    "status": "error",
                    "message": "Study UID tidak ditemukan"
                }, 404

        else:
            # Study kosong → cari via Accession Number
            if not accession:
                return {
                    "status": "error",
                    "message": "Study UID dan Accession Number kosong"
                }, 400

            study_uid, err = find_dicom_by_accession(accession)
            if err:
                return {
                    "status": "error",
                    "message": err
                }, 404

            instances = get_all_instances(study_uid)
            if not instances:
                return {
                    "status": "error",
                    "message": "Study ditemukan tapi tidak ada instance"
                }, 404

        # =====================================================
        # 3–8. Download, Modify (opsional), Send (LOOP)
        # =====================================================
        success_count = 0

        for idx, inst in enumerate(instances):
            local_path = os.path.join(
                Config.TEMP_DIR, f"{study_uid}_{idx}.dcm"
            )

            try:
                # 3. Download WADO (per SOP)
                download_wado(study_uid, inst, local_path)

                # 4–7. Modify DICOM (bersyarat)
                if patient_id or accession:
                    modify_dicom(
                        local_path,
                        patient_id=patient_id if patient_id else None,
                        acc_num=accession if accession else None,
                    )

                # 8. Kirim ke Router
                send_to_router(local_path)
                success_count += 1

            finally:
                # Cleanup per file
                if os.path.exists(local_path):
                    os.remove(local_path)

        return {
            "status": "success",
            "study_uid": study_uid,
            "total_instance": len(instances),
            "sent_instance": success_count,
            "patient_modified": bool(patient_id),
            "accession_modified": bool(accession),
            "router": f"{Config.ROUTER_IP}:{Config.ROUTER_PORT}",
        }, 200

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }, 500
