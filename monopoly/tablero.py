from .casilla import Casilla


class Tablero:
    """Equivalente a Tablero.java: 12 casillas normales en un circuito cerrado."""

    def __init__(self):
        self.casillas: list[Casilla] = [
            Casilla(f"Casilla {i}", "normal") for i in range(1, 13)
        ]

    def get_casilla(self, posicion: int) -> Casilla:
        return self.casillas[posicion % len(self.casillas)]

    def get_total_casillas(self) -> int:
        return len(self.casillas)
