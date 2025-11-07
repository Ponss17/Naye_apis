from flask import request, Response
from datetime import datetime, timezone
from .config import CHANNEL_LOGIN, CLIENT_ID, CLIENT_SECRET
from .api import get_user_id, get_follow_info, get_app_token
import requests


def _humanize_duration(delta_seconds: float) -> str:
    minutes = int(delta_seconds // 60)
    hours = minutes // 60
    days = hours // 24
    years = days // 365
    months = (days % 365) // 30
    days_rem = (days % 365) % 30

    parts: list[str] = []
    if years:
        parts.append(f"{years} años")
    if months:
        parts.append(f"{months} meses")
    if days_rem:
        parts.append(f"{days_rem} días")

    if not parts:
        hours_rem = hours % 24
        minutes_rem = minutes % 60
        if hours_rem:
            parts.append(f"{hours_rem} horas")
        if minutes_rem:
            parts.append(f"{minutes_rem} minutos")
        if not parts:
            parts.append("menos de un minuto")

    return ", ".join(parts)


def followage():
    user_login = request.args.get("user", "").strip().lower()
    channel_login = request.args.get("channel", "").strip().lower() or CHANNEL_LOGIN.lower()

    if not user_login:
        return Response("Debes proporcionar ?user=<login> del usuario.", mimetype="text/plain", status=400)
    if not channel_login:
        return Response("Falta configurar TWITCH_CHANNEL_LOGIN.", mimetype="text/plain", status=500)
    if not CLIENT_ID or not CLIENT_SECRET:
        return Response("Faltan TWITCH_CLIENT_ID y/o TWITCH_CLIENT_SECRET.", mimetype="text/plain", status=500)

    try:
        follower_id = get_user_id(user_login)
        channel_id = get_user_id(channel_login)
    except requests.exceptions.HTTPError as e:
        return Response("Error al autenticar con Twitch (Client ID/Secret). Verifica tus credenciales.", mimetype="text/plain", status=500)
    except requests.exceptions.RequestException:
        return Response("No se pudo contactar a la API de Twitch.", mimetype="text/plain", status=502)
    except Exception:
        return Response("Error inesperado al buscar usuarios en Twitch.", mimetype="text/plain", status=500)

    if not follower_id:
        return Response(f"No encontré al usuario '{user_login}'.", mimetype="text/plain", status=404)
    if not channel_id:
        return Response(f"No encontré el canal '{channel_login}'.", mimetype="text/plain", status=404)

    try:
        info = get_follow_info(follower_id, channel_id)
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, "status_code", 500)
        msg = ""
        try:
            body = e.response.json()
            msg = body.get("message") or body.get("error") or ""
        except Exception:
            try:
                msg = e.response.text[:200]
            except Exception:
                msg = ""
        return Response(f"Error de Twitch ({status}): {msg}", mimetype="text/plain", status=502)
    except requests.exceptions.RequestException as e:
        return Response("No se pudo consultar el follow en Twitch.", mimetype="text/plain", status=502)
    except Exception:
        return Response("Error inesperado al consultar follow.", mimetype="text/plain", status=500)
    if not info:
        return Response(f"{user_login} no sigue a {channel_login}.", mimetype="text/plain")

    followed_at_str = info.get("followed_at")
    try:
        followed_at = datetime.fromisoformat(followed_at_str.replace("Z", "+00:00"))
    except Exception:
        return Response("Error al interpretar fecha de follow.", mimetype="text/plain", status=500)

    now = datetime.now(timezone.utc)
    delta = (now - followed_at).total_seconds()
    human = _humanize_duration(delta)
    return Response(f"{user_login} sigue a {channel_login} desde hace {human}.", mimetype="text/plain")


def token():
    """
    Devuelve el app access token generado a partir de CLIENT_ID/CLIENT_SECRET
    usando grant_type=client_credentials. Útil para diagnosticar credenciales.

    Seguridad: este token otorga acceso de app. No lo expongas públicamente.
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        return Response("Faltan TWITCH_CLIENT_ID y/o TWITCH_CLIENT_SECRET.", mimetype="text/plain", status=500)
    try:
        tok = get_app_token()
        return Response(tok or "", mimetype="text/plain")
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, "status_code", 500)
        msg = ""
        try:
            body = e.response.json()
            msg = body.get("message") or body.get("error") or ""
        except Exception:
            try:
                msg = e.response.text[:200]
            except Exception:
                msg = ""
        return Response(f"Error de Twitch ({status}): {msg}", mimetype="text/plain", status=502)
    except requests.exceptions.RequestException:
        return Response("No se pudo obtener el token desde Twitch.", mimetype="text/plain", status=502)
    except Exception:
        return Response("Error inesperado al generar token.", mimetype="text/plain", status=500)
