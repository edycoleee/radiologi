import requests
import os
from config import Config
from common.auth import get_access_token


def lookup_imaging_by_acsn(acsn):
    """
    Cari ImagingStudy berdasarkan ACSN (Accession Number)
    dan kembalikan imagingStudy_id.
    """

    # -----------------------------
    # 1. Ambil token
    # -----------------------------
    token, err = get_access_token()
    if err:
        return err, 502

    # -----------------------------
    # 2. Build URL pencarian ImagingStudy
    # -----------------------------
    org_id = os.getenv("SS_ORG_ID") or Config.SS_ORG_ID
    identifier_system = f"http://sys-ids.kemkes.go.id/acsn/{org_id}"

    base_url = Config.SS_BASE_URL.rstrip("/")
    imaging_url = f"{base_url}/ImagingStudy?identifier={identifier_system}|{acsn}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/fhir+json",
    }

    # -----------------------------
    # 3. GET ImagingStudy
    # -----------------------------
    try:
        resp = requests.get(imaging_url, headers=headers, timeout=20)
    except requests.RequestException as exc:
        return {"error": "Failed to GET ImagingStudy", "detail": str(exc)}, 502

    ctype = resp.headers.get("Content-Type", "")

    # -----------------------------
    # 4. Parse response
    # -----------------------------
    try:
        if "json" in ctype:
            data = resp.json()

            # Case 1: Bundle
            if data.get("resourceType") == "Bundle":
                entries = data.get("entry") or []
                if not entries:
                    return {"error": "No ImagingStudy found", "detail": data}, 404

                # Cari ImagingStudy pertama
                for e in entries:
                    res = e.get("resource") or {}
                    if res.get("resourceType") == "ImagingStudy" and res.get("id"):
                        return {"imagingStudy_id": res["id"]}, 200

                # fallback: ambil resource pertama
                first = entries[0].get("resource") or {}
                if first.get("id"):
                    return {"imagingStudy_id": first["id"]}, 200

                return {"error": "No ImagingStudy id in results", "detail": data}, 502

            # Case 2: Single ImagingStudy
            if data.get("resourceType") == "ImagingStudy":
                return {"imagingStudy_id": data.get("id")}, 200

            # Case 3: Unexpected response
            return data, resp.status_code

        # Non‑JSON response
        return {"raw": resp.text}, resp.status_code

    except Exception:
        return {"raw": resp.text}, resp.status_code
