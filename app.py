# app.py

import pygame, sys
from enum import Enum, auto
import threading
import queue
from pathlib import Path
import json
import math

# --- Bloco de Suposições de Importação ---
# Estes imports dependem da estrutura do seu projeto.
# Certifique-se de que os caminhos e nomes estão corretos.
try:
    from interface.ui import TextRenderer, GrupoBotoes, BotaoConfiguracao
    from interface.face import Face
    from interface.transicao import Transicao
    from sensores.batimentos import ler_batimentos # Função de placeholder
    from voz.tts import TTS
    from comunicacao.envio_dados import enviar_servidor # Função de placeholder
except ImportError as e:
    print(f"Erro de importação: {e}")
    print("Verifique se a estrutura de pastas e os nomes dos arquivos estão corretos.")
    sys.exit()
# --- Fim do Bloco de Suposições ---


# --- Constantes de Cores e Tempo ---
FADE_T = 0.3
DELAY_BTWN = 0.2
DURACAO_OBRIGADO = 5.0
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
CINZA = (200, 200, 200)
SELECIONADO = (100, 100, 255)
VERDE = (0, 200, 0)
AMARELO = (255, 200, 0)
VERMELHO = (200, 0, 0)

# --- Definições de Estado ---

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
    ALERTA_TRISTEZA = auto()

class FaseRespiracao(Enum):
    INSPIRAR = auto()
    SEGURAR = auto()
    EXPIRAR = auto()

# --- Mapeamento de Áudio e Configuração de Estados ---

AUDIO_KEYS = {
    Estado.INICIO: "inicio",
    Estado.SELECIONAR_SENTIMENTO: "selecionar_sentimento",
    Estado.TIPO_SENTIMENTO: "tipo_sentimento",
    Estado.ESCALA: "escala",
    Estado.OBRIGADO: "obrigado",
    Estado.BATIMENTO_INSTRUCAO: "batimento_instrucao",
    Estado.BATIMENTO_MEDINDO: "batimento_medindo",
    Estado.AJUDA_IMEDIATA: "ajuda_imediata",
    Estado.RESPIRACAO: "respiracao_intro",
    Estado.GROUNDING: "grounding_q1",
    Estado.ALERTA_TRISTEZA: "alerta_frase1",
    "batimento_resultado_normal": "batimento_resultado_normal",
    "batimento_resultado_alto": "batimento_resultado_alto",
    "batimento_resultado_baixo": "batimento_resultado_baixo",
    "respiracao_inspire": "respiracao_inspire",
    "respiracao_segure": "respiracao_segure",
    "respiracao_expire": "respiracao_expire",
    "grounding_q1": "grounding_q1",
    "grounding_q2": "grounding_q2",
    "grounding_q3": "grounding_q3",
    "grounding_q4": "grounding_q4",
    "grounding_q5": "grounding_q5",
    "alerta_frase1": "alerta_frase1",
    "alerta_frase2": "alerta_frase2",
    "alerta_frase3": "alerta_frase3",
    "alerta_frase4": "alerta_frase4",
    "alerta_frase5": "alerta_frase5",
}

STATE_CONFIG = {
    Estado.INICIO: ("Olá! O que deseja fazer?", ["Registrar humor", "Registrar batimento", "Suporte imediato"]),
    Estado.SELECIONAR_SENTIMENTO: ("Como você está se sentindo?", ["Feliz", "Irritado", "Triste", "Ansioso"]),
    Estado.TIPO_SENTIMENTO: ("Esse sentimento é ligado a algo bom ou ruim?", ["Positivo", "Negativo", "Não sei"]),
    Estado.ESCALA: ("Em uma escala de 1 a 5, qual a intensidade desse sentimento?", [str(i) for i in range(1, 6)]),
    Estado.OBRIGADO: ("Obrigado! Registro concluído.", []),
    Estado.BATIMENTO_INSTRUCAO: ("Por favor, coloque o dedo no sensor para conferir seu batimento.", ["Iniciar Medição"]),
    Estado.BATIMENTO_MEDINDO: ("Medindo seu batimento cardíaco...", []),
    Estado.BATIMENTO_RESULTADO: ("", []),
    Estado.AJUDA_IMEDIATA: ("Vejo que você precisa de apoio. Vamos tentar relaxar. O que prefere?", ["Respiração Guiada", "Exercício Grounding"]),
    Estado.RESPIRACAO: ("Vamos respirar fundo. Siga as cores e as instruções.", ["Me sinto melhor", "Ainda preciso de ajuda"]),
    Estado.GROUNDING: ("", ["Próximo"]),
    Estado.CONFIG: ("", ["Voz", "Sexo: M", "Sexo: F", "Idade: +", "Idade: -", "Concluir"]),
    Estado.DORMINDO: ("", []),
    Estado.ALERTA_TRISTEZA: ("", []),
}

# --- Classe Principal da Aplicação ---

class App:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.init()

        info = pygame.display.Info()
        self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        self.clock = pygame.time.Clock()

        self.largura, self.altura = self.screen.get_size()

        # --- Fontes ---
        try:
            self.fonte_rosto = pygame.font.SysFont("JandaManateeSolid.ttf", int(self.altura * 0.6), bold=True)
        except pygame.error:
            print("Aviso: Fonte 'JandaManateeSolid.ttf' não encontrada. Usando Arial.")
            self.fonte_rosto = pygame.font.SysFont("Arial", int(self.altura * 0.6), bold=True)
        self.fonte_texto = pygame.font.SysFont("Arial", int(self.altura * 0.08), bold=True)
        self.fonte_botao = "Arial"
        self.fonte_guia = pygame.font.SysFont("Arial", int(self.altura * 0.06), bold=True)
        self.fonte_config_simbolo = pygame.font.SysFont("Symbola", 24, bold=True)

        # --- UI e Classes ---
        self.texto = TextRenderer(self.screen, self.fonte_texto)
        self.face = Face(self.fonte_rosto, self.screen)
        self.btn_group = GrupoBotoes(self.largura, self.altura, STATE_CONFIG[Estado.INICIO][1], self.fonte_botao)
        self.botao_config = BotaoConfiguracao(self.largura, self.altura, self.fonte_config_simbolo)

        # --- Variáveis de Estado ---
        self.estado = Estado.DORMINDO
        self.indice_selecionado = 0
        self.registro = {"sentimento": None, "tipo": None, "escala": None, "bpm": None}
        self.config = {"sexo": None, "idade": 0, "voz": "robo"}

        self.contador_tristes_consecutivas = 0
        self.limite_alerta_tristeza = 3
        self.arquivo_estado_alerta = Path("estado_alerta.json")
        self._carregar_estado_alerta()

        self._carregar_config_json()

        # --- Variáveis de Tempo e Lógica ---
        self.tempo = 0.0
        self.tempo_obrigado = None
        self.ultimo_evento = pygame.time.get_ticks() / 1000
        self.segundos_dormir = 30

        # --- TTS e Fala ---
        self.tts = TTS(voice_folder=self.config.get('voz', 'robo'))
        self.falando = False
        self.falando_primeiro = False
        self.ultimo_texto_falado_key = ""

        # --- Transições e Fades ---
        self.fade_fundo = Transicao(tempo_fade=1.0)
        self.fade_rosto = Transicao(tempo_fade=1.0)
        self.cor_fundo_atual = PRETO
        self.cor_rosto_atual = BRANCO
        self.fade_start_ms = pygame.time.get_ticks()

        # --- Variáveis de Estados Específicos ---
        self.config_text_surface = None
        self.config_text_rect = None
        self.config_precisa_atualizar = True

        self.batimento_resultado_texto = ""
        self.batimento_audio_key = ""
        self.medicao_thread = None
        self.medicao_queue = queue.Queue()

        self.grounding_perguntas = [
            "Concentre-se. Diga 5 coisas que você pode ver ao seu redor.",
            "Ótimo. Agora, 4 coisas que você pode tocar ou sentir.",
            "Continue. Diga 3 coisas que você pode ouvir neste momento.",
            "Quase lá. Mencione 2 cheiros que você consegue sentir.",
            "Para finalizar, diga 1 coisa que gosta muito"
        ]
        self.grounding_passo_atual = 0

        self.respiracao_intro_completa = False
        self.respiracao_fase = FaseRespiracao.INSPIRAR
        self.respiracao_timer = 0.0
        self.respiracao_raio_min = self.altura * 0.02
        self.respiracao_raio_max = self.altura * 0.05
        self.botoes_resp_animacao_iniciada = False
        self.respiracao_config = {
            FaseRespiracao.INSPIRAR: {"duracao": 4.0, "cor": VERDE, "texto": "Inspire...", "rosto": "O o O", "audio_key": "respiracao_inspire"},
            FaseRespiracao.SEGURAR:  {"duracao": 4.0, "cor": AMARELO, "texto": "Segure...", "rosto": "-- -- --", "audio_key": "respiracao_segure"},
            FaseRespiracao.EXPIRAR:  {"duracao": 6.0, "cor": VERMELHO, "texto": "Expire lentamente...", "rosto": "-- o --", "audio_key": "respiracao_expire"}
        }

        self.alerta_frases = [
            "Notei que você não tem se sentido bem nos últimos dias.",
            "Lembre-se que não há problema em não se sentir bem o tempo todo.",
            "Que tal conversar um pouco sobre o que pode estar acontecendo com uma pessoa que confia?",
            "Você também pode fazer um momento de reflexão comigo.",
            "E lembre-se, se isso persistir procure a ajuda de um profissional da saúde."
        ]
        self.alerta_audio_keys_frases = [
            "alerta_frase1", "alerta_frase2", "alerta_frase3", "alerta_frase4", "alerta_frase5"
        ]
        self.alerta_frase_atual_idx = 0

    def _carregar_config_json(self):
        cfg_path = Path("config.json")
        if cfg_path.exists():
            try:
                with open(cfg_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self.config['sexo'] = loaded_config.get('sexo')
                    idade_json = loaded_config.get('idade')
                    self.config['idade'] = int(idade_json) if isinstance(idade_json, (int, float, str)) and str(idade_json).isdigit() else 0
                    self.config['voz'] = loaded_config.get('voz', 'robo')
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Erro ao carregar ou converter config.json: {e}. Usando padrões.")
                self.config = {"sexo": None, "idade": 0, "voz": "robo"}
        else:
            print("config.json não encontrado. Usando configuração padrão.")
            self.config = {"sexo": None, "idade": 0, "voz": "robo"}

    def _carregar_estado_alerta(self):
        if self.arquivo_estado_alerta.exists():
            try:
                with open(self.arquivo_estado_alerta, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.contador_tristes_consecutivas = data.get("contador_tristes_consecutivas", 0)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Erro ao carregar {self.arquivo_estado_alerta}: {e}. Resetando contador.")
                self.contador_tristes_consecutivas = 0
        else:
            self.contador_tristes_consecutivas = 0
            print(f"{self.arquivo_estado_alerta} não encontrado. Iniciando contador de tristeza em 0.")

    def _salvar_estado_alerta(self):
        try:
            with open(self.arquivo_estado_alerta, 'w', encoding='utf-8') as f:
                json.dump({"contador_tristes_consecutivas": self.contador_tristes_consecutivas}, f, ensure_ascii=False, indent=4)
        except IOError as e:
            print(f"Erro ao salvar {self.arquivo_estado_alerta}: {e}")

    def _thread_medir_batimentos(self):
        print("Thread de medição iniciada.")
        bpm = ler_batimentos(10)
        self.medicao_queue.put(bpm)
        print(f"Thread de medição finalizada. BPM: {bpm}")

    def _resetar_para_inicio(self):
        self.estado = Estado.INICIO
        labels = STATE_CONFIG[Estado.INICIO][1]
        self.btn_group = GrupoBotoes(self.largura, self.altura, labels, self.fonte_botao)
        self.indice_selecionado = 0
        self.falando_primeiro = True
        self.ultimo_texto_falado_key = ""
        self.tempo_obrigado = None
        self.alerta_frase_atual_idx = 0
        self.botoes_resp_animacao_iniciada = False
        self.respiracao_intro_completa = False

    def _criar_botoes_config(self):
        voz_atual = self.config.get('voz', 'robo').capitalize()
        labels = [f"Voz: {voz_atual}", "Sexo: M", "Sexo: F", "Idade: +", "Idade: -", "Concluir"]
        self.btn_group = GrupoBotoes(self.largura, self.altura, labels, self.fonte_botao, base_color=CINZA, select_color=SELECIONADO, fade_duration=100, fade_delay=50)

    def run(self):
        while True:
            dt = self.clock.tick(60) / 1000.0
            self.tempo += dt
            self.handle_events()
            self.update_tempo(dt)
            self.render()
            pygame.display.flip()

    def handle_events(self):
        clicked = None
        for evento in pygame.event.get():
            if self.estado == Estado.BATIMENTO_MEDINDO and evento.type != pygame.QUIT:
                continue

            if self.estado == Estado.DORMINDO and evento.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self._resetar_para_inicio()
                self.ultimo_evento = self.tempo
                return

            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if evento.type == pygame.MOUSEBUTTONDOWN:
                if self.falando:
                    self.tts.stop()
                    self.falando = False
                    self.falando_primeiro = False
                    if self.btn_group and self.btn_group.buttons and self.estado not in [Estado.OBRIGADO, Estado.ALERTA_TRISTEZA, Estado.RESPIRACAO]:
                        self.btn_group.start_ms = pygame.time.get_ticks()
                    elif self.estado == Estado.RESPIRACAO and not self.botoes_resp_animacao_iniciada:
                        if self.btn_group and self.btn_group.buttons:
                            self.btn_group.start_ms = pygame.time.get_ticks()
                        self.botoes_resp_animacao_iniciada = True

                    self.ultimo_evento = self.tempo

                    if self.estado == Estado.RESPIRACAO and not self.respiracao_intro_completa:
                        # Pular a intro da respiração com um clique
                        self.falando_primeiro = False
                        self.respiracao_intro_completa = True
                        self.respiracao_timer = 0
                        fase_inicial_config = self.respiracao_config[self.respiracao_fase]
                        self.tts.speak(key=fase_inicial_config["audio_key"])
                        self.falando = True
                        self.ultimo_texto_falado_key = fase_inicial_config["audio_key"]

                    if self.estado == Estado.OBRIGADO:
                        self._resetar_para_inicio()
                    elif self.estado == Estado.ALERTA_TRISTEZA:
                        self.alerta_frase_atual_idx += 1
                        if self.alerta_frase_atual_idx < len(self.alerta_frases):
                            proxima_chave_audio_alerta = self.alerta_audio_keys_frases[self.alerta_frase_atual_idx]
                            self.tts.speak(key=proxima_chave_audio_alerta)
                            self.falando = True
                            self.ultimo_texto_falado_key = proxima_chave_audio_alerta
                            if self.alerta_frase_atual_idx == len(self.alerta_frases) - 1:
                                self.btn_group = GrupoBotoes(self.largura, self.altura, ["Concluir"], self.fonte_botao)
                                self.indice_selecionado = 0
                            elif self.btn_group and self.btn_group.buttons:
                                self.btn_group.start_ms = pygame.time.get_ticks()
                        else:
                            self._resetar_para_inicio()
                    return

                elif self.estado == Estado.OBRIGADO:
                    self._resetar_para_inicio()
                    return
                elif self.estado == Estado.ALERTA_TRISTEZA:
                    if self.btn_group and self.btn_group.buttons:
                        if self.btn_group.buttons[0].rect.collidepoint(evento.pos):
                            clicked = 0
                        else:
                            clicked = 0
                    else:
                        clicked = 0

            if self.estado == Estado.BATIMENTO_RESULTADO and evento.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                clicked = -1

            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                if self.estado == Estado.OBRIGADO:
                    self._resetar_para_inicio()
                    return
                elif self.estado == Estado.ALERTA_TRISTEZA:
                    clicked = 0

                if self.estado != Estado.DORMINDO: self.ultimo_evento = self.tempo

                n = len(self.btn_group.buttons) if self.btn_group else 0
                if n > 0 and clicked is None:
                    if evento.key == pygame.K_LEFT: self.indice_selecionado = (self.indice_selecionado - 1) % n
                    elif evento.key == pygame.K_RIGHT: self.indice_selecionado = (self.indice_selecionado + 1) % n
                    elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER): clicked = self.indice_selecionado

            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if self.botao_config.clicado(evento.pos) and self.estado != Estado.DORMINDO:
                    self.estado = Estado.CONFIG
                    self._criar_botoes_config()
                    self.indice_selecionado = 0
                    self.falando_primeiro = False
                    self.ultimo_texto_falado_key = ""
                    self.config_precisa_atualizar = True
                    return

                if self.estado != Estado.DORMINDO:
                    self.ultimo_evento = self.tempo
                    if self.btn_group and self.btn_group.buttons:
                        for i, btn in enumerate(self.btn_group.buttons):
                            if btn.rect.collidepoint(evento.pos):
                                clicked = i
                                break

        if clicked is not None:
            self.on_click(clicked)

    def on_click(self, clicked):
        self.fade_start_ms = pygame.time.get_ticks()
        estado_anterior = self.estado

        if self.estado == Estado.CONFIG:
            dados_mudaram = False
            if clicked == 0:
                self.config['voz'] = 'caruzo' if self.config.get('voz', 'robo') == 'robo' else 'robo'
                self.tts = TTS(voice_folder=self.config['voz'])
                print(f"Voz alterada para: {self.config['voz']}")
                self._criar_botoes_config()
                dados_mudaram = True
            elif clicked == 1 and self.config.get('sexo') != "Masculino": self.config['sexo'] = "Masculino"; dados_mudaram = True
            elif clicked == 2 and self.config.get('sexo') != "Feminino": self.config['sexo'] = "Feminino"; dados_mudaram = True
            elif clicked == 3: self.config['idade'] = min(120, self.config.get("idade", 0) + 1); dados_mudaram = True
            elif clicked == 4: self.config['idade'] = max(0, self.config.get("idade", 0) - 1); dados_mudaram = True

            if dados_mudaram: self.config_precisa_atualizar = True

            if clicked == 5:
                with open("config.json", "w", encoding='utf-8') as f: json.dump(self.config, f, ensure_ascii=False, indent=4)
                self._resetar_para_inicio()
            else:
                self.indice_selecionado = clicked
                return

        elif self.estado == Estado.INICIO:
            self.registro = {"sentimento": None, "tipo": None, "escala": None, "bpm": None}
            if clicked == 0: self.estado = Estado.SELECIONAR_SENTIMENTO
            elif clicked == 1: self.estado = Estado.BATIMENTO_INSTRUCAO
            elif clicked == 2: self.estado = Estado.AJUDA_IMEDIATA

        elif self.estado == Estado.SELECIONAR_SENTIMENTO:
            self.registro['sentimento'] = STATE_CONFIG[self.estado][1][clicked]
            if self.registro['sentimento'] == "Ansioso":
                self.estado = Estado.TIPO_SENTIMENTO
            else:
                self.estado = Estado.ESCALA

        elif self.estado == Estado.TIPO_SENTIMENTO:
            self.registro['tipo'] = STATE_CONFIG[self.estado][1][clicked]
            self.estado = Estado.ESCALA

        elif self.estado == Estado.ESCALA:
            self.registro['escala'] = STATE_CONFIG[self.estado][1][clicked]
            enviar_servidor(self.registro)

            emocao_registrada = self.registro.get('sentimento')
            if emocao_registrada == "Triste":
                self.contador_tristes_consecutivas += 1
            else:
                self.contador_tristes_consecutivas = 0
            self._salvar_estado_alerta()

            if self.contador_tristes_consecutivas >= self.limite_alerta_tristeza:
                self.estado = Estado.ALERTA_TRISTEZA
                self.alerta_frase_atual_idx = 0
                self.contador_tristes_consecutivas = 0
                self._salvar_estado_alerta()
                if len(self.alerta_frases) > 1:
                    labels_alerta = ["Próximo"]
                else:
                    labels_alerta = ["Concluir"]
                self.btn_group = GrupoBotoes(self.largura, self.altura, labels_alerta, self.fonte_botao)
                self.indice_selecionado = 0
            else:
                self.estado = Estado.OBRIGADO
                self.tempo_obrigado = self.tempo

        elif self.estado == Estado.OBRIGADO:
            if clicked == -1:
                self._resetar_para_inicio()

        elif self.estado == Estado.BATIMENTO_INSTRUCAO:
            if clicked == 0:
                self.estado = Estado.BATIMENTO_MEDINDO
                if self.medicao_thread is None or not self.medicao_thread.is_alive():
                    self.medicao_thread = threading.Thread(target=self._thread_medir_batimentos, daemon=True)
                    self.medicao_thread.start()

        elif self.estado == Estado.BATIMENTO_RESULTADO:
            if clicked == -1:
                self._resetar_para_inicio()

        elif self.estado == Estado.AJUDA_IMEDIATA:
            if clicked == 0:
                self.estado = Estado.RESPIRACAO
                self.respiracao_intro_completa = False
                self.respiracao_timer = 0.0
                self.botoes_resp_animacao_iniciada = False
            elif clicked == 1:
                self.estado = Estado.GROUNDING
                self.grounding_passo_atual = 0

        elif self.estado == Estado.RESPIRACAO:
            if clicked == 0:
                self._resetar_para_inicio()
            elif clicked == 1:
                self.estado = Estado.AJUDA_IMEDIATA

        elif self.estado == Estado.GROUNDING:
            if self.btn_group and len(self.btn_group.buttons) == 2 and self.btn_group.buttons[0].label == "Me sinto melhor":
                if clicked == 0:
                    self._resetar_para_inicio()
                elif clicked == 1:
                    self.estado = Estado.AJUDA_IMEDIATA
            elif clicked == 0:
                self.grounding_passo_atual += 1
                if self.grounding_passo_atual >= len(self.grounding_perguntas):
                    self.estado = Estado.AJUDA_IMEDIATA
                else:
                    proxima_chave_grounding = f"grounding_q{self.grounding_passo_atual + 1}"
                    if proxima_chave_grounding in AUDIO_KEYS:
                        self.tts.speak(key=proxima_chave_grounding)
                        self.falando = True
                        self.ultimo_texto_falado_key = proxima_chave_grounding
                    else:
                        self.falando = False

                    if self.grounding_passo_atual == len(self.grounding_perguntas) - 1:
                        labels_grounding_final = ["Me sinto melhor", "Ainda preciso de ajuda"]
                        self.btn_group = GrupoBotoes(self.largura, self.altura, labels_grounding_final, self.fonte_botao)
                    else:
                        labels_grounding_prox = STATE_CONFIG[Estado.GROUNDING][1]
                        self.btn_group = GrupoBotoes(self.largura, self.altura, labels_grounding_prox, self.fonte_botao)
                    self.indice_selecionado = 0
                    return

        elif self.estado == Estado.ALERTA_TRISTEZA:
            if clicked == 0:
                self.alerta_frase_atual_idx += 1
                if self.alerta_frase_atual_idx < len(self.alerta_frases):
                    proxima_chave_audio_alerta = self.alerta_audio_keys_frases[self.alerta_frase_atual_idx]
                    self.tts.speak(key=proxima_chave_audio_alerta)
                    self.falando = True
                    self.ultimo_texto_falado_key = proxima_chave_audio_alerta
                    self.falando_primeiro = False

                    if self.alerta_frase_atual_idx == len(self.alerta_frases) - 1:
                        labels_alerta = ["Concluir"]
                    else:
                        labels_alerta = ["Próximo"]
                    self.btn_group = GrupoBotoes(self.largura, self.altura, labels_alerta, self.fonte_botao)
                    self.indice_selecionado = 0
                else:
                    self._resetar_para_inicio()
                return

        if estado_anterior != self.estado:
            if self.estado not in [Estado.ALERTA_TRISTEZA, Estado.GROUNDING, Estado.CONFIG]:
                labels = STATE_CONFIG.get(self.estado, (None, []))[1]
                self.btn_group = GrupoBotoes(self.largura, self.altura, labels, self.fonte_botao)
            elif self.estado == Estado.GROUNDING and self.grounding_passo_atual < len(self.grounding_perguntas) - 1:
                labels = STATE_CONFIG[Estado.GROUNDING][1]
                self.btn_group = GrupoBotoes(self.largura, self.altura, labels, self.fonte_botao)
            elif self.estado == Estado.ALERTA_TRISTEZA and self.alerta_frase_atual_idx == 0:
                if len(self.alerta_frases) > 1: labels_alerta = ["Próximo"]
                else: labels_alerta = ["Concluir"]
                self.btn_group = GrupoBotoes(self.largura, self.altura, labels_alerta, self.fonte_botao)

            self.indice_selecionado = 0

            if not self.falando:
                if AUDIO_KEYS.get(self.estado) and self.estado != Estado.INICIO:
                    self.falando_primeiro = True
                else:
                    self.falando_primeiro = False
                self.ultimo_texto_falado_key = ""

    def update_tempo(self, dt):
        if self.estado == Estado.BATIMENTO_MEDINDO:
            try:
                bpm = self.medicao_queue.get_nowait()
                self.registro['bpm'] = bpm
                status_texto = "normal"
                audio_key_para_tocar = "batimento_resultado_normal"
                if bpm < 60: status_texto = "está abaixo do normal. Fique atento a possíveis motivos!"; audio_key_para_tocar = "batimento_resultado_baixo"
                elif bpm > 100: status_texto = "acima do normal"; audio_key_para_tocar = "batimento_resultado_alto"
                enviar_servidor(self.registro)
                self.batimento_resultado_texto = f"{bpm} bpm.\nSeu batimento está {status_texto} \nRegistro concluído."
                self.batimento_audio_key = audio_key_para_tocar
                self.estado = Estado.BATIMENTO_RESULTADO
                self.falando_primeiro = True
            except queue.Empty: pass

        if self.estado == Estado.RESPIRACAO and self.respiracao_intro_completa:
            self.respiracao_timer += dt
            config_fase_atual = self.respiracao_config[self.respiracao_fase]
            if self.respiracao_timer >= config_fase_atual["duracao"]:
                self.respiracao_timer = 0
                fase_anterior = self.respiracao_fase
                if self.respiracao_fase == FaseRespiracao.INSPIRAR: self.respiracao_fase = FaseRespiracao.SEGURAR
                elif self.respiracao_fase == FaseRespiracao.SEGURAR: self.respiracao_fase = FaseRespiracao.EXPIRAR
                elif self.respiracao_fase == FaseRespiracao.EXPIRAR: self.respiracao_fase = FaseRespiracao.INSPIRAR
                if fase_anterior != self.respiracao_fase:
                    nova_config_fase = self.respiracao_config[self.respiracao_fase]
                    fase_audio_key = nova_config_fase.get("audio_key")
                    if fase_audio_key:
                        self.tts.speak(key=fase_audio_key)
                        self.falando = True
                        self.ultimo_texto_falado_key = fase_audio_key
                    else: self.falando = False

        if self.estado == Estado.OBRIGADO and self.tempo_obrigado is not None and not self.falando:
            if self.ultimo_texto_falado_key in self.alerta_audio_keys_frases:
                pass
            elif self.tempo - self.tempo_obrigado >= DURACAO_OBRIGADO:
                self.estado = Estado.DORMINDO
                self.indice_selecionado = 0
                self.tempo_obrigado = None
                self.btn_group = GrupoBotoes(self.largura, self.altura, STATE_CONFIG[Estado.INICIO][1], self.fonte_botao)
                self.ultimo_texto_falado_key = ""

        if self.estado != Estado.DORMINDO and \
           self.estado != Estado.RESPIRACAO and \
           self.estado != Estado.BATIMENTO_MEDINDO and \
           self.estado != Estado.ALERTA_TRISTEZA and \
           not self.falando and \
           (self.tempo - self.ultimo_evento > self.segundos_dormir):
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

        cor_rosto_para_render = self.cor_rosto_atual
        rosto_override_para_render = None
        if self.estado == Estado.RESPIRACAO and self.respiracao_intro_completa:
            config_fase_atual_rosto = self.respiracao_config[self.respiracao_fase]
            rosto_override_para_render = config_fase_atual_rosto["rosto"]
        self.face.update(self.tempo, self.falando, dormindo=(self.estado==Estado.DORMINDO), cor=cor_rosto_para_render, rosto_override=rosto_override_para_render)
        self.face.desenhar(self.tempo)

        if self.estado != Estado.DORMINDO:
            texto_principal_estado, _ = STATE_CONFIG.get(self.estado, ("", []))
            chave_audio_principal_estado = AUDIO_KEYS.get(self.estado)

            if self.estado == Estado.GROUNDING:
                pergunta_atual = self.grounding_perguntas[self.grounding_passo_atual]
                self.texto.desenhar(pergunta_atual, cor=self.cor_rosto_atual)
                if not self.falando and self.btn_group:
                    self.btn_group.desenhar(self.screen, self.indice_selecionado)

            elif self.estado == Estado.RESPIRACAO:
                if not self.respiracao_intro_completa:
                    self.texto.desenhar(texto_principal_estado, cor=self.cor_rosto_atual)
                    if not self.falando and self.ultimo_texto_falado_key == "respiracao_intro":
                        self.respiracao_intro_completa = True
                        self.respiracao_timer = 0
                        self.falando_primeiro = False
                        fase_inicial_config = self.respiracao_config[self.respiracao_fase]
                        self.tts.speak(key=fase_inicial_config["audio_key"])
                        self.falando = True
                        self.ultimo_texto_falado_key = fase_inicial_config["audio_key"]
                else:
                    config_fase_render = self.respiracao_config[self.respiracao_fase]
                    progresso = self.respiracao_timer / config_fase_render["duracao"]
                    raio_atual = 0
                    if self.respiracao_fase == FaseRespiracao.INSPIRAR: raio_atual = self.respiracao_raio_min + (self.respiracao_raio_max - self.respiracao_raio_min) * progresso
                    elif self.respiracao_fase == FaseRespiracao.SEGURAR: raio_atual = self.respiracao_raio_max
                    elif self.respiracao_fase == FaseRespiracao.EXPIRAR: raio_atual = self.respiracao_raio_max - (self.respiracao_raio_max - self.respiracao_raio_min) * progresso
                    
                    texto_guia_surf = self.fonte_guia.render(config_fase_render["texto"], True, self.cor_rosto_atual)
                    texto_guia_rect = texto_guia_surf.get_rect()
                    padding = 20; largura_total_grupo = texto_guia_rect.width + padding + (raio_atual * 2)
                    x_inicio_grupo = (self.largura - largura_total_grupo) / 2; pos_y_centro = self.altura * 0.15
                    texto_guia_rect.left = x_inicio_grupo; texto_guia_rect.centery = pos_y_centro
                    self.screen.blit(texto_guia_surf, texto_guia_rect)
                    pos_bola_x = x_inicio_grupo + texto_guia_rect.width + padding + raio_atual
                    pygame.draw.circle(self.screen, config_fase_render["cor"], (pos_bola_x, pos_y_centro), raio_atual)

                    if not self.botoes_resp_animacao_iniciada and not self.falando:
                        self.botoes_resp_animacao_iniciada = True
                        if self.btn_group and self.btn_group.buttons:
                            self.btn_group.start_ms = pygame.time.get_ticks()

                    if self.botoes_resp_animacao_iniciada and self.btn_group:
                        self.btn_group.desenhar(self.screen, self.indice_selecionado)

            elif self.estado == Estado.BATIMENTO_RESULTADO:
                self.texto.desenhar(self.batimento_resultado_texto, cor=self.cor_rosto_atual)

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
                if self.btn_group and self.btn_group.buttons: self.btn_group.desenhar(self.screen, self.indice_selecionado)

            elif self.estado == Estado.ALERTA_TRISTEZA:
                if self.alerta_frase_atual_idx < len(self.alerta_frases):
                    frase_para_mostrar = self.alerta_frases[self.alerta_frase_atual_idx]
                    self.texto.desenhar(frase_para_mostrar, cor=self.cor_rosto_atual)
                if not self.falando and self.btn_group and self.btn_group.buttons:
                    self.btn_group.desenhar(self.screen, self.indice_selecionado)

            else:
                if texto_principal_estado:
                    self.texto.desenhar(texto_principal_estado, cor=self.cor_rosto_atual)
                if self.btn_group and self.btn_group.buttons and not self.falando_primeiro and self.estado != Estado.BATIMENTO_MEDINDO:
                    self.btn_group.desenhar(self.screen, self.indice_selecionado)

        if self.estado == Estado.INICIO: 
            self.botao_config.desenhar(self.screen)

        if self.falando_primeiro:
            if not self.falando:
                audio_key_para_tocar = None
                if self.estado == Estado.BATIMENTO_RESULTADO:
                    audio_key_para_tocar = self.batimento_audio_key
                elif chave_audio_principal_estado:
                    audio_key_para_tocar = chave_audio_principal_estado

                if audio_key_para_tocar and self.ultimo_texto_falado_key != audio_key_para_tocar:
                    self.tts.speak(key=audio_key_para_tocar)
                    self.falando = True
                    self.ultimo_texto_falado_key = audio_key_para_tocar

            if self.falando and not self.tts.speaking:
                self.falando = False
                self.falando_primeiro = False
                if self.estado == Estado.ALERTA_TRISTEZA:
                    if self.btn_group and self.btn_group.buttons:
                        self.btn_group.start_ms = pygame.time.get_ticks()
                elif self.estado != Estado.RESPIRACAO: # A respiração tem sua própria lógica de quando mostrar botões
                    if self.btn_group and self.btn_group.buttons:
                        self.btn_group.start_ms = pygame.time.get_ticks()

            elif not chave_audio_principal_estado and self.estado != Estado.BATIMENTO_RESULTADO:
                self.falando_primeiro = False
                if self.btn_group and self.btn_group.buttons:
                    self.btn_group.start_ms = pygame.time.get_ticks()
        else:
            if self.falando and not self.tts.speaking:
                self.falando = False
                if self.estado == Estado.ALERTA_TRISTEZA and self.ultimo_texto_falado_key in self.alerta_audio_keys_frases:
                    if self.btn_group and self.btn_group.buttons:
                        self.btn_group.start_ms = pygame.time.get_ticks()

if __name__ == '__main__':
    app = App()
    app.run()