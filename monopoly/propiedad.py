class Propiedad:
    """Equivalente a Propiedad.java."""

    def __init__(self, nombre: str, precio: int):
        self.nombre = nombre
        self.precio = precio
        self.propietario = None  # type: "Jugador | None"

    def get_nombre(self) -> str:
        return self.nombre

    def get_precio(self) -> int:
        return self.precio

    def get_propietario(self):
        return self.propietario

    def comprar(self, jugador) -> None:
        if self.propietario is None:
            self.propietario = jugador
