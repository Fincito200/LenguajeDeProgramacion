import random


class Dado:
    """Equivalente a Dado.java (random.nextInt(6) + 1 -> random.randint(1, 6))."""

    def tirar(self) -> int:
        return random.randint(1, 6)
