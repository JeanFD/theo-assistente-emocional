# voz/tts.py

import pygame
import threading
import os

class TTS:
    def __init__(self, voice_folder="masculino", volume=1.0):
        """
        Inicializa o sistema de Text-to-Speech.
        :param voice_folder: O nome da pasta da voz a ser usada (ex: 'robo', 'caruzo').
        """
        # O caminho base agora é o diretório 'voz' que contém as pastas das vozes.
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.audio_dir = os.path.join(base_dir, voice_folder)

        if not os.path.isdir(self.audio_dir):
            raise FileNotFoundError(f"Diretório de áudio não encontrado: '{self.audio_dir}'")

        self.sounds = {}
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            
        self.channel = pygame.mixer.Channel(0)
        self.volume = volume
        self.speaking = False
        self._thread = None
        self.current_voice = voice_folder

        self._load_sounds()

    def _load_sounds(self):
        """ Carrega os arquivos de áudio do diretório de voz atual. """
        self.sounds.clear() # Limpa sons de uma voz anterior
        print(f"[TTS] Carregando sons da voz: '{self.current_voice}' do diretório '{self.audio_dir}'")
        for fname in os.listdir(self.audio_dir):
            if fname.lower().endswith((".wav", ".ogg", ".mp3")):
                key = os.path.splitext(fname)[0]
                path = os.path.join(self.audio_dir, fname)
                try:
                    sound = pygame.mixer.Sound(path)
                    sound.set_volume(self.volume)
                    self.sounds[key] = sound
                except pygame.error as e:
                    print(f"[TTS] Erro ao carregar o áudio '{path}': {e}")
    
    def _play_sound_thread(self, sound_object):
        self.speaking = True
        self.channel.play(sound_object)
        while self.channel.get_busy():
            pygame.time.wait(50)
        self.speaking = False
        
    def speak(self, key="inicio"):
        if self.speaking:
            self.stop()
        sound_to_play = self.sounds.get(key)
        if not sound_to_play:
            print(f"[TTS] Áudio para a chave '{key}' não encontrado na voz '{self.current_voice}'.")
            self.speaking = False
            return
        
        self._thread = threading.Thread(target=self._play_sound_thread, args=(sound_to_play,), daemon=True)
        self._thread.start()

    def stop(self):
        if self.channel.get_busy():
            self.channel.stop()
        self.speaking = False