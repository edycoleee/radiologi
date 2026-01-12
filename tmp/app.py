import logging
import os
import subprocess
import requests
import tempfile
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, send_file, after_this_request
from flask_restx import Api, Resource, Namespace, fields
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from config import Config

app = Flask(__name__, template_folder="templates", static_folder="static")
Config.init_app()

# --- LOGGER SETTINGS ---
logger = logging.getLogger('DicomLogger')
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(Config.LOG_FILE, maxBytes=1_000_000, backupCount=3)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# --- API SETUP ---
api = Api(app, version='1.1', title='DICOM Gateway API', doc='/api/docs', prefix='/api')
dicom_ns = Namespace('dicom', description='DICOM Router Operations')
api.add_namespace(dicom_ns)

# --- MODELS ---
dicom_model = dicom_ns.model('DicomSend', {
    'study': fields.String(required=True, description="Study Instance UID"),
    'patientid': fields.String(required=False),
    'accesionnum': fields.String(required=False)
})

# --- HELPER FUNCTIONS (SatuSehat) ---

def fetch_ss_token():
    """Mengambil token akses dari SatuSehat OAuth2."""
    token_url = f"{Config.AUTH_URL}/accesstoken?grant_type=client_credentials"
    try:
        resp = requests.post(token_url, data={"client_id": Config.CLIENT_ID, "client_secret": Config.CLIENT_SECRET}, timeout=15)
        resp.raise_for_status()
        return resp.json().get("access_token"), None
    except Exception as e:
        return None, str(e)

def fhir_get(url, token):
    """Helper untuk melakukan request GET ke FHIR SatuSehat."""
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/fhir+json"}
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        return resp.json(), resp.status_code
    except Exception as e:
        return {"error": str(e)}, 502

# --- HELPER FUNCTIONS (DICOM/PACS) ---

def get_dicom_metadata(study_uid):
    url = f"{Config.DCM4CHEE_URL}/rs/studies/{study_uid}/metadata"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return {
        "series": data[0]["0020000E"]["Value"][0],
        "sop": data[0]["00080018"]["Value"][0]
    }

def download_wado(study_uid, meta, target_path):
    params = {
        "requestType": "WADO", "studyUID": study_uid,
        "seriesUID": meta['series'], "objectUID": meta['sop'],
        "contentType": "application/dicom"
    }
    with requests.get(f"{Config.DCM4CHEE_URL}/wado", params=params, stream=True) as r:
        r.raise_for_status()
        with open(target_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

def modify_dicom(file_path, patient_id=None, acc_num=None):
    cmd = ["dcmodify", "--ignore-errors"]
    if patient_id: cmd.extend(["-i", f"(0010,0020)={patient_id}"])
    if acc_num: cmd.extend(["-i", f"(0008,0050)={acc_num}"])
    cmd.append(file_path)
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"dcmodify error: {result.stderr}")
    if os.path.exists(f"{file_path}.bak"):
        os.remove(f"{file_path}.bak")

def send_to_router(file_path):
    cmd = [
        "storescu", "-v", "--propose-lossless",
        "-aec", Config.ROUTER_AET, 
        Config.ROUTER_IP, Config.ROUTER_PORT, 
        file_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if "Received Store Response (Success)" not in (result.stdout + result.stderr):
        raise Exception(f"StoreSCU Failed: {result.stderr}")

# --- API ENDPOINTS ---

@dicom_ns.route('/imageid/<string:acsn>')
@dicom_ns.doc(params={'acsn': 'Accession Number dari PACS/SatuSehat'})
class ImageId(Resource):
    def get(self, acsn):
        """Ambil ImagingStudy ID dari SatuSehat berdasarkan Accession Number"""
        token, err = fetch_ss_token()
        if err:
            logger.error(f"Auth SatuSehat failed: {err}")
            return {"status": "error", "message": "Auth SatuSehat failed", "detail": err}, 502
        
        identifier_system = f"http://sys-ids.kemkes.go.id/acsn/{Config.ORG_ID}"
        url = f"{Config.BASE_URL}/ImagingStudy?identifier={identifier_system}|{acsn}"
        
        data, status = fhir_get(url, token)
        
        if status != 200:
            return {"status": "error", "detail": data}, status

        if data.get("resourceType") == "Bundle":
            entries = data.get("entry") or []
            for e in entries:
                res = e.get("resource") or {}
                if res.get("resourceType") == "ImagingStudy":
                    # Fix: Penggunaan logger.info yang benar
                    logger.info(f"ImagingStudy found: {res.get('id')}")
                    return {
                        "status": "success",
                        "imagingStudy_id": res.get("id"),
                        "patient_reference": res.get("subject", {}).get("reference")
                    }, 200

        logger.error(f"No ImagingStudy found for Accession Number: {acsn}")    
        return {"status": "error", "message": "No ImagingStudy found for this Accession Number"}, 404

@dicom_ns.route('/process')
class ProcessDicom(Resource):
    @dicom_ns.expect(dicom_model)
    def post(self):
        """Ambil dari PACS -> Modifikasi -> Kirim ke Router"""
        data = dicom_ns.payload
        study_uid = data['study']
        p_id = data.get('patientid')
        acc = data.get('accesionnum')
        
        local_path = os.path.join(Config.TEMP_DIR, f"proc_{study_uid}.dcm")
        
        try:
            logger.info(f"Processing Study: {study_uid}")
            meta = get_dicom_metadata(study_uid)
            download_wado(study_uid, meta, local_path)
            
            if p_id or acc:
                modify_dicom(local_path, p_id, acc)
                
            send_to_router(local_path)
            return {"status": "success", "study": study_uid}, 200
        except Exception as e:
            logger.error(f"Process failed: {str(e)}")
            return {"status": "error", "message": str(e)}, 500
        finally:
            if os.path.exists(local_path): 
                os.remove(local_path)

@app.route("/")
def index():
    return render_template("page.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)