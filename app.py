import pygame, sys
from enum import Enum, auto
import threading
import queue

from interface.ui import * # Supondo que TextRenderer, GrupoBotoes, BotaoConfiguracao estão aqui
from interface.face import Face
from interface.transicao import Transicao
from sensores.batimentos import ler_batimentos # Função placeholder
from voz.tts import TTS # Sua classe TTS
from comunicacao.envio_dados import enviar_servidor # Função placeholder
from pathlib import Path
import json
import math

# Constantes de Tempo e Cor
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

class FaseRespiracao(Enum):
    INSPIRAR = auto()
    SEGURAR = auto()
    EXPIRAR = auto()

AUDIO_KEYS = {
    Estado.INICIO: "inicio",
    Estado.SELECIONAR_SENTIMENTO: "selecionar_sentimento",
    Estado.TIPO_SENTIMENTO: "tipo_sentimento",
    Estado.ESCALA: "escala",
    Estado.OBRIGADO: "obrigado",
    Estado.BATIMENTO_INSTRUCAO: "batimento_instrucao",
    Estado.BATIMENTO_MEDINDO: "batimento_medindo", # Geralmente sem fala, ou uma música suave
    Estado.AJUDA_IMEDIATA: "ajuda_imediata",
    Estado.RESPIRACAO: "respiracao_intro", # Chave para a introdução da respiração
    Estado.GROUNDING: "grounding_q1", # Chave para a primeira pergunta do grounding
    "batimento_resultado_normal": "batimento_resultado_normal",
    "batimento_resultado_alto": "batimento_resultado_alto",
    "batimento_resultado_baixo": "batimento_resultado_baixo",

    "respiracao_inspire": "respiracao_inspire",
    "respiracao_segure": "respiracao_segure",
    "respiracao_expire": "respiracao_expire",

    "grounding_q1": "grounding_q1", # Redundante, mas pode ser útil para clareza
    "grounding_q2": "grounding_q2",
    "grounding_q3": "grounding_q3",
    "grounding_q4": "grounding_q4",
    "grounding_q5": "grounding_q5",
}

STATE_CONFIG = {
    Estado.INICIO: ("Olá! O que deseja fazer?", ["Registrar humor", "Registrar batimento", "Suporte imediato"]),
    Estado.SELECIONAR_SENTIMENTO: ("Como você está se sentindo agora?", ["Feliz", "Neutro", "Triste", "Ansioso"]),
    Estado.TIPO_SENTIMENTO: ("Esse sentimento é positivo ou negativo?", ["Positivo", "Negativo", "Não sei"]),
    Estado.ESCALA: ("Em uma escala de 1 a 5, qual a intensidade desse sentimento?", [str(i) for i in range(1, 6)]),
    Estado.OBRIGADO: ("Obrigado! Seus dados foram registrados com sucesso.", []),
    Estado.BATIMENTO_INSTRUCAO: ("Por favor, coloque o dedo no sensor para conferir seu batimento.", ["Iniciar Medição"]),
    Estado.BATIMENTO_MEDINDO: ("Medindo seu batimento cardíaco...", []),
    Estado.BATIMENTO_RESULTADO: ("", []), # O texto será dinâmico
    Estado.AJUDA_IMEDIATA: ("Vejo que você precisa de apoio. Vamos tentar relaxar. O que prefere?", ["Respiração Guiada", "Exercício Grounding"]),
    Estado.RESPIRACAO: ("Vamos respirar fundo. Siga as cores e as instruções.", ["Estou melhor"]),
    Estado.GROUNDING: ("", ["Próximo"]), # O texto será dinâmico
    Estado.CONFIG: ("", ["Sexo: M", "Sexo: F", "Idade: +", "Idade: -", "Concluir"]),
    Estado.DORMINDO: ("", []),
}

class App:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.init() # Inicializa todos os módulos do Pygame, incluindo o mixer
        
        info = pygame.display.Info()
        self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        self.clock = pygame.time.Clock()

        self.largura, self.altura = self.screen.get_size()
        
        # Fontes
        try:
            self.fonte_rosto = pygame.font.SysFont("JandaManateeSolid.ttf", int(self.altura * 0.6), bold=True)
        except pygame.error:
            print("Aviso: Fonte 'JandaManateeSolid.ttf' não encontrada. Usando Arial como fallback para o rosto.")
            self.fonte_rosto = pygame.font.SysFont("Arial", int(self.altura * 0.6), bold=True)
        self.fonte_texto = pygame.font.SysFont("Arial", int(self.altura*0.08), bold=True)
        self.fonte_botao = "Arial" # Nome da fonte para ser usado pela classe Botao
        self.fonte_guia = pygame.font.SysFont("Arial", int(self.altura*0.06), bold=True)
        self.fonte_config_simbolo = pygame.font.SysFont("Symbola", 24, bold=True)


        # Componentes da UI e Lógica
        self.texto = TextRenderer(self.screen, self.fonte_texto)
        self.face = Face(self.fonte_rosto, self.screen)
        self.btn_group = GrupoBotoes(self.largura, self.altura, STATE_CONFIG[Estado.INICIO][1], self.fonte_botao)
        self.botao_config = BotaoConfiguracao(self.largura, self.altura, self.fonte_config_simbolo)

        self.estado = Estado.DORMINDO
        self.indice_selecionado = 0
        self.registro = {"sentimento": None, "tipo": None, "escala": None, "bpm": None}
        self.config = {"sexo": None, "idade": 0}
        self._carregar_config_json() # Carrega configuração do arquivo

        # Controle de Tempo e Eventos
        self.tempo = 0.0
        self.tempo_obrigado = 0
        self.ultimo_evento = pygame.time.get_ticks() / 1000
        self.segundos_dormir = 30

        # Controle de Fala (TTS)
        self.tts = TTS() # Sua classe TTS
        self.falando = False
        self.falando_primeiro = False # Indica se é a primeira fala ao entrar em um estado
        self.ultimo_texto_falado_key = "" # Chave do último áudio que começou a tocar

        # Transições Visuais
        self.fade_fundo = Transicao(tempo_fade=1.0)
        self.fade_rosto = Transicao(tempo_fade=1.0)
        self.cor_fundo_atual = PRETO
        self.cor_rosto_atual = BRANCO
        self.fade_start_ms = pygame.time.get_ticks() # Para animação de botões

        # Cache para texto da tela de Configuração
        self.config_text_surface = None
        self.config_text_rect = None
        self.config_precisa_atualizar = True
        
        # Medição de Batimentos
        self.batimento_resultado_texto = ""
        self.batimento_audio_key = "" # Chave de áudio para o resultado do batimento
        self.medicao_thread = None
        self.medicao_queue = queue.Queue()
        
        # Exercício de Grounding
        self.grounding_perguntas = [
            "Concentre-se. Diga 5 coisas que você pode ver ao seu redor.",
            "Ótimo. Agora, 4 coisas que você pode tocar ou sentir.",
            "Continue. Diga 3 coisas que você pode ouvir neste momento.",
            "Quase lá. Mencione 2 cheiros que você consegue sentir.",
            "Para finalizar, diga 1 coisa boa sobre você."
        ]
        self.grounding_passo_atual = 0

        # Exercício de Respiração
        self.respiracao_fase = FaseRespiracao.INSPIRAR
        self.respiracao_timer = 0.0
        self.respiracao_raio_min = self.altura * 0.02
        self.respiracao_raio_max = self.altura * 0.05
        self.precisa_falar_primeiro_comando_respiracao = False
        self.respiracao_config = {
            FaseRespiracao.INSPIRAR: {"duracao": 4.0, "cor": VERDE, "texto": "Inspire...", "rosto": "O o O", "audio_key": "respiracao_inspire"},
            FaseRespiracao.SEGURAR:  {"duracao": 4.0, "cor": AMARELO, "texto": "Segure...", "rosto": "-- -- --", "audio_key": "respiracao_segure"},
            FaseRespiracao.EXPIRAR:  {"duracao": 6.0, "cor": VERMELHO, "texto": "Expire lentamente...", "rosto": "-- o --", "audio_key": "respiracao_expire"}
        }

    def _carregar_config_json(self):
        cfg_path = Path("config.json")
        if cfg_path.exists():
            try:
                with open(cfg_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self.config['sexo'] = loaded_config.get('sexo')
                    # Garante que idade seja sempre número, default 0
                    idade_json = loaded_config.get('idade')
                    self.config['idade'] = int(idade_json) if isinstance(idade_json, (int, float, str)) and str(idade_json).isdigit() else 0
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Erro ao carregar ou converter config.json: {e}. Usando valores padrão.")
                self.config = {"sexo": None, "idade": 0} # Reset para padrão em caso de erro
        else:
            print("Arquivo config.json não encontrado. Usando configuração padrão.")
            self.config = {"sexo": None, "idade": 0}

    def _thread_medir_batimentos(self):
        print("Thread de medição iniciada.")
        # Simulação de leitura de batimentos
        # bpm = random.randint(55, 105) 
        # pygame.time.wait(5000) # Simula tempo de medição
        bpm = ler_batimentos() # Sua função real
        self.medicao_queue.put(bpm)
        print(f"Thread de medição finalizada. BPM: {bpm}")

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
            if self.estado == Estado.BATIMENTO_MEDINDO and evento.type != pygame.QUIT: # Permite sair durante medição
                continue

            if self.estado == Estado.DORMINDO and evento.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self.estado = Estado.INICIO
                self.ultimo_evento = self.tempo
                self.btn_group = GrupoBotoes(self.largura, self.altura, STATE_CONFIG[Estado.INICIO][1], self.fonte_botao)
                self.falando_primeiro = True
                self.ultimo_texto_falado_key = ""
                return

            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if evento.type == pygame.MOUSEBUTTONDOWN:
                if self.falando:  
                    print("Clique para pular a fala detectado.")
                    self.tts.stop()
                    self.falando = False
                    self.falando_primeiro = False # A "fala principal" foi interrompida
                    if self.btn_group and self.btn_group.buttons:
                        self.btn_group.start_ms = pygame.time.get_ticks()
                    self.ultimo_evento = self.tempo
                    
                    # Se pulou a introdução da respiração, precisa falar o primeiro comando
                    if self.estado == Estado.RESPIRACAO and self.precisa_falar_primeiro_comando_respiracao:
                        config_fase_para_falar = self.respiracao_config[self.respiracao_fase]
                        fase_audio_key = config_fase_para_falar.get("audio_key")
                        if fase_audio_key:
                            self.tts.speak(key=fase_audio_key)
                            self.falando = True # Marca que está falando o comando
                            self.ultimo_texto_falado_key = fase_audio_key
                        self.precisa_falar_primeiro_comando_respiracao = False
                    return # Consome o evento de clique

            if self.estado == Estado.BATIMENTO_RESULTADO and evento.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                clicked = -1 # Qualquer clique/tecla avança
            
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if self.estado != Estado.DORMINDO: self.ultimo_evento = self.tempo
                
                n = len(self.btn_group.buttons) if self.btn_group else 0
                if n > 0:
                    if evento.key == pygame.K_LEFT: self.indice_selecionado = (self.indice_selecionado - 1) % n
                    elif evento.key == pygame.K_RIGHT: self.indice_selecionado = (self.indice_selecionado + 1) % n
                    elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER): clicked = self.indice_selecionado
                
                if self.estado == Estado.OBRIGADO and evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER): 
                    clicked = -1 # Avança a tela de obrigado

            elif evento.type == pygame.MOUSEBUTTONDOWN: # Só chega aqui se a fala NÃO foi pulada
                if self.botao_config.clicado(evento.pos) and self.estado != Estado.DORMINDO:
                    self.estado = Estado.CONFIG
                    labels = STATE_CONFIG[Estado.CONFIG][1]
                    self.btn_group = GrupoBotoes(self.largura, self.altura, labels, self.fonte_botao, base_color=CINZA, select_color=SELECIONADO, fade_duration=100, fade_delay=50)
                    self.indice_selecionado = 0
                    self.falando_primeiro = False # Config não tem fala inicial
                    self.ultimo_texto_falado_key = ""
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
        self.fade_start_ms = pygame.time.get_ticks() # Para animação de botões
        estado_anterior = self.estado # Guarda o estado antes da transição

        if self.estado == Estado.CONFIG:
            dados_mudaram = False
            if clicked == 0 and self.config.get('sexo') != "Masculino": self.config['sexo'] = "Masculino"; dados_mudaram = True
            elif clicked == 1 and self.config.get('sexo') != "Feminino": self.config['sexo'] = "Feminino"; dados_mudaram = True
            elif clicked == 2: self.config['idade'] = min(120, self.config.get("idade", 0) + 1); dados_mudaram = True
            elif clicked == 3: self.config['idade'] = max(0, self.config.get("idade", 0) - 1); dados_mudaram = True

            if dados_mudaram: self.config_precisa_atualizar = True
             
            if clicked == 4: # Botão "Concluir"
                with open("config.json", "w", encoding='utf-8') as f: json.dump(self.config, f, ensure_ascii=False, indent=4)
                self.estado = Estado.INICIO
            else: # Apenas atualiza visualização dos botões de sexo
                if clicked in (0, 1):
                    # A classe Botao deve ter um método para atualizar seu estado visual
                    # Ex: btn.set_selected(True/False) ou recriar o GrupoBotoes
                    # Por simplicidade, vamos apenas manter o índice selecionado
                    pass
                self.indice_selecionado = clicked
                # Não recria botões aqui para manter a animação, a menos que seja necessário
                # Se a aparência do botão muda (ex: cor), o GrupoBotoes ou Botao deve lidar com isso.
                return # Permanece na tela de config
                 
        elif self.estado == Estado.INICIO:
            self.registro = {"sentimento": None, "tipo": None, "escala": None, "bpm": None} # Reseta registro
            if clicked == 0: self.estado = Estado.SELECIONAR_SENTIMENTO
            elif clicked == 1: self.estado = Estado.BATIMENTO_INSTRUCAO
            elif clicked == 2: self.estado = Estado.AJUDA_IMEDIATA
                 
        elif self.estado == Estado.SELECIONAR_SENTIMENTO:
            self.registro['sentimento'] = STATE_CONFIG[self.estado][1][clicked]
            self.estado = Estado.TIPO_SENTIMENTO if self.registro['sentimento'] == "Ansioso" else Estado.ESCALA # Exemplo de fluxo
        elif self.estado == Estado.TIPO_SENTIMENTO:
            self.registro['tipo'] = STATE_CONFIG[self.estado][1][clicked]
            self.estado = Estado.ESCALA
        elif self.estado == Estado.ESCALA:
            self.registro['escala'] = STATE_CONFIG[self.estado][1][clicked]
            enviar_servidor(self.registro)
            self.estado = Estado.OBRIGADO
            self.tempo_obrigado = self.tempo
        elif self.estado == Estado.OBRIGADO:
            self.estado = Estado.INICIO
         
        elif self.estado == Estado.BATIMENTO_INSTRUCAO:
            if clicked == 0: # Botão "Iniciar Medição"
                self.estado = Estado.BATIMENTO_MEDINDO
                if self.medicao_thread is None or not self.medicao_thread.is_alive():
                    self.medicao_thread = threading.Thread(target=self._thread_medir_batimentos, daemon=True)
                    self.medicao_thread.start()
                # Não define falando_primeiro aqui, BATIMENTO_MEDINDO tem sua própria fala
            # Não precisa de return aqui, a lógica de transição no final cuidará dos botões e fala.

        elif self.estado == Estado.BATIMENTO_RESULTADO:
            self.estado = Estado.INICIO # Volta para o início após o resultado

        elif self.estado == Estado.AJUDA_IMEDIATA:
            if clicked == 0: 
                self.estado = Estado.RESPIRACAO
                self.respiracao_fase = FaseRespiracao.INSPIRAR
                self.respiracao_timer = 0.0
                self.precisa_falar_primeiro_comando_respiracao = True
            elif clicked == 1: 
                self.estado = Estado.GROUNDING
                self.grounding_passo_atual = 0
                # A fala da primeira pergunta do grounding será iniciada pela lógica de transição

        elif self.estado == Estado.RESPIRACAO:
            # O único botão é "Estou melhor"
            self.estado = Estado.AJUDA_IMEDIATA

        elif self.estado == Estado.GROUNDING:
            if clicked == 0: # Botão "Próximo" ou "Finalizar"
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
                        print(f"Chave de áudio não encontrada para {proxima_chave_grounding}")
                        self.falando = False # Garante que não fique esperando uma fala inexistente

                    if self.grounding_passo_atual == len(self.grounding_perguntas) - 1:
                        labels = ["Finalizar"]
                        self.btn_group = GrupoBotoes(self.largura, self.altura, labels, self.fonte_botao)
                    else:
                        labels = STATE_CONFIG[Estado.GROUNDING][1] # Recria com "Próximo"
                        self.btn_group = GrupoBotoes(self.largura, self.altura, labels, self.fonte_botao)
                    self.indice_selecionado = 0
                    return # Retorna pois os botões mudaram e a fala foi iniciada

        # Lógica de transição comum (botões e fala inicial do novo estado)
        if estado_anterior != self.estado: # Se houve mudança de estado
            labels = STATE_CONFIG.get(self.estado, (None, []))[1]
            self.btn_group = GrupoBotoes(self.largura, self.altura, labels, self.fonte_botao)
            self.indice_selecionado = 0
            
            # Se uma fala específica NÃO foi iniciada DENTRO dos blocos de estado acima
            if not self.falando:
                # E o novo estado tem um áudio principal definido em AUDIO_KEYS
                # E não é o estado INICIO (que não tem fala inicial por padrão)
                if AUDIO_KEYS.get(self.estado) and self.estado != Estado.INICIO:
                    self.falando_primeiro = True
                else:
                    self.falando_primeiro = False # Para estados sem áudio principal ou INICIO
                self.ultimo_texto_falado_key = "" # Reseta para a fala principal do estado
            # Se self.falando já é True, uma fala específica foi iniciada, então não mexemos nas flags de fala aqui.
        
    def update_tempo(self, dt):
        if self.estado == Estado.BATIMENTO_MEDINDO:
            try:
                bpm = self.medicao_queue.get_nowait()
                self.registro['bpm'] = bpm
                
                status_texto = "normal"
                audio_key_para_tocar = "batimento_resultado_normal" # Usar string diretamente
                if bpm < 60:
                    status_texto = "abaixo do normal"
                    audio_key_para_tocar = "batimento_resultado_baixo"
                elif bpm > 100:
                    status_texto = "acima do normal"
                    audio_key_para_tocar = "batimento_resultado_alto"
                
                enviar_servidor(self.registro)
                self.batimento_resultado_texto = f"Seu batimento está {status_texto}: {bpm} bpm.\nDados enviados com sucesso."
                self.batimento_audio_key = audio_key_para_tocar # Guarda a chave para o render
                
                self.estado = Estado.BATIMENTO_RESULTADO
                # A fala do resultado será iniciada pela lógica de transição em on_click/render
            except queue.Empty:
                pass
        
        if self.estado == Estado.RESPIRACAO:
            self.respiracao_timer += dt
            config_fase_atual = self.respiracao_config[self.respiracao_fase]
            
            if self.respiracao_timer >= config_fase_atual["duracao"]:
                self.respiracao_timer = 0 # Reseta o timer para a nova fase
                fase_anterior = self.respiracao_fase

                if self.respiracao_fase == FaseRespiracao.INSPIRAR:
                    self.respiracao_fase = FaseRespiracao.SEGURAR
                elif self.respiracao_fase == FaseRespiracao.SEGURAR:
                    self.respiracao_fase = FaseRespiracao.EXPIRAR
                elif self.respiracao_fase == FaseRespiracao.EXPIRAR:
                    self.respiracao_fase = FaseRespiracao.INSPIRAR
                
                # Se a fase realmente mudou, fala o comando da nova fase
                if fase_anterior != self.respiracao_fase:
                    nova_config_fase = self.respiracao_config[self.respiracao_fase]
                    fase_audio_key = nova_config_fase.get("audio_key")
                    if fase_audio_key:
                        self.tts.speak(key=fase_audio_key)
                        self.falando = True
                        self.ultimo_texto_falado_key = fase_audio_key
                    else:
                        self.falando = False # Garante que não fique esperando fala


        if self.estado == Estado.OBRIGADO and self.tempo_obrigado is not None:
            if self.tempo - self.tempo_obrigado >= DURACAO_OBRIGADO:
                self.estado = Estado.DORMINDO
                self.indice_selecionado = 0
                self.tempo_obrigado = None
                self.btn_group = GrupoBotoes(self.largura, self.altura, STATE_CONFIG[Estado.INICIO][1], self.fonte_botao)
        
        if self.estado != Estado.DORMINDO and \
           self.estado != Estado.RESPIRACAO and \
           self.estado != Estado.BATIMENTO_MEDINDO and \
           (self.tempo - self.ultimo_evento > self.segundos_dormir):
            self.estado = Estado.DORMINDO

    def render(self):
        # --- Fade de Fundo e Rosto ---
        if self.estado != Estado.CONFIG: # Config tem fundo branco estático
            if self.estado == Estado.DORMINDO and not self.fade_fundo.is_active():
                self.fade_fundo.start(self.cor_fundo_atual, PRETO, self.tempo)
                self.fade_rosto.start(self.cor_rosto_atual, BRANCO, self.tempo)
            elif self.estado != Estado.DORMINDO and not self.fade_fundo.is_active() and self.cor_fundo_atual == PRETO:
                self.fade_fundo.start(self.cor_fundo_atual, BRANCO, self.tempo)
                self.fade_rosto.start(self.cor_rosto_atual, PRETO, self.tempo)
            
            nova_cor_fundo, _ = self.fade_fundo.update(self.tempo)
            nova_cor_rosto, _ = self.fade_rosto.update(self.tempo)
            self.cor_fundo_atual = nova_cor_fundo
            self.cor_rosto_atual = nova_cor_rosto
        
        self.screen.fill(self.cor_fundo_atual if self.estado != Estado.CONFIG else BRANCO)

        # --- Rosto ---
        cor_rosto_para_render = self.cor_rosto_atual
        rosto_override_para_render = None

        if self.estado == Estado.RESPIRACAO:
            config_fase_atual_rosto = self.respiracao_config[self.respiracao_fase]
            rosto_override_para_render = config_fase_atual_rosto["rosto"]
            # A cor do rosto não muda mais com a fase da respiração, mantém self.cor_rosto_atual

        self.face.update(self.tempo, self.falando, dormindo=(self.estado==Estado.DORMINDO), cor=cor_rosto_para_render, rosto_override=rosto_override_para_render)
        self.face.desenhar(self.tempo)

        # --- Textos e Botões Específicos do Estado ---
        if self.estado != Estado.DORMINDO:
            texto_principal_estado, _ = STATE_CONFIG.get(self.estado, ("", []))
            chave_audio_principal_estado = AUDIO_KEYS.get(self.estado)

            if self.estado == Estado.GROUNDING:
                pergunta_atual = self.grounding_perguntas[self.grounding_passo_atual]
                self.texto.desenhar(pergunta_atual, cor=self.cor_rosto_atual) # Texto no topo
                if not self.falando: # Só mostra botões se não estiver falando a pergunta
                    self.btn_group.desenhar(self.screen, self.indice_selecionado)

            elif self.estado == Estado.RESPIRACAO:
                config_fase_render = self.respiracao_config[self.respiracao_fase]
                progresso = self.respiracao_timer / config_fase_render["duracao"]
                raio_atual = 0
                if self.respiracao_fase == FaseRespiracao.INSPIRAR:
                    raio_atual = self.respiracao_raio_min + (self.respiracao_raio_max - self.respiracao_raio_min) * progresso
                elif self.respiracao_fase == FaseRespiracao.SEGURAR:
                    raio_atual = self.respiracao_raio_max
                elif self.respiracao_fase == FaseRespiracao.EXPIRAR:
                    raio_atual = self.respiracao_raio_max - (self.respiracao_raio_max - self.respiracao_raio_min) * progresso
                
                texto_guia_surf = self.fonte_guia.render(config_fase_render["texto"], True, self.cor_rosto_atual)
                texto_guia_rect = texto_guia_surf.get_rect()
                padding = 20
                largura_total_grupo = texto_guia_rect.width + padding + (raio_atual * 2)
                x_inicio_grupo = (self.largura - largura_total_grupo) / 2
                pos_y_centro = self.altura * 0.15
                texto_guia_rect.left = x_inicio_grupo
                texto_guia_rect.centery = pos_y_centro
                self.screen.blit(texto_guia_surf, texto_guia_rect)
                pos_bola_x = x_inicio_grupo + texto_guia_rect.width + padding + raio_atual
                pygame.draw.circle(self.screen, config_fase_render["cor"], (pos_bola_x, pos_y_centro), raio_atual)
                
                if not self.falando: # Só mostra botões se não estiver falando (introdução ou comando)
                    self.btn_group.desenhar(self.screen, self.indice_selecionado)

            elif self.estado == Estado.BATIMENTO_RESULTADO:
                self.texto.desenhar(self.batimento_resultado_texto, cor=self.cor_rosto_atual)
                # Não há botões, qualquer clique avança (tratado em handle_events)
            
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
            
            else: # Outros estados com texto principal e botões
                if texto_principal_estado:
                    self.texto.desenhar(texto_principal_estado, cor=self.cor_rosto_atual)
                if self.btn_group and self.btn_group.buttons and not self.falando_primeiro and self.estado != Estado.BATIMENTO_MEDINDO:
                    self.btn_group.desenhar(self.screen, self.indice_selecionado)
            
        if self.estado == Estado.INICIO: self.botao_config.desenhar(self.screen)
        
        # --- Lógica de Fala (TTS) ---
        if self.falando_primeiro:
            if not self.falando: # Se não começou a falar a "fala principal" do estado
                audio_key_para_tocar = None
                if self.estado == Estado.BATIMENTO_RESULTADO:
                    audio_key_para_tocar = self.batimento_audio_key
                elif chave_audio_principal_estado: # chave_audio_principal_estado = AUDIO_KEYS.get(self.estado)
                    audio_key_para_tocar = chave_audio_principal_estado

                if audio_key_para_tocar:
                    self.tts.speak(key=audio_key_para_tocar)
                    self.falando = True
                    self.ultimo_texto_falado_key = audio_key_para_tocar
            
            # Se estava falando a "fala principal" e ela ACABOU de terminar
            if self.falando and not self.tts.speaking:
                self.falando = False
                self.falando_primeiro = False # A "fala principal" já ocorreu

                if self.btn_group and self.btn_group.buttons:
                    self.btn_group.start_ms = pygame.time.get_ticks()

                # Se a introdução da respiração acabou, fala o primeiro comando
                if self.estado == Estado.RESPIRACAO and self.precisa_falar_primeiro_comando_respiracao:
                    config_fase_para_falar = self.respiracao_config[self.respiracao_fase]
                    fase_audio_key = config_fase_para_falar.get("audio_key")
                    if fase_audio_key:
                        self.tts.speak(key=fase_audio_key)
                        self.falando = True
                        self.ultimo_texto_falado_key = fase_audio_key
                    self.precisa_falar_primeiro_comando_respiracao = False
            
            # Se não há chave de áudio para o estado (e não é BATIMENTO_RESULTADO que tem sua própria chave)
            elif not chave_audio_principal_estado and self.estado != Estado.BATIMENTO_RESULTADO: 
                self.falando_primeiro = False
                if self.btn_group and self.btn_group.buttons:
                    self.btn_group.start_ms = pygame.time.get_ticks() # Mostra botões se não houver fala
        else: # Não é self.falando_primeiro (lógica para falas subsequentes ou se não houve fala inicial)
            if self.falando and not self.tts.speaking: # Se uma fala específica (não principal) terminou
                self.falando = False
                # Não altera falando_primeiro aqui
                # Os botões já devem estar visíveis ou sua visibilidade é controlada pelo estado específico
                if self.btn_group and self.btn_group.buttons and self.estado not in [Estado.RESPIRACAO, Estado.GROUNDING]:
                    # Para estados normais, garante que os botões apareçam após uma fala não-principal
                     self.btn_group.start_ms = pygame.time.get_ticks()