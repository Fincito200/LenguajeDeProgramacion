from .casilla import Casilla
from .dado import Dado
from .jugador import Jugador
from .tablero import Tablero

# El Java original tenia el numero de jugadores fijo en 2 (hardcodeado
# en el constructor de Juego). Aqui se generaliza a un rango
# configurable de 2 a 6 jugadores.
MIN_JUGADORES = 2
MAX_JUGADORES = 6


class Juego:
    """Equivalente a Juego.java: coordina jugadores, dado y tablero."""

    def __init__(self, num_jugadores: int = 2):
        if not (MIN_JUGADORES <= num_jugadores <= MAX_JUGADORES):
            raise ValueError(
                f"El numero de jugadores debe estar entre {MIN_JUGADORES} y {MAX_JUGADORES}."
            )
        self.jugadores: list[Jugador] = [
            Jugador(f"Jugador {i}") for i in range(1, num_jugadores + 1)
        ]
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
