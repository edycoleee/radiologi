from config import Config
from common.auth import get_access_token
from common.fhir_client import post_fhir

from .service_observation import build_observation_resource
from .service_diagnostic import build_diagnostic_resource


def process_batch2(data):
    """
    1. Build Observation
    2. POST Observation → get observation_id
    3. Build DiagnosticReport (inject observation_id)
    4. POST DiagnosticReport
    5. Return {observation_id, diagnostic_report_id}
    """

    # -----------------------------
    # 1. Ambil token
    # -----------------------------
    token, err = get_access_token()
    if err:
        return err, 502

    # -----------------------------
    # 2. Build Observation
    # -----------------------------
    try:
        obs_resource = build_observation_resource(data)
    except Exception as e:
        return {"error": str(e)}, 400

    # -----------------------------
    # 3. POST Observation
    # -----------------------------
    obs_url = Config.SS_BASE_URL.rstrip("/") + "/Observation"
    obs_resp, obs_status = post_fhir(obs_url, token, obs_resource)

    if obs_status >= 300:
        return {"error": "Failed to create Observation", "detail": obs_resp}, obs_status

    observation_id = obs_resp.get("id")
    if not observation_id:
        return {"error": "Observation created but no ID returned", "detail": obs_resp}, 500

    # Inject observation_id ke DiagnosticReport
    data["observation_id"] = observation_id

    # -----------------------------
    # 4. Build DiagnosticReport
    # -----------------------------
    try:
        drep_resource = build_diagnostic_resource(data)
    except Exception as e:
        return {"error": str(e)}, 400

    # -----------------------------
    # 5. POST DiagnosticReport
    # -----------------------------
    drep_url = Config.SS_BASE_URL.rstrip("/") + "/DiagnosticReport"
    drep_resp, drep_status = post_fhir(drep_url, token, drep_resource)

    if drep_status >= 300:
        return {
            "error": "Observation created but DiagnosticReport failed",
            "observation_id": observation_id,
            "detail": drep_resp,
        }, drep_status

    diagnostic_report_id = drep_resp.get("id")

    # -----------------------------
    # 6. Return final result
    # -----------------------------
    return {
        "observation_id": observation_id,
        "diagnostic_report_id": diagnostic_report_id,
    }, 200
