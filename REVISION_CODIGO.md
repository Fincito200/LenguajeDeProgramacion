# Revisión de código — 6 de noviembre de 2026

Proyecto: C:\Users\Usuario\Desktop\POO-LP\LenguajeDeProgramacion
Alcance inicial: revisión estática y pruebas focalizadas. Los hallazgos históricos se conservan abajo; los tres fueron corregidos el 6 de noviembre de 2026.

## Hallazgos

1. [P1] La partida no termina al alcanzar 100 puntos.
   Ubicación: monopoly/gui.py:708 y 734–737.
   El botón vuelve a habilitarse antes de resolver la tirada. Alcanzar 100 puntos solo muestra el ranking; después se avanza al siguiente turno, sin estado de partida terminada ni bloqueo del botón. Se puede volver al tablero, seguir sumando y exportar nuevos resultados.
   Prueba: un jugador con 90 puntos llegó a 100; una resolución posterior dio 10 puntos al rival y volvió a invocar el ranking.
   Corrección propuesta: conservar el botón deshabilitado durante la resolución y, tras la victoria, marcar la partida como finalizada y rechazar nuevas tiradas. Rehabilitarlo solo si la partida continúa.

2. [P2] Corrección vuelve a insertar todos los errores anteriores.
   Ubicación: monopoly/gui.py:759 y 570–575.
   Cada respuesta agrega errores_de(jugador), que reconstruye el historial completo de fallos. Un error seguido de un acierto produce dos bloques del mismo error. Con sucesivos fallos el texto crece por duplicación.
   Prueba: 1 fallo real seguido de 1 acierto produjo 2 entradas de corrección.
   Corrección propuesta: insertar únicamente el fallo de la respuesta actual, o regenerar el panel completo a partir de todos los jugadores en vez de anexarlo.

3. [P2] La validación y el reporte discrepan al comparar respuestas con espacios.
   Ubicación: monopoly/pregunta.py:94 y 112.
   evaluar_respuesta usa strip().lower(); errores_de solo lower(). Por ello « Lima » obtiene 10 puntos y cero fallos, pero figura en Corrección como incorrecta.
   Prueba: evaluar_respuesta devolvió True, puntos=10, fallos=0; errores_de devolvió un bloque de error.
   Corrección propuesta: compartir una misma normalización en ambos lugares, o guardar explícitamente el resultado de la evaluación en el registro.

## Validación y límites

- Todos los archivos Python pasaron análisis de sintaxis mediante ast.parse.
- Se ejecutó la lógica de Jugador, Juego y Pregunta con Python 3.14 local.
- Para los métodos de GUI se extrajeron sus cuerpos originales mediante AST y se usaron objetos y diálogos simulados, sin abrir ventanas. Esto verifica los flujos indicados, no la interfaz gráfica completa.
- La importación completa de GUI quedó bloqueada por la ausencia de Pillow (No module named PIL). Pillow está declarado en requirements.txt; no se instalaron dependencias.
- El salto a Corrección en vez de Score está expresamente documentado en README.md como conservación del comportamiento original; no se presenta aquí como error accidental.
- La exportación usa una ruta relativa, sobrescribe Estadisticas.txt y no maneja errores de escritura en la GUI. Conviene revisarlo si se requiere conservar partidas o tolerar destinos no escribibles; no se reprodujo un fallo de permisos real.
- No se modificó código fuente ni el archivo de estadísticas existente.

## Correcciones aplicadas

- Fin de partida: _partida_finalizada impide tirar y resolver turnos después de ganar. El botón permanece deshabilitado hasta completar cada turno; al ganar no se avanza al siguiente jugador.
- Corrección: el panel se reconstruye desde el historial de todos los jugadores, sin anexar errores ya mostrados. Los errores se agrupan por jugador.
- Respuestas: evaluación y reporte comparten _normalizar_respuesta, que elimina espacios exteriores e ignora mayúsculas.

Validación posterior: pruebas de lógica con victorias de 2 a 6 jugadores, bloqueo de tiradas posteriores, un solo ranking por partida, avance normal de turno, obtención y uso de comodines, cancelaciones, correcciones de ambos jugadores sin duplicación y respuestas con espacios/tabulaciones/mayúsculas. Todas pasaron. También pasaron el análisis de sintaxis de todos los módulos y git diff --check. Los métodos de GUI se ejecutaron desde sus cuerpos originales con controles simulados; no se abrió la ventana completa por ausencia de Pillow en el intérprete disponible.
