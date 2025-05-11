from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.properties import BooleanProperty, NumericProperty
import random, math

Window.clearcolor = (1, 1, 1, 1)

class TalkingFace(Label):
    blinking = BooleanProperty(False)
    mouth_index = NumericProperty(0)
    talking_states = ["0o0", "0-0"]

    def __init__(self, **kwargs):
        super().__init__(
            # propriedades internas
            text="0-0",
            font_size='200sp',
            halign='center', valign='middle',
            color=(0, 0, 0, 1),
            size_hint=(None, None), size=(500, 400),
            **kwargs
        )
        self.bind(size=self._upd_text_size)
        self._upd_text_size()
        # piscadas automáticas
        Clock.schedule_once(self._blink, random.uniform(2,5))
        self._float_time = 0            # fase do seno
        Clock.schedule_once(self._init_float, 0)
        # fala (vai iniciar/parar conforme o usuário)
        self.talk_event = None
        # preparo pra flutuação
        self._time = 0
        Clock.schedule_once(self._init_base, 0)

    def _upd_text_size(self, *a):
        self.text_size = self.size

    # —— piscada ——  
    def _blink(self, dt):
        if self.blinking: return
        self.blinking = True
        prev = self.text
        self.text = "^-^"
        Clock.schedule_once(lambda dt: self._end_blink(prev), 0.2)
        Clock.schedule_once(self._blink, random.uniform(2,5))

    def _end_blink(self, prev):
        self.text = prev
        self.blinking = False

    # —— fala ——  
    def _talk(self, dt):
        if self.blinking: return
        self.mouth_index = (self.mouth_index + 1) % len(self.talking_states)
        self.text = self.talking_states[self.mouth_index]

    def start_talking(self):
        if not self.talk_event:
            self.talk_event = Clock.schedule_interval(self._talk, 0.20)

    def stop_talking(self):
        if self.talk_event:
            self.talk_event.cancel()
            self.talk_event = None
            self.text = "0-0"
            self.mouth_index = 0

    # —— flutuação ——  
    def _init_base(self, dt):
        self.base_y = self.y
        Clock.schedule_interval(self._float, 1/60)

    def _init_float(self, dt):
         # guarda posição inicial
         self.base_y = self.y
         # atualiza 30× por segundo para economizar CPU
         Clock.schedule_interval(self._do_float, 1/30)

    def _float(self, dt):
        self._time += dt
        self.y = self.base_y + 10 * math.sin(self._time * 2)

    def _do_float(self, dt):
         # incrementa fase
         self._float_time += dt
         # amplitude de 5px, pulsando a 0.25 Hz (2π·0.25 ≃ 1.57 rad/s)
         desp = 5 * math.sin(self._float_time * 1.57)
         self.y = self.base_y + desp


class RobotFaceApp(App):
    def build(self):
        root = FloatLayout()

        # rostinho sempre no centro da janela
        face = TalkingFace(pos_hint={'center_x': .5, 'center_y': .5})
        root.add_widget(face)

        # botões fixos na parte de baixo
        ctrl = BoxLayout(
            size_hint=(1, .2),
            pos_hint={'x': 0, 'y': 0},
            spacing=10, padding=10
        )
        btn_talk = Button(text='Falar')
        btn_stop = Button(text='Parar')
        btn_blink = Button(text='Piscar')

        btn_talk.bind(on_press=lambda *_: face.start_talking())
        btn_stop.bind(on_press=lambda *_: face.stop_talking())
        btn_blink.bind(on_press=lambda *_: face._blink(0))

        ctrl.add_widget(btn_talk)
        ctrl.add_widget(btn_stop)
        ctrl.add_widget(btn_blink)
        root.add_widget(ctrl)

        return root

if __name__ == '__main__':
    RobotFaceApp().run()
