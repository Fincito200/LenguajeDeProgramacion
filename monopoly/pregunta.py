import random

from .jugador import Jugador
from .registro_pregunta import RegistroPregunta


class Pregunta:
    """Equivalente a Pregunta.java.

    En Java, `hacerPregunta` mezclaba la logica del juego con JOptionPane
    (dialogos de Swing). Aqui esa parte de interfaz se separo: este modulo
    solo contiene el banco de preguntas y la logica de evaluar una
    respuesta; los dialogos de Tkinter viven en gui.py (metodo
    `PrincipalApp._hacer_pregunta`).
    """

    def __init__(self, enunciado: str, respuesta: str):
        self.enunciado = enunciado
        self.respuesta = respuesta

    def get_enunciado(self) -> str:
        return self.enunciado

    def get_respuesta(self) -> str:
        return self.respuesta


PREGUNTAS: list[Pregunta] = [
    Pregunta("¿Capital de Perú?", "Lima"),
    Pregunta("¿2 + 2?", "4"),
    Pregunta("¿Color del cielo?", "Azul"),
    Pregunta("Si tengo 15 manzanas y regalo 7, ¿cuántas me quedan?", "8"),
    Pregunta("¿Cuál es el resultado de 6 × 4?", "24"),
    Pregunta("¿Qué planeta es conocido como \"el planeta rojo\"?", "Marte"),
    Pregunta("¿Cuántas sílabas tiene la palabra \"árbol\"?", "2"),
    Pregunta("¿Qué civilización antigua construyó Machu Picchu?", "Los Incas"),
    Pregunta("¿Qué animal pone huevos más grandes: el elefante o el avestruz?", "Avestruz"),
    Pregunta("¿Qué tipo de palabra es \"correr\": sustantivo o verbo?", "Verbo"),
]


def pregunta_aleatoria() -> Pregunta:
    return random.choice(PREGUNTAS)


def evaluar_respuesta(jugador: Jugador, pregunta: Pregunta, respuesta: str | None) -> bool:
    """Aplica el efecto de responder `respuesta` a `pregunta` sobre `jugador`.

    Replica la logica de puntaje/fallos/historial de Pregunta.hacerPregunta,
    sin la parte de UI. Devuelve True si la respuesta fue correcta.
    """
    respuesta_jugador = respuesta if respuesta is not None else "Sin respuesta"
    correcta = respuesta is not None and respuesta.strip().lower() == pregunta.get_respuesta().lower()

    if correcta:
        jugador.sumar_puntos(10)
    else:
        jugador.sumar_fallo()

    jugador.agregar_registro(
        RegistroPregunta(pregunta.get_enunciado(), respuesta_jugador, pregunta.get_respuesta())
    )
    return correcta


def errores_de(jugador: Jugador) -> str:
    """Reconstruye el bloque de texto de errores para un jugador, igual que
    el StringBuilder `errores` de Pregunta.hacerPregunta."""
    partes = []
    for registro in jugador.get_historial():
        if registro.get_respuesta_jugador().lower() != registro.get_respuesta_correcta().lower():
            partes.append(
                f"Jugador: {jugador.get_nombre()}\n"
                f"Pregunta: {registro.get_pregunta()}\n"
                f"Respuesta dada: {registro.get_respuesta_jugador()}\n"
                f"Respuesta correcta: {registro.get_respuesta_correcta()}\n"
                "===================\n"
            )
    return "".join(partes)
