"""Guardados JSON validados y escritura atómica, sin ejecutar datos del archivo."""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from uuid import UUID

from .juego import Juego, MAX_JUGADORES, MIN_JUGADORES
from .pregunta import Pregunta
from .registro_pregunta import RegistroPregunta

DIRECTORIO_DATOS = Path(__file__).resolve().parent.parent / "datos"
RUTA_PARTIDA = DIRECTORIO_DATOS / "partida.json"


def escribir_atomico(ruta: Path, texto: str) -> None:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=ruta.parent,
                                         prefix=f".{ruta.name}.", suffix=".tmp", delete=False) as archivo:
            temporal = Path(archivo.name)
            archivo.write(texto)
            archivo.flush()
            os.fsync(archivo.fileno())
        os.replace(temporal, ruta)
    finally:
        if temporal is not None and temporal.exists():
            temporal.unlink()


def estado_de(juego: Juego) -> dict:
    return {
        "version": 1,
        "id_partida": juego.id_partida,
        "creada": juego.creada,
        "turno_actual": juego.turno_actual,
        "finalizada": juego.finalizada,
        "motivo_fin": juego.motivo_fin,
        "preguntas": [{"enunciado": p.enunciado, "respuesta": p.respuesta} for p in juego.preguntas],
        "pendientes": list(juego.preguntas_pendientes),
        "mostradas": list(juego.preguntas_mostradas),
        "jugadores": [{
            "nombre": j.nombre, "puntos": j.puntos, "posicion": j.posicion,
            "comodines": j.comodines, "fallos": j.fallos,
            "historial": [{"pregunta": r.pregunta, "respuesta_jugador": r.respuesta_jugador,
                           "respuesta_correcta": r.respuesta_correcta} for r in j.historial],
        } for j in juego.jugadores],
    }


def _entero(valor, minimo: int, maximo: int) -> int:
    if type(valor) is not int or not minimo <= valor <= maximo:
        raise ValueError("Hay un número fuera de rango en el guardado.")
    return valor


def _texto(valor, maximo: int = 10000) -> str:
    if not isinstance(valor, str) or len(valor) > maximo:
        raise ValueError("Hay un texto inválido en el guardado.")
    return valor


def juego_desde(datos: dict) -> Juego:
    """Valida el documento completo antes de entregar un estado a la interfaz."""
    try:
        if not isinstance(datos, dict) or type(datos["version"]) is not int or datos["version"] != 1:
            raise ValueError("Versión de guardado no compatible.")
        ident = UUID(_texto(datos["id_partida"], 32))
        creada = datetime.fromisoformat(_texto(datos["creada"], 64))
        if creada.tzinfo is None:
            raise ValueError("La fecha del guardado no tiene zona horaria.")
        jugadores = datos["jugadores"]
        if not isinstance(jugadores, list):
            raise ValueError("Lista de jugadores inválida.")
        _entero(len(jugadores), MIN_JUGADORES, MAX_JUGADORES)
        banco = datos["preguntas"]
        if not isinstance(banco, list) or not 1 <= len(banco) <= 10000:
            raise ValueError("Banco de preguntas inválido.")
        preguntas = [Pregunta(_texto(p["enunciado"]), _texto(p["respuesta"])) for p in banco]
        if any(not p.enunciado.strip() or not p.respuesta.strip() for p in preguntas):
            raise ValueError("Las preguntas no pueden estar vacías.")
        if len({p.enunciado for p in preguntas}) != len(preguntas):
            raise ValueError("El banco contiene preguntas duplicadas.")
        pendientes, mostradas = datos["pendientes"], datos["mostradas"]
        if not isinstance(pendientes, list) or not isinstance(mostradas, list):
            raise ValueError("Estado de preguntas inválido.")
        indices = pendientes + mostradas
        for indice in indices:
            _entero(indice, 0, len(preguntas) - 1)
        if len(indices) != len(preguntas) or set(indices) != set(range(len(preguntas))):
            raise ValueError("Hay preguntas repetidas o faltantes en el guardado.")
        juego = Juego(len(jugadores))
        juego.id_partida = ident.hex
        juego.creada = creada.isoformat()
        juego.turno_actual = _entero(datos["turno_actual"], 0, len(jugadores) - 1)
        juego.preguntas = preguntas
        juego.preguntas_pendientes = list(pendientes)
        juego.preguntas_mostradas = list(mostradas)
        for j, valor in zip(juego.jugadores, jugadores):
            j.nombre = _texto(valor["nombre"], 200)
            if not j.nombre.strip():
                raise ValueError("Un jugador no tiene nombre.")
            j.puntos = _entero(valor["puntos"], 0, 100)
            if j.puntos % 10:
                raise ValueError("El puntaje debe ser múltiplo de 10.")
            j.posicion = _entero(valor["posicion"], 0, juego.tablero.get_total_casillas() - 1)
            j.comodines = _entero(valor["comodines"], 0, 1000000)
            j.fallos = _entero(valor["fallos"], 0, len(preguntas))
            historial = valor["historial"]
            if not isinstance(historial, list) or len(historial) > len(preguntas):
                raise ValueError("Historial de preguntas inválido.")
            j.historial = [RegistroPregunta(_texto(r["pregunta"]), _texto(r["respuesta_jugador"]),
                                          _texto(r["respuesta_correcta"])) for r in historial]
        registradas = [r.pregunta for j in juego.jugadores for r in j.historial]
        if len(registradas) != len(set(registradas)) or not set(registradas) <= {preguntas[i].enunciado for i in mostradas}:
            raise ValueError("El historial no coincide con las preguntas mostradas.")
        finalizada = datos["finalizada"]
        if type(finalizada) is not bool:
            raise ValueError("Estado final inválido.")
        motivo = "100_puntos" if any(j.puntos >= 100 for j in juego.jugadores) else ("sin_preguntas" if not pendientes else "")
        if finalizada != bool(motivo) or datos["motivo_fin"] != motivo:
            raise ValueError("La condición de final de partida es inconsistente.")
        juego.finalizada = finalizada
        juego.motivo_fin = motivo
        return juego
    except (KeyError, TypeError, AttributeError, OverflowError) as error:
        raise ValueError("El archivo no contiene una partida válida.") from error


def guardar_partida(juego: Juego, ruta: Path = RUTA_PARTIDA) -> Path:
    ruta = Path(ruta)
    datos = estado_de(juego)
    juego_desde(datos)
    if ruta.exists():
        try:
            anterior = ruta.read_text(encoding="utf-8")
            juego_desde(json.loads(anterior))
        except (ValueError, OSError):
            pass
        else:
            escribir_atomico(ruta.with_suffix(ruta.suffix + ".bak"), anterior)
    escribir_atomico(ruta, json.dumps(datos, ensure_ascii=False, indent=2))
    return ruta


def cargar_partida(ruta: Path = RUTA_PARTIDA) -> Juego:
    ruta = Path(ruta)
    errores = []
    for candidata in [ruta, ruta.with_suffix(ruta.suffix + ".bak")]:
        try:
            if candidata.stat().st_size > 10_000_000:
                raise ValueError("El guardado supera el tamaño permitido.")
            juego = juego_desde(json.loads(candidata.read_text(encoding="utf-8")))
            juego.recuperada_desde_copia = candidata != ruta
            return juego
        except (OSError, ValueError, UnicodeError) as error:
            errores.append(error)
    raise ValueError("No se pudo abrir una partida válida ni su copia de recuperación.") from errores[0]
