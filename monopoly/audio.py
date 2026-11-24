"""Reproducción mediante SDL en Windows, macOS y Linux (pygame-ce)."""

import os
from pathlib import Path


class ReproductorMusica:
    def __init__(self):
        self._mixer = None
        self.reproduciendo = False

    def alternar(self, ruta: Path) -> bool:
        if self.reproduciendo:
            self.detener()
            return False
        if not ruta.is_file():
            raise FileNotFoundError(f"Coloca el archivo de música en:\n{ruta}")
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
        try:
            from pygame import mixer
        except ImportError as error:
            raise RuntimeError("Falta pygame-ce. Instala las dependencias de requirements.txt.") from error
        if not mixer.get_init():
            mixer.init()
        mixer.music.load(str(ruta))
        mixer.music.set_volume(0.25)
        mixer.music.play(loops=-1)
        self._mixer = mixer
        self.reproduciendo = True
        return True

    def detener(self) -> None:
        if self._mixer is not None:
            self._mixer.music.stop()
            self._mixer.music.unload()
        self.reproduciendo = False

    def cerrar(self) -> None:
        self.detener()
        if self._mixer is not None:
            self._mixer.quit()
