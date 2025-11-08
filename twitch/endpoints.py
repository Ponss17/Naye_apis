from flask import request, Response, url_for
from datetime import datetime, timezone
from .config import CHANNEL_LOGIN, CLIENT_ID, CLIENT_SECRET, USER_ACCESS_TOKEN, ENDPOINT_PASSWORD
import urllib.parse
from .api import get_user_id, get_follow_info, get_app_token, validate_token
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
    except RuntimeError as e:
        return Response(str(e), mimetype="text/plain", status=500)
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
    # Protección por contraseña
    pwd = request.args.get("password") or request.headers.get("X-Endpoint-Password")
    if (ENDPOINT_PASSWORD or "") and pwd != (ENDPOINT_PASSWORD or ""):
        return Response("Acceso no autorizado. Proporcione ?password=<clave>.", mimetype="text/plain", status=403)

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


def status():
    """
    Muestra información de configuración y validación del token de aplicación:
    - Canal configurado y su ID
    - client_id asociado al token
    - scopes y expiración
    """
    lines = []
    lines.append("Estado de Twitch")
    lines.append("")

    # Canal configurado
    channel_login = (CHANNEL_LOGIN or "").strip()
    if not channel_login:
        lines.append("Canal: (no configurado) -> define TWITCH_CHANNEL_LOGIN")
    else:
        try:
            cid = get_user_id(channel_login)
            if cid:
                lines.append(f"Canal: {channel_login} (id: {cid})")
            else:
                lines.append(f"Canal: {channel_login} (no encontrado)")
        except Exception:
            lines.append(f"Canal: {channel_login} (error al resolver id)")

    # Valida el token de app
    if not CLIENT_ID or not CLIENT_SECRET:
        lines.append("Token: no disponible (faltan CLIENT_ID/SECRET)")
    else:
        try:
            tok = get_app_token()
            info = validate_token(tok)
            client_id = info.get("client_id", "")
            user_id = info.get("user_id")
            expires_in = info.get("expires_in")
            scopes = info.get("scopes", [])
            lines.append(f"Token tipo: app (client_credentials)")
            lines.append(f"Token client_id: {client_id}")
            lines.append(f"Token user_id: {user_id}")
            lines.append(f"Token expires_in: {expires_in}s")
            lines.append(f"Token scopes: {', '.join(scopes) if scopes else '(sin scopes)'}")
        except requests.exceptions.HTTPError as e:
            status = getattr(e.response, "status_code", 500)
            lines.append(f"Token: error HTTP {status} al validar")
        except requests.exceptions.RequestException:
            lines.append("Token: no se pudo validar (problema de red)")
        except Exception:
            lines.append("Token: error inesperado al validar")

    # Valida el token de usuario (si está configurado)
    user_tok = (USER_ACCESS_TOKEN or "").strip()
    if not user_tok:
        lines.append("")
        lines.append("Token usuario: (no configurado) -> define TWITCH_USER_TOKEN")
    else:
        try:
            info = validate_token(user_tok)
            client_id = info.get("client_id", "")
            user_id = info.get("user_id")
            expires_in = info.get("expires_in")
            scopes = info.get("scopes", [])
            has_followers = "moderator:read:followers" in scopes
            lines.append("")
            lines.append("Token usuario: presente")
            lines.append(f"Token usuario client_id: {client_id}")
            lines.append(f"Token usuario user_id: {user_id}")
            lines.append(f"Token usuario expires_in: {expires_in}s")
            lines.append(f"Token usuario scopes: {', '.join(scopes) if scopes else '(sin scopes)'}")
            lines.append(f"Scope requerido moderator:read:followers: {'OK' if has_followers else 'FALTA'}")
        except requests.exceptions.HTTPError as e:
            status = getattr(e.response, "status_code", 500)
            lines.append("")
            lines.append(f"Token usuario: error HTTP {status} al validar")
        except requests.exceptions.RequestException:
            lines.append("")
            lines.append("Token usuario: no se pudo validar (problema de red)")
        except Exception:
            lines.append("")
            lines.append("Token usuario: error inesperado al validar")

    body = "\n".join(lines) + "\n"
    return Response(body, mimetype="text/plain")


def oauth_callback():
    """
    Página de callback para flujo OAuth implícito de Twitch.
    Muestra el token de usuario si llega en el fragmento (#access_token=...).
    Protegida con contraseña configurable.
    """
    # Protección por contraseña
    pwd = request.args.get("password") or request.headers.get("X-Endpoint-Password")
    if (ENDPOINT_PASSWORD or "") and pwd != (ENDPOINT_PASSWORD or ""):
        unauthorized = """
<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
    <title>Acceso protegido</title>
    <style>
      body { font-family: system-ui, sans-serif; padding: 24px; }
      input { padding: 8px; font-size: 14px; }
      button { padding: 8px 12px; font-size: 14px; }
    </style>
  </head>
  <body>
    <h1>Acceso protegido</h1>
    <p>Ingresa la clave para acceder al callback.</p>
    <input type=\"password\" id=\"pw\" placeholder=\"Contraseña\">
    <button id=\"go\">Entrar</button>
    <script>
      (function(){
        const go = document.getElementById('go');
        go.addEventListener('click', function(){
          const pw = document.getElementById('pw').value;
          const url = new URL(window.location.href);
          url.searchParams.set('password', pw);
          window.location.href = url.toString();
        });
      })();
    </script>
  </body>
</html>
        """
        return Response(unauthorized, mimetype="text/html", status=401)

    redirect_uri = url_for('oauth_callback', _external=True)
    # Forzar https en Render si el proxy no indica correctamente el esquema
    host = request.host or ""
    xfp = (request.headers.get('X-Forwarded-Proto') or '').split(',')[0].strip()
    if 'onrender.com' in host and xfp != 'https' and redirect_uri.startswith('http://'):
        redirect_uri = 'https://' + host + url_for('oauth_callback')
    auth_url = (
        "https://id.twitch.tv/oauth2/authorize?client_id="
        + (CLIENT_ID or "")
        + "&redirect_uri="
        + urllib.parse.quote(redirect_uri, safe="")
        + "&response_type=token&scope=moderator%3Aread%3Afollowers&force_verify=true"
    )
    html_template = """
<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
    <title>OAuth Token</title>
    <style>
      body { font-family: system-ui, sans-serif; padding: 24px; }
      pre { background: #111; color: #0f0; padding: 16px; border-radius: 8px; overflow-x: auto; }
    </style>
  </head>
  <body>
    <h1>Token de Usuario</h1>
    <p>Si llegaste aquí desde Twitch OAuth, abajo verás tu <code>access_token</code>.</p>
    <pre id=\"out\">Esperando datos del fragmento...</pre>
    <h2>¿No ves el token?</h2>
    <p>Inicia el flujo OAuth con tu <code>client_id</code> configurado: <strong>__CLIENT_ID__</strong></p>
    <p>Redirect URI actual: <code>__REDIRECT_URI__</code></p>
    <p><a href=\"__AUTH_URL__\">Autorizar con Twitch (implicit grant)</a></p>
    <script>
      (function(){
        const hash = new URLSearchParams(window.location.hash.slice(1));
        const token = hash.get('access_token');
        const error = hash.get('error_description') || hash.get('error');
        const out = document.getElementById('out');
        if (token) {
          out.textContent = token;
        } else if (error) {
          out.textContent = 'Error: ' + error;
        } else {
          out.textContent = 'No se encontró access_token en el fragmento (#...).';
        }
      })();
    </script>
  </body>
</html>
    """
    html = (
        html_template
        .replace("__CLIENT_ID__", CLIENT_ID or "")
        .replace("__AUTH_URL__", auth_url)
        .replace("__REDIRECT_URI__", redirect_uri)
    )
    return Response(html, mimetype="text/html")
