# ♥️ API de Nayecute

Esta es una API en Flask que muestra el **rango actual de Valorant** de [Naye](https://www.twitch.tv/nayecutee) usando la API de [henrikdev](https://docs.henrikdev.xyz/).  
Está hosteada en Render y puede mantenerse despierta con UptimeRobot.

## 🔹 Endpoints

- `/` → Muestra un mensaje de bienvenida con la lista de endpoints disponibles.
- `/valorant` → Índice de endpoints específicos de Valorant.
 - `/twitch` → Índice de endpoints de Twitch.

Nota sobre configuración de Twitch
- Si quieres ver cómo configurar y usar Twitch (OAuth, tokens y endpoints), revisa [docs/twitch.md](./docs/twitch.md).

## 🔹 Valorant

- `/rango` → Devuelve el **rango actual, puntos, cambio de MMR y último agente jugado**.
- `/ultima-ranked` → Devuelve detalles de la **última partida ranked** (mapa, agente, KDA y resultado).

### Ejemplos de respuesta:

#### Endpoint `/valorant/rango`:

```python
🎀💕 Actualmente estoy en Diamante 2 con 53 puntos 🤗✨. Mi última ranked fue con Jett, gané 18 puntos nayecuTeAmor
```
```python
🎀💕 Actualmente estoy en Oro 1 con 45 puntos 🤗✨. Mi última ranked fue con Phoenix, perdí 12 puntos 😢
```
```python
🎀💕 Actualmente estoy en Platino 3 con 0 puntos 🤗✨. Mi última ranked fue con Sage, no cambié de puntos 😐
```

#### Endpoint `/valorant/ultima-ranked`:
```python
🎀💕 Mi última ranked fue en Ascent con Jett, mi KDA fue 15/7/3. ganamos y gané 18 puntos nayecuTeAmor 🤗✨
```
```python
🎀💕 Mi última ranked fue en Haven con Sage, mi KDA fue 8/10/12. perdimos y perdí 14 puntos 😢
```
```python
🎀💕 Mi última ranked fue en Split con Omen, mi KDA fue 11/9/5. empatamos y no cambié de puntos 😐
```

## 🔹 Variables necesarias

- `API_KEY` → Tu API key de HenrikDev  
- `PORT` → Render lo maneja automáticamente

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

## 🔹 Despliegue en Render

- `render.yaml` → Configuración automática para Render  
- Guía completa: [DEPLOY_RENDER.md](./DEPLOY_RENDER.md)

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