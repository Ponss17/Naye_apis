# Guía de integración con Twitch

Esta guía explica cómo configurar la aplicación en Twitch, obtener el token de usuario con el flujo **Implicit Grant** y usar los endpoints disponibles.

## Variables de entorno en Render

Define estas variables en tu servicio de Render (Settings → Environment):

- `TWITCH_CLIENT_ID`: Client ID de tu app en Twitch.
- `TWITCH_CLIENT_SECRET`: Client Secret de tu app (para el token de aplicación).
- `TWITCH_CHANNEL_LOGIN`: Login del canal (por ejemplo `ponss17`).
- `TWITCH_USER_TOKEN`: Access token de usuario (obtenido vía implicit grant).
- `TWITCH_ENDPOINT_PASSWORD`: Clave para proteger `/twitch/token` y `/oauth/callback`.

> Nota: Si `TWITCH_ENDPOINT_PASSWORD` no está definida, los endpoints protegidos se comportan como abiertos.

## Redirect URIs en Twitch Developer Console

En https://dev.twitch.tv/console/apps, edita tu aplicación y registra ambos Redirect URLs:

- Producción: `https://<tu-dominio-render>.onrender.com/oauth/callback`
- Local: `http://localhost:5000/oauth/callback`

Ambos deben estar dados de alta para poder iniciar el flujo desde producción o local.

## Obtener el token de usuario (Implicit Grant)

1. Abre `https://<tu-dominio-render>.onrender.com/oauth/callback`.
2. Si tienes clave de endpoint, ingrésala (o pasa `?password=<TU_CLAVE>`).
3. Verifica que “Redirect URI actual” muestre el URL de producción con `https`.
4. Haz clic en “Autorizar con Twitch (implicit grant)”.
5. Al volver al callback, verás el `access_token` en la página; copia ese valor.
6. Guarda el token como `TWITCH_USER_TOKEN` en Render.

### Validar el token

- Abre `/twitch/status` para validar el token de app y el de usuario.
- Verifica que el scope `moderator:read:followers` esté presente.

## Endpoints disponibles

- `/oauth/callback`
  - Página para iniciar y completar el flujo OAuth implícito.
  - Protegida por contraseña si defines `TWITCH_ENDPOINT_PASSWORD`.

- `/twitch/status`
  - Muestra configuración y valida tokens de app y usuario.

- `/twitch/followage?user=<login>`
  - Retorna desde cuándo `<login>` sigue al canal configurado.

- `/twitch/token`
  - Genera un **app access token** (client credentials).
  - Protegido: requiere `?password=<clave>` o header `X-Endpoint-Password: <clave>`.

## Troubleshooting

- Si Twitch muestra advertencia de salir a `http://localhost:5000`, verifica que estás iniciando el flujo desde producción (`https://.../oauth/callback`) y que el “Redirect URI actual” es `https`.
- Asegúrate de que los Redirect URIs coincidan exactamente con la URL mostrada.
- Si `status` indica que faltan credenciales, revisa variables de entorno en Render.