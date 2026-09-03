from .comodin import Comodin
from .propiedad import Propiedad


class Casilla:
    """Equivalente a Casilla.java.

    Java tenia tres constructores sobrecargados (nombre+tipo, nombre+comodin,
    nombre+propiedad). Python no soporta sobrecarga de metodos, asi que se usan
    parametros opcionales con nombre para lograr el mismo efecto.
    """

    def __init__(self, nombre: str, tipo: str = "normal",
                 comodin: Comodin | None = None,
                 propiedad: Propiedad | None = None):
        self.nombre = nombre
        self.comodin = comodin
        self.propiedad = propiedad

        if comodin is not None:
            self.tipo = "comodin"
        elif propiedad is not None:
            self.tipo = "propiedad"
        else:
            self.tipo = tipo

    def get_nombre(self) -> str:
        return self.nombre

    def get_tipo(self) -> str:
        return self.tipo

    def get_comodin(self) -> Comodin | None:
        return self.comodin

    def get_propiedad(self) -> Propiedad | None:
        return self.propiedad
