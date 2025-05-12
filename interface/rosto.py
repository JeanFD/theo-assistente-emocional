import pygame
import sys
import math

# Inicialização
pygame.init()
info = pygame.display.Info()
largura, altura = info.current_w, info.current_h
tela = pygame.display.set_mode((largura, altura), pygame.FULLSCREEN)

pygame.display.set_caption("Rosto do Robô")

# Cores
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
AZUL = (70, 130, 180)
CINZA = (200, 200, 200)
SELECIONADO = (100, 149, 237)

# Fonte e rosto
fonte = pygame.font.SysFont("monospace", 200, bold=True)
rosto_base = ["0-0", "^-^"]
indice_rosto = 0

# Fonte dos botões
fonte_botao = pygame.font.SysFont("arial", 32, bold=True)
rotulos = ["Estou bem", "Me sinto triste", "Sair"]

# Proporções relativas à tela
espaco = largura * 0.02  # 2% da largura para espaçamento entre botões
margem_lateral = largura * 0.05  # 5% da largura como margem lateral
altura_botao = altura * 0.18     # 18% da altura para altura dos botões

# Largura do botão baseada na largura total disponível
total_largura_util = largura - 2 * margem_lateral
largura_botao = (total_largura_util - espaco * 2) / 3  # 3 botões, 2 espaços

# Centraliza grupo de botões horizontalmente
total_largura = largura_botao * 3 + espaco * 2
inicio_x = (largura - total_largura) // 2

# Posição vertical dos botões (ex: 70% da altura da tela)
pos_y = altura - altura * 0.2

botoes = []
for i, rotulo in enumerate(rotulos):
    x = inicio_x + i * (largura_botao + espaco)
    botoes.append(pygame.Rect(x, pos_y, largura_botao, altura_botao))

# Navegação por seleção
indice_selecionado = 0

# Tempo
relogio = pygame.time.Clock()
tempo = 0
ultimo_tempo_troca = 0
piscando = False

# Loop principal
while True:
    tela.fill(BRANCO)

    # Rosto flutuando
    tempo += 0.05
    deslocamentoy = math.sin(tempo / 2) * 20
    deslocamentox = math.cos(tempo / 2) * 10
    texto_rosto = fonte.render(rosto_base[indice_rosto], True, PRETO)
    rect_rosto = texto_rosto.get_rect(center=(largura // 2 + int(deslocamentox), altura // 2 + int(deslocamentoy)))
    tela.blit(texto_rosto, rect_rosto)

    # Alternar rosto a cada 3s
    if not piscando and (tempo - ultimo_tempo_troca >= 3):
        indice_rosto = 1
        ultimo_tempo_troca = tempo
        piscando = True
    elif piscando and (tempo - ultimo_tempo_troca >= 0.5):
        indice_rosto = 0
        ultimo_tempo_troca = tempo
        piscando = False

    # Desenhar botões
    for i, botao in enumerate(botoes):
        cor = SELECIONADO if i == indice_selecionado else CINZA
        sombra = pygame.Rect(botao.x + 5, botao.y + 5, botao.width, botao.height)
        pygame.draw.rect(tela, cor, botao, border_radius=12)
        texto = fonte_botao.render(rotulos[i], True, BRANCO)
        texto_rect = texto.get_rect(center=botao.center)
        tela.blit(texto, texto_rect)

    # Eventos
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        elif evento.type == pygame.MOUSEBUTTONDOWN:
            for i, botao in enumerate(botoes):
                if botao.collidepoint(evento.pos):
                    indice_selecionado = i
                    if i == 0:
                        print("Usuário está bem")
                    elif i == 1:
                        print("Usuário se sente triste")
                    elif i == 2:
                        pygame.quit()
                        sys.exit()

        elif evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_LEFT:
                indice_selecionado = (indice_selecionado - 1) % len(botoes)
            elif evento.key == pygame.K_RIGHT:
                indice_selecionado = (indice_selecionado + 1) % len(botoes)
            elif evento.key == pygame.K_RETURN or evento.key == pygame.K_KP_ENTER:
                if indice_selecionado == 0:
                    print("Usuário está bem")
                elif indice_selecionado == 1:
                    print("Usuário se sente triste")
                elif indice_selecionado == 2:
                    pygame.quit()
                    sys.exit()

    pygame.display.flip()
    relogio.tick(30)
