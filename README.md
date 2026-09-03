# LenguajeDeProgramacion — Monopoly (Python)

Port completo a **Python 3 + Tkinter** del proyecto Java `ProyectoFinalPOO`
(NetBeans + Swing): un mini-Monopoly de 12 casillas con preguntas
educativas de cultura general, comodines, puntaje, soporte para
**2 a 6 jugadores** y exportación de estadísticas a un `.txt`.

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
| `Juego.java` | `juego.py` | **Numero de jugadores generalizado.** El Java original creaba siempre exactamente 2 `Jugador` ("Jugador 1"/"Jugador 2") hardcodeados en el constructor. `Juego.__init__` ahora recibe `num_jugadores` (2 a `MAX_JUGADORES=6`, constantes `MIN_JUGADORES`/`MAX_JUGADORES` nuevas en el módulo) y genera esa cantidad de jugadores; fuera de ese rango lanza `ValueError`. |
| `RegistroPregunta.java` | `registro_pregunta.py` | `toString()` → `__str__`. |
| `Pregunta.java` | `pregunta.py` | **Se separó la lógica de la UI y se amplió el banco de preguntas.** En Java, `hacerPregunta(...)` mezclaba el banco de preguntas, la validación de la respuesta *y* los `JOptionPane`; además solo tenía 10 preguntas. En Python el banco de preguntas y `evaluar_respuesta()`/`errores_de()` quedan en `pregunta.py` (sin dependencias de interfaz, lo que facilita testear la lógica sin abrir ventanas), y los diálogos de Tkinter están en `gui.py::_hacer_pregunta`. El banco de preguntas se amplió de 10 a **40**, agregando matemáticas, ciencia, geografía, historia y lenguaje (todas con respuesta corta y objetiva, en el mismo estilo/dificultad que las 10 originales) para que el aspecto educativo del juego no se sienta repetitivo. |
| `Principal.java` (+ `Principal.form`) | `gui.py` | Swing `JFrame`/`JTabbedPane`/`GroupLayout` generado por el editor visual de NetBeans → `tkinter.Tk`/`ttk.Notebook`/`grid`/`pack` escritos a mano. Ver detalle abajo. |
| — | `estadisticas.py` | Se extrajo `exportarEstadisticas()` de `Principal.java` a su propio módulo por responsabilidad única; el formato del `.txt` generado es idéntico. |

## Diferencias notables de implementación (Java Swing vs. Python Tkinter)

- **2 a 6 jugadores (mejora, no existe en el Java original)**: la
  pestaña "Jugadores" ahora tiene un `ttk.Spinbox` de solo lectura para
  elegir cuántos van a jugar (`MIN_JUGADORES`/`MAX_JUGADORES` en
  `juego.py`); al cambiarlo se regeneran dinámicamente los campos de
  nombre (`gui.py::_regenerar_campos_nombre`) y la tarjeta crece para
  acomodarlos. Al confirmar, `Juego(n)` crea esa cantidad de jugadores.
  Esto obligó a generalizar todo lo que antes asumía "exactamente 2
  jugadores" en `gui.py`: las tarjetas de jugador en la pestaña
  Monopoly se arman en una grilla de hasta 3 columnas
  (`_reconstruir_paneles_jugadores`/`_panel_jugador`), las fichas en el
  tablero usan marcadores "J1".."J6" con un color por jugador
  (`PLAYER_COLORS`, 6 colores en vez de los 2 fijos del original), la
  condición de victoria revisa si **cualquier** jugador llegó a 100
  puntos (antes comparaba `puntosJ1 >= 100 || puntosJ2 >= 100`
  literalmente), y la pestaña Score arma un ranking completo ordenado
  por puntaje (medalla 🥇🥈🥉 para el top 3, puesto numerado para el
  resto) en vez de los dos labels fijos de "1er/2do puesto" que tenía
  el Java original.
- **Diseño visual (mejora, no existe en el Java original)**: el Swing
  original usaba los colores/fuentes por defecto de NetBeans sin un
  tema unificado. `gui.py` define una paleta de colores y tipografía
  centralizadas (`PALETTE`, `FONT_*` al inicio del archivo), un tema
  `ttk` propio para pestañas/botones/entradas (`_configurar_estilos`),
  un ícono de ventana, y tarjetas con esquinas redondeadas dibujadas a
  mano sobre `tk.Canvas` (helper `_rounded_rect`, ya que Tkinter no
  tiene una primitiva nativa para esto) para: el panel de "Jugadores",
  las 12 casillas del tablero (con iconos 🏁/🃏 e insignias de color
  por jugador en vez del sufijo de texto "-J1-J2"), los paneles de
  puntos/comodines y las tarjetas de resultado en "Score". La ventana
  ahora arranca maximizada (`self.state("zoomed")`) para aprovechar
  toda la pantalla en vez de un tamaño fijo que podía quedar chico o
  solapado con otras ventanas.
- **Pestaña Reglas con scroll**: la imagen `reglas.jpg` puede ser más
  alta que el area visible de la ventana. En vez de encogerla hasta que
  el texto se vuelva ilegible (como pasaba antes), ahora se muestra
  dentro de un `Canvas` con barra de scroll vertical (y soporte para la
  rueda del mouse) para poder recorrer todas las reglas completas sin
  importar el tamaño de la ventana.
- **Panel central del tablero compactado**: el logo, las tarjetas de
  jugador, el dado y los botones "Tirar"/"Música" se ajustaron a un
  tamaño más chico y el dado quedó en la misma fila que los botones (no
  apilado arriba), para que entren completos dentro del área central
  del tablero (2×2 casillas) incluso en ventanas más chicas — antes el
  botón "Tirar" podía quedar recortado fuera de la vista.
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
- **Regla del comodín ajustada (cambio de diseño pedido explícitamente,
  no existe en el Java original)**: en el Java original, apenas un
  jugador ganaba el comodín (`jugadorActual.getPosicion() == 5`), la
  condición `jugadorActual.getComodines() > 0` ya era verdadera en la
  misma tirada, así que el mismo turno le mostraba un `JOptionPane`
  aparte preguntando si quería usarlo antes incluso de ver la pregunta.
  En Python, `_resolver_tirada()` separa ambos eventos: si el jugador
  **gana** el comodín en esta tirada, el turno termina ahí mismo (sin
  hacerle pregunta); recién en un turno **posterior**, la pregunta se
  muestra con normalidad. Además, en vez de un dialogo previo de
  sí/no, `_dialogo_pregunta()` reemplaza al simple
  `tkinter.simpledialog.askstring` por una ventana propia (`Toplevel`)
  con un tercer botón **"🃏 Usar Comodín"** integrado junto a OK/Cancelar
  — visible únicamente si el jugador tiene comodines —, que salta la
  pregunta sin sumar puntos ni contar como fallo (a propósito, para que
  el comodín no se pueda usar como una forma gratuita de ganar
  puntaje).
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
   jugador en la lista (`idx == 0` → "J1", `idx == 1` → "J2", ...,
   generalizado a "J{idx+1}" para hasta 6 jugadores).
2. ~~Las estadísticas de la pestaña Score pueden quedar "cruzadas" con el
   puesto~~ — **corregido**. En el Java original, `jlblResultado1`
   siempre mostraba los puntos/fallos de `j1` y `jlblResultado2` los de
   `j2`, en ese orden fijo, mientras que `jlblPuntos1`/`jlblPuntos2`
   ("1er Puesto"/"2do Puesto") se calculaban por separado comparando
   puntajes — si `j2` tenía más puntos que `j1`, el label de "1er
   Puesto" quedaba arriba de la fila de estadísticas de `j1` (el que en
   realidad perdió). La corrección original (calcular `ganador`/
   `perdedor` juntos) luego se generalizó del todo al agregar soporte
   para 2-6 jugadores: `gui.py::_mostrar_score` ahora ordena a **todos**
   los jugadores por puntaje y genera una tarjeta por puesto
   (`_tarjeta_score`), así que cada tarjeta siempre trae su puesto y sus
   estadísticas juntos — ya no hay forma de que queden cruzados.
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
