
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

# Fonte e rosto
fonte = pygame.font.SysFont("monospace", 200, bold=True)
rosto_base = ["0-0", "0o0"]
indice_rosto = 0

# Botões (x, y, largura, altura)
botoes = [
    pygame.Rect(100, altura - 200, 200, 60),
    pygame.Rect(350, altura - 200, 200, 60),
    pygame.Rect(600, altura - 200, 200, 60),
]

# Fonte dos botões
fonte_botao = pygame.font.SysFont("arial", 30, bold=True)
rotulos = ["Estou bem", "Me sinto triste", "Sair"]

# Tempo
relogio = pygame.time.Clock()
tempo = 0

# Loop principal
while True:
    tela.fill(BRANCO)

    # Rosto flutuando
    tempo += 0.05
    deslocamento = math.sin(tempo) * 20
    texto_rosto = fonte.render(rosto_base[indice_rosto], True, PRETO)
    rect_rosto = texto_rosto.get_rect(center=(largura // 2, altura // 2 + int(deslocamento)))
    tela.blit(texto_rosto, rect_rosto)

    # Alternar rosto a cada 0.5s
    if int(tempo * 10) % 5 == 0:
        indice_rosto = (indice_rosto + 1) % 2

    # Desenhar botões
    for i, botao in enumerate(botoes):
        pygame.draw.rect(tela, AZUL, botao, border_radius=10)
        texto = fonte_botao.render(rotulos[i], True, BRANCO)
        tela.blit(texto, (botao.x + 20, botao.y + 15))

    # Eventos
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if botoes[0].collidepoint(evento.pos):
                print("Usuário está bem")
            elif botoes[1].collidepoint(evento.pos):
                print("Usuário se sente triste")
            elif botoes[2].collidepoint(evento.pos):
                pygame.quit()
                sys.exit()

    pygame.display.flip()
    relogio.tick(30)

