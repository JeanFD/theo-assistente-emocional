import pyttsx3
import platform
import threading

class TTS:
    def __init__(self, rate=150, volume=1.0, voice=None):
        system = platform.system().lower()
        if system == 'windows':
            driver = 'sapi5'
        else:
            driver = 'espeak'

        try:
            self.engine = pyttsx3.init(driver)
        except Exception as e:
            print(f"[TTS] não conseguiu init('{driver}'): {e}, tentando padrão")
            self.engine = pyttsx3.init()

        self.engine.setProperty('rate', rate)
        self.engine.setProperty('volume', volume)
        if voice:
            self.engine.setProperty('voice', voice)

        self._lock = threading.Lock()
        self.speaking = False

    def speak(self, text: str):
        def _run():
            with self._lock:
                self.speaking = True
                self.engine.say(text)
                self.engine.runAndWait()
                self.speaking = False 
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()