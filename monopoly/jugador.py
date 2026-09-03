from .registro_pregunta import RegistroPregunta


class Jugador:
    """Equivalente a Jugador.java."""

    def __init__(self, nombre: str):
        self.nombre = nombre
        self.puntos = 0
        self.comodines = 0
        self.posicion = 0  # Inicio
        self.fallos = 0
        self.historial: list[RegistroPregunta] = []

    def mover(self, pasos: int, total_casillas: int) -> None:
        self.posicion = (self.posicion + pasos) % total_casillas

    def get_posicion(self) -> int:
        return self.posicion

    def ganar_comodin(self) -> None:
        self.comodines += 1

    def sumar_puntos(self, puntos: int) -> None:
        self.puntos += puntos

    def get_puntos(self) -> int:
        return self.puntos

    def get_comodines(self) -> int:
        return self.comodines

    def get_nombre(self) -> str:
        return self.nombre

    def set_nombre(self, nombre: str) -> None:
        self.nombre = nombre

    def usar_comodin(self) -> None:
        if self.comodines > 0:
            self.comodines -= 1

    def get_fallos(self) -> int:
        return self.fallos

    def sumar_fallo(self) -> None:
        self.fallos += 1

    def agregar_registro(self, registro: RegistroPregunta) -> None:
        self.historial.append(registro)

    def get_historial(self) -> list[RegistroPregunta]:
        return self.historial
