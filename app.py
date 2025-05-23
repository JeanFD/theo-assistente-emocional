import pygame, sys
from enum import Enum, auto
from interface.ui import TextRenderer, GrupoBotoes
from interface.face import Face
from interface.transicao import Transicao
from sensores.batimentos import ler_batimentos
from voz.tts import TTS
from comunicacao.envio_dados import enviar_servidor

FADE_T = 0.3   
DELAY_BTWN = 0.2
DURACAO_OBRIGADO = 5.0
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)

class Estado(Enum):
    INICIO = auto()
    SELECIONAR_SENTIMENTO = auto()
    TIPO_SENTIMENTO = auto()
    ESCALA = auto()
    OBRIGADO = auto() 
    BATIMENTO = auto()
    BATIMENTO_FINALIZADO = auto()
    AJUDA_IMEDIATA = auto()
    RESPIRACAO = auto()
    GROUNDING = auto()
    DORMINDO = auto()

AUDIO_KEYS = {
    Estado.INICIO: "inicio",
    Estado.SELECIONAR_SENTIMENTO: "selecionar_sentimento",
    Estado.TIPO_SENTIMENTO: "tipo_sentimento",
    Estado.ESCALA: "escala",
    Estado.OBRIGADO: "obrigado",
    Estado.BATIMENTO: "batimento",
    Estado.BATIMENTO_FINALIZADO: "batimento_finalizado",
    Estado.AJUDA_IMEDIATA: "ajuda_imediata",
    Estado.RESPIRACAO: "respiracao",
    Estado.GROUNDING: "grounding",
}

STATE_CONFIG = {
    Estado.INICIO: ("Olá! O que deseja fazer?", ["Registrar humor", "Registrar batimento", "Suporte imediato"]),
    Estado.SELECIONAR_SENTIMENTO: ("Como você está se sentindo agora?", ["Feliz", "Neutro", "Triste", "Ansioso"]),
    Estado.TIPO_SENTIMENTO: ("Esse sentimento é positivo ou negativo?", ["Positivo", "Negativo", "Não sei"]),
    Estado.ESCALA: ("Em uma escala de 1 a 5, qual a intensidade desse sentimento?", [str(i) for i in range(1, 6)]),
    Estado.OBRIGADO: ("Obrigado! Seus dados foram registrados com sucesso.", []),
    Estado.BATIMENTO: ("Seu batimento cardíaco é de {} bpm.", ["OK"]),
    Estado.BATIMENTO_FINALIZADO: ("", []),
    Estado.AJUDA_IMEDIATA: ("Vejo que você precisa de apoio. Vamos tentar relaxar. O que prefere?", ["Respiração", "Grounding", "Voltar"]),
    Estado.RESPIRACAO: ("Respire: Inspire 3s (LED verde), segure 1s (LED amarelo), expire 3s (LED vermelho).\nRepita algumas vezes.", ["Estou melhor", "Continuo ansioso"]),
    Estado.GROUNDING: ("Diga 3 coisas que você vê agora.", ["Próxima pergunta", "Voltar"]),
    Estado.DORMINDO: ("", [])
}

class App:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.init()
        info = pygame.display.Info()
        self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        self.clock = pygame.time.Clock()

        pygame.mouse.set_visible(False)

        largura, altura = self.screen.get_size()
        self.fonte_rosto = pygame.font.SysFont("JandaManateeSolid.ttf", int(altura * 0.8), bold=True)
        self.fonte_texto = pygame.font.SysFont("Arial", int(altura*0.08), bold=True)
        self.fonte_botao = "Arial"

        self.texto = TextRenderer(self.screen, self.fonte_texto)
        self.face = Face(self.fonte_rosto, self.screen)
        self.btn_group = GrupoBotoes(largura, altura, STATE_CONFIG[Estado.INICIO][1], self.fonte_botao)

        self.estado = Estado.DORMINDO
        self.indice_selecionado = 0
        self.registro = {"sentimento": None, "tipo": None, "escala": None, "sexo": None, "bpm": None}

        self.tempo = 0.0
        self.tempo_obrigado = 0
        self.falando = False
        self.tts = TTS()                                       
        self.ultimo_texto = ""
        self.ultimo_evento = pygame.time.get_ticks() / 1000
        self.segundos_dormir = 30

        self.falando_primeiro = False 

        self.fade_fundo = Transicao(tempo_fade=1.0)
        self.fade_rosto = Transicao(tempo_fade=1.0)
        self.cor_fundo_atual = PRETO
        self.cor_rosto_atual = BRANCO

        self.fade_start_ms = pygame.time.get_ticks()
    
    def run(self):
        while True:
            dt = self.clock.tick(60) / 1000.0
            self.tempo += dt
            self.handle_events()
            self.update_tempo()
            self.render()

    def handle_events(self):
        clicked = None
        for evento in pygame.event.get():
            
            if self.estado == Estado.DORMINDO and evento.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self.estado = Estado.INICIO
                self.ultimo_evento = self.tempo
                self.btn_group = GrupoBotoes(self.screen.get_width(), self.screen.get_height(), STATE_CONFIG[Estado.INICIO][1], self.fonte_botao)
                self.ultimo_texto = ""

                self.falando_primeiro = True
                return

            if evento.type == pygame.QUIT:
                pygame.quit(), sys.exit()
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    pygame.quit(), sys.exit()
                if self.estado != Estado.DORMINDO:
                    self.ultimo_evento = self.tempo
                n = len(self.btn_group.buttons)
                if n > 0:
                    if evento.key == pygame.K_LEFT:
                        self.indice_selecionado = (self.indice_selecionado - 1) % n
                    elif evento.key == pygame.K_RIGHT:
                        self.indice_selecionado = (self.indice_selecionado + 1) % n
                    elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        clicked = self.indice_selecionado
                if self.estado == Estado.OBRIGADO and evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    clicked = -1
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if self.estado != Estado.DORMINDO:
                    self.ultimo_evento = self.tempo
                for i, btn in enumerate(self.btn_group.buttons):
                    if btn.rect.collidepoint(evento.pos):
                        clicked = i
                        break

        if clicked is not None:
            self.on_click(clicked)

    def on_click(self, clicked):
        self.fade_start_ms = pygame.time.get_ticks()

        if self.estado == Estado.INICIO:
            self.registro = {"sentimento": None, "tipo": None, "escala": None, "sexo": None, "bpm": None}
            if clicked == 0: self.estado = Estado.SELECIONAR_SENTIMENTO
            elif clicked == 1: self.estado = Estado.BATIMENTO
            elif clicked == 2: self.estado = Estado.AJUDA_IMEDIATA
        elif self.estado == Estado.SELECIONAR_SENTIMENTO:
            self.registro['sentimento'] = STATE_CONFIG[self.estado][1][clicked]
            self.estado = Estado.TIPO_SENTIMENTO if clicked == 3 else Estado.ESCALA
        elif self.estado == Estado.TIPO_SENTIMENTO:
            self.registro['tipo'] = STATE_CONFIG[self.estado][1][clicked]
            self.estado = Estado.ESCALA
        elif self.estado == Estado.ESCALA:
            self.registro['escala'] = STATE_CONFIG[self.estado][1][clicked]
            print(self.registro)
            enviar_servidor(self.registro)
            self.estado = Estado.OBRIGADO
            self.tempo_obrigado = self.tempo
        elif self.estado == Estado.OBRIGADO:
            self.estado = Estado.INICIO
        elif self.estado == Estado.BATIMENTO:
            self.registro['bpm'] = ler_batimentos()
            self.estado = Estado.BATIMENTO_FINALIZADO
        elif self.estado == Estado.BATIMENTO_FINALIZADO:
            self.estado = Estado.OBRIGADO
            self.tempo_obrigado = self.tempo
        elif self.estado == Estado.AJUDA_IMEDIATA:
            if clicked == 0: self.estado = Estado.RESPIRACAO
            elif clicked == 1: self.estado = Estado.GROUNDING
            elif clicked == 2: self.estado = Estado.INICIO
        elif self.estado in (Estado.RESPIRACAO, Estado.GROUNDING):
            self.estado = Estado.AJUDA_IMEDIATA

        # Atualiza botões para novo estado
        labels = STATE_CONFIG[self.estado][1]
        self.btn_group = GrupoBotoes(self.screen.get_width(), self.screen.get_height(), labels, self.fonte_botao)
        self.indice_selecionado = 0
        self.falando_primeiro = True  # ADICIONEI
        self.ultimo_texto = ""

    def update_tempo(self):
        if self.estado == Estado.OBRIGADO and self.tempo_obrigado is not None:
            if self.tempo - self.tempo_obrigado >= DURACAO_OBRIGADO:
                self.estado = Estado.DORMINDO
                self.indice_selecionado = 0
                self.tempo_obrigado = None
                self.btn_group = GrupoBotoes(self.screen.get_width(), self.screen.get_height(), STATE_CONFIG[Estado.INICIO][1], self.fonte_botao)
        # Vai dormir se ficar inativo
        if self.estado != Estado.DORMINDO and (self.tempo - self.ultimo_evento > self.segundos_dormir):
            self.estado = Estado.DORMINDO

    def render(self):
        if self.estado == Estado.DORMINDO and not self.fade_fundo.is_active():
            self.fade_fundo.start(self.cor_fundo_atual, PRETO, self.tempo)
            self.fade_rosto.start(self.cor_rosto_atual, BRANCO, self.tempo)
        elif self.estado != Estado.DORMINDO and not self.fade_fundo.is_active() and self.cor_fundo_atual == (0,0,0):
            self.fade_fundo.start(self.cor_fundo_atual, BRANCO, self.tempo)
            self.fade_rosto.start(self.cor_rosto_atual, PRETO, self.tempo)

        nova_cor_fundo, _ = self.fade_fundo.update(self.tempo)
        nova_cor_rosto, _ = self.fade_rosto.update(self.tempo)
        self.cor_fundo_atual = nova_cor_fundo
        self.cor_rosto_atual = nova_cor_rosto
        self.screen.fill(self.cor_fundo_atual)

        text, _ = STATE_CONFIG.get(self.estado, ("", []))
        key = AUDIO_KEYS.get(self.estado) 
        if self.estado != Estado.DORMINDO:
            self.texto.desenhar(text)
            if self.btn_group.buttons and not self.falando_primeiro:
                self.btn_group.desenhar(self.screen, self.indice_selecionado)

        self.face.update(self.tempo, self.falando, dormindo=(self.estado==Estado.DORMINDO), cor=self.cor_rosto_atual)
        self.face.desenhar(self.tempo)

        if self.falando_primeiro:
            if not self.falando and key:
                self.tts.speak(key)     
                self.falando = True
                self.ultimo_texto = key 
            elif self.falando and not self.tts.speaking:
                self.falando = False
                self.falando_primeiro = False
                self.btn_group.start_ms = pygame.time.get_ticks()
        else:
            if key and key != self.ultimo_texto and self.estado != Estado.DORMINDO:
                self.tts.speak(key)
                self.falando = True
                self.ultimo_texto = key
            elif self.falando and not self.tts.speaking:
                self.falando = False
        pygame.display.flip()

