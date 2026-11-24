"""Interfaz grafica del juego, equivalente a Principal.java (Swing -> Tkinter).

Java usaba NetBeans GUI Builder (GroupLayout/AbsoluteLayout) para un
JFrame con un JTabbedPane de 5 pestañas: Jugadores, Reglas, Monopoly,
Correccion y Score, con el numero de jugadores fijo en 2. Aqui se
recrea la misma estructura con tkinter.ttk.Notebook (grid/pack en vez
de GroupLayout), con un tema visual propio (paleta de colores,
tipografia y tiles con esquinas redondeadas dibujadas a mano en
Canvas), y se generaliza el juego para soportar de 2 a 6 jugadores
elegidos por el usuario (ver monopoly.juego.MIN_JUGADORES/MAX_JUGADORES).
"""

from __future__ import annotations

import random
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageSequence, ImageTk

from .estadisticas import exportar_estadisticas
from .audio import ReproductorMusica
from .juego import MAX_JUGADORES, MIN_JUGADORES, Juego
from .pregunta import errores_de, evaluar_respuesta
from .persistencia import DIRECTORIO_DATOS, RUTA_PARTIDA, cargar_partida, guardar_partida

ASSETS_DIR = Path(__file__).resolve().parent / "assets"

# ----------------------------------------------------------------------
# Tema visual: paleta de colores y tipografia centralizadas para que
# toda la app se vea consistente.
# ----------------------------------------------------------------------
PALETTE = {
    "bg": "#0E2F2B",        # verde-teal oscuro (fondo general / tablero)
    "bg_soft": "#F4F1E8",   # crema calido (fondo de paneles claros)
    "surface": "#FFFFFF",   # tarjetas
    "tile": "#FDF6E3",      # casilla normal
    "tile_special": "#FCE29B",  # casilla especial (Inicio / comodin)
    "tile_border": "#0E2F2B",
    "tile_text": "#12312C",
    "accent": "#2E7D6B",    # verde azulado principal (botones primarios)
    "accent_dark": "#1F5A4D",
    "accent2": "#E0A93E",   # dorado (acentos / hover secundario)
    "text": "#1B2421",
    "muted": "#5B6B66",
    "success": "#2E7D32",
    "danger": "#C62828",
}

# Un color por jugador (hasta MAX_JUGADORES). El Java original solo
# necesitaba 2 colores fijos (J1 azul / J2 rojo); al soportar hasta 6
# jugadores se define una paleta mas amplia para las fichas, tarjetas y
# tokens del tablero.
PLAYER_COLORS = [
    "#3B82F6",  # J1 azul
    "#F35B6B",  # J2 rojo/rosado
    "#22C55E",  # J3 verde
    "#A855F7",  # J4 violeta
    "#F59E0B",  # J5 naranja
    "#06B6D4",  # J6 cian
]

FONT_FAMILY = "Segoe UI"
FONT_TITLE = (FONT_FAMILY, 24, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 12)
FONT_BODY = (FONT_FAMILY, 11)
FONT_BODY_BOLD = (FONT_FAMILY, 11, "bold")
FONT_LABEL = (FONT_FAMILY, 9)
FONT_TILE = (FONT_FAMILY, 10, "bold")
FONT_TOKEN = (FONT_FAMILY, 8, "bold")
FONT_DICE = (FONT_FAMILY, 32, "bold")
FONT_BUTTON = (FONT_FAMILY, 11, "bold")
FONT_CARD_NAME = (FONT_FAMILY, 11, "bold")
FONT_SCORE_TITLE = (FONT_FAMILY, 13, "bold")
FONT_SCORE_BODY = (FONT_FAMILY, 11)

# Nombres por defecto de las 12 casillas tal como quedan luego de
# actualizarTablero() en el Java original (que sobreescribe cualquier
# nombre inicial con "Inicio" / "Casilla N").
NOMBRES_CASILLAS = ["Inicio"] + [f"Casilla {i}" for i in range(2, 13)]

# Indice de la casilla que otorga comodin (posicion 5, "Casilla 6").
CASILLA_COMODIN_IDX = 5

# Posiciones (fila, columna) de una grilla 4x4 que dibuja las 12 casillas
# formando el circuito de un tablero de Monopoly, dejando el centro libre
# para el dado, los botones y los paneles de jugadores.
POSICIONES_TABLERO = [
    (0, 0), (0, 1), (0, 2), (0, 3),
    (1, 3), (2, 3), (3, 3), (3, 2),
    (3, 1), (3, 0), (2, 0), (1, 0),
]

# Sentinela devuelto por _dialogo_pregunta cuando el jugador elige el
# boton "Usar Comodín" en vez de responder o cancelar. Se usa identidad
# (is) en vez de un string magico para que no pueda confundirse con una
# respuesta real escrita por el jugador.
_USAR_COMODIN = object()


def _rounded_rect(canvas: tk.Canvas, x1, y1, x2, y2, radius=16, **kwargs):
    """Dibuja un rectangulo con esquinas redondeadas en un Canvas.

    Tkinter no tiene una primitiva nativa para esto (a diferencia de
    Swing, donde un LineBorder con `round=true` ya lo resuelve); se
    construye a mano con un poligono suavizado.
    """
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class PrincipalApp(tk.Tk):
    """Equivalente a la clase Principal (JFrame) del proyecto Java."""

    def __init__(self, ruta_guardado: Path = RUTA_PARTIDA,
                 directorio_resultados: Path | None = None):
        super().__init__()
        self.title("Monopoly")
        self.configure(bg=PALETTE["bg"])
        self.minsize(1150, 700)
        self.geometry("1250x740")
        # Arranca maximizada para aprovechar toda la pantalla (en vez de
        # una ventana fija que puede quedar chica/solapada con otras
        # apps segun la resolucion del monitor). "zoomed" es el estado
        # nativo de maximizado en Tk sobre Windows.
        try:
            self.state("zoomed")
        except tk.TclError:
            pass

        # A diferencia del Java original (que creaba el Juego con 2
        # jugadores fijos apenas arrancaba la app), aqui no existe
        # partida hasta que el usuario elige cuantos van a jugar (2-6)
        # y confirma sus nombres en la pestaña "Jugadores".
        self.juego: Juego | None = None
        self._partida_finalizada = False
        self._turno_en_curso = False
        self._ruta_guardado = Path(ruta_guardado)
        self._directorio_resultados = directorio_resultados
        self._audio = ReproductorMusica()
        self.casilla_canvas: list[tk.Canvas] = []
        self.paneles_jugadores: list[dict[str, "_TextProxy"]] = []
        self.entries_jugadores: list[ttk.Entry] = []
        self._reproduciendo = False
        self._imagenes: list[ImageTk.PhotoImage] = []  # evita garbage-collect

        self._configurar_estilos()
        self._configurar_icono()

        self.notebook = ttk.Notebook(self, style="Monopoly.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self._tab_jugadores = tk.Frame(self.notebook, bg=PALETTE["bg_soft"])
        self._tab_reglas = tk.Frame(self.notebook, bg=PALETTE["bg_soft"])
        self._tab_monopoly = tk.Frame(self.notebook, bg=PALETTE["bg"])
        self._tab_correccion = tk.Frame(self.notebook, bg=PALETTE["bg_soft"])
        self._tab_score = tk.Frame(self.notebook, bg=PALETTE["bg_soft"])

        self.notebook.add(self._tab_jugadores, text="  Jugadores  ")
        self.notebook.add(self._tab_reglas, text="  Reglas  ")
        self.notebook.add(self._tab_monopoly, text="  Monopoly  ")
        self.notebook.add(self._tab_correccion, text="  Correccion  ")
        self.notebook.add(self._tab_score, text="  Score  ")

        self._build_tab_jugadores()
        self._build_tab_reglas()
        self._build_tab_monopoly()
        self._build_tab_correccion()
        self._build_tab_score()
        self._crear_menu_partida()
        self.protocol("WM_DELETE_WINDOW", self._cerrar)

        self.update_idletasks()
        self.eval("tk::PlaceWindow . center")

    def _crear_menu_partida(self):
        barra = tk.Menu(self)
        partida = tk.Menu(barra, tearoff=False)
        partida.add_command(label="Nueva partida", command=self._nueva_partida)
        partida.add_command(label="Continuar última partida", command=self._continuar_partida)
        partida.add_command(label="Abrir partida…", command=self._abrir_partida)
        partida.add_separator()
        partida.add_command(label="Guardar partida", command=lambda: self._guardar_partida(avisar=True))
        partida.add_command(label="Guardar como…", command=self._guardar_como)
        partida.add_command(label="Historial de resultados", command=self._ver_historial)
        partida.add_separator()
        partida.add_command(label="Salir", command=self._cerrar)
        barra.add_cascade(label="Partida", menu=partida)
        self.config(menu=barra)

    def _guardar_partida(self, avisar=False):
        if self.juego is None:
            if avisar:
                messagebox.showinfo("Guardar", "Primero configura una partida.")
            return True
        if self._turno_en_curso:
            messagebox.showinfo("Guardar", "Termina el turno antes de guardar.")
            return False
        try:
            guardar_partida(self.juego, self._ruta_guardado)
        except (OSError, ValueError) as error:
            messagebox.showerror("No se pudo guardar", str(error))
            return False
        if avisar:
            messagebox.showinfo("Partida guardada", f"Puedes cerrar y continuar después.\n{self._ruta_guardado}")
        return True

    def _guardar_como(self):
        if self._turno_en_curso or self.juego is None:
            return
        ruta = filedialog.asksaveasfilename(title="Guardar partida", defaultextension=".json",
                                          filetypes=[("Partida Monopoly", "*.json")])
        if ruta:
            anterior = self._ruta_guardado
            self._ruta_guardado = Path(ruta)
            if not self._guardar_partida(avisar=True):
                self._ruta_guardado = anterior

    def _abrir_partida(self):
        if self._turno_en_curso:
            return
        ruta = filedialog.askopenfilename(title="Abrir partida", filetypes=[("Partida Monopoly", "*.json")])
        if ruta:
            self._cargar_partida(Path(ruta))

    def _continuar_partida(self):
        self._cargar_partida(self._ruta_guardado)

    def _cargar_partida(self, ruta: Path):
        if self._turno_en_curso:
            return
        try:
            cargada = cargar_partida(ruta)
        except (OSError, ValueError) as error:
            messagebox.showerror("No se pudo continuar", str(error))
            return
        if self.juego is not None and not self._guardar_partida():
            return
        self._ruta_guardado = ruta
        self.juego = cargada
        self._partida_finalizada = cargada.finalizada
        self.spin_num_jugadores.config(state="readonly")
        self.spin_num_jugadores.set(len(cargada.jugadores))
        self._regenerar_campos_nombre()
        for entry, jugador in zip(self.entries_jugadores, cargada.jugadores):
            entry.insert(0, jugador.nombre)
            entry.config(state="disabled")
        self.spin_num_jugadores.config(state="disabled")
        self.btn_confirmar.config(state="disabled")
        self._reconstruir_paneles_jugadores([j.nombre for j in cargada.jugadores])
        self._actualizar_tablero()
        self._actualizar_errores()
        self.btn_tirar.config(state="disabled" if cargada.finalizada else "normal")
        if cargada.finalizada:
            self._mostrar_score(avisar=False)
        else:
            self.notebook.select(self._tab_monopoly)
        if cargada.recuperada_desde_copia:
            messagebox.showwarning("Guardado recuperado", "Se recuperó la copia anterior porque el archivo principal no era válido.")

    def _nueva_partida(self):
        if self._turno_en_curso:
            return
        if self.juego is not None:
            if not messagebox.askyesno("Nueva partida", "Se guardará la partida actual. ¿Quieres empezar otra?"):
                return
            if not self._guardar_partida():
                return
        self.juego = None
        self._partida_finalizada = False
        self.spin_num_jugadores.config(state="readonly")
        self._regenerar_campos_nombre()
        self.btn_confirmar.config(state="normal")
        self.btn_tirar.config(state="disabled")
        self.notebook.select(self._tab_jugadores)

    def _ver_historial(self):
        carpeta = self._directorio_resultados or DIRECTORIO_DATOS / "resultados"
        ventana = tk.Toplevel(self)
        ventana.title("Historial de resultados")
        ventana.geometry("850x550")
        lista = tk.Listbox(ventana, width=42, exportselection=False)
        lista.pack(side="left", fill="y", padx=10, pady=10)
        texto = tk.Text(ventana, wrap="word", state="disabled")
        texto.pack(side="left", expand=True, fill="both", padx=(0, 10), pady=10)
        scroll = ttk.Scrollbar(ventana, command=texto.yview)
        scroll.pack(side="right", fill="y")
        texto.config(yscrollcommand=scroll.set)
        archivos = sorted(carpeta.glob("*.txt"), key=lambda p: p.stat().st_mtime, reverse=True)
        for archivo in archivos:
            lista.insert("end", archivo.stem)
        if not archivos:
            lista.insert("end", "Aún no hay partidas terminadas")

        def mostrar(_evento=None):
            if not archivos or not lista.curselection():
                return
            try:
                contenido = archivos[lista.curselection()[0]].read_text(encoding="utf-8")
            except OSError as error:
                messagebox.showerror("Historial", str(error), parent=ventana)
                return
            texto.config(state="normal")
            texto.delete("1.0", "end")
            texto.insert("end", contenido)
            texto.config(state="disabled")

        lista.bind("<<ListboxSelect>>", mostrar)
        if archivos:
            lista.selection_set(0)
            mostrar()

    def _cerrar(self):
        if self._turno_en_curso:
            messagebox.showinfo("Turno en curso", "Termina el turno antes de cerrar para conservar su resultado.")
            return
        if not self._guardar_partida():
            if not messagebox.askyesno("Salir sin guardar", "El guardado falló. ¿Quieres salir perdiendo el avance desde el último guardado?"):
                return
        self._audio.cerrar()
        self.destroy()

    # ------------------------------------------------------------------
    # Tema / estilos ttk (Notebook, botones, entradas)
    # ------------------------------------------------------------------
    def _configurar_estilos(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Monopoly.TNotebook", background=PALETTE["bg"], borderwidth=0, tabmargins=(8, 8, 8, 0),
        )
        style.configure(
            "Monopoly.TNotebook.Tab",
            background=PALETTE["accent_dark"], foreground="#DDEDE8",
            font=FONT_BODY_BOLD, padding=(16, 10), borderwidth=0,
        )
        style.map(
            "Monopoly.TNotebook.Tab",
            background=[("selected", PALETTE["accent2"])],
            foreground=[("selected", PALETTE["text"])],
            expand=[("selected", (1, 1, 1, 0))],
        )

        style.configure(
            "Accent.TButton", background=PALETTE["accent"], foreground="white",
            font=FONT_BUTTON, padding=(18, 10), borderwidth=0, focuscolor=PALETTE["accent"],
        )
        style.map("Accent.TButton", background=[("active", PALETTE["accent_dark"]), ("disabled", "#9AA6A2")])

        style.configure(
            "Secondary.TButton", background=PALETTE["surface"], foreground=PALETTE["text"],
            font=FONT_BODY_BOLD, padding=(14, 9), borderwidth=1, relief="flat",
        )
        style.map("Secondary.TButton", background=[("active", "#EDEAE0")])

        style.configure(
            "Monopoly.TEntry", padding=8, fieldbackground="#FFFFFF",
            bordercolor=PALETTE["accent"], lightcolor=PALETTE["accent"], darkcolor=PALETTE["accent"],
        )
        style.configure(
            "Monopoly.TSpinbox", padding=6, fieldbackground="#FFFFFF", arrowsize=14,
        )

    def _configurar_icono(self):
        try:
            icono = Image.open(ASSETS_DIR / "Sin-título-2.png")
            icono.thumbnail((64, 64))
            icono_tk = ImageTk.PhotoImage(icono)
            self._imagenes.append(icono_tk)
            self.iconphoto(True, icono_tk)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Tab 1: Jugadores (jpanelIntroduccion)
    # ------------------------------------------------------------------
    def _build_tab_jugadores(self):
        frame = self._tab_jugadores

        fondo_img = Image.open(ASSETS_DIR / "welcome.png")
        fondo_tk = ImageTk.PhotoImage(fondo_img)
        self._imagenes.append(fondo_tk)
        tk.Label(frame, image=fondo_tk, bd=0).place(x=0, y=0, relwidth=1, relheight=1)

        self._card_w = 460

        # Velo semitransparente simulado con una franja solida detras de
        # la tarjeta para que el texto siempre sea legible sobre la
        # imagen de fondo. El alto de la tarjeta se recalcula segun la
        # cantidad de jugadores elegida (ver _redibujar_card_jugadores),
        # por eso no se dibuja aqui con un tamaño fijo.
        self._sombra_jugadores = tk.Canvas(frame, bg=frame["bg"], highlightthickness=0)
        self._sombra_jugadores.place(relx=0.5, rely=0.5, anchor="center")

        card = tk.Frame(self._sombra_jugadores, bg=PALETTE["surface"])
        self._card_jugadores = card

        tk.Label(card, text="🎩 Empieza a Jugar!", font=FONT_TITLE,
                 fg=PALETTE["accent_dark"], bg=PALETTE["surface"]).pack(pady=(4, 4))
        tk.Label(card, text="Elige cuántos van a jugar e ingresa sus nombres",
                 font=FONT_SUBTITLE, fg=PALETTE["muted"], bg=PALETTE["surface"],
                 wraplength=self._card_w - 60, justify="center").pack(pady=(0, 16))

        selector = tk.Frame(card, bg=PALETTE["surface"])
        selector.pack(pady=(0, 14))
        tk.Label(selector, text="Número de jugadores:", font=FONT_LABEL,
                 fg=PALETTE["muted"], bg=PALETTE["surface"]).pack(side="left", padx=(0, 8))
        self.spin_num_jugadores = ttk.Spinbox(
            selector, from_=MIN_JUGADORES, to=MAX_JUGADORES, width=4,
            font=FONT_BODY_BOLD, style="Monopoly.TSpinbox", state="readonly",
            justify="center", command=self._regenerar_campos_nombre,
        )
        self.spin_num_jugadores.set(2)
        self.spin_num_jugadores.pack(side="left")

        self.contenedor_nombres = tk.Frame(card, bg=PALETTE["surface"])
        self.contenedor_nombres.pack(fill="x")

        self.btn_confirmar = ttk.Button(
            card, text="Confirmar Jugadores", style="Accent.TButton",
            command=self._confirmar_jugadores,
        )
        self.btn_confirmar.pack(pady=(16, 4), fill="x", padx=30)
        ttk.Button(card, text="Continuar partida guardada", style="Secondary.TButton",
                   command=self._continuar_partida).pack(pady=(4, 4), fill="x", padx=30)
        ttk.Button(card, text="Historial de resultados", style="Secondary.TButton",
                   command=self._ver_historial).pack(pady=(4, 4), fill="x", padx=30)

        self._regenerar_campos_nombre()

    def _campo_nombre(self, parent, placeholder, color, posicion=None):
        wrapper = tk.Frame(parent, bg=PALETTE["surface"])
        if posicion is None:
            wrapper.pack(pady=6, padx=30, fill="x")
        else:
            fila, columna = posicion
            wrapper.grid(row=fila, column=columna, pady=6, padx=18, sticky="ew")
        tk.Label(wrapper, text=placeholder, font=FONT_LABEL, fg=color,
                 bg=PALETTE["surface"]).pack(anchor="w")
        entry = ttk.Entry(wrapper, font=FONT_BODY, style="Monopoly.TEntry")
        entry.pack(fill="x", ipady=3)
        return entry

    def _regenerar_campos_nombre(self):
        """Reconstruye los campos de nombre segun el numero de jugadores
        elegido en el Spinbox (2 a MAX_JUGADORES); no tiene equivalente
        en el Java original, que siempre tenia exactamente 2 campos fijos
        (jtxtJ1/jtxtJ2)."""
        n = int(self.spin_num_jugadores.get())
        self._card_w = 560 if n > 3 else 460
        self.contenedor_nombres.columnconfigure(0, weight=1)
        self.contenedor_nombres.columnconfigure(1, weight=1)

        for widget in self.contenedor_nombres.winfo_children():
            widget.destroy()

        self.entries_jugadores = [
            self._campo_nombre(self.contenedor_nombres, f"Jugador {i + 1}", PLAYER_COLORS[i],
                               divmod(i, 2) if n > 3 else None)
            for i in range(n)
        ]

        self._redibujar_card_jugadores()

    def _redibujar_card_jugadores(self):
        """Ajusta el tamaño de la tarjeta de la pestaña Jugadores al
        contenido actual (crece con mas campos de nombre)."""
        card = self._card_jugadores
        card.update_idletasks()
        card_w = self._card_w
        card_h = card.winfo_reqheight() + 16

        sombra = self._sombra_jugadores
        sombra.configure(width=card_w + 12, height=card_h + 12)
        sombra.delete("all")
        _rounded_rect(sombra, 8, 10, card_w + 8, card_h + 10, radius=24,
                      fill="#0A1F1B", outline="")
        _rounded_rect(sombra, 0, 0, card_w, card_h, radius=24,
                      fill=PALETTE["surface"], outline="")
        sombra.create_window(card_w / 2, card_h / 2, window=card, width=card_w)

    def _confirmar_jugadores(self):
        nombres = [entry.get().strip() for entry in self.entries_jugadores]

        if any(not nombre for nombre in nombres):
            messagebox.showinfo("Aviso", "Por favor ingresa el nombre de todos los jugadores.")
            return
        if self._ruta_guardado.exists():
            if not messagebox.askyesno("Nueva partida", "Se reemplazará el guardado para continuar. Los resultados anteriores se conservan. ¿Empezar una partida nueva?"):
                return

        # A diferencia del Java original (que solo cambiaba la etiqueta
        # visible y dejaba el objeto Jugador con el nombre interno
        # "Jugador 1"/"Jugador 2"), aqui tambien se actualiza el nombre
        # real de cada Jugador para que se refleje en toda la partida
        # (mensajes de dialogo y la pestaña Score al finalizar).
        self.juego = Juego(len(nombres))
        for jugador, nombre in zip(self.juego.get_jugadores(), nombres):
            jugador.set_nombre(nombre)

        self._reconstruir_paneles_jugadores(nombres)
        self._actualizar_tablero()

        for entry in self.entries_jugadores:
            entry.config(state="disabled")
        self.spin_num_jugadores.config(state="disabled")
        self.btn_confirmar.config(state="disabled")
        self.btn_tirar.config(state="normal")
        self._guardar_partida()

        messagebox.showinfo(
            "Listo",
            f"¡{len(nombres)} jugadores confirmados! Ve a la pestaña \"Monopoly\" para comenzar.",
        )

    # ------------------------------------------------------------------
    # Tab 2: Reglas (jPanelReglas)
    # ------------------------------------------------------------------
    def _build_tab_reglas(self):
        frame = self._tab_reglas
        tk.Label(frame, text="📜 Reglas del juego", font=FONT_TITLE,
                 fg=PALETTE["accent_dark"], bg=PALETTE["bg_soft"]).pack(pady=(16, 8))
        tk.Label(frame, text="Todo lo que necesitas para jugar, en una sola pantalla.",
                 font=FONT_LABEL, fg=PALETTE["text"], bg=PALETTE["bg_soft"]).pack(pady=(0, 8))

        contenedor = tk.Frame(frame, bg=PALETTE["surface"])
        contenedor.pack(expand=True, fill="both", padx=24, pady=(0, 24))

        # Texto real en dos columnas: todas las reglas quedan visibles,
        # con la misma letra del juego y sin reducir una imagen larga.
        for columna in range(2):
            contenedor.columnconfigure(columna, weight=1, uniform="reglas")
        for fila in range(3):
            contenedor.rowconfigure(fila, weight=1)
        reglas = [
            ("1. Configura la partida",
             "Elige de 2 a 6 jugadores y confirma sus nombres.\n"
             "Todos empiezan en Inicio con 0 puntos. El tablero tiene 12 casillas."),
            ("2. Lanza el dado",
             "En tu turno, pulsa Tirar. Avanza de 1 a 6 casillas según el resultado.\n"
             "Al pasar la última casilla, el recorrido vuelve al inicio."),
            ("3. Responde la pregunta",
             "Cada acierto suma 10 puntos. Una respuesta incorrecta o cancelada cuenta como fallo.\n"
             "Se ignoran mayúsculas y espacios exteriores; las tildes sí cuentan."),
            ("4. Aprovecha los comodines",
             "Caer en la casilla 6 te da un comodín y termina tu turno sin pregunta.\n"
             "En otro turno, Usar Comodín salta la pregunta sin sumar puntos ni fallos."),
            ("5. Final de la partida",
             "Gana quien llega a 100 puntos. Las 40 preguntas no se repiten.\n"
             "Si se agotan, se clasifica por puntaje; los empates conservan el orden de los jugadores."),
            ("6. Guarda y continúa",
             "El avance se guarda al terminar cada turno y al cerrar.\n"
             "Usa el menú Partida para guardar, abrir o continuar. Los resultados anteriores quedan en Historial."),
        ]
        for indice, (titulo, texto) in enumerate(reglas):
            columna, fila = divmod(indice, 3)
            bloque = tk.Frame(contenedor, bg=PALETTE["surface"])
            bloque.grid(row=fila, column=columna, sticky="nsew", padx=24, pady=12)
            tk.Label(bloque, text=titulo, font=FONT_BODY_BOLD, anchor="w",
                     fg=PALETTE["accent_dark"], bg=PALETTE["surface"]).pack(fill="x", pady=(0, 8))
            contenido = tk.Label(bloque, text=texto, font=FONT_BODY, anchor="nw", justify="left",
                                 wraplength=440, fg=PALETTE["text"], bg=PALETTE["surface"])
            contenido.pack(fill="x")
            bloque.bind("<Configure>", lambda evento, etiqueta=contenido:
                        etiqueta.config(wraplength=max(240, evento.width)))

    # ------------------------------------------------------------------
    # Tab 3: Monopoly (jpanelMonopoly)
    # ------------------------------------------------------------------
    def _build_tab_monopoly(self):
        frame = self._tab_monopoly
        tablero_frame = tk.Frame(frame, bg=PALETTE["bg"])
        tablero_frame.pack(expand=True, fill="both", padx=16, pady=16)

        for col in range(4):
            tablero_frame.columnconfigure(col, weight=1, minsize=190)
        for row in range(4):
            tablero_frame.rowconfigure(row, weight=1, minsize=130)

        self.casilla_canvas = [None] * 12
        for idx, (row, col) in enumerate(POSICIONES_TABLERO):
            canvas = tk.Canvas(tablero_frame, bg=PALETTE["bg"], highlightthickness=0)
            canvas.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)
            canvas._idx = idx
            canvas._jugadores_aqui = []
            canvas.bind("<Configure>", lambda evt, c=canvas: self._redibujar_casilla(c))
            self.casilla_canvas[idx] = canvas

        centro = tk.Frame(tablero_frame, bg=PALETTE["bg"])
        centro.grid(row=1, column=1, rowspan=2, columnspan=2, sticky="nsew")
        # El contenido se centra verticalmente dentro del area disponible
        # (en vez de apilarse desde arriba) para que se vea equilibrado
        # tanto en una ventana maximizada como en una mas chica.
        centro_interior = tk.Frame(centro, bg=PALETTE["bg"])
        centro_interior.place(relx=0.5, rely=0.5, anchor="center")

        icono_img = Image.open(ASSETS_DIR / "Sin-título-2.png")
        icono_img.thumbnail((64, 64))
        icono_tk = ImageTk.PhotoImage(icono_img)
        self._imagenes.append(icono_tk)
        self._logo_tablero = tk.Label(centro_interior, image=icono_tk, bg=PALETTE["bg"])
        self._logo_tablero.pack(pady=(0, 4))

        # Placeholder hasta que se confirmen los jugadores en la pestaña
        # "Jugadores"; se reemplaza por las tarjetas reales en
        # _reconstruir_paneles_jugadores.
        self.panel_jugadores_frame = tk.Frame(centro_interior, bg=PALETTE["bg"])
        self.panel_jugadores_frame.pack(pady=4)
        tk.Label(
            self.panel_jugadores_frame,
            text="Configura los jugadores en la pestaña \"Jugadores\"",
            font=FONT_BODY, fg=PALETTE["muted"], bg=PALETTE["bg"],
            wraplength=320, justify="center",
        ).pack()

        # Dado y botones en una misma fila horizontal (en vez de
        # apilados) para ocupar menos espacio vertical y evitar que se
        # corten en ventanas mas chicas.
        accion = tk.Frame(centro_interior, bg=PALETTE["bg"])
        accion.pack(pady=(10, 0))

        dado_canvas = tk.Canvas(accion, width=72, height=72, bg=PALETTE["bg"], highlightthickness=0)
        dado_canvas.pack(side="left", padx=(0, 14))
        _rounded_rect(dado_canvas, 3, 3, 69, 69, radius=16, fill=PALETTE["surface"],
                      outline=PALETTE["accent2"], width=3)
        self._dado_texto_id = dado_canvas.create_text(36, 36, text="1", font=FONT_DICE, fill=PALETTE["text"])
        self._dado_canvas = dado_canvas
        self.lbl_numero_dado = _TextProxy(dado_canvas, self._dado_texto_id)

        botones = tk.Frame(accion, bg=PALETTE["bg"])
        botones.pack(side="left")

        # Empieza deshabilitado: no hay partida hasta confirmar
        # jugadores en la pestaña "Jugadores".
        self.btn_tirar = ttk.Button(botones, text="🎲  Tirar", style="Accent.TButton",
                                     command=self._tirar, state="disabled")
        self.btn_tirar.pack(pady=(0, 6))
        ttk.Button(botones, text="🎵  Música", style="Secondary.TButton",
                   command=self._toggle_musica).pack()
        self.lbl_turno = tk.Label(centro_interior, text="", font=FONT_LABEL,
                                 fg=PALETTE["surface"], bg=PALETTE["bg"], wraplength=400)
        self.lbl_turno.pack(pady=(4, 0))

    def _reconstruir_paneles_jugadores(self, nombres: list[str]):
        """Reemplaza el placeholder (o las tarjetas de una partida
        anterior) por una tarjeta por jugador, en una grilla de hasta 3
        columnas para que quepan cómodamente hasta 6 jugadores."""
        for widget in self.panel_jugadores_frame.winfo_children():
            widget.destroy()
        if len(nombres) > 3:
            self._logo_tablero.pack_forget()
        elif not self._logo_tablero.winfo_manager():
            self._logo_tablero.pack(before=self.panel_jugadores_frame, pady=(0, 4))

        self.paneles_jugadores = []
        columnas = min(3, len(nombres))
        for i, nombre in enumerate(nombres):
            fila, col = divmod(i, columnas)
            proxies = self._panel_jugador(
                self.panel_jugadores_frame, nombre, PLAYER_COLORS[i % len(PLAYER_COLORS)], i, fila, col,
            )
            self.paneles_jugadores.append(proxies)

    def _panel_jugador(self, parent, nombre_defecto, color, indice, fila, col):
        card_w, card_h = 150, 84
        canvas = tk.Canvas(parent, width=card_w, height=card_h, bg=PALETTE["bg"], highlightthickness=0)
        canvas.grid(row=fila, column=col, padx=5, pady=4)
        _rounded_rect(canvas, 2, 2, card_w - 2, card_h - 2, radius=12,
                      fill=PALETTE["surface"], outline=color, width=2)

        avatar_r = 11
        cx, cy = 18, 18
        canvas.create_oval(cx - avatar_r, cy - avatar_r, cx + avatar_r, cy + avatar_r, fill=color, outline="")
        canvas.create_text(cx, cy, text=str(indice + 1), fill="white", font=(FONT_FAMILY, 9, "bold"))

        nombre_id = canvas.create_text(34, 18, text=nombre_defecto, font=FONT_CARD_NAME,
                                        fill=PALETTE["text"], anchor="w", width=card_w - 44)
        puntos_id = canvas.create_text(12, 48, text="⭐ Puntos: 0", font=(FONT_FAMILY, 9),
                                        fill=PALETTE["muted"], anchor="w")
        comodines_id = canvas.create_text(12, 67, text="🃏 Comodines: 0", font=(FONT_FAMILY, 9),
                                           fill=PALETTE["muted"], anchor="w")

        return {
            "nombre": _TextProxy(canvas, nombre_id),
            "puntos": _TextProxy(canvas, puntos_id, prefijo="⭐ "),
            "comodines": _TextProxy(canvas, comodines_id, prefijo="🃏 "),
        }

    def _redibujar_casilla(self, canvas: tk.Canvas):
        canvas.delete("all")
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if w < 8 or h < 8:
            return

        idx = canvas._idx
        especial = idx == 0 or idx == CASILLA_COMODIN_IDX
        fill = PALETTE["tile_special"] if especial else PALETTE["tile"]

        _rounded_rect(canvas, 3, 3, w - 3, h - 3, radius=14, fill=fill,
                      outline=PALETTE["tile_border"], width=2)

        hay_jugadores = bool(canvas._jugadores_aqui)
        texto_y = h / 2 - 12 if hay_jugadores else h / 2
        icono = "🏁 " if idx == 0 else ("🃏 " if idx == CASILLA_COMODIN_IDX else "")
        canvas.create_text(w / 2, texto_y, text=f"{icono}{NOMBRES_CASILLAS[idx]}",
                            font=FONT_TILE, fill=PALETTE["tile_text"], justify="center",
                            width=w - 16)

        if hay_jugadores:
            n = len(canvas._jugadores_aqui)
            espacio = 26
            inicio_x = w / 2 - (espacio * (n - 1)) / 2
            for i, marcador in enumerate(canvas._jugadores_aqui):
                indice_jugador = int(marcador[1:]) - 1
                color = PLAYER_COLORS[indice_jugador % len(PLAYER_COLORS)]
                cx = inicio_x + i * espacio
                cy = h - 18
                canvas.create_oval(cx - 10, cy - 10, cx + 10, cy + 10, fill=color, outline="white", width=2)
                canvas.create_text(cx, cy, text=marcador, font=FONT_TOKEN, fill="white")

    # ------------------------------------------------------------------
    # Tab 4: Correccion (jpanelCorrecion)
    # ------------------------------------------------------------------
    def _build_tab_correccion(self):
        frame = self._tab_correccion
        tk.Label(frame, text="📝 Historial de respuestas incorrectas", font=FONT_TITLE,
                 fg=PALETTE["accent_dark"], bg=PALETTE["bg_soft"]).pack(pady=(16, 8), anchor="w", padx=24)

        contenedor = tk.Frame(frame, bg=PALETTE["surface"])
        contenedor.pack(expand=True, fill="both", padx=24, pady=(0, 24))

        scroll = ttk.Scrollbar(contenedor)
        scroll.pack(side="right", fill="y")

        self.txt_errores = tk.Text(
            contenedor, wrap="word", yscrollcommand=scroll.set, state="normal",
            bg=PALETTE["surface"], fg=PALETTE["text"], font=FONT_BODY,
            relief="flat", padx=16, pady=16, borderwidth=0,
        )
        self.txt_errores.pack(expand=True, fill="both")
        scroll.config(command=self.txt_errores.yview)
        self.txt_errores.config(state="disabled")

    def _actualizar_errores(self):
        if self.juego is None:
            return
        texto = "".join(errores_de(jugador) for jugador in self.juego.get_jugadores())
        self.txt_errores.config(state="normal")
        self.txt_errores.delete("1.0", "end")
        self.txt_errores.insert("end", texto)
        self.txt_errores.config(state="disabled")
        self.txt_errores.see("end")

    # ------------------------------------------------------------------
    # Tab 5: Score (jpanelScore)
    # ------------------------------------------------------------------
    def _build_tab_score(self):
        frame = self._tab_score

        izquierda = tk.Frame(frame, bg=PALETTE["bg_soft"])
        izquierda.pack(side="left", fill="both", expand=True, padx=(24, 12), pady=24)

        tk.Label(izquierda, text="🏆 Resultados", font=FONT_TITLE,
                 fg=PALETTE["accent_dark"], bg=PALETTE["bg_soft"]).pack(anchor="w", pady=(0, 12))

        creditos = tk.Canvas(izquierda, width=360, height=44, bg=PALETTE["bg_soft"], highlightthickness=0)
        creditos.pack(side="bottom", anchor="w", pady=(12, 0))
        _rounded_rect(creditos, 0, 0, 360, 44, radius=12, fill=PALETTE["surface"], outline="")
        creditos.create_text(180, 22,
                             text="✒️ A.Copara, A.Chavez,\nD.Bocanegra, A.Zarabia, E.Saavedra",
                             font=FONT_LABEL, fill=PALETTE["muted"], justify="center")

        # Las tarjetas de resultado se generan dinamicamente en
        # _mostrar_score (una por jugador, ordenadas por puntaje), ya
        # que ahora la partida puede tener entre 2 y 6 jugadores en vez
        # de los 2 fijos del Java original. Se envuelven en un Canvas
        # con scroll por si 6 tarjetas no entran verticalmente.
        lista_frame = tk.Frame(izquierda, bg=PALETTE["bg_soft"])
        lista_frame.pack(fill="both", expand=True)

        self.score_scroll_canvas = tk.Canvas(lista_frame, bg=PALETTE["bg_soft"], highlightthickness=0)
        score_scroll = ttk.Scrollbar(lista_frame, orient="vertical", command=self.score_scroll_canvas.yview)
        self.score_scroll_canvas.configure(yscrollcommand=score_scroll.set)
        self.score_scroll_canvas.pack(side="left", fill="both", expand=True)
        score_scroll.pack(side="left", fill="y")

        self.score_cards_frame = tk.Frame(self.score_scroll_canvas, bg=PALETTE["bg_soft"])
        self.score_scroll_canvas.create_window((0, 0), window=self.score_cards_frame, anchor="nw")
        self.score_cards_frame.bind(
            "<Configure>",
            lambda e: self.score_scroll_canvas.configure(scrollregion=self.score_scroll_canvas.bbox("all")),
        )

        derecha = tk.Frame(frame, bg=PALETTE["bg_soft"])
        derecha.pack(side="right", fill="both", expand=True, padx=(12, 24), pady=24)
        self._gif_label = tk.Label(derecha, bg=PALETTE["bg_soft"])
        self._gif_label.pack(expand=True)
        self._cargar_gif_animado(ASSETS_DIR / "aaaaaa.gif")

    def _tarjeta_score(self, parent, medalla, color, texto_puesto, texto_resultado):
        card_w, card_h = 380, 90
        canvas = tk.Canvas(parent, width=card_w, height=card_h, bg=PALETTE["bg_soft"], highlightthickness=0)
        canvas.pack(pady=6)
        _rounded_rect(canvas, 2, 2, card_w - 2, card_h - 2, radius=16,
                      fill=PALETTE["surface"], outline=color, width=3)
        canvas.create_text(38, card_h / 2, text=medalla, font=(FONT_FAMILY, 22))
        canvas.create_text(72, 30, text=texto_puesto, font=FONT_SCORE_TITLE,
                            fill=PALETTE["text"], anchor="w", width=card_w - 90)
        canvas.create_text(72, 60, text=texto_resultado, font=FONT_SCORE_BODY,
                            fill=PALETTE["muted"], anchor="w", width=card_w - 90)

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
            cuadro.thumbnail((300, 300))
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
        if self.juego is None:
            return
        turno = self.juego.get_jugador_actual().get_nombre()
        estado = "Partida terminada" if self.juego.finalizada else f"Turno: {turno}"
        self.lbl_turno.config(text=f"{estado} | Preguntas restantes: {len(self.juego.preguntas_pendientes)}")

        for canvas in self.casilla_canvas:
            canvas._jugadores_aqui = []

        for idx, jugador in enumerate(self.juego.get_jugadores()):
            pos = jugador.get_posicion()
            marcador = f"J{idx + 1}"
            if 0 <= pos < len(self.casilla_canvas):
                self.casilla_canvas[pos]._jugadores_aqui.append(marcador)

        for canvas in self.casilla_canvas:
            self._redibujar_casilla(canvas)

        for i, jugador in enumerate(self.juego.get_jugadores()):
            proxies = self.paneles_jugadores[i]
            proxies["puntos"].config(text=f"Puntos: {jugador.get_puntos()}")
            proxies["comodines"].config(text=f"Comodines: {jugador.get_comodines()}")

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
        if self.juego is None or self._partida_finalizada or self._turno_en_curso:
            return
        self._turno_en_curso = True
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
            self._resolver_tirada(valor_dado)

    def _resolver_tirada(self, valor_dado: int):
        """Continua jbtnTirarActionPerformed una vez que la animacion del
        dado terminó y se conoce el resultado final."""
        if self.juego is None or self._partida_finalizada:
            return
        self.btn_tirar.config(state="disabled")
        jugador_actual = self.juego.get_jugador_actual()
        jugador_actual.mover(valor_dado, len(self.casilla_canvas))

        # Si el jugador GANA el comodín en esta tirada, el turno termina
        # ahi mismo: no se le hace pregunta esta vez. Recien en un turno
        # futuro (cuando ya tiene el comodin en mano desde antes), la
        # pregunta se muestra con normalidad pero el dialogo agrega un
        # boton extra "Usar Comodín" (ver _dialogo_pregunta) para
        # saltarla sin sumar puntos.
        if jugador_actual.get_posicion() == 5:
            jugador_actual.ganar_comodin()
            messagebox.showinfo("Comodín", f"{jugador_actual.get_nombre()} ganó un comodín")
        else:
            self._hacer_pregunta(jugador_actual)

        self._actualizar_tablero()

        # A diferencia del Java original (que comparaba puntosJ1 >= 100
        # || puntosJ2 >= 100, hardcodeado a 2 jugadores), aqui se revisa
        # si CUALQUIERA de los N jugadores llego a 100 puntos.
        if self.juego.comprobar_final():
            self._partida_finalizada = True
            self._turno_en_curso = False
            self._actualizar_tablero()
            self._guardar_partida()
            if self.juego.motivo_fin == "sin_preguntas":
                messagebox.showinfo("Fin de la partida", "Se agotaron las preguntas sin repetir. Se clasificará a los jugadores por sus puntos.")
            self._mostrar_score()
            return

        self.juego.siguiente_turno()
        self._turno_en_curso = False
        self._actualizar_tablero()
        self._guardar_partida()
        self.btn_tirar.config(state="normal")

    def _hacer_pregunta(self, jugador):
        pregunta = self.juego.sacar_pregunta()
        if pregunta is None:
            return
        respuesta = self._dialogo_pregunta(jugador, pregunta.get_enunciado())

        if respuesta is _USAR_COMODIN:
            # Saltar la pregunta con el comodin es neutral a proposito:
            # no suma puntos ni cuenta como fallo, para que el jugador
            # no pueda aprovecharse del comodin como una forma gratuita
            # de ganar puntos.
            jugador.usar_comodin()
            messagebox.showinfo("Comodín", "Has usado un comodín. Saltaste la pregunta sin sumar puntos.")
            return

        correcta = evaluar_respuesta(jugador, pregunta, respuesta)

        if correcta:
            messagebox.showinfo("Resultado", "Correcto, +10 puntos")
        else:
            messagebox.showinfo("Resultado", "Incorrecto, será para la proxima")

        self._actualizar_errores()

    def _dialogo_pregunta(self, jugador, enunciado: str):
        """Ventana modal propia para la pregunta: a diferencia de
        `tkinter.simpledialog.askstring` (que solo trae OK/Cancelar), se
        le agrega un tercer boton "Usar Comodín", visible unicamente si
        el jugador todavia tiene comodines disponibles.

        Devuelve la respuesta escrita (str), None si se canceló/cerró
        sin responder, o el sentinela `_USAR_COMODIN` si el jugador
        eligió saltar la pregunta con su comodín.
        """
        resultado = {"valor": None}

        dialogo = tk.Toplevel(self)
        dialogo.title("Pregunta")
        dialogo.configure(bg=PALETTE["surface"])
        dialogo.resizable(False, False)
        dialogo.transient(self)

        tk.Label(dialogo, text=enunciado, font=FONT_BODY_BOLD, bg=PALETTE["surface"],
                 fg=PALETTE["text"], wraplength=360, justify="left").pack(padx=20, pady=(20, 12))

        entry = ttk.Entry(dialogo, font=FONT_BODY, style="Monopoly.TEntry", width=32)
        entry.pack(padx=20, pady=(0, 16), fill="x")

        botones = tk.Frame(dialogo, bg=PALETTE["surface"])
        botones.pack(padx=20, pady=(0, 20), fill="x")

        def _cerrar(valor):
            resultado["valor"] = valor
            dialogo.destroy()

        entry.bind("<Return>", lambda e: _cerrar(entry.get()))
        dialogo.protocol("WM_DELETE_WINDOW", lambda: _cerrar(None))

        if jugador.get_comodines() > 0:
            ttk.Button(botones, text="🃏 Usar Comodín", style="Secondary.TButton",
                       command=lambda: _cerrar(_USAR_COMODIN)).pack(side="left")

        ttk.Button(botones, text="Cancelar", style="Secondary.TButton",
                   command=lambda: _cerrar(None)).pack(side="right", padx=(6, 0))
        ttk.Button(botones, text="OK", style="Accent.TButton",
                   command=lambda: _cerrar(entry.get())).pack(side="right")

        entry.focus_set()
        dialogo.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - dialogo.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - dialogo.winfo_height()) // 2
        dialogo.geometry(f"+{x}+{y}")

        dialogo.grab_set()
        self.wait_window(dialogo)
        return resultado["valor"]

    def _mostrar_score(self, avisar=True):
        # A diferencia del Java original (que solo comparaba j1 vs j2
        # para decidir 1er/2do puesto), aqui se arma un ranking completo
        # de los N jugadores ordenados por puntaje, con medalla para el
        # top 3 y puesto numerado para el resto.
        for widget in self.score_cards_frame.winfo_children():
            widget.destroy()

        jugadores = self.juego.get_jugadores()
        ranking = sorted(jugadores, key=lambda j: j.get_puntos(), reverse=True)
        medallas = ["🥇", "🥈", "🥉"]

        for puesto, jugador in enumerate(ranking, start=1):
            medalla = medallas[puesto - 1] if puesto <= 3 else f"{puesto}°"
            color = PLAYER_COLORS[jugadores.index(jugador) % len(PLAYER_COLORS)]
            texto_puesto = f"{puesto}° Puesto: {jugador.get_nombre()}"
            texto_resultado = f"{jugador.get_nombre()} puntos: {jugador.get_puntos()} | Fallos: {jugador.get_fallos()}"
            self._tarjeta_score(self.score_cards_frame, medalla, color, texto_puesto, texto_resultado)

        self.notebook.select(self._tab_score)
        try:
            ruta = exportar_estadisticas(self.juego, directorio=self._directorio_resultados)
        except OSError as error:
            messagebox.showerror("Resultados sin exportar", f"La partida terminó, pero no se pudo escribir el reporte.\n{error}")
            return
        if avisar:
            messagebox.showinfo("Estadísticas", f"Resultado conservado en el historial.\n{ruta}")

    def _toggle_musica(self):
        try:
            self._reproduciendo = self._audio.alternar(ASSETS_DIR / "songMonkey.wav")
        except Exception as error:
            messagebox.showerror("Música", f"Error al reproducir audio: {error}")


class _TextProxy:
    """Envoltorio minimo para que un item de texto de un Canvas se pueda
    actualizar con la misma API `.config(text=...)` que usan los
    tk.Label, sin tener que reescribir toda la logica de juego que ya
    llama a `.config(text=...)` sobre las etiquetas."""

    def __init__(self, canvas: tk.Canvas, item_id: int, prefijo: str = ""):
        self._canvas = canvas
        self._item_id = item_id
        self._prefijo = prefijo

    def config(self, text: str | None = None, **kwargs):
        if text is not None:
            self._canvas.itemconfig(self._item_id, text=f"{self._prefijo}{text}")

    def cget(self, key):
        if key == "text":
            return self._canvas.itemcget(self._item_id, "text")
        raise KeyError(key)


def main():
    app = PrincipalApp()
    app.mainloop()


if __name__ == "__main__":
    main()
