"""Interfaz grafica del juego, equivalente a Principal.java (Swing -> Tkinter).

Java usaba NetBeans GUI Builder (GroupLayout/AbsoluteLayout) para un
JFrame con un JTabbedPane de 5 pestañas: Jugadores, Reglas, Monopoly,
Correccion y Score. Aqui se recrea la misma estructura con
tkinter.ttk.Notebook, usando grid/pack en vez de GroupLayout.
"""

from __future__ import annotations

import random
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

from PIL import Image, ImageSequence, ImageTk

from .estadisticas import exportar_estadisticas
from .juego import Juego
from .pregunta import errores_de, evaluar_respuesta, pregunta_aleatoria

ASSETS_DIR = Path(__file__).resolve().parent / "assets"

# Nombres por defecto de las 12 casillas tal como quedan luego de
# actualizarTablero() en el Java original (que sobreescribe cualquier
# nombre inicial con "Inicio" / "Casilla N").
NOMBRES_CASILLAS = ["Inicio"] + [f"Casilla {i}" for i in range(2, 13)]

# Posiciones (fila, columna) de una grilla 4x4 que dibuja las 12 casillas
# formando el circuito de un tablero de Monopoly, dejando el centro libre
# para el dado, los botones y los paneles de jugadores.
POSICIONES_TABLERO = [
    (0, 0), (0, 1), (0, 2), (0, 3),
    (1, 3), (2, 3), (3, 3), (3, 2),
    (3, 1), (3, 0), (2, 0), (1, 0),
]


class PrincipalApp(tk.Tk):
    """Equivalente a la clase Principal (JFrame) del proyecto Java."""

    def __init__(self):
        super().__init__()
        self.title("Monopoly")
        self.minsize(1100, 650)
        self.geometry("1200x680")
        self.resizable(False, False)

        self.juego = Juego()
        self.casilla_labels: list[tk.Label] = []
        self._reproduciendo = False
        self._imagenes: list[ImageTk.PhotoImage] = []  # evita garbage-collect

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=6, pady=6)

        self._tab_jugadores = ttk.Frame(self.notebook)
        self._tab_reglas = ttk.Frame(self.notebook)
        self._tab_monopoly = ttk.Frame(self.notebook)
        self._tab_correccion = ttk.Frame(self.notebook)
        self._tab_score = ttk.Frame(self.notebook)

        self.notebook.add(self._tab_jugadores, text="Jugadores")
        self.notebook.add(self._tab_reglas, text="Reglas")
        self.notebook.add(self._tab_monopoly, text="Monopoly")
        self.notebook.add(self._tab_correccion, text="Correccion")
        self.notebook.add(self._tab_score, text="Score")

        self._build_tab_jugadores()
        self._build_tab_reglas()
        self._build_tab_monopoly()
        self._build_tab_correccion()
        self._build_tab_score()

        self._actualizar_tablero()
        self.eval("tk::PlaceWindow . center")

    # ------------------------------------------------------------------
    # Tab 1: Jugadores (jpanelIntroduccion)
    # ------------------------------------------------------------------
    def _build_tab_jugadores(self):
        frame = self._tab_jugadores

        fondo_img = Image.open(ASSETS_DIR / "welcome.png")
        fondo_tk = ImageTk.PhotoImage(fondo_img)
        self._imagenes.append(fondo_tk)
        fondo_lbl = tk.Label(frame, image=fondo_tk)
        fondo_lbl.place(x=0, y=0, relwidth=1, relheight=1)

        panel = tk.Frame(frame, bg="white", bd=0)
        panel.place(relx=0.5, rely=0.5, anchor="center")

        titulo = tk.Label(panel, text="Empieza a Jugar!", font=("Arial", 18, "bold"),
                           fg="#006400", bg="white")
        titulo.grid(row=0, column=0, columnspan=2, pady=(0, 18))

        tk.Label(panel, text="Jugador1", bg="white").grid(row=1, column=0, sticky="w")
        self.entry_j1 = tk.Entry(panel, font=("Arial", 12), width=18)
        self.entry_j1.grid(row=2, column=0, columnspan=2, pady=(0, 10))

        tk.Label(panel, text="Jugador2", bg="white").grid(row=3, column=0, sticky="w")
        self.entry_j2 = tk.Entry(panel, font=("Arial", 12), width=18)
        self.entry_j2.grid(row=4, column=0, columnspan=2, pady=(0, 14))

        self.btn_confirmar = tk.Button(
            panel, text="Confirmar Jugadores", bg="#4CAF50", fg="white",
            font=("Arial", 12, "bold"), command=self._confirmar_jugadores,
        )
        self.btn_confirmar.grid(row=5, column=0, columnspan=2)

    def _confirmar_jugadores(self):
        nombre1 = self.entry_j1.get().strip()
        nombre2 = self.entry_j2.get().strip()

        if not nombre1 or not nombre2:
            messagebox.showinfo("Aviso", "Por favor ingresa ambos nombres.")
            return

        # A diferencia del Java original (que solo cambiaba la etiqueta
        # visible y dejaba el objeto Jugador con el nombre interno
        # "Jugador 1"/"Jugador 2"), aqui tambien se actualiza el nombre
        # real del Jugador para que se refleje en toda la partida
        # (mensajes de dialogo y la pestaña Score al finalizar).
        j1, j2 = self.juego.get_jugadores()
        j1.set_nombre(nombre1)
        j2.set_nombre(nombre2)

        self.lbl_j1_nombre.config(text=nombre1)
        self.lbl_j2_nombre.config(text=nombre2)

        self.entry_j1.config(state="disabled")
        self.entry_j2.config(state="disabled")
        self.btn_confirmar.config(state="disabled")

    # ------------------------------------------------------------------
    # Tab 2: Reglas (jPanelReglas)
    # ------------------------------------------------------------------
    def _build_tab_reglas(self):
        frame = self._tab_reglas
        imagen = Image.open(ASSETS_DIR / "reglas.jpg")
        imagen.thumbnail((1271, 653))
        imagen_tk = ImageTk.PhotoImage(imagen)
        self._imagenes.append(imagen_tk)
        tk.Label(frame, image=imagen_tk).pack(expand=True, fill="both")

    # ------------------------------------------------------------------
    # Tab 3: Monopoly (jpanelMonopoly)
    # ------------------------------------------------------------------
    def _build_tab_monopoly(self):
        frame = self._tab_monopoly
        frame.configure()
        tablero_frame = tk.Frame(frame, bg="#006666", bd=2)
        tablero_frame.pack(expand=True, fill="both", padx=10, pady=10)

        for col in range(4):
            tablero_frame.columnconfigure(col, weight=1, minsize=180)
        for row in range(4):
            tablero_frame.rowconfigure(row, weight=1, minsize=110)

        self.casilla_labels = []
        for idx, (row, col) in enumerate(POSICIONES_TABLERO):
            lbl = tk.Label(
                tablero_frame, text=NOMBRES_CASILLAS[idx],
                bg="#FFF9C4", fg="#FF9966", font=("Comic Sans MS", 14),
                relief="solid", bd=2, wraplength=170, justify="center",
            )
            lbl.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)
            self.casilla_labels.append(lbl)

        centro = tk.Frame(tablero_frame, bg="#006666")
        centro.grid(row=1, column=1, rowspan=2, columnspan=2, sticky="nsew")

        icono_img = Image.open(ASSETS_DIR / "Sin-título-2.png")
        icono_img.thumbnail((110, 110))
        icono_tk = ImageTk.PhotoImage(icono_img)
        self._imagenes.append(icono_tk)
        tk.Label(centro, image=icono_tk, bg="#006666").pack(pady=(6, 4))

        panel_jugadores = tk.Frame(centro, bg="#006666")
        panel_jugadores.pack(pady=4)

        panel_j1 = tk.Frame(panel_jugadores, bg="#E3F2FD", bd=1, relief="solid")
        panel_j1.grid(row=0, column=0, padx=6, sticky="n")
        self.lbl_j1_nombre = tk.Label(panel_j1, text="Jugador 1", bg="#E3F2FD",
                                       fg="#FF5252", font=("Comic Sans MS", 14))
        self.lbl_j1_nombre.pack(anchor="w", padx=8, pady=(6, 0))
        self.lbl_j1_puntos = tk.Label(panel_j1, text="Puntos: 0", bg="#E3F2FD",
                                       font=("Comic Sans MS", 12))
        self.lbl_j1_puntos.pack(anchor="w", padx=8)
        self.lbl_j1_comodines = tk.Label(panel_j1, text="Comodines: 0", bg="#E3F2FD",
                                          font=("Comic Sans MS", 12))
        self.lbl_j1_comodines.pack(anchor="w", padx=8, pady=(0, 6))

        panel_j2 = tk.Frame(panel_jugadores, bg="#FFEBEE", bd=1, relief="solid")
        panel_j2.grid(row=0, column=1, padx=6, sticky="n")
        self.lbl_j2_nombre = tk.Label(panel_j2, text="Jugador 2", bg="#FFEBEE",
                                       fg="#448AFF", font=("Comic Sans MS", 14))
        self.lbl_j2_nombre.pack(anchor="w", padx=8, pady=(6, 0))
        self.lbl_j2_puntos = tk.Label(panel_j2, text="Puntos: 0", bg="#FFEBEE",
                                       font=("Comic Sans MS", 12))
        self.lbl_j2_puntos.pack(anchor="w", padx=8)
        self.lbl_j2_comodines = tk.Label(panel_j2, text="Comodines: 0", bg="#FFEBEE",
                                          font=("Comic Sans MS", 12))
        self.lbl_j2_comodines.pack(anchor="w", padx=8, pady=(0, 6))

        self.lbl_numero_dado = tk.Label(centro, text="1", bg="#006666", fg="white",
                                         font=("Arial", 36, "bold"))
        self.lbl_numero_dado.pack(pady=6)

        botones = tk.Frame(centro, bg="#006666")
        botones.pack(pady=6)

        self.btn_tirar = tk.Button(botones, text="Tirar", bg="#2196F3", fg="white",
                                    font=("Arial", 12, "bold"), command=self._tirar)
        self.btn_tirar.grid(row=0, column=0, padx=6)
        tk.Button(botones, text="Reproducir/Pausar Musica",
                  command=self._toggle_musica).grid(row=0, column=1, padx=6)

    # ------------------------------------------------------------------
    # Tab 4: Correccion (jpanelCorrecion)
    # ------------------------------------------------------------------
    def _build_tab_correccion(self):
        frame = self._tab_correccion
        scroll = tk.Scrollbar(frame)
        scroll.pack(side="right", fill="y")

        self.txt_errores = tk.Text(frame, wrap="word", yscrollcommand=scroll.set, state="normal")
        self.txt_errores.pack(expand=True, fill="both", padx=6, pady=6)
        scroll.config(command=self.txt_errores.yview)
        self.txt_errores.config(state="disabled")

    def _agregar_errores(self, texto: str):
        if not texto:
            return
        self.txt_errores.config(state="normal")
        self.txt_errores.insert("end", texto)
        self.txt_errores.config(state="disabled")

    # ------------------------------------------------------------------
    # Tab 5: Score (jpanelScore)
    # ------------------------------------------------------------------
    def _build_tab_score(self):
        frame = self._tab_score

        izquierda = tk.Frame(frame)
        izquierda.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        self.lbl_puntos1 = tk.Label(izquierda, text='1er Puesto: ""', font=("Arial", 12),
                                     fg="#003366", relief="groove", padx=8, pady=4)
        self.lbl_puntos1.pack(fill="x", pady=6)
        self.lbl_resultado1 = tk.Label(izquierda, text='Jugador X puntos: "" | Fallos: ""',
                                        font=("Arial", 12), fg="#003366",
                                        relief="groove", padx=8, pady=4)
        self.lbl_resultado1.pack(fill="x", pady=6)

        self.lbl_puntos2 = tk.Label(izquierda, text='2do Puesto: ""', font=("Arial", 12),
                                     fg="#003366", relief="groove", padx=8, pady=4)
        self.lbl_puntos2.pack(fill="x", pady=6)
        self.lbl_resultado2 = tk.Label(izquierda, text='Jugador X puntos: "" | Fallos: ""',
                                        font=("Arial", 12), fg="#003366",
                                        relief="groove", padx=8, pady=4)
        self.lbl_resultado2.pack(fill="x", pady=6)

        tk.Label(izquierda, text="J.Olivares, A.Copara, A.Chavez", font=("Segoe UI", 10),
                 relief="groove", padx=8, pady=4).pack(fill="x", pady=(20, 0))

        derecha = tk.Frame(frame)
        derecha.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        self._gif_label = tk.Label(derecha)
        self._gif_label.pack(expand=True)
        self._cargar_gif_animado(ASSETS_DIR / "aaaaaa.gif")

    def _cargar_gif_animado(self, ruta: Path):
        """Anima el GIF de la pestaña Score usando PIL, ya que Tkinter no
        reproduce GIFs animados de forma nativa."""
        try:
            imagen = Image.open(ruta)
        except FileNotFoundError:
            return

        frames = []
        for cuadro in ImageSequence.Iterator(imagen):
            cuadro = cuadro.convert("RGBA")
            cuadro.thumbnail((280, 280))
            frames.append(ImageTk.PhotoImage(cuadro))
        self._imagenes.extend(frames)

        if not frames:
            return

        def animar(indice=0):
            self._gif_label.configure(image=frames[indice])
            siguiente = (indice + 1) % len(frames)
            self.after(90, animar, siguiente)

        animar()

    # ------------------------------------------------------------------
    # Logica de juego (equivalente a jbtnTirarActionPerformed, etc.)
    # ------------------------------------------------------------------
    def _actualizar_tablero(self):
        for idx, lbl in enumerate(self.casilla_labels):
            lbl.config(text=NOMBRES_CASILLAS[idx])

        for idx, jugador in enumerate(self.juego.get_jugadores()):
            pos = jugador.get_posicion()
            marcador = "J1" if idx == 0 else "J2"
            if 0 <= pos < len(self.casilla_labels):
                lbl = self.casilla_labels[pos]
                if marcador not in lbl.cget("text"):
                    lbl.config(text=f"{lbl.cget('text')}-{marcador}")

        j1, j2 = self.juego.get_jugadores()
        self.lbl_j1_puntos.config(text=f"Puntos: {j1.get_puntos()}")
        self.lbl_j2_puntos.config(text=f"Puntos: {j2.get_puntos()}")
        self.lbl_j1_comodines.config(text=f"Comodines: {j1.get_comodines()}")
        self.lbl_j2_comodines.config(text=f"Comodines: {j2.get_comodines()}")

    # Duracion total de la animacion del dado (ms) y el intervalo entre
    # cada numero aleatorio que se muestra mientras "gira".
    ANIMACION_DADO_MS = 1000
    ANIMACION_DADO_INTERVALO_MS = 80

    def _tirar(self):
        """Inicia la animacion del dado; no existe en el Java original
        (jbtnTirarActionPerformed calculaba y aplicaba el resultado de
        forma inmediata y sincronica). El valor real de la tirada ya se
        calcula aqui con Juego.get_dado().tirar() y se guarda, pero no se
        aplica al jugador hasta que termina la animacion en
        _resolver_tirada."""
        self.btn_tirar.config(state="disabled")
        valor_dado = self.juego.get_dado().tirar()
        pasos = self.ANIMACION_DADO_MS // self.ANIMACION_DADO_INTERVALO_MS
        self._animar_dado(valor_dado, pasos)

    def _animar_dado(self, valor_dado: int, pasos_restantes: int):
        if pasos_restantes > 0:
            self.lbl_numero_dado.config(text=str(random.randint(1, 6)))
            self.after(self.ANIMACION_DADO_INTERVALO_MS, self._animar_dado, valor_dado, pasos_restantes - 1)
        else:
            self.lbl_numero_dado.config(text=str(valor_dado))
            self.btn_tirar.config(state="normal")
            self._resolver_tirada(valor_dado)

    def _resolver_tirada(self, valor_dado: int):
        """Continua jbtnTirarActionPerformed una vez que la animacion del
        dado terminó y se conoce el resultado final."""
        jugador_actual = self.juego.get_jugador_actual()
        jugador_actual.mover(valor_dado, len(self.casilla_labels))

        if jugador_actual.get_posicion() == 5:
            jugador_actual.ganar_comodin()
            messagebox.showinfo("Comodín", f"{jugador_actual.get_nombre()} ganó un comodín")

        quiere_usar_comodin = False
        if jugador_actual.get_comodines() > 0:
            usar = messagebox.askyesno(
                "Usar comodín",
                f"{jugador_actual.get_nombre()} ¿Quieres usar un comodín para saltar la pregunta?",
            )
            if usar:
                jugador_actual.usar_comodin()
                quiere_usar_comodin = True
                messagebox.showinfo("Comodín", "Has usado un comodín. No respondes pregunta esta vez.")

        if not quiere_usar_comodin:
            self._hacer_pregunta(jugador_actual)

        self._actualizar_tablero()

        puntos_j1 = self.juego.get_jugadores()[0].get_puntos()
        puntos_j2 = self.juego.get_jugadores()[1].get_puntos()
        if puntos_j1 >= 100 or puntos_j2 >= 100:
            self._mostrar_score()

        self.juego.siguiente_turno()

    def _hacer_pregunta(self, jugador):
        pregunta = pregunta_aleatoria()
        respuesta = simpledialog.askstring("Pregunta", pregunta.get_enunciado(), parent=self)
        correcta = evaluar_respuesta(jugador, pregunta, respuesta)

        if correcta:
            messagebox.showinfo("Resultado", "Correcto, +10 puntos")
        else:
            messagebox.showinfo("Resultado", "Incorrecto, será para la proxima")

        self._agregar_errores(errores_de(jugador))

    def _mostrar_score(self):
        j1, j2 = self.juego.get_jugadores()

        # A diferencia del Java original -donde jlblResultado1/2 siempre
        # mostraban los datos de j1/j2 en ese orden fijo, sin importar
        # cual quedaba en 1er o 2do puesto (podian aparecer "cruzados")-
        # aqui se determina primero el ganador/perdedor y las etiquetas
        # de puesto y de estadisticas se arman juntas, para que la fila
        # de puntos/fallos siempre corresponda al jugador del puesto de
        # arriba.
        if j1.get_puntos() >= j2.get_puntos():
            ganador, perdedor = j1, j2
        else:
            ganador, perdedor = j2, j1

        primero = f"1er Puesto: {ganador.get_nombre()}"
        segundo = f"2do Puesto: {perdedor.get_nombre()}"
        resultado1 = f"{ganador.get_nombre()} puntos: {ganador.get_puntos()} | Fallos: {ganador.get_fallos()}"
        resultado2 = f"{perdedor.get_nombre()} puntos: {perdedor.get_puntos()} | Fallos: {perdedor.get_fallos()}"

        self.lbl_resultado1.config(text=resultado1)
        self.lbl_resultado2.config(text=resultado2)
        self.lbl_puntos1.config(text=primero)
        self.lbl_puntos2.config(text=segundo)

        # Fiel al original: Principal.java hace
        # jtblMonopolyPrincipal.setSelectedIndex(3), que en realidad
        # selecciona la pestaña "Correccion" (indice 3), no "Score"
        # (indice 4) -- el comentario del propio autor admite que el
        # indice quedo sin ajustar. Se conserva ese comportamiento aqui
        # por fidelidad; ver README para el detalle.
        self.notebook.select(self._tab_correccion)

        exportar_estadisticas(self.juego)
        messagebox.showinfo("Estadísticas", "Estadísticas exportadas exitosamente en Estadisticas.txt")

    def _toggle_musica(self):
        ruta = ASSETS_DIR / "songMonkey.wav"
        if not ruta.exists():
            messagebox.showerror(
                "Música",
                "No se encontró 'songMonkey.wav'.\n"
                "Este archivo de audio tampoco estaba presente en el "
                "proyecto Java original (referenciado en el codigo pero "
                "ausente de src/proyectofinalpoo).",
            )
            return

        if sys.platform != "win32":
            messagebox.showerror("Música", "La reproducción de audio solo está implementada para Windows (winsound).")
            return

        import winsound

        try:
            if not self._reproduciendo:
                winsound.PlaySound(str(ruta), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
                self._reproduciendo = True
            else:
                winsound.PlaySound(None, winsound.SND_PURGE)
                self._reproduciendo = False
        except Exception as error:
            messagebox.showerror("Música", f"Error al reproducir audio: {error}")


def main():
    app = PrincipalApp()
    app.mainloop()


if __name__ == "__main__":
    main()
