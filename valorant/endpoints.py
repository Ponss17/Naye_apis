import requests
from flask import Response
from .config import NOMBRE, TAG, REGION, API_KEY
from .rangos_es import Rangos_ES

# Cambio de rango.
def rango():
    """Endpoint de rango según tu implementación original usando v2/mmr y current_data."""
    url = (
        f"https://api.henrikdev.xyz/valorant/v2/mmr/"
        f"{REGION}/{NOMBRE.replace(' ', '%20')}/{TAG}?api_key={API_KEY}"
    )
    try:
        res = requests.get(url, timeout=10)
        data = res.json()

        current_data = data.get('data', {}).get('current_data', None)
        if not current_data:
            return Response("No hay datos actuales disponibles.", mimetype='text/plain')

        rango_en = current_data.get('currenttierpatched', 'Desconocido')
        rango_es = Rangos_ES.get(rango_en, rango_en)
        puntos = current_data.get('ranking_in_tier', 'Desconocido')
        delta = current_data.get('mmr_change_to_last_game', None)

        if isinstance(delta, int):
            if delta > 0:
                delta_txt = f"gané {delta} puntos"
            elif delta < 0:
                delta_txt = f"perdí {abs(delta)} puntos"
            else:
                delta_txt = "no cambié de puntos"
        else:
            delta_txt = "cambio de puntos desconocido"

        ultimo_agente = obtener_ultimo_agente()

        if ultimo_agente:
            respuesta = (
                f"🎀💕actualmente estoy en {rango_es} con {puntos} puntos 🤗✨, "
                f"mi última partida fue con {ultimo_agente} y {delta_txt}"
            )
        else:
            respuesta = (
                f"🎀💕actualmente estoy en {rango_es} con {puntos} puntos 🤗✨, "
                f"mi última partida: {delta_txt}"
            )
    except Exception as e:
        print("Error:", e)
        respuesta = "Rango no disponible"
    return Response(respuesta, mimetype='text/plain')


def obtener_ultimo_agente():
    """Obtiene el último agente jugado por el usuario"""
    try:
        url = (
            f"https://api.henrikdev.xyz/valorant/v3/matches/"
            f"{REGION}/{NOMBRE.replace(' ', '%20')}/{TAG}?api_key={API_KEY}"
        )
        res = requests.get(url, timeout=10)
        data = res.json()

        if data.get('status') == 200 and data.get('data') and len(data['data']) > 0:
            ultima_partida = data['data'][0]

            for jugador in ultima_partida['players']['all_players']:
                if jugador['name'].lower() == NOMBRE.lower() and jugador['tag'].lower() == TAG.lower():
                    return jugador['character']

        return None
    except Exception as e:
        print(f"Error al obtener último agente: {e}")
        return None

# Ultima ranked 
def ultima_ranked():
    """Mantengo este endpoint adicional para detalles de la última ranked."""
    try:
        url = (
            f"https://api.henrikdev.xyz/valorant/v3/matches/"
            f"{REGION}/{NOMBRE.replace(' ', '%20')}/{TAG}?api_key={API_KEY}"
        )
        res = requests.get(url, timeout=10)
        data = res.json()

        if data.get('status') != 200 or not data.get('data'):
            return Response("No hay partidas recientes", mimetype='text/plain')

        match = data['data'][0]
        mapa = match.get('metadata', {}).get('map')

        personaje = "?"
        k, d, a = 0, 0, 0
        gano = False
        team = None
        for p in match.get('players', {}).get('all_players', []):
            if p.get('name', '').lower() == NOMBRE.lower() and p.get('tag', '').lower() == TAG.lower():
                personaje = p.get('character')
                stats = p.get('stats', {})
                k, d, a = stats.get('kills', 0), stats.get('deaths', 0), stats.get('assists', 0)
                team = p.get('team')
                break

        if team:
            gano = match.get('teams', {}).get(team.lower(), {}).get('has_won', False)

        mmr_url = (
            f"https://api.henrikdev.xyz/valorant/v2/mmr/"
            f"{REGION}/{NOMBRE.replace(' ', '%20')}/{TAG}?api_key={API_KEY}"
        )
        mmr_res = requests.get(mmr_url, timeout=10)
        mmr_data = mmr_res.json().get('data', {}).get('current_data', {})
        delta = mmr_data.get('mmr_change_to_last_game')
        if isinstance(delta, int):
            if delta > 0:
                delta_txt = f"gané {delta} puntos"
            elif delta < 0:
                delta_txt = f"perdí {abs(delta)} puntos"
            else:
                delta_txt = "no cambié de puntos"
        else:
            delta_txt = "cambio de puntos desconocido"

        resultado_txt = "ganamos" if gano else "perdimos"
        mensaje = (
            f"🎀💕 Mi última ranked fue en {mapa} con {personaje}, mi KDA fue {k}/{d}/{a}. "
            f"{resultado_txt} y {delta_txt} 🤗✨"
        )
        return Response(mensaje, mimetype="text/plain")
    except Exception as e:
        return Response(f"Error obteniendo última ranked: {e}", mimetype="text/plain", status=500)
