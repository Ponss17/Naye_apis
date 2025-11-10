# Documentación técnica: Valorant

Esta API expone dos endpoints de Valorant apoyándose en HenrikDev y en utilidades comunes de caché y sesión HTTP.

## Endpoints

### `/valorant/rango`
- Fuente: `GET https://api.henrikdev.xyz/valorant/v2/mmr/{REGION}/{NOMBRE}/{TAG}?api_key=...`
- Devuelve rango actual (traducido a ES), puntos y delta de MMR respecto a la última partida.
- Incluye el último agente jugado consultando el endpoint de partidas.

Ejemplos:
```python
🎀💕 Actualmente estoy en Diamante 2 con 53 puntos 🤗✨. Mi última ranked fue con Jett, gané 18 puntos nayecuTeAmor
```
```python
🎀💕 Actualmente estoy en Oro 1 con 45 puntos 🤗✨. Mi última ranked fue con Phoenix, perdí 12 puntos 😢
```
```python
🎀💕 Actualmente estoy en Platino 3 con 0 puntos 🤗✨. Mi última ranked fue con Sage, no cambié de puntos 😐
```

### `/valorant/ultima-ranked`
- Fuente: `GET https://api.henrikdev.xyz/valorant/v3/matches/{REGION}/{NOMBRE}/{TAG}?api_key=...`
- Devuelve mapa, agente, KDA (kills/deaths/assists), si ganó/perdió y el delta de MMR de la última partida.

Ejemplos:
```python
🎀💕 Mi última ranked fue en Ascent con Jett, mi KDA fue 15/7/3. ganamos y gané 18 puntos nayecuTeAmor 🤗✨
```
```python
🎀💕 Mi última ranked fue en Haven con Sage, mi KDA fue 8/10/12. perdimos y perdí 14 puntos 😢
```
```python
🎀💕 Mi última ranked fue en Split con Omen, mi KDA fue 11/9/5. empatamos y no cambié de puntos 😐
```

 

## Configuración

Editar `valorant/config.py`:

```python
NOMBRE = "Ponssloveless"
TAG    = "8882"
REGION = "na"  # na, eu, kr, latam, ap
API_KEY = os.environ.get("API_KEY", "")
```

• Requiere `API_KEY` de HenrikDev en entorno.

## Caché y sesión HTTP

- Caché TTL: `common.cache.SimpleTTLCache` con TTL configurable vía `VALORANT_CACHE_TTL` (por defecto 15 segundos).
- Sesión HTTP: `common.http.get_session()` añade reintentos con backoff y `keep-alive`.
- Claves de caché:
  - `rango:{REGION}:{NOMBRE}:{TAG}`
  - `ultima:{REGION}:{NOMBRE}:{TAG}`

## Manejo de errores

- Errores de red y HTTP se capturan y devuelven como `502` con mensajes legibles.
- Errores inesperados devuelven `500` con un texto sencillo.

## Personalización y notas

- Traducciones de rango: `valorant/rangos_es.py`.
- Mensajes se formatean en español y se pueden ajustar en `valorant/endpoints.py`.
- Si cambias jugador/region, no necesitas modificar código de endpoints; sólo `valorant/config.py`.