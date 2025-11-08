
from flask import Flask, Response
import os
import urllib.parse
from werkzeug.middleware.proxy_fix import ProxyFix
from valorant.index import valorant_index
from valorant.endpoints import rango, ultima_ranked
from twitch.endpoints import followage, token, status, oauth_callback
from twitch.index import twitch_index

app = Flask(__name__)
# Preferir https en URLs externas y respetar cabeceras de proxy
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

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


# Valorant
app.add_url_rule('/valorant', view_func=valorant_index)
app.add_url_rule('/valorant/rango', view_func=rango)
app.add_url_rule('/valorant/ultima-ranked', view_func=ultima_ranked)

# twitch
app.add_url_rule('/twitch', view_func=twitch_index)
app.add_url_rule('/twitch/followage', view_func=followage)
app.add_url_rule('/twitch/token', view_func=token)
app.add_url_rule('/twitch/status', view_func=status)
app.add_url_rule('/oauth/callback', view_func=oauth_callback)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

