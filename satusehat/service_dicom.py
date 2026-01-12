import os
import subprocess
import requests
from config import Config


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


# ---------------------------------------------------------
# MAIN SERVICE: Process DICOM
# ---------------------------------------------------------
def process_dicom(data):
    study_uid = data["study"]
    patient_id = data.get("patientid")
    accession = data.get("accesionnum")

    local_path = os.path.join(Config.TEMP_DIR, f"proc_{study_uid}.dcm")

    try:
        # 1. Metadata
        meta = get_dicom_metadata(study_uid)

        # 2. Download WADO
        download_wado(study_uid, meta, local_path)

        # 3. Modify DICOM (optional)
        if patient_id or accession:
            modify_dicom(local_path, patient_id, accession)

        # 4. Send to Router
        send_to_router(local_path)

        return {
            "status": "success",
            "study_uid": study_uid,
            "router": f"{Config.ROUTER_IP}:{Config.ROUTER_PORT}",
        }, 200

    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

    finally:
        if os.path.exists(local_path):
            os.remove(local_path)
