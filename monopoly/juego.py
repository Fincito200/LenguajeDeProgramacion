from .casilla import Casilla
from .dado import Dado
from .jugador import Jugador
from .tablero import Tablero


class Juego:
    """Equivalente a Juego.java: coordina jugadores, dado y tablero."""

    def __init__(self):
        self.jugadores: list[Jugador] = [Jugador("Jugador 1"), Jugador("Jugador 2")]
        self.turno_actual = 0
        self.dado = Dado()
        self.tablero = Tablero()

    def get_casilla_actual(self, jugador: Jugador) -> Casilla:
        return self.tablero.get_casilla(jugador.get_posicion())

    def get_jugador_actual(self) -> Jugador:
        return self.jugadores[self.turno_actual]

    def siguiente_turno(self) -> None:
        self.turno_actual = (self.turno_actual + 1) % len(self.jugadores)

    def get_dado(self) -> Dado:
        return self.dado

    def get_jugadores(self) -> list[Jugador]:
        return self.jugadores
