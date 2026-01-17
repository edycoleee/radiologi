#config.py
import os
from dotenv import load_dotenv

# Memuat file .env
load_dotenv()

class Config:
    # --- PACS & ROUTER CONFIG ---
    DCM4CHEE_URL = os.getenv("DCM4CHEE_URL", "http://192.10.10.23:8081/dcm4chee-arc/aets/DCM4CHEE")
    
    ROUTER_IP = os.getenv("ROUTER_IP", "192.10.10.51")
    ROUTER_PORT = os.getenv("ROUTER_PORT", "11112")
    ROUTER_AET = os.getenv("ROUTER_AET", "DCMROUTER")
    
    # --- SATUSEHAT CONFIG ---
    # Menggunakan environment variable agar credential tidak hardcoded di production
    SS_AUTH_URL = os.getenv("SS_AUTH_URL", "https://api-satusehat.kemkes.go.id/oauth2/v1")
    SS_BASE_URL = os.getenv("SS_BASE_URL", "https://api-satusehat.kemkes.go.id/fhir-r4/v1")
    SS_ORG_ID = os.getenv("SS_ORG_ID")
    SS_CLIENT_ID = os.getenv("SS_CLIENT_ID")
    SS_CLIENT_SECRET = os.getenv("SS_CLIENT_SECRET")

    # --- SYSTEM CONFIG ---
    LOG_FILE = os.getenv("LOG_FILE", "app_dicom.log")
    TEMP_DIR = os.getenv("TEMP_DIR", "/tmp/dicom_gateway_tmp")

    @classmethod
    def init_app(cls):
        """Memastikan folder temporary tersedia saat aplikasi start"""
        if not os.path.exists(cls.TEMP_DIR):
            try:
                os.makedirs(cls.TEMP_DIR, exist_ok=True)
                print(f"[*] Temporary directory created at: {cls.TEMP_DIR}")
            except Exception as e:
                print(f"[!] Failed to create temp directory: {e}")