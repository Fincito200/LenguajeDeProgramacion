import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from monopoly.estadisticas import exportar_estadisticas
from monopoly.juego import Juego
from monopoly.persistencia import cargar_partida, estado_de, guardar_partida, juego_desde
from monopoly.pregunta import evaluar_respuesta


class PartidasTest(unittest.TestCase):
    def test_banco_global_sin_repeticion_ni_reinicio_al_agotarse(self):
        juego = Juego(6)
        vistas = [juego.sacar_pregunta().enunciado for _ in range(40)]
        self.assertEqual(len(set(vistas)), 40)
        self.assertIsNone(juego.sacar_pregunta())
        self.assertTrue(juego.comprobar_final())
        self.assertEqual(juego.motivo_fin, "sin_preguntas")
        self.assertEqual(len(Juego().preguntas_pendientes), 40)

    def test_victoria_se_conserva(self):
        juego = Juego()
        for _ in range(10):
            pregunta = juego.sacar_pregunta()
            evaluar_respuesta(juego.jugadores[0], pregunta, pregunta.respuesta)
        self.assertTrue(juego.comprobar_final())
        restaurada = juego_desde(estado_de(juego))
        self.assertEqual(restaurada.motivo_fin, "100_puntos")
        self.assertIsNone(restaurada.sacar_pregunta())

    def test_guardado_restaura_todo_y_no_repite_preguntas(self):
        for n in range(2, 7):
            with self.subTest(jugadores=n), tempfile.TemporaryDirectory() as carpeta:
                juego = Juego(n)
                vistas = []
                for i in range(6):
                    j = juego.get_jugador_actual()
                    j.set_nombre(f"José {juego.turno_actual}")
                    j.mover(i + 1, 12)
                    p = juego.sacar_pregunta()
                    vistas.append(p.enunciado)
                    if i == 1:
                        j.ganar_comodin()
                        j.usar_comodin()  # La pregunta mostrada se consume al saltar.
                    else:
                        evaluar_respuesta(j, p, p.respuesta if i % 2 else None)
                    juego.siguiente_turno()
                ruta = Path(carpeta) / "partida.json"
                guardar_partida(juego, ruta)
                nueva = cargar_partida(ruta)
                self.assertEqual(estado_de(nueva), estado_de(juego))
                siguientes = [nueva.sacar_pregunta().enunciado for _ in range(34)]
                self.assertFalse(set(vistas) & set(siguientes))
                self.assertEqual(len(set(siguientes)), 34)

    def test_guardado_contiene_su_propio_banco(self):
        original = Juego()
        datos = estado_de(original)
        with patch("monopoly.juego.PREGUNTAS", []):
            restaurada = juego_desde(datos)
        self.assertEqual(len(restaurada.preguntas), 40)
        self.assertEqual(restaurada.preguntas_pendientes, original.preguntas_pendientes)

    def test_recuperacion_de_copia_y_no_reemplazarla_por_archivo_corrupto(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "partida.json"
            juego = Juego()
            guardar_partida(juego, ruta)
            anterior = estado_de(juego)
            juego.siguiente_turno()
            guardar_partida(juego, ruta)
            ruta.write_text("{roto", encoding="utf-8")
            recuperada = cargar_partida(ruta)
            self.assertTrue(recuperada.recuperada_desde_copia)
            self.assertEqual(estado_de(recuperada), anterior)
            copia = ruta.with_suffix(".json.bak").read_bytes()
            guardar_partida(recuperada, ruta)
            self.assertEqual(ruta.with_suffix(".json.bak").read_bytes(), copia)

    def test_copia_se_usa_si_falta_archivo_principal(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "partida.json"
            guardar_partida(Juego(), ruta)
            guardar_partida(cargar_partida(ruta), ruta)
            ruta.unlink()
            self.assertTrue(cargar_partida(ruta).recuperada_desde_copia)

    def test_archivo_invalido_no_se_acepta(self):
        estado = estado_de(Juego())
        variaciones = []
        for campo, valor in [("turno_actual", 20), ("version", 9), ("finalizada", "no"),
                             ("id_partida", "../salida"), ("pendientes", [0] * 40)]:
            cambio = copy.deepcopy(estado)
            cambio[campo] = valor
            variaciones.append(cambio)
        for campo, valor in [("posicion", -1), ("puntos", 1), ("nombre", " "), ("fallos", True)]:
            cambio = copy.deepcopy(estado)
            cambio["jugadores"][0][campo] = valor
            variaciones.append(cambio)
        for cambio in variaciones:
            with self.subTest(cambio=cambio), self.assertRaises(ValueError):
                juego_desde(cambio)

    def test_fallo_de_escritura_no_destruye_guardado_anterior(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "partida.json"
            juego = Juego()
            guardar_partida(juego, ruta)
            anterior = ruta.read_bytes()
            juego.siguiente_turno()
            with patch("monopoly.persistencia.os.replace", side_effect=OSError("disco no escribible")):
                with self.assertRaises(OSError):
                    guardar_partida(juego, ruta)
            self.assertEqual(ruta.read_bytes(), anterior)
            self.assertFalse(list(Path(carpeta).glob("*.tmp")))

    def test_historial_conserva_partidas_y_no_duplica_al_recargar(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta)
            primera, segunda = Juego(), Juego()
            for juego in [primera, segunda]:
                for _ in range(40):
                    juego.sacar_pregunta()
                juego.comprobar_final()
            reporte1 = exportar_estadisticas(primera, directorio=ruta)
            bytes1 = reporte1.read_bytes()
            reporte2 = exportar_estadisticas(segunda, directorio=ruta)
            exportar_estadisticas(juego_desde(estado_de(primera)), directorio=ruta)
            self.assertNotEqual(reporte1, reporte2)
            self.assertEqual(reporte1.read_bytes(), bytes1)
            self.assertEqual(len(list(ruta.glob("[0-9a-f]" * 32 + ".txt"))), 2)

    def test_formato_json_sin_codigo_ejecutable(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "partida.json"
            guardar_partida(Juego(), ruta)
            self.assertEqual(json.loads(ruta.read_text(encoding="utf-8"))["version"], 1)
            ruta.write_text('{"version": 1}', encoding="utf-8")
            with self.assertRaises(ValueError):
                cargar_partida(ruta)


if __name__ == "__main__":
    unittest.main()
