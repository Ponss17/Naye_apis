import time
from typing import Optional
import requests
from .config import CLIENT_ID, CLIENT_SECRET

APP_TOKEN = None
APP_TOKEN_EXPIRY = 0


def get_app_token():
    global APP_TOKEN, APP_TOKEN_EXPIRY
    now = time.time()
    if APP_TOKEN and now < APP_TOKEN_EXPIRY:
        return APP_TOKEN

    url = "https://id.twitch.tv/oauth2/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
    }
    r = requests.post(url, data=data, timeout=10)
    r.raise_for_status()
    payload = r.json()
    APP_TOKEN = payload.get("access_token")
    expires_in = payload.get("expires_in", 0)
    # Renovar 60s antes de expirar
    APP_TOKEN_EXPIRY = now + int(expires_in) - 60
    return APP_TOKEN


def _headers():
    return {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {get_app_token()}",
    }


def get_user_id(login: str) -> Optional[str]:
    url = "https://api.twitch.tv/helix/users"
    params = {"login": login}
    r = requests.get(url, headers=_headers(), params=params, timeout=10)
    r.raise_for_status()
    data = r.json().get("data", [])
    if not data:
        return None
    return data[0].get("id")


def get_follow_info(follower_id: str, channel_id: str):
    url = "https://api.twitch.tv/helix/users/follows"
    params = {"from_id": follower_id, "to_id": channel_id, "first": 1}
    r = requests.get(url, headers=_headers(), params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    total = data.get("total", 0)
    if total < 1:
        return None
    follow = data.get("data", [])[0]
    return follow  # contiene followed_at


def validate_token(token: str) -> dict:
    """
    Valida un token contra https://id.twitch.tv/oauth2/validate
    Devuelve el JSON con client_id, user_id, expires_in, scopes, etc.
    """
    url = "https://id.twitch.tv/oauth2/validate"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()
