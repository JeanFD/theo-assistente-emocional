import pygame
import threading
import os

class TTS:
    """
    Reproduz áudios pré-carregados a partir da pasta 'audio' ao lado deste módulo.
    Cada arquivo deve ter nome de chave correspondente (sem extensão).
    """
    def __init__(self, audio_dir="audio", volume=1.0):
        # Inicializa o mixer do pygame
        pygame.mixer.init()
        # Define caminho absoluto da pasta de áudios (mesmo diretório de tts.py)
        base_dir = os.path.dirname(__file__)
        self.audio_dir = os.path.join(base_dir, audio_dir)
        if not os.path.isdir(self.audio_dir):
            raise FileNotFoundError(f"Diretório de áudio não encontrado: '{self.audio_dir}'")

        self.sounds = {}
        self.channel = pygame.mixer.Channel(0)
        self.volume = volume
        self.speaking = False

        # Carrega todos os arquivos de áudio válidos
        for fname in os.listdir(self.audio_dir):
            if fname.lower().endswith((".wav", ".ogg", ".mp3")):
                key = os.path.splitext(fname)[0]
                path = os.path.join(self.audio_dir, fname)
                sound = pygame.mixer.Sound(path)
                sound.set_volume(self.volume)
                self.sounds[key] = sound

    def speak(self, key = "inicio"):
        # Reproduz o áudio correspondente à chave (nome do arquivo sem extensão)
        sound = self.sounds.get(key)
        if not sound:
            print(f"[TTS] Áudio para '{key}' não encontrado em '{self.audio_dir}'.")
            return

        def _run():
            self.speaking = True
            self.channel.play(sound)
            while self.channel.get_busy():
                pygame.time.wait(100)
            self.speaking = False

        threading.Thread(target=_run, daemon=True).start()
