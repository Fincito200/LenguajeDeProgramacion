class Comodin:
    """Equivalente a Comodin.java."""

    def __init__(self, nombre: str, efecto: str):
        self.nombre = nombre
        self.efecto = efecto

    def get_nombre(self) -> str:
        return self.nombre

    def get_efecto(self) -> str:
        return self.efecto
