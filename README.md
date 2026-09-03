# LenguajeDeProgramacion — Monopoly (Python)

Port completo a **Python 3 + Tkinter** del proyecto Java `ProyectoFinalPOO`
(NetBeans + Swing): un mini-Monopoly de 12 casillas con preguntas de
cultura general, comodines, puntaje y exportación de estadísticas a un
`.txt`.

El objetivo fue mantener la **misma arquitectura orientada a objetos** del
original (mismas clases, mismos métodos, mismo flujo de juego) traducida a
Python idiomático, no un rediseño del juego.

## Cómo ejecutarlo

```bash
pip install -r requirements.txt
python main.py
```

Requiere Python 3.10+ (usa sintaxis `str | None`). La reproducción de
música usa `winsound`, que es exclusivo de Windows (ver sección de
limitaciones).

## Estructura del proyecto

```
LenguajeDeProgramacion/
├── main.py                    # Punto de entrada (equivalente a Principal.main)
├── requirements.txt           # Pillow (manejo de imágenes .jpg/.gif en Tkinter)
└── monopoly/
    ├── casilla.py              # Casilla.java
    ├── comodin.py               # Comodin.java
    ├── dado.py                  # Dado.java
    ├── jugador.py                # Jugador.java
    ├── juego.py                  # Juego.java
    ├── pregunta.py                # Pregunta.java (logica, sin UI)
    ├── propiedad.py                # Propiedad.java
    ├── registro_pregunta.py         # RegistroPregunta.java
    ├── tablero.py                    # Tablero.java
    ├── estadisticas.py                # Principal.exportarEstadisticas()
    ├── gui.py                          # Principal.java (JFrame -> Tk)
    └── assets/                          # welcome.png, reglas.jpg, aaaaaa.gif, Sin-título-2.png
```

## Mapeo de clases Java → Python

| Java (`ProyectoFinalPOO/src/proyectofinalpoo`) | Python (`LenguajeDeProgramacion/monopoly`) | Notas |
|---|---|---|
| `Casilla.java` | `casilla.py` | 3 constructores sobrecargados → 1 constructor con parámetros opcionales (`tipo`, `comodin`, `propiedad`). |
| `Comodin.java` | `comodin.py` | Traducción directa (getters → atributos + métodos `get_*` de compatibilidad). |
| `Propiedad.java` | `propiedad.py` | Traducción directa. No se usa actualmente en el flujo de juego (tampoco se usaba en el Java original: la clase existe pero ninguna casilla la instancia). |
| `Dado.java` | `dado.py` | `new Random().nextInt(6)+1` → `random.randint(1, 6)`. |
| `Jugador.java` | `jugador.py` | Traducción directa, incluyendo el `historial` de `RegistroPregunta` para el `.txt`. |
| `Tablero.java` | `tablero.py` | 12 casillas fijas, igual que el original. |
| `Juego.java` | `juego.py` | Traducción directa (turnos, dado, tablero). |
| `RegistroPregunta.java` | `registro_pregunta.py` | `toString()` → `__str__`. |
| `Pregunta.java` | `pregunta.py` | **Se separó la lógica de la UI.** En Java, `hacerPregunta(...)` mezclaba el banco de preguntas, la validación de la respuesta *y* los `JOptionPane`. En Python el banco de preguntas y `evaluar_respuesta()`/`errores_de()` quedan en `pregunta.py` (sin dependencias de interfaz), y los diálogos de Tkinter están en `gui.py::_hacer_pregunta`. Facilita testear la lógica sin abrir ventanas. |
| `Principal.java` (+ `Principal.form`) | `gui.py` | Swing `JFrame`/`JTabbedPane`/`GroupLayout` generado por el editor visual de NetBeans → `tkinter.Tk`/`ttk.Notebook`/`grid`/`pack` escritos a mano. Ver detalle abajo. |
| — | `estadisticas.py` | Se extrajo `exportarEstadisticas()` de `Principal.java` a su propio módulo por responsabilidad única; el formato del `.txt` generado es idéntico. |

## Diferencias notables de implementación (Java Swing vs. Python Tkinter)

- **Layout**: el `.form`/`GroupLayout` de NetBeans (coordenadas y tamaños
  fijos generados por el editor visual) se reemplazó por layouts
  declarativos de Tkinter (`grid` para el tablero de 12 casillas en forma
  de anillo 4×4, `pack`/`place` para el resto). El resultado visual es
  equivalente pero no pixel-a-pixel idéntico.
- **Imágenes**: `Sin-título-2.png` y `welcome.png` se cargan igual que en
  Java (formatos nativos), pero `reglas.jpg` (JPEG) y `aaaaaa.gif`
  (GIF animado) requieren **Pillow**, ya que `tkinter.PhotoImage` por sí
  solo solo soporta GIF/PGM/PPM estáticos y no JPEG. El GIF de la pestaña
  Score se anima manualmente con `PIL.ImageSequence` + `Canvas.after()`,
  algo que Swing/`ImageIcon` sí hace de forma nativa.
- **Diálogos**: `JOptionPane.showInputDialog` / `showMessageDialog` /
  `showConfirmDialog` → `tkinter.simpledialog.askstring` /
  `messagebox.showinfo` / `messagebox.askyesno`.
- **Animación del dado (mejora, no existe en el Java original)**:
  `jbtnTirarActionPerformed` en Java calculaba el número y lo aplicaba de
  forma inmediata y síncrona. En Python, `_tirar()` dispara
  `_animar_dado()`, que durante ~1 segundo (`ANIMACION_DADO_MS`, en pasos
  de `ANIMACION_DADO_INTERVALO_MS` vía `Tk.after`) muestra números
  aleatorios de "relleno" en `jlblNumeroDado` antes de mostrar el
  resultado real (que ya se calculó con `Dado.tirar()` desde el inicio,
  así que no afecta el resultado del juego). El botón "Tirar" se
  deshabilita mientras dura la animación para evitar tiradas dobles; el
  resto de la lógica original (mover ficha, comodín, pregunta, etc.)
  quedó en `_resolver_tirada()`, que se ejecuta recién al terminar la
  animación.
- **Audio**: Java usaba `javax.sound.sampled.Clip` en loop sobre
  `songMonkey.wav`. Python usa el módulo estándar `winsound` (Windows) con
  `SND_LOOP`. **Este archivo de audio nunca existió en el proyecto Java
  fuente** (está referenciado en `Principal.java` pero no en
  `src/proyectofinalpoo/`, ni en `build/classes/`) — por lo tanto el botón
  de música en ambas versiones falla si no se agrega manualmente un
  `songMonkey.wav`; la versión Python simplemente lo indica con un
  mensaje claro en vez de solo hacer `printStackTrace()` en consola.
- **Tipado**: se añadieron *type hints* (`list[Jugador]`, `str | None`,
  etc.) que Java obtiene gratis por ser un lenguaje estáticamente
  tipado; en Python son opcionales pero se agregaron para conservar la
  misma claridad de contratos entre clases.
- **Persistencia (`Estadisticas.txt`)**: el formato de salida es
  intencionalmente idéntico línea por línea al del Java original
  (`FileWriter`/`BufferedWriter` → `open(..., encoding="utf-8")`).

## Comportamientos del original que se conservaron/corrigieron

Para que la comparación fuera honesta, inicialmente se mantuvieron tres
particularidades del Java original en vez de "arreglarlas
silenciosamente". Dos de ellas (sobre los nombres de jugador en Score)
ya se corrigieron a pedido explícito; la tercera se mantiene documentada
como un bug conocido del original.

1. ~~El nombre del jugador en la pestaña Score no es el que se escribió
   en "Jugadores"~~ — **corregido**. En el Java original,
   `Principal.jbtnNombreConfirmaActionPerformed` solo cambiaba el texto
   de las etiquetas `jlblJ1`/`jlblJ2`, nunca el atributo `nombre` del
   objeto `Jugador` (que seguía siendo `"Jugador 1"` / `"Jugador 2"`
   internamente), por lo que el resumen final de Score siempre mostraba
   "Jugador 1" / "Jugador 2" en vez del nombre elegido. Se replicó así
   inicialmente en `gui.py`, pero se corrigió: ahora
   `_confirmar_jugadores` también llama a `Jugador.set_nombre(...)`
   (método nuevo en `jugador.py`, sin equivalente directo en el Java
   original), así que el nombre personalizado se propaga a los diálogos
   y a la pestaña Score. Como efecto colateral, `_actualizar_tablero`
   dejó de identificar jugadores comparando `nombre == "Jugador 1"`
   (ese truco se habría roto al renombrar) y ahora usa la posición del
   jugador en la lista (`idx == 0` → "J1", `idx == 1` → "J2").
2. ~~Las estadísticas de la pestaña Score pueden quedar "cruzadas" con el
   puesto~~ — **corregido**. En el Java original, `jlblResultado1`
   siempre mostraba los puntos/fallos de `j1` y `jlblResultado2` los de
   `j2`, en ese orden fijo, mientras que `jlblPuntos1`/`jlblPuntos2`
   ("1er Puesto"/"2do Puesto") se calculaban por separado comparando
   puntajes — si `j2` tenía más puntos que `j1`, el label de "1er
   Puesto" quedaba arriba de la fila de estadísticas de `j1` (el que en
   realidad perdió). `gui.py::_mostrar_score` ahora calcula primero
   quién es `ganador`/`perdedor` y arma las cuatro etiquetas a partir de
   esos dos, así que la fila de puntos/fallos siempre corresponde al
   mismo jugador que el puesto de arriba.
3. **Al llegar a 100 puntos, `mostrarScore()` no selecciona la pestaña
   Score**: hace `jtblMonopolyPrincipal.setSelectedIndex(3)`, pero el
   índice 3 corresponde a la pestaña "Correccion" (orden de pestañas:
   0 Jugadores, 1 Reglas, 2 Monopoly, 3 Correccion, 4 Score). El propio
   comentario del autor (`// Ajusta con el índice de tu pestaña Score`)
   admite que el índice quedó sin corregir. `gui.py::_mostrar_score`
   reproduce el mismo salto a "Correccion" por fidelidad — para
   corregirlo bastaría con cambiar `self.notebook.select(self._tab_correccion)`
   por `self.notebook.select(self._tab_score)`.

## Verificación realizada

- `python -m py_compile` sobre todos los módulos (sin errores de sintaxis).
- Prueba de humo de la lógica de juego sin UI (mover jugador, ganar
  comodín, responder pregunta, registrar errores, exportar
  `Estadisticas.txt`) vía script suelto — el contenido generado coincide
  con el formato del `Estadisticas.txt` de ejemplo que ya traía el
  proyecto Java.
- Arranque real de `python main.py`: la ventana Tkinter abre sin
  excepciones y carga las 5 pestañas con sus imágenes.
