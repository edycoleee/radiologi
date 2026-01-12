from config import Config
from common.auth import get_access_token
from common.fhir_client import post_fhir
from .service_encounter import build_encounter_resource
from .service_servicereq import build_servicereq_resource


def process_batch1(data):
    """
    1. Build Encounter
    2. POST Encounter → dapat Encounter ID
    3. Build ServiceRequest (inject Encounter ID)
    4. POST ServiceRequest
    5. Return {encounter_id, service_request_id}
    """

    # -----------------------------
    # 1. Ambil token
    # -----------------------------
    token, err = get_access_token()
    # print("tahap 1. Ambil token",token)
    if err:
        return err, 502

    # -----------------------------
    # 2. Build Encounter
    # -----------------------------
    try:
        encounter_resource = build_encounter_resource(data)
        # print("2. Build Encounter")
    except Exception as e:
        return {"error": str(e)}, 400

    # -----------------------------
    # 3. POST Encounter
    # -----------------------------
    encounter_url = Config.SS_BASE_URL.rstrip("/") + "/Encounter"
    enc_resp, enc_status = post_fhir(encounter_url, token, encounter_resource)
    if enc_status >= 300:
        return {"error": "Failed to create Encounter", "detail": enc_resp}, enc_status

    # Ambil Encounter ID dari response
    encounter_id = enc_resp.get("id")
    # print("3. POST Encounter",encounter_id)
    if not encounter_id:
        return {"error": "Encounter created but no ID returned", "detail": enc_resp}, 500

    # Inject Encounter ID ke payload ServiceRequest
    data["encounter_id"] = encounter_id

    # -----------------------------
    # 4. Build ServiceRequest
    # -----------------------------
    try:
        sreq_resource = build_servicereq_resource(data)
        #print("4. Build ServiceRequest",sreq_resource)
    except Exception as e:
        return {"error": str(e)}, 400

    # -----------------------------
    # 5. POST ServiceRequest
    # -----------------------------
    sreq_url = Config.SS_BASE_URL.rstrip("/") + "/ServiceRequest"
    sreq_resp, sreq_status = post_fhir(sreq_url, token, sreq_resource)

    if sreq_status >= 300:
        return {
            "error": "Encounter created but ServiceRequest failed",
            "encounter_id": encounter_id,
            "detail": sreq_resp,
        }, sreq_status

    # Ambil ServiceRequest ID
    service_request_id = sreq_resp.get("id")
    # print("5. POST ServiceRequest",service_request_id)
    
    # -----------------------------
    # 6. Return final result
    # -----------------------------
    return {
        "encounter_id": encounter_id,
        "service_request_id": service_request_id,
    }, 200
