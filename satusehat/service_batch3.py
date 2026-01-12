from config import Config
from common.auth import get_access_token
from common.fhir_client import post_fhir

from .service_encounter import build_encounter_resource
from .service_servicereq import build_servicereq_resource
from .service_observation import build_observation_resource
from .service_diagnostic import build_diagnostic_resource
from .service_imaging import lookup_imaging_by_acsn


def process_batch3(data):
    """
    Full radiology workflow:
    1. Encounter
    2. ServiceRequest
    3. ImagingStudy (lookup by ACSN)
    4. Observation
    5. DiagnosticReport
    """

    # -----------------------------
    # 1. Token
    # -----------------------------
    token, err = get_access_token()
    if err:
        return err, 502

    # -----------------------------
    # 2. Encounter
    # -----------------------------
    try:
        encounter_resource = build_encounter_resource(data)
    except Exception as e:
        return {"error": str(e)}, 400

    enc_url = Config.SS_BASE_URL.rstrip("/") + "/Encounter"
    enc_resp, enc_status = post_fhir(enc_url, token, encounter_resource)

    if enc_status >= 300:
        return {"error": "Failed to create Encounter", "detail": enc_resp}, enc_status

    encounter_id = enc_resp.get("id")
    data["encounter_id"] = encounter_id

    # -----------------------------
    # 3. ServiceRequest
    # -----------------------------
    try:
        sreq_resource = build_servicereq_resource(data)
    except Exception as e:
        return {"error": str(e)}, 400

    sreq_url = Config.SS_BASE_URL.rstrip("/") + "/ServiceRequest"
    sreq_resp, sreq_status = post_fhir(sreq_url, token, sreq_resource)

    if sreq_status >= 300:
        return {
            "error": "Encounter created but ServiceRequest failed",
            "encounter_id": encounter_id,
            "detail": sreq_resp,
        }, sreq_status

    service_request_id = sreq_resp.get("id")
    data["service_request_id"] = service_request_id

    # -----------------------------
    # 4. ImagingStudy (lookup by ACSN)
    # -----------------------------
    acsn = data.get("noacsn")
    img_resp, img_status = lookup_imaging_by_acsn(acsn)

    if img_status != 200:
        return {
            "error": "ServiceRequest created but ImagingStudy lookup failed",
            "encounter_id": encounter_id,
            "service_request_id": service_request_id,
            "detail": img_resp,
        }, img_status

    imaging_study_id = img_resp.get("imagingStudy_id")
    data["imaging_study_id"] = imaging_study_id

    # -----------------------------
    # 5. Observation
    # -----------------------------
    try:
        obs_resource = build_observation_resource(data)
    except Exception as e:
        return {"error": str(e)}, 400

    obs_url = Config.SS_BASE_URL.rstrip("/") + "/Observation"
    obs_resp, obs_status = post_fhir(obs_url, token, obs_resource)

    if obs_status >= 300:
        return {
            "error": "ImagingStudy found but Observation failed",
            "encounter_id": encounter_id,
            "service_request_id": service_request_id,
            "imaging_study_id": imaging_study_id,
            "detail": obs_resp,
        }, obs_status

    observation_id = obs_resp.get("id")
    data["observation_id"] = observation_id

    # -----------------------------
    # 6. DiagnosticReport
    # -----------------------------
    try:
        drep_resource = build_diagnostic_resource(data)
    except Exception as e:
        return {"error": str(e)}, 400

    drep_url = Config.SS_BASE_URL.rstrip("/") + "/DiagnosticReport"
    drep_resp, drep_status = post_fhir(drep_url, token, drep_resource)

    if drep_status >= 300:
        return {
            "error": "Observation created but DiagnosticReport failed",
            "encounter_id": encounter_id,
            "service_request_id": service_request_id,
            "imaging_study_id": imaging_study_id,
            "observation_id": observation_id,
            "detail": drep_resp,
        }, drep_status

    diagnostic_report_id = drep_resp.get("id")

    # -----------------------------
    # 7. Final Output
    # -----------------------------
    return {
        "encounter_id": encounter_id,
        "service_request_id": service_request_id,
        "imaging_study_id": imaging_study_id,
        "observation_id": observation_id,
        "diagnostic_report_id": diagnostic_report_id,
    }, 200
