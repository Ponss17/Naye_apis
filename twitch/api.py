import time
from typing import Optional
import os
import requests
from .config import CLIENT_ID, CLIENT_SECRET, APP_TOKEN as CONFIG_APP_TOKEN, USER_ACCESS_TOKEN

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
    # Renueva el token 60s antes de expirar
    APP_TOKEN_EXPIRY = now + int(expires_in) - 60
    return APP_TOKEN

def _headers():
    token = CONFIG_APP_TOKEN or get_app_token()
    return {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {token}",
    }

def _headers_user(token: Optional[str] = None):
    tok = (token or USER_ACCESS_TOKEN or "").strip()
    if not tok:
        raise RuntimeError("Falta TWITCH_USER_TOKEN/USER_ACCESS_TOKEN para consultar seguidores")
    return {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {tok}",
    }

def create_clip(channel: str, has_delay: bool | None = None, user_token: str | None = None):
    token_to_use = (user_token or os.environ.get("TWITCH_USER_TOKEN") or "").strip()
    if not token_to_use:
        raise RuntimeError("Falta TWITCH_USER_TOKEN con scope 'clips:edit'")
    broadcaster_id = get_user_id(channel)
    if not broadcaster_id:
        raise RuntimeError(f"No se pudo resolver el ID del canal '{channel}'")
    url = "https://api.twitch.tv/helix/clips"
    body = {"broadcaster_id": broadcaster_id}
    if has_delay is not None:
        body["has_delay"] = bool(has_delay)
    resp = requests.post(url, headers=_headers_user(token_to_use), json=body, timeout=20)
    resp.raise_for_status()
    payload = resp.json()
    items = payload.get("data", [])
    return items[0] if items else None


def get_clip_url(clip_id: str):
    url = "https://api.twitch.tv/helix/clips"
    params = {"id": clip_id}
    resp = requests.get(url, headers=_headers(), params=params, timeout=10)
    resp.raise_for_status()
    payload = resp.json()
    data = payload.get("data", [])
    if not data:
        return None
    return data[0].get("url")

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
    url = "https://api.twitch.tv/helix/channels/followers"
    params = {"broadcaster_id": channel_id, "user_id": follower_id, "first": 1}
    r = requests.get(url, headers=_headers_user(), params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    items = data.get("data", [])
    if not items:
        return None
    follow = items[0]
    return follow

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
