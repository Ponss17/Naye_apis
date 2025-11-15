
from flask import Flask, Response, url_for
import os
import urllib.parse
from werkzeug.middleware.proxy_fix import ProxyFix
from valorant.index import valorant_index
from valorant.endpoints import rango, ultima_ranked
from twitch.endpoints import followage, token, status, oauth_callback, clip
from twitch.index import twitch_index
from common.response import text_response
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
from common.http import get_session

app = Flask(__name__, static_folder='img', static_url_path='/img')
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
logging.basicConfig(level=logging.INFO)

limiter = Limiter(get_remote_address, app=app, default_limits=["100 per minute"], storage_uri=os.environ.get("RATELIMIT_STORAGE_URI", "memory://")) 
_session = get_session()

# Cabeceras de seguridad para las respuestas
@app.after_request
def add_security_headers(resp: Response):
    resp.headers.setdefault('X-Content-Type-Options', 'nosniff')
    resp.headers.setdefault('X-Frame-Options', 'DENY')
    resp.headers.setdefault('Referrer-Policy', 'no-referrer')
    resp.headers.setdefault(
        'Content-Security-Policy',
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'"
    )
    return resp

@app.route('/')
def index():
    v_index = url_for('valorant_index')
    t_index = url_for('twitch_index')
    v_rango = url_for('rango')
    v_ultima = url_for('ultima_ranked')
    t_callback = url_for('oauth_callback')
    t_status = url_for('status')
    t_follow = url_for('followage') + '?user=ponss17'
    t_token = url_for('token')
    html = f"""
<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
    <title>API de Nayecute</title>
    <style>
      :root {{ --bg: #0e0f12; --card: #1c1f24; --border: #30343a; --text: #eaeaea; --muted: #a8b0bd; --accent: #7c3aed; --accent2: #ef4444; }}
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center; background: var(--bg); color: var(--text); font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial; padding: 24px; }}
      .card {{ width: 100%; max-width: 980px; background: var(--card); border: 1px solid var(--border); border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.4); padding: 24px; }}
      h1 {{ margin: 0 0 12px; font-size: 28px; }}
      p {{ margin: 8px 0; color: var(--muted); }}
      .grid {{ display: grid; grid-template-columns: 1fr; gap: 12px; margin-top: 12px; }}
      @media (min-width: 800px) {{ .grid {{ grid-template-columns: 1fr 1fr; }} }}
      .item {{ background: #10151b; border: 1px solid #1f2530; border-radius: 12px; padding: 16px; }}
      .title {{ display: flex; align-items: center; gap: 12px; }}
      .title img {{ height: 32px; width: auto; border-radius: 6px; }}
      .title a {{ color: white; text-decoration: none; font-weight: 600; }}
      .title a:hover {{ text-decoration: underline; }}
      ul {{ margin: 8px 0 0; padding-left: 18px; color: var(--muted); }}
      li {{ margin: 6px 0; }}
      a.btn {{ display: inline-block; text-decoration: none; background: var(--accent); color: white; padding: 8px 12px; border-radius: 10px; font-weight: 600; }}
      a.btn.red {{ background: var(--accent2); }}
      .row {{ display: flex; gap: 8px; align-items: center; margin-top: 8px; flex-wrap: wrap; }}
    </style>
  </head>
  <body>
    <div class=\"card\">
      <div class=\"title\">
        <img src=\"{url_for('static', filename='user/naye_icon.webp')}\" alt=\"Naye\" loading=\"lazy\" />
        <h1>API de Nayecute</h1>
      </div>
      <p>Selecciona una sección para ver sus endpoints y ejemplos.</p>
      <div class=\"grid\">
        <div class=\"item\">
          <div class=\"title\">
            <img src=\"{url_for('static', filename='valorant/valorant_Icon_purple.webp')}\" alt=\"Valorant\" loading=\"lazy\" />
            <a href=\"{v_index}\">Valorant</a>
          </div>
          <ul>
            <li><a href=\"{v_rango}\">/valorant/rango</a> — rango actual, puntos y MMR</li>
            <li><a href=\"{v_ultima}\">/valorant/ultima-ranked</a> — última partida (mapa, agente, KDA, resultado)</li>
          </ul>
          <div class=\"row\">
            <a class=\"btn red\" href=\"{v_index}\">Ir al índice de Valorant</a>
          </div>
        </div>

        <div class=\"item\"> 
          <div class=\"title\">
            <img src=\"{url_for('static', filename='twitch/twitch.webp')}\" alt=\"Twitch\" loading=\"lazy\" />
            <a href=\"{t_index}\">Twitch</a>
          </div>
          <ul>
            <li><a href=\"{t_callback}\">/oauth/callback</a> — flujo implícito para obtener access_token</li>
            <li><a href=\"{t_status}\">/twitch/status</a> — validar tokens y configuración</li>
            <li><a href=\"{t_follow}\">/twitch/followage?user=ponss17</a> — followage de un usuario de ejemplo</li>
            <li><a href=\"{t_token}\">/twitch/token</a> — app token (protegido)</li>
          </ul>
          <div class=\"row\"> 
            <a class=\"btn\" href=\"{t_index}\">Ir al índice de Twitch</a>
          </div>
        </div>
      </div>
    </div>
  </body>
</html>
    """
    return Response(html, mimetype="text/html")


# Valorant
app.add_url_rule('/valorant', view_func=valorant_index)
app.add_url_rule('/valorant/rango', view_func=limiter.limit("30 per minute")(rango))
app.add_url_rule('/valorant/ultima-ranked', view_func=limiter.limit("30 per minute")(ultima_ranked))

# twitch
app.add_url_rule('/twitch', view_func=twitch_index)
app.add_url_rule('/twitch/followage', view_func=limiter.limit("60 per minute")(followage))
app.add_url_rule('/twitch/token', view_func=limiter.limit("10 per minute")(token))
app.add_url_rule('/twitch/status', view_func=limiter.limit("30 per minute")(status))
app.add_url_rule('/oauth/callback', view_func=oauth_callback, methods=['GET','POST'])
app.add_url_rule('/twitch/clip', view_func=limiter.limit("10 per minute")(clip), methods=['GET', 'POST'])


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

