class RegistroPregunta:
    """Equivalente a RegistroPregunta.java: guarda una pregunta respondida
    para el historial y el reporte de estadisticas."""

    def __init__(self, pregunta: str, respuesta_jugador: str, respuesta_correcta: str):
        self.pregunta = pregunta
        self.respuesta_jugador = respuesta_jugador
        self.respuesta_correcta = respuesta_correcta

    def __str__(self) -> str:
        return (
            f"Pregunta: {self.pregunta}\n"
            f"Respuesta dada: {self.respuesta_jugador}\n"
            f"Respuesta correcta: {self.respuesta_correcta}\n"
        )

    def get_pregunta(self) -> str:
        return self.pregunta

    def get_respuesta_jugador(self) -> str:
        return self.respuesta_jugador

    def get_respuesta_correcta(self) -> str:
        return self.respuesta_correcta
