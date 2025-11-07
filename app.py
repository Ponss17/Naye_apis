
from flask import Flask, Response
import os
from valorant.index import valorant_index
from valorant.endpoints import rango, ultima_ranked
from twitch.endpoints import followage, token, status

app = Flask(__name__)

@app.route('/')
def index():
    mensaje = """
API de Nayecute

 Endpoints disponibles:

 /valorant
     Muestra los endpoints disponibles para Valorant(solo esos momentaneamente).

/valorant/rango
     Muestra el rango actual, puntos y cambio de MMR

/valorant/ultima-ranked
     Detalles de la última partida ranked (mapa, agente, KDA y resultado)

funcionando jiji, cualquier duda con ponsscito :)
"""
    return Response(mensaje, mimetype="text/plain")

# OAuth callback simple para extraer access_token del fragmento
@app.route('/oauth/callback')
def oauth_callback():
    html = """
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
    return Response(html, mimetype="text/html")

# Valorant
app.add_url_rule('/valorant', view_func=valorant_index)
app.add_url_rule('/valorant/rango', view_func=rango)
app.add_url_rule('/valorant/ultima-ranked', view_func=ultima_ranked)

# twitch
app.add_url_rule('/twitch/followage', view_func=followage)
app.add_url_rule('/twitch/token', view_func=token)
app.add_url_rule('/twitch/status', view_func=status)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

