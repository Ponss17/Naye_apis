from flask import Response, request, url_for


def twitch_index():
    base_callback = url_for('oauth_callback', _external=True)
    follow_example = url_for('followage', _external=True) + '?user=ponss17'
    status_link = url_for('status', _external=True)
    token_link = url_for('token', _external=True)
    html = f"""
<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
    <title>Endpoints de Twitch</title>
    <style>
      :root {{ --bg: #0e0f12; --card: #1c1f24; --border: #30343a; --text: #eaeaea; --muted: #a8b0bd; --accent: #7c3aed; }}
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center; background: var(--bg); color: var(--text); font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial; padding: 24px; }}
      .card {{ width: 100%; max-width: 860px; background: var(--card); border: 1px solid var(--border); border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.4); padding: 24px; }}
      h1 {{ margin: 0 0 12px; font-size: 28px; }}
      p {{ margin: 8px 0; color: var(--muted); }}
      .grid {{ display: grid; grid-template-columns: 1fr; gap: 12px; margin-top: 12px; }}
      @media (min-width: 720px) {{ .grid {{ grid-template-columns: 1fr 1fr; }} }}
      .item {{ background: #10151b; border: 1px solid #1f2530; border-radius: 12px; padding: 16px; }}
      .title {{ font-weight: 700; margin-bottom: 6px; }}
      code {{ background: #111827; color: #f59e0b; padding: 2px 6px; border-radius: 6px; }}
      a.btn {{ display: inline-block; text-decoration: none; background: var(--accent); color: white; padding: 8px 12px; border-radius: 10px; font-weight: 600; }}
      .row {{ display: flex; gap: 8px; align-items: center; margin-top: 8px; flex-wrap: wrap; }}
    </style>
  </head>
  <body>
    <div class=\"card\">
      <h1>Endpoints de Twitch</h1>
      <p>Listado de rutas disponibles y ejemplos de uso.</p>
      <div class=\"grid\">
        <div class=\"item\">
          <div class=\"title\">Callback OAuth</div>
          <p>Inicia y completa el flujo OAuth implícito para obtener <code>access_token</code>.</p>
          <div class=\"row\">
            <a class=\"btn\" href=\"{base_callback}\">Abrir /oauth/callback</a>
          </div>
        </div>

        <div class=\"item\">
          <div class=\"title\">Estado</div>
          <p>Muestra configuración y valida tokens de aplicación y usuario.</p>
          <div class=\"row\">
            <a class=\"btn\" href=\"{status_link}\">Abrir /twitch/status</a>
          </div>
        </div>

        <div class=\"item\">
          <div class=\"title\">Followage</div>
          <p>Consulta desde cuándo un usuario sigue al canal configurado.</p>
          <p>Ejemplo: <code>/twitch/followage?user=ponss17</code></p>
          <div class=\"row\">
            <a class=\"btn\" href=\"{follow_example}\">Probar /twitch/followage</a>
          </div>
        </div>

        <div class=\"item\">
          <div class=\"title\">Token de aplicación</div>
          <p>Genera un <code>app access token</code> (requiere contraseña).</p>
          <p>Usa <code>?password=TU_CLAVE</code> o header <code>X-Endpoint-Password</code>.</p>
          <div class=\"row\">
            <a class=\"btn\" href=\"{token_link}\">Abrir /twitch/token</a>
          </div>
        </div>
      </div>
    </div>
  </body>
</html>
    """
    return Response(html, mimetype="text/html")