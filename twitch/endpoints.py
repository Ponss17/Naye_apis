from flask import request, Response, url_for
from datetime import datetime, timezone
from .config import CHANNEL_LOGIN, CLIENT_ID, CLIENT_SECRET, USER_ACCESS_TOKEN, ENDPOINT_PASSWORD
import urllib.parse
import requests
import re
import logging
from common.response import text_response
from common.http import get_session
from common.cache import SimpleTTLCache
from twitch.api import get_user_id, get_follow_info, validate_token, create_clip, get_clip_url

_session = get_session()
_cache = SimpleTTLCache(default_ttl=15)


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
        return text_response("Debes proporcionar ?user=<login> del usuario.", 400)
    if not re.fullmatch(r"^[A-Za-z0-9_]{1,32}$", user_login):
        return text_response("'user' inválido. Usa A–Z, 0–9 y _.", 400)
    if not channel_login:
        return text_response("Falta configurar TWITCH_CHANNEL_LOGIN.", 500)
    if not CLIENT_ID or not CLIENT_SECRET:
        return text_response("Faltan TWITCH_CLIENT_ID y/o TWITCH_CLIENT_SECRET.", 500)

    cache_key = f"followage:{user_login}:{channel_login}"
    cached = _cache.get(cache_key)
    if cached:
        return text_response(cached)

    try:
        follower_id = get_user_id(user_login)
        channel_id = get_user_id(channel_login)
    except requests.exceptions.HTTPError as e:
        logging.exception("HTTP error en followage get_user_id")
        return text_response("Error al autenticar con Twitch (Client ID/Secret).", 500)
    except requests.exceptions.RequestException:
        logging.exception("Error de red en followage get_user_id")
        return text_response("No se pudo contactar a la API de Twitch.", 502)
    except Exception:
        logging.exception("Error inesperado en followage get_user_id")
        return text_response("Error inesperado al buscar usuarios en Twitch.", 500)

    if not follower_id:
        return text_response(f"No encontré al usuario '{user_login}'.", 404)
    if not channel_id:
        return text_response(f"No encontré el canal '{channel_login}'.", 404)

    try:
        info = get_follow_info(follower_id, channel_id)
    except RuntimeError as e:
        return text_response(str(e), 500)
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
        return text_response(f"Error de Twitch ({status}): {msg}", 502)
    except requests.exceptions.RequestException as e:
        logging.exception("Error de red en followage get_follow_info")
        return text_response("No se pudo consultar el follow en Twitch.", 502)
    except Exception:
        logging.exception("Error inesperado en followage get_follow_info")
        return text_response("Error inesperado al consultar follow.", 500)
    if not info:
        return text_response(f"{user_login} no sigue a {channel_login}.")

    followed_at_str = info.get("followed_at")
    try:
        followed_at = datetime.fromisoformat(followed_at_str.replace("Z", "+00:00"))
    except Exception:
        return text_response("Error al interpretar fecha de follow.", 500)

    now = datetime.now(timezone.utc)
    delta = (now - followed_at).total_seconds()
    human = _humanize_duration(delta)
    result = f"{user_login} sigue a {channel_login} desde hace {human}."
    _cache.set(cache_key, result)
    return text_response(result)


def token():
    """
    Devuelve el app access token generado a partir de CLIENT_ID/CLIENT_SECRET
    usando grant_type=client_credentials. Útil para diagnosticar credenciales.

    Seguridad: este token otorga acceso de app. No lo expongas públicamente.
    """
    # Protección por contraseña (normaliza espacios, acepta query/header/cookie y distingue origen)
    pwd_source = None
    raw_pwd = None
    val = request.args.get("password")
    if val is not None:
        raw_pwd = val
        pwd_source = "query"
    if raw_pwd is None:
        val = request.headers.get("X-Endpoint-Password")
        if val is not None:
            raw_pwd = val
            pwd_source = "header"
    if raw_pwd is None:
        val = request.cookies.get("endpoint_pwd")
        if val is not None:
            raw_pwd = val
            pwd_source = "cookie"

    pwd = (raw_pwd or "").strip()
    expected = (ENDPOINT_PASSWORD or "").strip()
    if expected and pwd != expected:
        # Intentos explícitos (query/header) → 401 con mensaje. Cookie inválida o sin intento → 200 con formulario.
        explicit_attempt = pwd_source in ("query", "header") and bool((raw_pwd or "").strip())
        if explicit_attempt:
            return text_response("Acceso no autorizado. Proporcione ?password=<clave> o header X-Endpoint-Password.", 401)
        # Formulario básico para acceso manual
        html = """
<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
    <title>Token de aplicación (protegido)</title>
    <style>
      :root { --bg:#0e0f12; --card:#1c1f24; --border:#30343a; --text:#eaeaea; --muted:#a8b0bd; --accent:#7c3aed; }
      * { box-sizing:border-box; }
      body { margin:0; min-height:100vh; display:flex; align-items:center; justify-content:center; background:var(--bg); color:var(--text); font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial; padding:24px; }
      .card { width:100%; max-width:520px; background:var(--card); border:1px solid var(--border); border-radius:16px; box-shadow:0 10px 30px rgba(0,0,0,0.4); padding:24px; }
      h1 { margin:0 0 8px; font-size:24px; }
      p { margin:8px 0; color:var(--muted); }
      .row { display:flex; gap:8px; align-items:center; margin-top:12px; }
      input { flex:1; padding:10px 12px; border-radius:10px; border:1px solid var(--border); background:#111827; color:var(--text); }
      button { padding:10px 14px; border-radius:10px; border:1px solid var(--border); background:var(--accent); color:white; font-weight:600; cursor:pointer; }
    </style>
  </head>
  <body>
    <div class=\"card\">
      <h1>Acceso protegido</h1>
      <p>Ingresa la clave para ver el app token.</p>
      <div class=\"row\">
        <input type=\"password\" id=\"pw\" placeholder=\"Contraseña\" autocomplete=\"current-password\">
        <button type=\"button\" id=\"go\">Entrar</button>
      </div>
    </div>
    <script>
      (function(){
        const pwInput = document.getElementById('pw');
        const go = document.getElementById('go');
        function submitPwd(){
          const pw = pwInput.value.trim();
          const url = new URL(window.location.href);
          url.searchParams.set('password', pw);
          window.location.replace(url.toString());
        }
        go.addEventListener('click', submitPwd);
        pwInput.addEventListener('keydown', function(e){ if (e.key === 'Enter') submitPwd(); });
        setTimeout(function(){ pwInput.focus(); pwInput.select && pwInput.select(); }, 10);
      })();
    </script>
  </body>
</html>
        """
        resp = Response(html, mimetype="text/html", status=200)
        # Limpiar cookie inválida si existía
        if pwd_source == "cookie":
            try:
                host = request.host or ""
                xfp = (request.headers.get('X-Forwarded-Proto') or '').split(',')[0].strip()
                secure = ('onrender.com' in host and xfp == 'https') or request.is_secure
                resp.delete_cookie('endpoint_pwd', secure=secure, httponly=True, samesite='Lax')
            except Exception:
                pass
        resp.headers['Cache-Control'] = 'no-store'
        return resp

    if not CLIENT_ID or not CLIENT_SECRET:
        return text_response("Faltan TWITCH_CLIENT_ID y/o TWITCH_CLIENT_SECRET.", 500)
    try:
        tok = get_app_token()
        resp = text_response(tok or "")
        # Recordar acceso por 10 minutos tras validación correcta
        try:
            host = request.host or ""
            xfp = (request.headers.get('X-Forwarded-Proto') or '').split(',')[0].strip()
            secure = ('onrender.com' in host and xfp == 'https') or request.is_secure
            if expected:
                resp.set_cookie('endpoint_pwd', expected, max_age=600, secure=secure, httponly=True, samesite='Lax')
        except Exception:
            pass
        resp.headers['Cache-Control'] = 'no-store'
        return resp
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
        return text_response(f"Error de Twitch ({status}): {msg}", 502)
    except requests.exceptions.RequestException:
        return text_response("No se pudo obtener el token desde Twitch.", 502)
    except Exception:
        return text_response("Error inesperado al generar token.", 500)


def status():
    """
    Muestra información de configuración y validación del token de aplicación:
    - Canal configurado
    - Estado de validez de tokens (sin mostrar datos sensibles)
    - Presencia de scopes requeridos
    """
    lines = []
    lines.append("Estado de Twitch")
    lines.append("")

    # Canal configurado
    channel_login = (CHANNEL_LOGIN or "").strip()
    if not channel_login:
        lines.append("Canal: (no configurado) -> define TWITCH_CHANNEL_LOGIN")
    else:
        lines.append(f"Canal configurado: {channel_login}")

    # Valida el token de app
    if not CLIENT_ID or not CLIENT_SECRET:
        lines.append("Token de app: no disponible (faltan CLIENT_ID/SECRET)")
    else:
        try:
            tok = get_app_token()
            validate_token(tok)
            lines.append("Token de app: válido")
        except requests.exceptions.HTTPError as e:
            status = getattr(e.response, "status_code", 500)
            lines.append(f"Token de app: error HTTP {status} al validar")
        except requests.exceptions.RequestException:
            lines.append("Token de app: no se pudo validar (problema de red)")
        except Exception:
            lines.append("Token de app: error inesperado al validar")

    # Valida el token de usuario (si está configurado)
    user_tok = (USER_ACCESS_TOKEN or "").strip()
    if not user_tok:
        lines.append("")
        lines.append("Token usuario: (no configurado) -> define TWITCH_USER_TOKEN")
    else:
        try:
            info = validate_token(user_tok)
            scopes = info.get("scopes", [])
            has_followers = "moderator:read:followers" in scopes
            lines.append("")
            lines.append("Token usuario: presente")
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
    return text_response(body)


def oauth_callback():
    """
    Página de callback para flujo OAuth implícito de Twitch.
    Muestra el token de usuario si llega en el fragmento (#access_token=...).
    Protegida con contraseña configurable.
    """
    # Soporte de cierre de sesión del callback: borra la cookie y muestra login
    if (request.args.get("logout") or "").lower() in ("1", "true", "yes"): 
        unauthorized = """
<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
    <title>Acceso protegido</title>
    <style>
      :root { --bg: #0e0f12; --card: #1c1f24; --border: #30343a; --text: #eaeaea; --muted: #a8b0bd; --accent: #7c3aed; }
      * { box-sizing: border-box; }
      body { margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center; background: var(--bg); color: var(--text); font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial; padding: 24px; }
      .card { width: 100%; max-width: 520px; background: var(--card); border: 1px solid var(--border); border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.4); padding: 24px; }
      h1 { margin: 0 0 8px; font-size: 26px; }
      p { margin: 8px 0; color: var(--muted); }
      .row { display: flex; gap: 8px; align-items: center; margin-top: 12px; }
      input { flex: 1; padding: 10px 12px; border-radius: 10px; border: 1px solid var(--border); background: #111827; color: var(--text); }
      button { padding: 10px 14px; border-radius: 10px; border: 1px solid var(--border); background: var(--accent); color: white; font-weight: 600; cursor: pointer; }
    </style>
  </head>
  <body>
    <div class=\"card\">
      <h1>Acceso protegido</h1>
      <p>Ingresa la clave para acceder al callback.</p>
      <div class=\"row\">
        <input type=\"password\" id=\"pw\" placeholder=\"Contraseña\" autocomplete=\"current-password\">
        <button type=\"button\" id=\"go\">Entrar</button>
      </div>
    </div>
    <script>
      (function(){
        const pwInput = document.getElementById('pw');
        const go = document.getElementById('go');
        function submitPwd(){
          const pw = pwInput.value.trim();
          const url = new URL(window.location.href);
          url.searchParams.delete('logout');
          url.searchParams.set('password', pw);
          const base = url.origin + url.pathname;
          const search = url.searchParams.toString();
          const next = base + (search ? ('?' + search) : '') + (window.location.hash || '');
          window.location.replace(next);
        }
        go.addEventListener('click', submitPwd);
        pwInput.addEventListener('keydown', function(e){ if (e.key === 'Enter') submitPwd(); });
        setTimeout(function(){ pwInput.focus(); pwInput.select && pwInput.select(); }, 10);
      })();
    </script>
  </body>
</html>
        """
        resp = Response(unauthorized, mimetype="text/html")
        # Borra cookie de acceso recordado
        try:
            host = request.host or ""
            xfp = (request.headers.get('X-Forwarded-Proto') or '').split(',')[0].strip()
            secure = ('onrender.com' in host and xfp == 'https') or request.is_secure
            resp.delete_cookie('endpoint_pwd', secure=secure, httponly=True, samesite='Lax')
        except Exception:
            pass
        resp.headers['Cache-Control'] = 'no-store'
        return resp

    pwd_source = None
    raw_pwd = None
    if request.method == "POST":
        val = request.form.get("password")
        if val is not None:
            raw_pwd = val
            pwd_source = "form"
    if raw_pwd is None:
        val = request.args.get("password")
        if val is not None:
            raw_pwd = val
            pwd_source = "query"
    if raw_pwd is None:
        val = request.headers.get("X-Endpoint-Password")
        if val is not None:
            raw_pwd = val
            pwd_source = "header"
    if raw_pwd is None:
        val = request.cookies.get("endpoint_pwd")
        if val is not None:
            raw_pwd = val
            pwd_source = "cookie"

    pwd = (raw_pwd or "").strip()
    expected = (ENDPOINT_PASSWORD or "").strip()
    if expected and pwd != expected:
        # Solo mostrar error (401) si hubo intento explícito (form/query/header). Para cookie inválida devolver 200.
        show_error = bool((raw_pwd or "").strip()) and pwd_source != "cookie"
        unauthorized = """
<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
    <title>Acceso protegido</title>
    <style>
      :root { --bg: #0e0f12; --card: #1c1f24; --border: #30343a; --text: #eaeaea; --muted: #a8b0bd; --accent: #7c3aed; }
      * { box-sizing: border-box; }
      body { margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center; background: var(--bg); color: var(--text); font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial; padding: 24px; }
      .card { width: 100%; max-width: 520px; background: var(--card); border: 1px solid var(--border); border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.4); padding: 24px; }
      h1 { margin: 0 0 8px; font-size: 26px; }
      p { margin: 8px 0; color: var(--muted); }
      .row { display: flex; gap: 8px; align-items: center; margin-top: 12px; }
      input { flex: 1; padding: 10px 12px; border-radius: 10px; border: 1px solid var(--border); background: #111827; color: var(--text); }
      button { padding: 10px 14px; border-radius: 10px; border: 1px solid var(--border); background: var(--accent); color: white; font-weight: 600; cursor: pointer; }
      .error { color: #ef4444; font-weight: 600; }
    </style>
  </head>
  <body>
    <div class=\"card\">
      <h1>Acceso protegido</h1>
      <p>Ingresa la clave para acceder al callback.</p>
      __ERROR__
      <div class=\"row\">
        <input type=\"password\" id=\"pw\" placeholder=\"Contraseña\" autocomplete=\"current-password\">
        <button type=\"button\" id=\"go\">Entrar</button>
      </div>
    </div>
    <script>
      (function(){
        const pwInput = document.getElementById('pw');
        const go = document.getElementById('go');
        function submitPwd(){
          const pw = pwInput.value.trim();
          const url = new URL(window.location.href);
          url.searchParams.set('password', pw);
          const base = url.origin + url.pathname;
          const search = url.searchParams.toString();
          const next = base + (search ? ('?' + search) : '') + (window.location.hash || '');
          window.location.replace(next);
        }
        go.addEventListener('click', submitPwd);
        pwInput.addEventListener('keydown', function(e){ if (e.key === 'Enter') submitPwd(); });
        setTimeout(function(){ pwInput.focus(); pwInput.select && pwInput.select(); }, 10);
      })();
    </script>
  </body>
</html>
        """
        error_html = "<p class=\"error\">Contraseña incorrecta. Intenta nuevamente.</p>" if show_error else ""
        html = unauthorized.replace("__ERROR__", error_html)
        # Si no hubo intento de contraseña, devolver 200 para evitar ruido de 401 en logs.
        # Sólo marcar 401 cuando hubo intento y la contraseña es incorrecta.
        status_code = 401 if show_error else 200
        resp = Response(html, mimetype="text/html", status=status_code)
        # Si la cookie era inválida, limpiarla para evitar bucles de 401.
        if pwd_source == "cookie":
            try:
                host = request.host or ""
                xfp = (request.headers.get('X-Forwarded-Proto') or '').split(',')[0].strip()
                secure = ('onrender.com' in host and xfp == 'https') or request.is_secure
                resp.delete_cookie('endpoint_pwd', secure=secure, httponly=True, samesite='Lax')
            except Exception:
                pass
        resp.headers['Cache-Control'] = 'no-store'
        return resp

    redirect_uri = url_for('oauth_callback', _external=True)
    host = request.host or ""
    xfp = (request.headers.get('X-Forwarded-Proto') or '').split(',')[0].strip()
    if 'onrender.com' in host and xfp != 'https' and redirect_uri.startswith('http://'):
        redirect_uri = 'https://' + host + url_for('oauth_callback')
    auth_url = (
        "https://id.twitch.tv/oauth2/authorize?client_id="
        + (CLIENT_ID or "")
        + "&redirect_uri="
        + urllib.parse.quote(redirect_uri, safe="")
        + "&response_type=token&scope=moderator%3Aread%3Afollowers%20clips%3Aedit&force_verify=true"
    )
    html_template = """
<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
    <title>OAuth Token</title>
    <style>
      :root {
        --bg: #0e0f12; --card: #1c1f24; --border: #30343a; --text: #eaeaea; --muted: #a8b0bd; --accent: #7c3aed;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center;
        background: var(--bg); color: var(--text); font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, \"Apple Color Emoji\", \"Segoe UI Emoji\";
        padding: 24px;
      }
      .card {
        width: 100%; max-width: 720px; background: var(--card); border: 1px solid var(--border);
        border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.4); padding: 24px;
      }
      h1 { margin: 0 0 8px; font-size: 28px; }
      p { margin: 8px 0; color: var(--muted); }
      .row { display: flex; gap: 8px; align-items: center; margin-top: 8px; }
      a.btn {
        display: inline-block; text-decoration: none; background: var(--accent); color: white;
        padding: 10px 14px; border-radius: 10px; font-weight: 600;
      }
      code { background: #111827; color: #f59e0b; padding: 2px 6px; border-radius: 6px; }
      pre {
        background: #0b0f14; color: #16a34a; padding: 16px; border-radius: 12px; overflow-x: auto;
        border: 1px dashed #1f2937; margin: 12px 0 0;
      }
      .meta { display: grid; grid-template-columns: 1fr; gap: 8px; margin-top: 12px; }
      .meta-item { background: #10151b; border: 1px solid #1f2530; border-radius: 12px; padding: 12px; }
      .label { font-size: 12px; color: var(--muted); }
    </style>
  </head>
  <body>
    <div class=\"card\">
      <h1>Token de Usuario</h1>
      <p>Si llegaste aquí desde Twitch OAuth, abajo verás tu <code>access_token</code>.</p>
      <pre id=\"out\">Esperando datos del fragmento...</pre>
      <div class=\"meta\">
        <div class=\"meta-item\"><div class=\"label\">Client ID</div><div><code>__CLIENT_ID__</code></div></div>
        <div class=\"meta-item\"><div class=\"label\">Redirect URI actual</div><div><code>__REDIRECT_URI__</code></div></div>
      </div>
      <div class=\"row\">
        <a class=\"btn\" href=\"__AUTH_URL__\">Autorizar con Twitch (implicit grant)</a>
        <a class=\"btn red\" href=\"__LOGOUT_URL__\">Cerrar sesión de callback</a>
      </div>
    </div>
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
        .replace("__LOGOUT_URL__", redirect_uri + "?logout=1")
    )
    resp = Response(html, mimetype="text/html")
    # Recuerda acceso por 10 minutos para no pedir la contraseña tras el redirect de Twitch
    try:
        host = request.host or ""
        xfp = (request.headers.get('X-Forwarded-Proto') or '').split(',')[0].strip()
        secure = ('onrender.com' in host and xfp == 'https') or request.is_secure
        resp.set_cookie('endpoint_pwd', expected, max_age=600, secure=secure, httponly=True, samesite='Lax')
    except Exception:
        pass
    resp.headers['Cache-Control'] = 'no-store'
    return resp


def clip():
    expected = (ENDPOINT_PASSWORD or "").strip()
    raw_pwd = (request.headers.get("X-Endpoint-Password") or request.cookies.get("endpoint_pwd") or "").strip()
    if expected and raw_pwd != expected:
        return text_response("Acceso no autorizado. Envíe header X-Endpoint-Password.", 401)

    channel_login = request.args.get("channel", "").strip().lower() or (CHANNEL_LOGIN or "").strip().lower()
    if not channel_login:
        return text_response("Falta configurar TWITCH_CHANNEL_LOGIN o pasar ?channel=<login>.", 400)
    if not re.fullmatch(r"^[A-Za-z0-9_]{1,32}$", channel_login):
        return text_response("'channel' inválido. Usa A–Z, 0–9 y _.", 400)

    has_delay = (request.args.get("has_delay") or "").strip().lower() in ("1", "true", "yes")

    try:
        clip_obj = create_clip(channel_login, has_delay=has_delay)
    except RuntimeError as e:
        return text_response(str(e), 500)
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
        return text_response(f"Error de Twitch ({status}): {msg}", 502)
    except requests.exceptions.RequestException:
        return text_response("No se pudo contactar a la API de Twitch.", 502)
    except Exception:
        logging.exception("Error inesperado en /twitch/clip")
        return text_response("Error inesperado al crear clip.", 500)

    if not clip_obj:
        return text_response("No se pudo crear el clip (¿canal no está en vivo?).", 502)

    clip_id = clip_obj.get("id") or ""
    edit_url = clip_obj.get("edit_url") or ""
    clip_url = edit_url
    try:
        u = get_clip_url(clip_id)
        if u:
            clip_url = u
    except Exception:
        pass
    return text_response(clip_url or edit_url or "")
