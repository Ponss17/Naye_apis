from flask import Response, url_for


def valorant_index():
    rango_url = url_for('rango', _external=True)
    ultima_url = url_for('ultima_ranked', _external=True)
    html = f"""
<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
    <title>Endpoints de Valorant</title>
    <style>
      :root {{ --bg: #0e0f12; --card: #1c1f24; --border: #30343a; --text: #eaeaea; --muted: #a8b0bd; --accent: #ef4444; }}
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center; background: var(--bg); color: var(--text); font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial; padding: 24px; }}
      .card {{ width: 100%; max-width: 860px; background: var(--card); border: 1px solid var(--border); border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.4); padding: 24px; }}
      h1 {{ margin: 0 0 12px; font-size: 28px; }}
      p {{ margin: 8px 0; color: var(--muted); }}
      .grid {{ display: grid; grid-template-columns: 1fr; gap: 12px; margin-top: 12px; }}
      @media (min-width: 720px) {{ .grid {{ grid-template-columns: 1fr 1fr; }} }}
      .item {{ background: #10151b; border: 1px solid #1f2530; border-radius: 12px; padding: 16px; }}
      .title {{ font-weight: 700; margin-bottom: 6px; }}
      a.btn {{ display: inline-block; text-decoration: none; background: var(--accent); color: white; padding: 8px 12px; border-radius: 10px; font-weight: 600; }}
      .row {{ display: flex; gap: 8px; align-items: center; margin-top: 8px; flex-wrap: wrap; }}
    </style>
  </head>
  <body>
    <div class=\"card\">
      <h1><img src=\"{url_for('static', filename='valorant/valorant_Icon_purple.webp')}\" alt=\"Valorant\" loading=\"lazy\" style=\"height:32px;width:auto;vertical-align:middle;margin-right:8px;border-radius:6px;\" />Endpoints de Valorant</h1>
      <p>Listado de rutas disponibles y ejemplos de uso.</p>
      <div class=\"grid\">
        <div class=\"item\">
          <div class=\"title\">Rango actual</div>
          <p>Muestra el rango, puntos y cambio de MMR.</p>
          <div class=\"row\">
            <a class=\"btn\" href=\"{rango_url}\">Abrir /valorant/rango</a>
          </div>
        </div>

        <div class=\"item\">
          <div class=\"title\">Última ranked</div>
          <p>Detalles de la última partida (mapa, agente, KDA, resultado).</p>
          <div class=\"row\">
            <a class=\"btn\" href=\"{ultima_url}\">Abrir /valorant/ultima-ranked</a>
          </div>
        </div>
      </div>
    </div>
  </body>
</html>
    """
    return Response(html, mimetype="text/html")