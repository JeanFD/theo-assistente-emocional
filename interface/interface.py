import pygame, sys, math
from enum import Enum, auto
from interface.ui import criar_botoes, desenhar_frase, desenhar_botoes_fade
from interface.rosto import desenhar_rosto, atualizar_estado_rosto
from sensores.batimentos import ler_batimentos
from voz.tts import TTS
from comunicacao.envio_dados import enviar_servidor

FADE_T = 0.3   
DELAY_BTWN = 0.2

BRANCO = (255, 255, 255)

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

def inicializar_pygame():
    pygame.init()
    info = pygame.display.Info()
    screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
    clock = pygame.time.Clock()
    return screen, clock

def main():
    screen, clock = inicializar_pygame()
    largura, altura = screen.get_size()
    fonte_rosto = pygame.font.SysFont("JandaManateeSolid.ttf", int(altura * 0.5), bold=True)
    fonte_frase = pygame.font.SysFont("Arial", int(altura*0.1), bold=True)
    fonte_botao = "Arial"

    btn_inicio  = criar_botoes(largura,altura,["Registrar humor","Registrar batimento","Suporte imediato"])
    btn_sentimento  = criar_botoes(largura,altura,["Feliz","Neutro","Triste","Ansioso"])
    btn_tipo    = criar_botoes(largura,altura,["Bom","Ruim","Não sei"])
    btn_ajuda        = criar_botoes(largura, altura, ["Respiração","Grounding","Voltar"])
    btn_respiro_opts = criar_botoes(largura, altura, ["Estou melhor","Continuo ansioso"])
    btn_ground_opts  = criar_botoes(largura, altura, ["Próxima pergunta","Voltar"])
    btn_escala     = criar_botoes(largura, altura, [str(i) for i in range(1,6)])

    estado = Estado.INICIO
    indice_selecionado = 0
    registro = {"sentimento":None, "tipo":None, "escala":None}

    tempo = 0.0
    indice_rosto = 0
    ultimo_tempo_troca = 0
    piscando = False
    falando = False
    tts = TTS(rate=200)                                       
    ultimo_texto = ""
    falando = False
    tts = TTS(rate=200)                                       
    ultimo_texto = ""

    fade_start_ms = pygame.time.get_ticks()
    duration_ms   = int(FADE_T * 1000)
    delay_ms      = int(DELAY_BTWN * 1000)
    DURACAO_OBRIGADO = 5.0

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        tempo += dt
        if estado == Estado.INICIO:
            botoes = btn_inicio
            text = "O que deseja fazer?"
        elif estado == Estado.SELECIONAR_SENTIMENTO:
            botoes = btn_sentimento
            text = "Como você se sente?"
        elif estado == Estado.TIPO_SENTIMENTO:
            botoes = btn_tipo
            text = "Ligado a algo bom ou ruim?"
        elif estado == Estado.ESCALA:
            botoes = btn_escala
            text = "Em escala de 1 a 5, quão forte é?"
        elif estado == Estado.OBRIGADO:
            botoes = []
            text = "Obrigada, aguardarei os próximos registros"       

        elif estado == Estado.BATIMENTO:
            bpm = 120 #registro['bpm']
            texto = f"Seu batimento: {bpm} bpm"
            # avalia normal/anormal
            normal = 73 <= bpm <= 78
            #((registro['sexo']=="Mulher" and 73 <= bpm <= 78)
                    # or (registro['sexo']=="Homem"  and 70 <= bpm <= 76))
            text = texto + ("\nEstá normal." if normal else "\nEstá anormal, fique atento.")
            botoes = criar_botoes(largura, altura, ["OK"])

        elif estado == Estado.AJUDA_IMEDIATA:
            botoes, text = btn_ajuda, (
                "Você está passando por um momento difícil. Estou aqui com você.\n"
                "Vamos tentar algumas coisas para te acalmar, tudo bem?"
            )
        elif estado == Estado.RESPIRACAO:
            botoes, text = btn_respiro_opts, (
                "Respire: Inspire 3s (LED verde), segure 1s (LED amarelo), expire 3s (LED vermelho).\n"
                "Repita algumas vezes."
            )
        
        elif estado == Estado.GROUNDING:
            botoes, text = btn_ground_opts, "Diga 3 coisas que você vê agora."

        clicked = None
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                running = False

            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    running = False
                
                elif estado in (Estado.INICIO, Estado.SELECIONAR_SENTIMENTO, Estado.TIPO_SENTIMENTO, Estado.ESCALA):
                    if evento.key == pygame.K_LEFT:
                        indice_selecionado = (indice_selecionado - 1) % len(botoes)
                    elif evento.key == pygame.K_RIGHT:
                        indice_selecionado = (indice_selecionado + 1) % len(botoes)
                    elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        clicked = indice_selecionado

                elif estado == Estado.OBRIGADO:
                    if evento.key == pygame.K_RETURN:
                        clicked = -1

            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if estado in (Estado):
                    for i, (botao, _) in enumerate(botoes):
                        if botao.collidepoint(evento.pos):
                            clicked = i
                            break
                elif estado == Estado.OBRIGADO:
                    clicked = -1

        if clicked is not None:
            if estado == Estado.INICIO:
                if clicked == 0:
                    estado = Estado.SELECIONAR_SENTIMENTO
                    indice_selecionado = 0
                elif clicked == 1:
                    estado = Estado.BATIMENTO
                    indice_selecionado = -1
                elif clicked == 2:
                    estado = Estado.AJUDA_IMEDIATA
                    indice_selecionado = 0
                indice_selecionado = 0

            elif estado == Estado.SELECIONAR_SENTIMENTO:
                registro['sentimento'] = botoes[clicked][1]
                if clicked == 0:
                    estado = Estado.ESCALA
                    indice_selecionado = 0
                elif clicked == 1:
                    estado = Estado.ESCALA
                    indice_selecionado = 0
                elif clicked == 2:
                    estado = Estado.ESCALA
                    indice_selecionado = 0
                elif clicked == 3:
                    estado = Estado.TIPO_SENTIMENTO
                    indice_selecionado = 0

            elif estado == Estado.TIPO_SENTIMENTO:
                registro['tipo'] = botoes[clicked][1]
                if clicked == 0:
                    estado = Estado.ESCALA
                    indice_selecionado = 0
                elif clicked == 1:
                    estado = Estado.ESCALA
                    indice_selecionado = 0
                elif clicked == 2:
                    estado = Estado.ESCALA
                    indice_selecionado = 0

            elif estado == Estado.ESCALA:
                registro['escala'] = botoes[clicked][1]
                estado = Estado.OBRIGADO
                print(registro)
                enviar_servidor(registro)
                indice_selecionado = 0    
                inicio_obrigado = tempo
                
            elif estado == Estado.BATIMENTO:
                print("aqui")
                registro['bpm'] = ler_batimentos()
                if clicked == 0:
                    estado = Estado.INICIO
                    indice_selecionado = 0

            elif estado == Estado.INICIO and clicked == 2:
                estado = Estado.AJUDA_IMEDIATA

            elif estado == Estado.AJUDA_IMEDIATA:
                if clicked == 0:
                    estado = Estado.RESPIRACAO
                elif clicked == 1:
                    estado = Estado.GROUNDING
                else:  # “Voltar”
                    estado = Estado.INICIO

            elif estado == Estado.RESPIRACAO:
                # trate respostas “Estou melhor” ou “Continuo ansioso”
                if clicked == 0:
                    text = "Ótimo, fico feliz em ajudar."
                else:
                    text = "Tudo bem, continue respirando devagar."
                botoes = criar_botoes(largura, altura, ["Voltar"])
                estado = Estado.AJUDA_IMEDIATA

            elif estado == Estado.GROUNDING:
                # implemente “Próxima pergunta” ou “Voltar”
                if clicked == 0:
                    text = "Descreva um objeto perto de você em detalhes."
                    botoes = criar_botoes(largura, altura, ["Voltar"])
                    estado = Estado.AJUDA_IMEDIATA
                else:
                    estado = Estado.AJUDA_IMEDIATA

            
            fade_start_ms = pygame.time.get_ticks()
            
        if estado == Estado.OBRIGADO:
            if tempo - inicio_obrigado >= DURACAO_OBRIGADO or clicked == -1:
                estado = Estado.INICIO
            indice_selecionado = 0  

            fade_start_ms = pygame.time.get_ticks()

        screen.fill(BRANCO)      
        desenhar_frase(screen, fonte_frase, text)

        resultado = atualizar_estado_rosto(tempo, ultimo_tempo_troca, piscando, falando)
        if resultado:
            indice_rosto, ultimo_tempo_troca, piscando = resultado

        desenhar_rosto(screen, fonte_rosto, indice_rosto, tempo)

        if text != ultimo_texto:
            tts.speak(text)
            ultimo_texto = text
        falando = tts.speaking

        if botoes:
            desenhar_botoes_fade(screen, botoes, fonte_botao, indice_selecionado, fade_start_ms, duration_ms, delay_ms)

        pygame.display.flip()

    pygame.quit()
    sys.exit()