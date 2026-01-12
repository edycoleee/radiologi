import requests

def post_fhir(url, token, resource):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/fhir+json",
    }

    try:
        resp = requests.post(url, json=resource, headers=headers, timeout=20)
    except Exception as e:
        return {"error": "Failed to POST resource", "detail": str(e)}, 502

    ctype = resp.headers.get("Content-Type", "")
    if "json" in ctype:
        try:
            return resp.json(), resp.status_code
        except:
            return {"raw": resp.text}, resp.status_code

    return {"raw": resp.text}, resp.status_code
