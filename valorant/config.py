import os

# El nombre del jugador debe ser igual al que se usa en el juego.
# El tg no contiene el hastag(#) solo el valor.
NOMBRE = "Nayecute Twitch"
TAG    = "965"
REGION = "na"

# Aqui puedes definir tu api key de HenrikDev.
# Se recomienda setearla como variable de entorno o utilizar un archivo .env.
API_KEY = os.environ.get("API_KEY", "")
