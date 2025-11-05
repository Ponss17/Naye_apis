from flask import Response


def valorant_index():
    mensaje = (
        "Endpoints de Valorant:\n\n"
        "/valorant/rango\n"
        "    Muestra el rango actual, puntos y cambio de MMR\n\n"
        "/valorant/ultima-ranked\n"
        "    Detalles de la última partida ranked (mapa, agente, KDA y resultado)\n"
    )
    return Response(mensaje, mimetype="text/plain")