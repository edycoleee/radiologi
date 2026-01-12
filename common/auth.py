import requests
from config import Config

def get_access_token():
    token_url = Config.SS_AUTH_URL.rstrip("/") + "/accesstoken?grant_type=client_credentials"

    try:
        resp = requests.post(
            token_url,
            data={
                "client_id": Config.SS_CLIENT_ID,
                "client_secret": Config.SS_CLIENT_SECRET,
            },
            timeout=15,
        )
        resp.raise_for_status()
    except Exception as e:
        return None, {"error": "Failed to fetch token", "detail": str(e)}

    data = resp.json()
    token = data.get("access_token") or data.get("accessToken")
    return token, None
