from .juego import Juego


def exportar_estadisticas(juego: Juego, ruta: str = "Estadisticas.txt") -> None:
    """Equivalente a Principal.exportarEstadisticas(): escribe el resumen de
    puntajes, fallos e historial de preguntas de cada jugador."""
    with open(ruta, "w", encoding="utf-8") as archivo:
        for jugador in juego.get_jugadores():
            archivo.write("=====================================\n")
            archivo.write(f"Jugador: {jugador.get_nombre()}\n")
            archivo.write(f"Puntaje: {jugador.get_puntos()}\n")
            archivo.write(f"Fallos: {jugador.get_fallos()}\n\n")
            archivo.write(">>> Historial de preguntas:\n")

            for registro in jugador.get_historial():
                archivo.write(str(registro) + "\n")
