from pathlib import Path

from .juego import Juego
from .persistencia import DIRECTORIO_DATOS, escribir_atomico


def exportar_estadisticas(juego: Juego, ruta: str | Path | None = None,
                          directorio: Path | None = None) -> Path:
    """Conserva un reporte por partida; consultar el ranking no lo duplica."""
    carpeta = Path(directorio) if directorio is not None else DIRECTORIO_DATOS / "resultados"
    destino = Path(ruta) if ruta is not None else carpeta / f"{juego.id_partida}.txt"
    if ruta is None:
        anterior = Path(__file__).resolve().parent.parent / "Estadisticas.txt"
        legado = destino.parent / "resultado_anterior_a_historial.txt"
        if anterior.exists() and not legado.exists():
            escribir_atomico(legado, anterior.read_text(encoding="utf-8"))
        if destino.exists():
            return destino
    lineas = [f"Partida: {juego.id_partida}\n", f"Creada: {juego.creada}\n",
              f"Final: {juego.motivo_fin or 'en curso'}\n\n"]
    for jugador in sorted(juego.get_jugadores(), key=lambda j: j.get_puntos(), reverse=True):
        lineas.extend(["=====================================\n", f"Jugador: {jugador.get_nombre()}\n",
                       f"Puntaje: {jugador.get_puntos()}\n", f"Fallos: {jugador.get_fallos()}\n\n",
                       ">>> Historial de preguntas:\n"])
        lineas.extend(str(registro) + "\n" for registro in jugador.get_historial())
    escribir_atomico(destino, "".join(lineas))
    return destino
