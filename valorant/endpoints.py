import os
import requests
import time
import urllib.parse
import logging
from .config import NOMBRE, TAG, REGION, API_KEY
from .rangos_es import Rangos_ES
from common.response import text_response
from common.http import get_session
from common.cache import SimpleTTLCache

_session = get_session()

CACHE_TTL = int(os.environ.get("VALORANT_CACHE_TTL", "15"))
_cache = SimpleTTLCache(default_ttl=CACHE_TTL)

def _quoted(s: str) -> str:
    return urllib.parse.quote(s or "", safe='')

def _format_delta(delta):
    if isinstance(delta, int):
        if delta > 0:
            return f"gané {delta} puntos"
        elif delta < 0:
            return f"perdí {abs(delta)} puntos"
        else:
            return "no cambié de puntos"
    return "cambio de puntos desconocido"

# Cambio de rango.
def rango():
    """Endpoint de rango según tu implementación original usando v2/mmr y current_data."""
    if not (API_KEY or "").strip():
        return text_response("Falta API_KEY.", 500)

    name_q = _quoted(NOMBRE)
    tag_q = _quoted(TAG)
    url = (
        f"https://api.henrikdev.xyz/valorant/v2/mmr/"
        f"{REGION}/{name_q}/{tag_q}?api_key={API_KEY}"
    )

    cache_key = f"rango:{REGION}:{name_q}:{tag_q}"
    cached = _cache.get(cache_key)
    if cached:
        return text_response(cached)

    try:
        res = _session.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()

        current_data = data.get('data', {}).get('current_data')
        if not current_data:
            return text_response("No hay datos actuales disponibles.")

        rango_en = current_data.get('currenttierpatched', 'Desconocido')
        rango_es = Rangos_ES.get(rango_en, rango_en)
        puntos = current_data.get('ranking_in_tier', 'Desconocido')
        delta_txt = _format_delta(current_data.get('mmr_change_to_last_game'))

        ultimo_agente = obtener_ultimo_agente()

        if ultimo_agente:
            respuesta = (
                f"🎀💕 actualmente estoy en {rango_es} con {puntos} puntos 🤗✨, "
                f"mi última partida fue con {ultimo_agente} y {delta_txt}"
            )
        else:
            respuesta = (
                f"🎀💕 actualmente estoy en {rango_es} con {puntos} puntos 🤗✨, "
                f"mi última partida: {delta_txt}"
            )
        _cache.set(cache_key, respuesta)
        return text_response(respuesta)
    except requests.exceptions.HTTPError:
        logging.exception("HTTP error en /valorant/rango")
        return text_response("Servicio de Valorant devolvió error.", 502)
    except requests.exceptions.RequestException:
        logging.exception("Error de red en /valorant/rango")
        return text_response("No se pudo contactar a la API de Valorant.", 502)
    except Exception:
        logging.exception("Error inesperado en /valorant/rango")
        return text_response("Rango no disponible", 500)


def obtener_ultimo_agente():
    """Obtiene el último agente jugado por el usuario"""
    try:
        name_q = _quoted(NOMBRE)
        tag_q = _quoted(TAG)
        url = (
            f"https://api.henrikdev.xyz/valorant/v3/matches/"
            f"{REGION}/{name_q}/{tag_q}?api_key={API_KEY}"
        )
        res = _session.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()

        if data.get('status') == 200 and data.get('data') and len(data['data']) > 0:
            ultima_partida = data['data'][0]

            for jugador in ultima_partida.get('players', {}).get('all_players', []):
                if jugador.get('name', '').lower() == NOMBRE.lower() and jugador.get('tag', '').lower() == TAG.lower():
                    return jugador.get('character')

        return None
    except requests.exceptions.RequestException:
        logging.exception("Error de red al obtener último agente")
        return None
    except Exception:
        logging.exception("Error inesperado al obtener último agente")
        return None

# Ultima ranked 
def ultima_ranked():
    """Mantengo este endpoint adicional para detalles de la última ranked."""
    try:
        name_q = _quoted(NOMBRE)
        tag_q = _quoted(TAG)

        cache_key = f"ultima:{REGION}:{name_q}:{tag_q}"
        cached = _cache.get(cache_key)
        if cached:
            return text_response(cached)

        url = (
            f"https://api.henrikdev.xyz/valorant/v3/matches/"
            f"{REGION}/{name_q}/{tag_q}?api_key={API_KEY}"
        )
        res = _session.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()

        if data.get('status') != 200 or not data.get('data'):
            return text_response("No hay partidas recientes")

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
            f"{REGION}/{name_q}/{tag_q}?api_key={API_KEY}"
        )
        mmr_res = _session.get(mmr_url, timeout=10)
        mmr_res.raise_for_status()
        mmr_data = mmr_res.json().get('data', {}).get('current_data', {})
        delta_txt = _format_delta(mmr_data.get('mmr_change_to_last_game'))

        resultado_txt = "ganamos" if gano else "perdimos"
        mensaje = (
            f"🎀💕 Mi última ranked fue en {mapa} con {personaje}, mi KDA fue {k}/{d}/{a}. "
            f"{resultado_txt} y {delta_txt} 🤗✨"
        )
        _cache.set(cache_key, mensaje)
        return text_response(mensaje)
    except requests.exceptions.HTTPError:
        logging.exception("HTTP error en /valorant/ultima-ranked")
        return text_response("Servicio de Valorant devolvió error.", 502)
    except requests.exceptions.RequestException:
        logging.exception("Error de red en /valorant/ultima-ranked")
        return text_response("No se pudo contactar a la API de Valorant.", 502)
    except Exception as e:
        logging.exception("Error inesperado en /valorant/ultima-ranked")
        return text_response("Error obteniendo última ranked", 500)
