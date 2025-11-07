
from flask import Flask, Response
import os
from valorant.index import valorant_index
from valorant.endpoints import rango, ultima_ranked
from twitch.endpoints import followage, token

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

# Valorant
app.add_url_rule('/valorant', view_func=valorant_index)
app.add_url_rule('/valorant/rango', view_func=rango)
app.add_url_rule('/valorant/ultima-ranked', view_func=ultima_ranked)

# twitch
app.add_url_rule('/twitch/followage', view_func=followage)
app.add_url_rule('/twitch/token', view_func=token)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

