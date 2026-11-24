# Monopoly educativo en Python

Aplicación de escritorio adaptada del proyecto Java ProyectoFinalPOO. Usa programación orientada a objetos, Tkinter para la interfaz, Pillow para las imágenes y pygame-ce para el audio.

## Ejecutar

Requiere Python 3.10 o posterior y Tkinter. En Linux puede ser necesario instalar Tkinter desde el gestor del sistema.

```console
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

En Windows, después de preparar el entorno también puedes abrir `Iniciar_Monopoly.bat` con doble clic. En macOS y Linux, los ejecutables del entorno están en `.venv/bin/`.

Para comparar con Java, abre `Iniciar_Monopoly_Java.bat`. Requiere el proyecto original `ProyectoFinalPOO` en una carpeta hermana de `LenguajeDeProgramacion` y un JDK con `javac` disponible en PATH o JAVA_HOME. El acceso compila y ejecuta las fuentes originales sin modificarlas; conserva sus recursos y comportamiento para la exposición.

## Reglas actuales

- Entre dos y seis jugadores recorren doce casillas con un dado de 1 a 6.
- Una respuesta correcta suma 10 puntos; una incorrecta o cancelada añade un fallo.
- Caer en la casilla 6 entrega un comodín y termina el turno sin pregunta. En otro turno, usarlo permite saltar una pregunta sin sumar puntos ni fallos.
- Las cuarenta preguntas se barajan una vez por partida. Una pregunta mostrada queda consumida para todos los jugadores, incluso si se cancela o se usa un comodín.
- La partida acaba al alcanzar 100 puntos o al agotar las preguntas. En este último caso se clasifica por el puntaje obtenido; si hay empate se conserva el orden de los participantes.
- El final abre Score y bloquea nuevas tiradas. Corrección muestra los fallos sin duplicarlos.

## Guardar y continuar

La aplicación guarda automáticamente al confirmar los participantes, al terminar cada turno y al cerrar. No guarda estados intermedios de una animación o pregunta: hay que terminar el turno para cerrar o guardar.

En la pantalla inicial, **Continuar partida guardada** abre `datos/partida.json`. El menú **Partida** también ofrece guardar, guardar como, abrir otro archivo, comenzar otra partida y consultar el historial.

El JSON contiene los nombres, puntos, posiciones, comodines, fallos, respuestas, turno, condición final y el banco de preguntas con su orden pendiente. La selección no se reinicia al cargar. Los guardados se escriben de forma atómica y conservan una copia anterior `.json.bak`; si se recupera esa copia, la interfaz lo avisa. Un archivo inválido no sustituye el estado del juego en pantalla.

Los datos se resuelven desde la carpeta del proyecto, aunque se inicie desde otro directorio. `Guardar como` permite elegir otro archivo; después se continúa trabajando sobre ese destino. Para abrir ese destino en otra sesión se usa **Abrir partida**.

## Historial de resultados

Cada partida terminada produce un archivo independiente `datos/resultados/<id_partida>.txt`. Reabrir un resultado no crea duplicados ni modifica los anteriores. El menú **Historial de resultados** permite consultarlos dentro del juego.

Si existe un `Estadisticas.txt` de la versión anterior, su contenido se conserva una vez como `resultado_anterior_a_historial.txt`. El archivo original no se borra. La carpeta `datos/` está excluida de Git.

## Música

El botón Música inicia o detiene `monopoly/assets/songMonkey.wav` en bucle al 25 % de volumen. Al cerrar se detiene y se libera el dispositivo.

El WAV incluido se convirtió del archivo proporcionado por el usuario, `Musica que ocupa spreen de fondo 3_160k.mp3`, con duración aproximada de 218,48 segundos, PCM de 16 bits, estéreo y 44 100 Hz. No se afirma que sea el audio original del proyecto Java. El MP3 fuente se conserva en assets.

pygame-ce/SDL sustituye a winsound y permite utilizar el mismo código en Windows, macOS y Linux si el dispositivo y sus controladores están disponibles. Se comprobó reproducción real y parada en Windows; macOS y Linux no se ejecutaron en esta revisión. La procedencia del archivo es la aportada por el usuario y no se atribuye una licencia a la música.

## Organización

- `juego.py`: jugadores, turnos, banco sin repetición y condición final.
- `jugador.py`, `tablero.py`, `casilla.py`, `dado.py`: objetos del juego.
- `pregunta.py` y `registro_pregunta.py`: preguntas, evaluación e historial.
- `persistencia.py`: validación, recuperación y guardado JSON.
- `estadisticas.py`: reportes independientes por partida.
- `audio.py`: reproducción mediante pygame-ce.
- `gui.py`: ventanas, diálogos y menús.

`Propiedad` existe por compatibilidad con el proyecto Java; no hay compra ni alquiler integrados en la partida.

## Validación

```console
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Las pruebas cubren preguntas únicas, agotamiento, victoria, guardado y carga para dos a seis jugadores, conservación del banco, recuperación de archivos dañados, rechazo de datos inválidos, fallo de escritura e historial sin sobrescrituras.

El 24 de noviembre de 2026 se completó una partida en la interfaz real de Windows: 22 preguntas distintas, un comodín usado, errores y cancelación registrados, cierre y continuación durante la partida, ranking final con 100 y 80 puntos, bloqueo del dado y consulta del resultado en el historial. Las pruebas usaron una carpeta de datos separada.

## Cambios frente a Java

Java utiliza Swing y dos jugadores fijos; Python utiliza Tkinter y permite de dos a seis. El banco creció de 10 a 40 preguntas y la evaluación se separó de la interfaz. Se añadieron animación, clasificación coherente, preguntas sin repetición, guardados y recuperación, historial de resultados y reproducción con SDL. Son mejoras de esta implementación, no limitaciones del lenguaje Java.
