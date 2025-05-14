import pygame
import sys
import math

BRANCO      = (255, 255, 255)
PRETO       = (0,     0,   0)
AZUL        = (70,  130, 180)
CINZA       = (200, 200, 200)
SELECIONADO = ( 50, 175, 200)

FADE_T      = 0.5          # s de fade‑in e fade‑out
SHOW_T      = 2.5          # s totalmente visível
T_TOTAL     = 2*FADE_T+SHOW_T

ROSTO_BASE = ["O - O", "^ - ^"]

def inicializar_pygame():
    pygame.init()
    info = pygame.display.Info()
    screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
    clock = pygame.time.Clock()
    return screen, clock

def desenhar_frase(screen, fonte, texto, t_decorrido, centro):
    # if t_decorrido > T_TOTAL:           # já terminou
    #     return False                    # sinaliza que não precisa mais exibir

    # # calcula alpha
    # if t_decorrido < FADE_T:            # fade‑in
    #     alpha = int(255 * t_decorrido/FADE_T)
    #     y_off = 30 * (1 - t_decorrido/FADE_T)   # sobe levemente
    # elif t_decorrido > FADE_T + SHOW_T:  # fade‑out
    #     alpha = int(255 * (1 - (t_decorrido-FADE_T-SHOW_T)/FADE_T))
    #     y_off = 0
    # else:                               # totalmente visível
    #     alpha = 255
    #     y_off = 0

    # surf = fonte.render(texto, True, PRETO)
    # # surf.set_alpha(alpha)
    # rect = surf.get_rect(center=(screen.get_width()//2, centro_rosto_y))
    # screen.blit(surf, rect)

    texto = fonte.render(texto, True, PRETO)
    screen.blit(texto, texto.get_rect(center=(centro[0]//2, centro[1]*0.08)))

    return True

def desenhar_rosto(screen, fonte, estado, centro):
    texto = fonte.render(ROSTO_BASE[estado], True, PRETO)
    screen.blit(texto, texto.get_rect(center=centro))

def atualizar_estado_rosto(tempo, ultimo_tempo_troca, piscando):
    if not piscando and (tempo - ultimo_tempo_troca >= 2.4):
        return 1, tempo, True
    elif piscando and (tempo - ultimo_tempo_troca >= 0.3):
        return 0, tempo, False
    return None

def create_buttons(screen_width, screen_height, rotulos):
    margem = screen_width * 0.05
    espaco = screen_width * 0.02
    altura_botao = screen_height * 0.18
    largura_botao = (screen_width - (2 * margem) - (len(rotulos) - 1) * espaco) / len(rotulos)
    y = screen_height - screen_height * 0.2
    botoes = []
    x0 = (screen_width - (len(rotulos)*largura_botao + (len(rotulos)-1)*espaco)) / 2
    for i, rtl in enumerate(rotulos):
        botao = pygame.Rect(x0 + i * (largura_botao + espaco), y, largura_botao, altura_botao)
        botoes.append((botao, rtl))
    return botoes

def desenhar_botoes(screen, botoes, fonte_botao, indice_selecionado):
    for i, (botao, rotulo) in enumerate(botoes):
        cor = SELECIONADO if i == indice_selecionado else CINZA
        #sombra = pygame.Rect(botao.x + 5, botao.y + 5, botao.width, botao.height)
        pygame.draw.rect(screen, cor, botao, border_radius=12)
        texto = fonte_botao.render(rotulo, True, BRANCO)
        texto_rect = texto.get_rect(center=botao.center)
        screen.blit(texto, texto_rect)

def desenhar_botoes_fade(screen, botoes, fonte_botao, indice_selecionado,
                        animation_start, fade_duration, delay_between):
    now = pygame.time.get_ticks()
    for i, (botao, rotulo) in enumerate(botoes):
        t_i = now - (animation_start + i * delay_between)
        if t_i <= 0:
            alpha = 0
        elif t_i >= fade_duration:
            alpha = 255
        else:
            alpha = int(255 * (t_i / fade_duration))

        surf = pygame.Surface((botao.width, botao.height), pygame.SRCALPHA)
        cor = SELECIONADO if i == indice_selecionado else CINZA
        surf.fill((*cor, alpha))

        txt = fonte_botao.render(rotulo, True, BRANCO)
        txt.set_alpha(alpha)
        txt_rect = txt.get_rect(center=(botao.width // 2, botao.height // 2))
        surf.blit(txt, txt_rect)

        screen.blit(surf, (botao.x, botao.y))

def manipular_entrada(evento, botoes, indice_selecionado):
    running = True
    msg = None
    selected_idx = indice_selecionado
    if evento.type == pygame.MOUSEBUTTONDOWN:
        for i, (botao, rotulo) in enumerate(botoes):
            if botao.collidepoint(evento.pos):
                selected_idx = i
                if i == 0:   msg = "Usuário está bem"
                elif i == 1: msg = "Usuário se sente triste"
                elif i == 2: running = False
    elif evento.type == pygame.KEYDOWN:
        if evento.key == pygame.K_LEFT:
            selected_idx = (selected_idx - 1) % len(botoes)
        elif evento.key == pygame.K_RIGHT:
            selected_idx = (selected_idx + 1) % len(botoes)
        elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if selected_idx == 0:   msg = "Usuário está bem"
            elif selected_idx == 1: msg = "Usuário se sente triste"
            elif selected_idx == 2: running = False
    return selected_idx, running, msg

def main():
    screen, clock = inicializar_pygame()
    largura, altura = screen.get_size()
    fonte_rosto = pygame.font.SysFont("JandaManateeSolid.ttf", int(altura * 0.5), bold=True)
    fonte_botao = pygame.font.SysFont("Arial", int(altura * 0.05), bold=True)
    fonte_frase = pygame.font.SysFont("Arial", int(altura*0.1), bold=True)

    mensagem_atual  = None     # texto
    inicio_mensagem = 0 
    rotulos = ["1", "2", "3"]
    botoes = create_buttons(largura, altura, rotulos)

    animation_start = pygame.time.get_ticks()
    fade_duration   = 500
    delay_between   = 500

    tempo = 0
    ultimo_tempo_troca = 0
    piscando = False
    indice_rosto = 0
    indice_selecionado = 0
    running = True

    while running:
        dt = clock.tick(60) / 1000.0  # segundos desde último frame
        tempo += dt

        screen.fill(BRANCO)
        resultado = atualizar_estado_rosto(tempo, ultimo_tempo_troca, piscando)
        if resultado:
            indice_rosto, ultimo_tempo_troca, piscando = resultado
        
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                running = False
            else:
                indice_selecionado, running, msg = manipular_entrada(evt, botoes, indice_selecionado)
                if msg:
                    print (msg)
                    mensagem_atual  = msg
                    inicio_mensagem = tempo

        if mensagem_atual:
            ativo = desenhar_frase(
                screen, fonte_frase, mensagem_atual,
                tempo - inicio_mensagem,
                (largura, altura)                     # y do rosto
            )
            if not ativo:
                mensagem_atual = None


        x_off = math.cos(tempo*2) * 10
        y_off = math.sin(tempo*2) * 20
        centro = (largura // 2 + int(x_off), int(altura//2 + int(y_off))
        desenhar_rosto(screen, fonte_rosto, indice_rosto, centro)
        desenhar_botoes_fade(
            screen, botoes, fonte_botao, indice_selecionado,
            animation_start, fade_duration, delay_between
        )

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()