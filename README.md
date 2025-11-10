# ♥️ API de Nayecute

API en Flask con endpoints para Valorant y Twitch, desplegada en Render. Incluye caché con TTL, sesión HTTP con reintentos, cabeceras de seguridad globales y `Flask-Limiter` para rate limiting.

Guías técnicas:
- Valorant: `common/valorant.md`
- Render y healthcheck: `common/render.md`
- Twitch: `docs/twitch.md`

## 🔹 Endpoints

- `/` → Índice general con accesos a Valorant y Twitch.
- `/valorant` → Índice de endpoints de Valorant.
  - `/valorant/rango` → Rango actual, puntos y cambio de MMR.
  - `/valorant/ultima-ranked` → Última partida (mapa, agente, KDA, resultado).
- `/twitch` → Índice de endpoints de Twitch.
  - `/oauth/callback` → Flujo OAuth implícito para obtener `access_token` (protegido opcionalmente).
  - `/twitch/status` → Valida tokens y configuración.
  - `/twitch/followage?user=<login>` → Desde cuándo `<login>` sigue al canal.
  - `/twitch/token` → Genera app token (protegido).

• Guía completa de Twitch: [docs/twitch.md](./docs/twitch.md)

## 🔹 Valorant (resumen)

- Fuente: API de HenrikDev (`/v2/mmr` y `/v3/matches`).
- Configuración: `valorant/config.py` (`NOMBRE`, `TAG`, `REGION`, `API_KEY`).
- Caché: `SimpleTTLCache` con TTL por defecto de `VALORANT_CACHE_TTL=15s`.
- Sesión HTTP: reintentos con backoff y `keep-alive` mediante `common/http.get_session()`.

Endpoints:
- `/valorant/rango` → rango actual, puntos, cambio de MMR y último agente.
- `/valorant/ultima-ranked` → mapa, agente, KDA, resultado y delta MMR.
• Ejemplos de respuesta y detalles: ver [common/valorant.md](./common/valorant.md)

 
- Los mensajes se pueden modificar.

## 🔹 Variables necesarias

- Generales: `PORT` (Render lo maneja), `API_USER_AGENT` (opcional, UA HTTP).
- Valorant: `API_KEY` (HenrikDev), `VALORANT_CACHE_TTL` (TTL en segundos, por defecto 15).
- Twitch: ver [docs/twitch.md](./docs/twitch.md).

## 🔹 Personalizar para otro jugador

Si quieres mostrar el rango de otro jugador de Valorant, cambia estas variables en el archivo `valorant/config.py`:

```python
#Ejemplo de usuario.
NOMBRE = "Ponssloveless"
TAG    = "8882"
REGION = "na"
```

- regiones disponibles: `na`, `eu`, `kr`, `latam`, `ap`


Luego la API seguirá funcionando igual, pero mostrará los datos del jugador que hayas configurado.  
Se obtiene automáticamente:  
- **Rango y puntos** desde `/v2/mmr/{region}/{name}/{tag}`  
- **Último agente** desde la última partida competitiva usando `/by-puuid/...`

## 🔹 Despliegue en Render (resumen)

- Archivo: `render.yaml` (service `web` con healthcheck en `/healthz`).
- Healthcheck: `/healthz` verifica rápidamente dependencias externas (HenrikDev y doc de Twitch).
- Env vars: `API_KEY`, y las de Twitch si usas esa sección.
- Guía técnica ampliada: `common/render.md`.

## 🚀 Despliegue rápido

- 1  Sube este código a GitHub  
- 2  Conecta el repo a Render  
- 3  Configura la variable `API_KEY` con tu clave de HenrikDev  
- 4  ¡Listo! Tu API estará en línea

## 🌙 Mantener la API despierta

- Render Free apaga servicios si no reciben visitas  
- Usa UptimeRobot para hacer ping cada 5 minutos y mantenerla activa

## 🏁Final

- Hecho con cariño para [naye](https://www.twitch.tv/nayecutee)  ❤️ 
- Usando la API de [henrikdev](https://docs.henrikdev.xyz/)  para traer datos oficiales de Valorant. 

- Puedes usarla libremente y adaptarla para otros jugadores cambiando los datos de arriba (en `valorant/config.py`), siempre que mantengas los créditos a mi repositorio original :).

## 🔒 Seguridad y límites

- Cabeceras globales: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Content-Security-Policy`.
- No cache en endpoints sensibles (OAuth/token): `Cache-Control: no-store`.
- Rate limiting con `Flask-Limiter` por endpoint.

## 🧪 Desarrollo local

- Instalar dependencias: `pip install -r requirements.txt`.
- Arrancar: `python app.py` (en `http://127.0.0.1:5000`).
- Índices: `/`, `/valorant`, `/twitch`.
