import pygame, sys, math
from enum import Enum, auto
from interface.ui import criar_botoes, desenhar_frase, desenhar_botoes_fade, fonte
from interface.face import Face
from interface.transicao import Transicao
from interface.tema import (
    BRANCO, PRETO, AZUL_MARINHO,
    COR_FUNDO, COR_TEXTO, BOTAO_PADRAO,
    COR_FELIZ, COR_TRISTE, COR_ANSIOSO, COR_IRRITADO,
)
from voz.tts import TTS
# from comunicacao.envio_dados import enviar_servidor

FADE_T = 0.3
DELAY_BTWN = 0.2
DURACAO_OBRIGADO = 5.0

RESP_INSPIRE_DUR = 4.0
RESP_SEGURE_DUR  = 2.0
RESP_EXPIRE_DUR  = 4.0

GROUNDING_TEXTOS = {
    1: "O que você consegue ver?",
    2: "O que você consegue ouvir?",
    3: "O que você consegue tocar?",
    4: "O que você consegue cheirar?",
    5: "O que você consegue saborear?",
}

RESP_TEXTOS = {
    "intro":   "Vamos respirar juntos...",
    "inspire": "Inspire...",
    "segure":  "Segure...",
    "expire":  "Expire...",
}


class Estado(Enum):
    INICIO = auto()
    SELECIONAR_SENTIMENTO = auto()
    TIPO_SENTIMENTO = auto()
    ESCALA = auto()
    OBRIGADO = auto()
    AJUDA_IMEDIATA = auto()
    RESPIRACAO = auto()
    GROUNDING = auto()
    DORMINDO = auto()


TTS_KEYS = {
    Estado.INICIO: "inicio",
    Estado.SELECIONAR_SENTIMENTO: "selecionar_sentimento",
    Estado.TIPO_SENTIMENTO: "tipo_sentimento",
    Estado.ESCALA: "escala",
    Estado.OBRIGADO: "obrigado",
    Estado.AJUDA_IMEDIATA: "ajuda_imediata",
    Estado.RESPIRACAO: "respiracao_intro",
    Estado.GROUNDING: "grounding_q1",
}

# Mapeia estado -> expressao do rosto
EXPRESSAO_POR_ESTADO = {
    Estado.INICIO: "feliz",
    Estado.SELECIONAR_SENTIMENTO: "neutro",
    Estado.TIPO_SENTIMENTO: "neutro",
    Estado.ESCALA: "neutro",
    Estado.OBRIGADO: "feliz",
    Estado.AJUDA_IMEDIATA: "triste",
    Estado.RESPIRACAO: "neutro",
    Estado.GROUNDING: "neutro",
    Estado.DORMINDO: "dormindo",
}

STATE_CONFIG = {
    Estado.INICIO: ("O que deseja fazer?", ["Registrar humor", "Suporte imediato"]),
    Estado.SELECIONAR_SENTIMENTO: ("Como você se sente?", ["Feliz", "Neutro", "Triste", "Ansioso"]),
    Estado.TIPO_SENTIMENTO: ("Aconteceu algo bom ou ruim?", ["Bom", "Ruim", "Não sei"]),
    Estado.ESCALA: ("Com que intensidade?", [str(i) for i in range(1, 6)]),
    Estado.OBRIGADO: ("Obrigado! Até logo.", []),
    Estado.AJUDA_IMEDIATA: ("Estou aqui com você. Vamos respirar?", ["Respiração", "Grounding", "Voltar"]),
    Estado.RESPIRACAO: ("Inspire... segure... expire.", ["Estou melhor", "Continuo ansioso"]),
    Estado.GROUNDING: ("Diga 3 coisas que você vê agora.", ["Próxima pergunta", "Voltar"]),
    Estado.DORMINDO: ("", []),
}

# Cores especificas por botao quando o estado e' SELECIONAR_SENTIMENTO
CORES_SENTIMENTO = [COR_FELIZ, AZUL_MARINHO, COR_TRISTE, COR_ANSIOSO]

# Escala visual: blobs crescentes (5 niveis) com tonalidade
def _gradiente_escala():
    """5 cores progressivamente mais intensas para a escala de intensidade."""
    return [
        (200, 215, 230),  # leve
        (130, 200, 230),
        (60, 180, 220),
        (240, 130, 80),
        (230, 60, 80),   # intenso
    ]
CORES_ESCALA = _gradiente_escala()


class App:
    def __init__(self):
        pygame.init()
        info = pygame.display.Info()
        self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        self.clock = pygame.time.Clock()

        pygame.mouse.set_visible(False)

        largura, altura = self.screen.get_size()
        self.fonte_texto = fonte(int(altura * 0.075), bold=True)
        self.fonte_botao = None  # nao usado mais, fontes vem do tema

        self.face = Face(self.screen)

        self.buttons_cache = {st: criar_botoes(largura, altura, labels) for st, (_, labels) in STATE_CONFIG.items()}

        self.estado = Estado.DORMINDO
        self.indice_selecionado = 0
        self.registro = {"sentimento": None, "tipo": None, "escala": None, "sexo": None}

        self.tempo = 0.0
        self.tempo_obrigado = 0
        self.falando = False

        self.tts = TTS()
        self.ultimo_texto = ""

        self.resp_fase = None           # "intro" | "inspire" | "segure" | "expire"
        self.resp_tempo_fase = 0.0
        self.grounding_q = 1            # questão atual (1–5)

        self.ultimo_evento = pygame.time.get_ticks() / 1000
        self.segundos_dormir = 30
        self.teclado_ativo = False
        self.ultimo_estado = Estado.DORMINDO

        self.fade_fundo = Transicao(tempo_fade=0.8)
        self.cor_fundo_atual = PRETO

        self.fade_start_ms = pygame.time.get_ticks()

    def run(self):
        while True:
            dt = self.clock.tick(60) / 1000.0
            self.tempo += dt
            self.handle_events()
            self.update_tempo()
            self.render(dt)

    def handle_events(self):
        clicked = None
        for evento in pygame.event.get():
            if self.estado == Estado.DORMINDO and evento.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self.estado = Estado.INICIO
                self.ultimo_evento = self.tempo
                return
            if evento.type == pygame.QUIT:
                pygame.quit(), sys.exit()

            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    pygame.quit(), sys.exit()

                if self.estado in STATE_CONFIG:
                    n = len(self.buttons_cache[self.estado])
                    if evento.key == pygame.K_LEFT and n > 0:
                        self.teclado_ativo = True
                        self.indice_selecionado = (self.indice_selecionado - 1) % n
                    elif evento.key == pygame.K_RIGHT and n > 0:
                        self.teclado_ativo = True
                        self.indice_selecionado = (self.indice_selecionado + 1) % n
                    elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and n > 0:
                        clicked = self.indice_selecionado

                if self.estado == Estado.OBRIGADO and evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    clicked = -1

            elif evento.type == pygame.MOUSEBUTTONDOWN:
                self.teclado_ativo = False
                for i, (btn, _) in enumerate(self.buttons_cache.get(self.estado, [])):
                    if btn.collidepoint(evento.pos):
                        clicked = i
                        break

        if clicked is not None:
            self.on_click(clicked)

    def on_click(self, clicked):
        self.fade_start_ms = pygame.time.get_ticks()
        self.ultimo_evento = self.tempo
        self.teclado_ativo = False

        if self.estado == Estado.INICIO:
            if clicked == 0:
                self.estado = Estado.SELECIONAR_SENTIMENTO
            elif clicked == 1:
                self.estado = Estado.AJUDA_IMEDIATA
            self.indice_selecionado = 0

        elif self.estado == Estado.SELECIONAR_SENTIMENTO:
            self.registro['sentimento'] = STATE_CONFIG[self.estado][1][clicked]
            if clicked == 1:  # Neutro — sem intensidade nem tipo
                self.estado = Estado.OBRIGADO
                self.tempo_obrigado = self.tempo
            elif clicked == 3:  # Ansioso — pede tipo antes da escala
                self.estado = Estado.TIPO_SENTIMENTO
            else:
                self.estado = Estado.ESCALA
            self.indice_selecionado = 0

        elif self.estado == Estado.TIPO_SENTIMENTO:
            self.registro['tipo'] = STATE_CONFIG[self.estado][1][clicked]
            self.estado = Estado.ESCALA
            self.indice_selecionado = 0

        elif self.estado == Estado.ESCALA:
            self.registro['escala'] = STATE_CONFIG[self.estado][1][clicked]
            print(self.registro)
            # enviar_servidor(self.registro)
            self.estado = Estado.OBRIGADO
            self.tempo_obrigado = self.tempo
            self.indice_selecionado = 0

        elif self.estado == Estado.OBRIGADO:
            self.estado = Estado.DORMINDO
            self.indice_selecionado = 0

        elif self.estado == Estado.AJUDA_IMEDIATA:
            if clicked == 0:
                self.estado = Estado.RESPIRACAO
                self.resp_fase = "intro"
                self.resp_tempo_fase = self.tempo
                self._tts_play("respiracao_intro")
            elif clicked == 1:
                self.estado = Estado.GROUNDING
                self.grounding_q = 1
                self._tts_play("grounding_q1")
            elif clicked == 2:
                self.estado = Estado.INICIO
            self.indice_selecionado = 0

        elif self.estado == Estado.RESPIRACAO:
            self.resp_fase = None
            self.tts.stop()
            self.falando = False
            self.estado = Estado.AJUDA_IMEDIATA
            self.indice_selecionado = 0

        elif self.estado == Estado.GROUNDING:
            if clicked == 0 and self.grounding_q < 5:
                self.grounding_q += 1
                self._tts_play(f"grounding_q{self.grounding_q}")
            else:
                self.estado = Estado.AJUDA_IMEDIATA
                self.grounding_q = 1
            self.indice_selecionado = 0

        elif self.estado == Estado.DORMINDO:
            self.estado = Estado.INICIO

    def _desenhar_circulo_respiracao(self):
        fase = self.resp_fase
        if not fase or fase == "intro":
            return

        elapsed = self.tempo - self.resp_tempo_fase
        h = self.screen.get_height()
        cx = self.screen.get_width() // 2

        r_min = int(h * 0.022)
        r_max = int(h * 0.052)

        def ease(t):
            return -(math.cos(math.pi * t) - 1) / 2

        if fase == "inspire":
            t = min(1.0, elapsed / RESP_INSPIRE_DUR)
            r = int(r_min + (r_max - r_min) * ease(t))
        elif fase == "segure":
            r = r_max
        elif fase == "expire":
            t = min(1.0, elapsed / RESP_EXPIRE_DUR)
            r = int(r_max - (r_max - r_min) * ease(t))
        else:
            return

        # Posição: à esquerda do texto, alinhado verticalmente com ele
        texto_fase = RESP_TEXTOS.get(fase, "")
        tw, _ = self.fonte_texto.size(texto_fase)
        padding = int(h * 0.02)
        # Usa r_max como reserva fixa de espaço para o círculo não deslocar o texto
        x = cx - tw // 2 - padding - r_max
        y = int(h * 0.13)

        pygame.draw.circle(self.screen, (0, 160, 225), (x, y), r)
        pygame.draw.circle(self.screen, (15, 36, 56), (x, y), r, 2)

    def _tts_play(self, key):
        self.tts.stop()
        self.tts.speak(key)
        self.falando = True
        self.ultimo_texto = key

    def _avancar_resp(self, nova_fase):
        self.resp_fase = nova_fase
        self.resp_tempo_fase = self.tempo
        self._tts_play(f"respiracao_{nova_fase}")

    def update_tempo(self):
        if self.estado == Estado.OBRIGADO and self.tempo_obrigado is not None:
            if self.tempo - self.tempo_obrigado >= DURACAO_OBRIGADO:
                self.estado = Estado.DORMINDO
                self.indice_selecionado = 0
                self.tempo_obrigado = None
        if self.estado != Estado.DORMINDO and (self.tempo - self.ultimo_evento > self.segundos_dormir):
            self.estado = Estado.DORMINDO

        if self.estado == Estado.RESPIRACAO and self.resp_fase is not None:
            elapsed = self.tempo - self.resp_tempo_fase
            if self.resp_fase == "intro" and not self.tts.speaking:
                self._avancar_resp("inspire")
            elif self.resp_fase == "inspire" and elapsed >= RESP_INSPIRE_DUR:
                self._avancar_resp("segure")
            elif self.resp_fase == "segure" and elapsed >= RESP_SEGURE_DUR:
                self._avancar_resp("expire")
            elif self.resp_fase == "expire" and elapsed >= RESP_EXPIRE_DUR:
                self._avancar_resp("inspire")

    def render(self, dt):
        estado_mudou = self.estado != self.ultimo_estado
        self.ultimo_estado = self.estado

        # Fundo: branco quando ativo, preto quando dormindo
        cor_alvo = PRETO if self.estado == Estado.DORMINDO else COR_FUNDO
        if estado_mudou and self.cor_fundo_atual != cor_alvo:
            self.fade_fundo.start(self.cor_fundo_atual, cor_alvo)
        nova_cor_fundo, _ = self.fade_fundo.update()
        self.cor_fundo_atual = nova_cor_fundo

        self.screen.fill(self.cor_fundo_atual)

        # Texto: cor escolhida por luminancia para contraste
        luminancia = sum(self.cor_fundo_atual) / 3
        cor_texto = COR_TEXTO if luminancia > 127 else BRANCO
        text, _ = STATE_CONFIG.get(self.estado, ("", []))
        if self.estado == Estado.RESPIRACAO and self.resp_fase:
            text = RESP_TEXTOS.get(self.resp_fase, text)
        elif self.estado == Estado.GROUNDING:
            text = GROUNDING_TEXTOS.get(self.grounding_q, text)
        desenhar_frase(self.screen, self.fonte_texto, text, cor=cor_texto)

        # Rosto
        dormindo = self.estado == Estado.DORMINDO
        if estado_mudou:
            self.face.set_expressao(EXPRESSAO_POR_ESTADO.get(self.estado, "neutro"))
        self.face.update(dt, self.tempo, falando=self.falando, dormindo=dormindo)
        self.face.desenhar(self.tempo)

        # Circulo animado de respiracao (na frente do rosto)
        if self.estado == Estado.RESPIRACAO:
            self._desenhar_circulo_respiracao()

        # TTS — RESPIRACAO e GROUNDING gerenciam o proprio audio via on_click/update_tempo
        if self.estado not in (Estado.RESPIRACAO, Estado.GROUNDING):
            tts_key = TTS_KEYS.get(self.estado, "")
            if tts_key and tts_key != self.ultimo_texto:
                self.tts.speak(tts_key)
                self.falando = True
                self.ultimo_texto = tts_key
        if self.falando and not self.tts.speaking:
            self.falando = False

        # Botoes
        botoes = self.buttons_cache.get(self.estado, [])
        if botoes:
            cores = None
            if self.estado == Estado.SELECIONAR_SENTIMENTO:
                cores = CORES_SENTIMENTO
            elif self.estado == Estado.ESCALA:
                cores = CORES_ESCALA
            desenhar_botoes_fade(
                self.screen, botoes, self.fonte_botao, self.indice_selecionado,
                self.fade_start_ms, FADE_T * 1000, DELAY_BTWN * 1000, self.teclado_ativo,
                cores_por_botao=cores,
            )
        pygame.display.flip()
