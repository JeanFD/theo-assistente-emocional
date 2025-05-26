import pygame, sys
from enum import Enum, auto
from interface.ui import *
from interface.face import Face
from interface.transicao import Transicao
from sensores.batimentos import ler_batimentos
from voz.tts import TTS
from comunicacao.envio_dados import enviar_servidor
from pathlib import Path
import json

FADE_T = 0.3
DELAY_BTWN = 0.2
DURACAO_OBRIGADO = 5.0
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
CINZA = (200, 200, 200)
SELECIONADO = (100, 100, 255)

class Estado(Enum):
    INICIO = auto()
    SELECIONAR_SENTIMENTO = auto()
    TIPO_SENTIMENTO = auto()
    ESCALA = auto()
    OBRIGADO = auto()
    BATIMENTO_INSTRUCAO = auto()
    BATIMENTO_MEDINDO = auto()
    BATIMENTO_RESULTADO = auto()
    AJUDA_IMEDIATA = auto()
    RESPIRACAO = auto()
    GROUNDING = auto()
    DORMINDO = auto()
    CONFIG = auto()

AUDIO_KEYS = {
    Estado.INICIO: "inicio",
    Estado.SELECIONAR_SENTIMENTO: "selecionar_sentimento",
    Estado.TIPO_SENTIMENTO: "tipo_sentimento",
    Estado.ESCALA: "escala",
    Estado.OBRIGADO: "obrigado",
    Estado.BATIMENTO_INSTRUCAO: "batimento_instrucao",
    Estado.BATIMENTO_MEDINDO: "batimento_medindo",
    Estado.AJUDA_IMEDIATA: "ajuda_imediata",
    Estado.RESPIRACAO: "respiracao",
    Estado.GROUNDING: "grounding",
    "batimento_resultado_normal": "batimento_resultado_normal",
    "batimento_resultado_alto": "batimento_resultado_alto",
    "batimento_resultado_baixo": "batimento_resultado_baixo",
}

STATE_CONFIG = {
    Estado.INICIO: ("Olá! O que deseja fazer?", ["Registrar humor", "Registrar batimento", "Suporte imediato"]),
    Estado.SELECIONAR_SENTIMENTO: ("Como você está se sentindo agora?", ["Feliz", "Neutro", "Triste", "Ansioso"]),
    Estado.TIPO_SENTIMENTO: ("Esse sentimento é positivo ou negativo?", ["Positivo", "Negativo", "Não sei"]),
    Estado.ESCALA: ("Em uma escala de 1 a 5, qual a intensidade desse sentimento?", [str(i) for i in range(1, 6)]),
    Estado.OBRIGADO: ("Obrigado! Seus dados foram registrados com sucesso.", []),
    Estado.BATIMENTO_INSTRUCAO: ("Por favor, coloque o dedo no sensor para aferir seu batimento.", ["Iniciar Medição"]),
    Estado.BATIMENTO_MEDINDO: ("Medindo seu batimento cardíaco...", []),
    Estado.BATIMENTO_RESULTADO: ("", []),
    Estado.AJUDA_IMEDIATA: ("Vejo que você precisa de apoio. Vamos tentar relaxar. O que prefere?", ["Respiração", "Grounding", "Voltar"]),
    Estado.RESPIRACAO: ("Respire: Inspire 3s (LED verde), segure 1s (LED amarelo), expire 3s (LED vermelho).\nRepita algumas vezes.", ["Estou melhor", "Continuo ansioso"]),
    Estado.GROUNDING: ("Diga 3 coisas que você vê agora.", ["Próxima pergunta", "Voltar"]),
    Estado.CONFIG: ("", ["Sexo: M", "Sexo: F", "Idade: +", "Idade: -", "Concluir"]),
    Estado.DORMINDO: ("", []),
}

class App:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.init()
        info = pygame.display.Info()
        self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        self.clock = pygame.time.Clock()

        largura, altura = self.screen.get_size()
        self.fonte_rosto = pygame.font.SysFont("JandaManateeSolid.ttf", int(altura * 0.8), bold=True)
        self.fonte_texto = pygame.font.SysFont("Arial", int(altura*0.08), bold=True)
        self.fonte_botao = "Arial"

        self.texto = TextRenderer(self.screen, self.fonte_texto)
        self.face = Face(self.fonte_rosto, self.screen)
        self.btn_group = GrupoBotoes(largura, altura, STATE_CONFIG[Estado.INICIO][1], self.fonte_botao)
        self.botao_config = BotaoConfiguracao(largura, altura, pygame.font.SysFont("Symbola", 24, bold=True))

        self.estado = Estado.DORMINDO
        self.indice_selecionado = 0
        self.registro = {"sentimento": None, "tipo": None, "escala": None, "bpm": None}
        self.config = {"sexo": None, "idade": 0}
        cfg_path = Path("config.json")
        if cfg_path.exists():
            with open(cfg_path) as f:
                loaded_config = json.load(f)
                loaded_config['idade'] = int(loaded_config.get('idade', 0)) if loaded_config.get('idade') not in (None, "") else 0
                self.config.update(loaded_config)

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
        self.config_text_surface = None
        self.config_text_rect = None
        self.config_precisa_atualizar = True
        
        self.batimento_resultado_texto = ""
        self.batimento_audio_key = ""

        # Alterado: Novo sinalizador para controlar o início da medição
        self.deve_iniciar_medicao = False

    def run(self):
        while True:
            dt = self.clock.tick(60) / 1000.0
            self.tempo += dt
            
            self.handle_events()
            self.update_tempo()
            self.render()

            # Alterado: Lógica de medição movida para o loop principal
            # Isso garante que a tela "Medindo..." seja renderizada antes do programa pausar
            if self.deve_iniciar_medicao:
                self.deve_iniciar_medicao = False # Desativa o sinalizador para não medir de novo

                # A função bloqueante é chamada aqui. A tela já está mostrando "Medindo..."
                bpm = ler_batimentos()
                self.registro['bpm'] = bpm
                
                status_texto = "Normal"
                audio_key_para_tocar = AUDIO_KEYS["batimento_resultado_normal"]
                if bpm < 60:
                    status_texto = "Abaixo do normal"
                    audio_key_para_tocar = AUDIO_KEYS["batimento_resultado_baixo"]
                elif bpm > 100:
                    status_texto = "Acima do normal"
                    audio_key_para_tocar = AUDIO_KEYS["batimento_resultado_alto"]
                
                enviar_servidor(self.registro)

                self.batimento_resultado_texto = f"Seu batimento: {bpm} bpm.\n({status_texto})\n\nDados enviados. Clique para voltar."
                self.batimento_audio_key = audio_key_para_tocar
                
                # Transiciona para o estado de resultado
                self.estado = Estado.BATIMENTO_RESULTADO
                self.ultimo_texto = ""
                self.falando_primeiro = True

            pygame.display.flip()


    def handle_events(self):
        clicked = None
        for evento in pygame.event.get():
            # Alterado: Ignora todos os eventos enquanto estiver medindo
            if self.estado == Estado.BATIMENTO_MEDINDO:
                continue

            if self.estado == Estado.DORMINDO and evento.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self.estado = Estado.INICIO
                self.ultimo_evento = self.tempo
                self.btn_group = GrupoBotoes(self.screen.get_width(), self.screen.get_height(), STATE_CONFIG[Estado.INICIO][1], self.fonte_botao)
                self.ultimo_texto = ""
                self.falando_primeiro = True
                return

            if evento.type == pygame.QUIT:
                pygame.quit(), sys.exit()

            if self.estado == Estado.BATIMENTO_RESULTADO and evento.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                clicked = -1
            
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    pygame.quit(), sys.exit()
                if self.estado != Estado.DORMINDO: self.ultimo_evento = self.tempo
                n = len(self.btn_group.buttons)
                if n > 0:
                    if evento.key == pygame.K_LEFT: self.indice_selecionado = (self.indice_selecionado - 1) % n
                    elif evento.key == pygame.K_RIGHT: self.indice_selecionado = (self.indice_selecionado + 1) % n
                    elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER): clicked = self.indice_selecionado
                if self.estado == Estado.OBRIGADO and evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER): clicked = -1

            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if self.botao_config.clicado(evento.pos) and self.estado != Estado.DORMINDO:
                    self.estado = Estado.CONFIG
                    labels = ["Masculino","Feminino","+","–","Confirmar"]
                    self.btn_group = GrupoBotoes(self.screen.get_width(), self.screen.get_height(), labels, self.fonte_botao, base_color=CINZA, select_color=SELECIONADO, fade_duration=100, fade_delay=50)
                    self.indice_selecionado = 0
                    self.falando_primeiro = False
                    return

                if self.estado != Estado.DORMINDO:
                    self.ultimo_evento = self.tempo
                    for i, btn in enumerate(self.btn_group.buttons):
                        if btn.rect.collidepoint(evento.pos): clicked = i; break
        if clicked is not None:
            self.on_click(clicked)

    def on_click(self, clicked):
        self.fade_start_ms = pygame.time.get_ticks()

        if self.estado == Estado.CONFIG:
            dados_mudaram = False
            if clicked == 0 and self.config.get('sexo') != "Masculino": self.config['sexo'] = "Masculino"; dados_mudaram = True
            elif clicked == 1 and self.config.get('sexo') != "Feminino": self.config['sexo'] = "Feminino"; dados_mudaram = True
            elif clicked == 2: self.config['idade'] = min(120, self.config.get("idade", 0) + 1); dados_mudaram = True
            elif clicked == 3: self.config['idade'] = max(0, self.config.get("idade", 0) - 1); dados_mudaram = True

            if dados_mudaram: self.config_precisa_atualizar = True
            
            if clicked == 4:
                with open("config.json", "w") as f: json.dump(self.config, f)
                self.estado = Estado.INICIO
                self.falando_primeiro = True; self.ultimo_texto = ""; self.config_precisa_atualizar = True
            else:
                if clicked in (0, 1):
                    for i, btn in enumerate(self.btn_group.buttons):
                        if i == 0: btn.set_text("Masculino", selecionado=(self.config.get('sexo') == "Masculino"))
                        elif i == 1: btn.set_text("Feminino", selecionado=(self.config.get('sexo') == "Feminino"))
                self.indice_selecionado = clicked; return
                
        elif self.estado == Estado.INICIO:
            self.registro = {"sentimento": None, "tipo": None, "escala": None, "sexo": None, "bpm": None}
            if clicked == 0: self.estado = Estado.SELECIONAR_SENTIMENTO
            elif clicked == 1: self.estado = Estado.BATIMENTO_INSTRUCAO
            elif clicked == 2: self.estado = Estado.AJUDA_IMEDIATA
                
        elif self.estado == Estado.SELECIONAR_SENTIMENTO:
            self.registro['sentimento'] = STATE_CONFIG[self.estado][1][clicked]
            self.estado = Estado.TIPO_SENTIMENTO if clicked == 3 else Estado.ESCALA
        elif self.estado == Estado.TIPO_SENTIMENTO:
            self.registro['tipo'] = STATE_CONFIG[self.estado][1][clicked]
            self.estado = Estado.ESCALA
        elif self.estado == Estado.ESCALA:
            self.registro['escala'] = STATE_CONFIG[self.estado][1][clicked]
            enviar_servidor(self.registro); self.estado = Estado.OBRIGADO; self.tempo_obrigado = self.tempo
        elif self.estado == Estado.OBRIGADO:
            self.estado = Estado.INICIO
        
        elif self.estado == Estado.BATIMENTO_INSTRUCAO:
            # Alterado: Apenas muda o estado e ativa o sinalizador. A medição foi movida.
            self.estado = Estado.BATIMENTO_MEDINDO
            self.deve_iniciar_medicao = True
            self.ultimo_texto = ""; self.falando_primeiro = True
            return # Retorna para evitar a recriação de botões

        elif self.estado == Estado.BATIMENTO_RESULTADO:
            self.estado = Estado.INICIO; self.falando_primeiro = True

        elif self.estado == Estado.AJUDA_IMEDIATA:
            if clicked == 0: self.estado = Estado.RESPIRACAO
            elif clicked == 1: self.estado = Estado.GROUNDING
            elif clicked == 2: self.estado = Estado.INICIO
        elif self.estado in (Estado.RESPIRACAO, Estado.GROUNDING):
            self.estado = Estado.AJUDA_IMEDIATA

        labels = STATE_CONFIG[self.estado][1]
        self.btn_group = GrupoBotoes(self.screen.get_width(), self.screen.get_height(), labels, self.fonte_botao)
        self.indice_selecionado = 0
        if self.estado != Estado.INICIO: self.falando_primeiro = True
        self.ultimo_texto = ""

    def update_tempo(self):
        if self.estado == Estado.OBRIGADO and self.tempo_obrigado is not None:
            if self.tempo - self.tempo_obrigado >= DURACAO_OBRIGADO:
                self.estado = Estado.DORMINDO; self.indice_selecionado = 0; self.tempo_obrigado = None
                self.btn_group = GrupoBotoes(self.screen.get_width(), self.screen.get_height(), STATE_CONFIG[Estado.INICIO][1], self.fonte_botao)
        if self.estado != Estado.DORMINDO and (self.tempo - self.ultimo_evento > self.segundos_dormir):
            self.estado = Estado.DORMINDO

    def render(self):
        if self.estado != Estado.CONFIG:
            if self.estado == Estado.DORMINDO and not self.fade_fundo.is_active():
                self.fade_fundo.start(self.cor_fundo_atual, PRETO, self.tempo); self.fade_rosto.start(self.cor_rosto_atual, BRANCO, self.tempo)
            elif self.estado != Estado.DORMINDO and not self.fade_fundo.is_active() and self.cor_fundo_atual == PRETO:
                self.fade_fundo.start(self.cor_fundo_atual, BRANCO, self.tempo); self.fade_rosto.start(self.cor_rosto_atual, PRETO, self.tempo)
            
            nova_cor_fundo, _ = self.fade_fundo.update(self.tempo); nova_cor_rosto, _ = self.fade_rosto.update(self.tempo)
            self.cor_fundo_atual = nova_cor_fundo; self.cor_rosto_atual = nova_cor_rosto
        
        self.screen.fill(self.cor_fundo_atual if self.estado != Estado.CONFIG else BRANCO)

        text, _ = STATE_CONFIG.get(self.estado, ("", []))
        key = AUDIO_KEYS.get(self.estado)

        if self.estado != Estado.DORMINDO:
            if self.estado == Estado.BATIMENTO_RESULTADO:
                self.texto.desenhar(self.batimento_resultado_texto, self.cor_rosto_atual)
            elif self.estado == Estado.CONFIG:
                if self.config_precisa_atualizar:
                    sexo_txt = self.config.get('sexo') or "—"; idade_txt = self.config.get('idade', 0)
                    texto_cfg = f"Configurações\nSexo: {sexo_txt}\nIdade: {idade_txt} anos"
                    lines = texto_cfg.split('\n'); rendered_lines = [self.fonte_texto.render(line, True, PRETO) for line in lines]
                    total_height = sum(line.get_height() for line in rendered_lines); max_width = max(line.get_width() for line in rendered_lines)
                    self.config_text_surface = pygame.Surface((max_width, total_height), pygame.SRCALPHA)
                    current_y = 0
                    for line_surface in rendered_lines: self.config_text_surface.blit(line_surface, (0, current_y)); current_y += line_surface.get_height()
                    screen_rect = self.screen.get_rect(); self.config_text_rect = self.config_text_surface.get_rect(center=(screen_rect.centerx, int(screen_rect.height * 0.2)))
                    self.config_precisa_atualizar = False
                if self.config_text_surface: self.screen.blit(self.config_text_surface, self.config_text_rect)
                if self.btn_group.buttons: self.btn_group.desenhar(self.screen, self.indice_selecionado)
            else:
                self.texto.desenhar(text,self.cor_rosto_atual)
                # Alterado: Não desenha botões no estado de medição
                if self.btn_group.buttons and not self.falando_primeiro and self.estado != Estado.BATIMENTO_MEDINDO:
                    self.btn_group.desenhar(self.screen, self.indice_selecionado)
        
        self.face.update(self.tempo, self.falando, dormindo=(self.estado==Estado.DORMINDO), cor=self.cor_rosto_atual)
        self.face.desenhar(self.tempo)
        
        if self.estado == Estado.INICIO: self.botao_config.desenhar(self.screen)
        
        if self.falando_primeiro:
            if not self.falando:
                if self.estado == Estado.BATIMENTO_RESULTADO:
                    self.tts.speak(key=self.batimento_audio_key)
                    self.falando = True; self.ultimo_texto = self.batimento_audio_key
                elif key:
                    self.tts.speak(key=key)
                    self.falando = True; self.ultimo_texto = key

            if self.falando and not self.tts.speaking:
                self.falando = False; self.falando_primeiro = False; self.btn_group.start_ms = pygame.time.get_ticks()
            elif not key and self.estado != Estado.BATIMENTO_RESULTADO:
                self.falando_primeiro = False; self.btn_group.start_ms = pygame.time.get_ticks()
        else:
            if key and key != self.ultimo_texto and self.estado != Estado.DORMINDO:
                self.tts.speak(key=key)
                self.falando = True; self.ultimo_texto = key
            elif self.falando and not self.tts.speaking:
                self.falando = False
        
        # O pygame.display.flip() foi movido para o final do loop principal 'run'