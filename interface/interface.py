import pygame, sys, math
from enum import Enum, auto
from interface.ui import criar_botoes, desenhar_frase, desenhar_botoes_fade

BRANCO      = (255, 255, 255)
PRETO       = (0,     0,   0)
AZUL        = (70,  130, 180)
CINZA       = (200, 200, 200)
SELECIONADO = ( 50, 175, 200)

FADE_T      = 0.5   
DELAY_BTWN  = 0.5

ROSTO_BASE = ["O - O", "^ - ^"]

class Estado(Enum):
    INICIO = auto()
    SELECIONAR_SENTIMENTO = auto()
    TIPO_SENTIMENTO = auto()
    ESCALA = auto()
    OBRIGADO = auto() 

def inicializar_pygame():
    pygame.init()
    info = pygame.display.Info()
    screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
    clock = pygame.time.Clock()
    return screen, clock


def desenhar_rosto(screen, fonte, estado, tempo):
    x_off = math.cos(tempo*2) * 10
    y_off = math.sin(tempo*2) * 20
    surf = fonte.render(ROSTO_BASE[estado], True, PRETO)
    screen.blit(surf, surf.get_rect(center=((screen.get_width()//2)+x_off, (screen.get_height()//2)+y_off)))

def atualizar_estado_rosto(tempo, ultimo_tempo_troca, piscando):
    if not piscando and (tempo - ultimo_tempo_troca >= 2.4):
        return 1, tempo, True
    elif piscando and (tempo - ultimo_tempo_troca >= 0.3):
        return 0, tempo, False
    return None

def main():
    screen, clock = inicializar_pygame()
    largura, altura = screen.get_size()
    fonte_rosto = pygame.font.SysFont("JandaManateeSolid.ttf", int(altura * 0.5), bold=True)
    fonte_frase = pygame.font.SysFont("Arial", int(altura*0.1), bold=True)
    fonte_botao = "Arial"

    btn_inicio  = criar_botoes(largura,altura,["Registrar humor","Registrar batimento","Suporte imediato"])
    btn_sentimento  = criar_botoes(largura,altura,["Feliz","Neutro","Triste","Ansioso"])
    btn_tipo    = criar_botoes(largura,altura,["Bom","Ruim","Não sei"])
    btn_escala     = criar_botoes(largura, altura, [str(i) for i in range(1,6)])

    estado = Estado.INICIO
    indice_selecionado = 0
    registro = {"sentimento":None, "tipo":None, "escala":None}

    tempo = 0.0
    indice_rosto = 0
    ultimo_tempo_troca = 0
    piscando = False

    fade_start_ms = pygame.time.get_ticks()
    duration_ms   = int(FADE_T * 1000)
    delay_ms      = int(DELAY_BTWN * 1000)

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
        else:
            botoes = []
            text = "Obrigada, aguardarei os próximos registros"


        resultado = atualizar_estado_rosto(tempo, ultimo_tempo_troca, piscando)
        if resultado:
            indice_rosto, ultimo_tempo_troca, piscando = resultado
        

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
                    if estado in (Estado.INICIO, Estado.SELECIONAR_SENTIMENTO, Estado.TIPO_SENTIMENTO, Estado.ESCALA):
                        for i, (botao, _) in enumerate(botoes):
                            if botao.collidepoint(evento.pos):
                                clicked = i
                                break
                    elif estado == Estado.OBRIGADO:
                        clicked = -1

        if clicked is not None:
            if estado == Estado.OBRIGADO and clicked == -1:
                estado = Estado.INICIO
                indice_selecionado = 0

            elif estado == Estado.INICIO:
                if clicked == 0:
                    estado = Estado.SELECIONAR_SENTIMENTO
                    indice_selecionado = 0
                elif clicked == 1:
                    print("Registrar batimento")
                elif clicked == 2:
                    print("Suporte imediato")
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
                indice_selecionado = 0    
            
            if estado == Estado.OBRIGADO:
                print(registro)
                inicio_mensagem = tempo
            fade_start_ms = pygame.time.get_ticks()

        screen.fill(BRANCO)      
        desenhar_frase(screen, fonte_frase, text)
        desenhar_rosto(screen, fonte_rosto, indice_rosto, tempo)

        if botoes:
            desenhar_botoes_fade(screen, botoes, fonte_botao, indice_selecionado, fade_start_ms, duration_ms, delay_ms)

        pygame.display.flip()

    pygame.quit()
    sys.exit()
