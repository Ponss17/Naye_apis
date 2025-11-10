# Documentación técnica: Render y Healthcheck

Esta API está desplegada en Render y usa un healthcheck dedicado para detectar degradación externa.

## Archivo `render.yaml`

Servicio web con `python app.py` y healthcheck explícito:

```yaml
services:
  - type: web
    name: naye-api
    runtime: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: python app.py
    healthCheckPath: /healthz
```

• `healthCheckPath` apunta a `/healthz` para validar dependencias externas.

## Endpoint `/healthz`

- Verifica:
  - `https://api.henrikdev.xyz/valorant/version` (HenrikDev)
  - `https://dev.twitch.tv/docs/api/reference` (documentación de Twitch)
- Respuestas:
  - `ok` si ambas están < 500
  - `degraded` con `502` si alguna falla
  - `down` con `502` si hay excepción

## Variables de entorno útiles

- Valorant: `API_KEY`, `VALORANT_CACHE_TTL`
- Twitch: ver `docs/twitch.md` (`TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET`, etc.)
- HTTP: `API_USER_AGENT` (opcional, para personalizar el User-Agent de `requests`)

## Mantener activo en plan Free

- Render apaga servicios si no reciben tráfico.
- Usa UptimeRobot para hacer ping al índice `/` o a `/healthz` cada 5 minutos.

## Notas de seguridad

- Cabeceras seguras globales en `app.py` (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Content-Security-Policy`).
- `Cache-Control: no-store` en endpoints sensibles de Twitch (token y callback).