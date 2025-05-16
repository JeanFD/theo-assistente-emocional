import pygame

# Constantes de cor
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
CINZA = (200, 200, 200)
SELECIONADO = (50, 175, 200)


def desenhar_frase(screen, fonte, texto):
    max_width = screen.get_width() * 0.8
    words = texto.split(' ')
    lines = []
    line = ''
    for word in words:
        test = f"{line} {word}" if line else word
        if fonte.size(test)[0] <= max_width:
            line = test
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    # calcula posição inicial para centralizar verticalmente
    line_height = fonte.get_linesize()
    total_height = line_height * len(lines)
    y_start = screen.get_height() * 0.20 - total_height / 2
    for i, l in enumerate(lines):
        surf = fonte.render(l, True, PRETO)
        rect = surf.get_rect(center=(screen.get_width()//2, y_start + i * line_height))
        screen.blit(surf, rect)

def criar_botoes(screen_width, screen_height, rotulos):
    if rotulos is None or len(rotulos) == 0:
        return []
    margem, espaco = screen_width * 0.05, screen_width * 0.02
    altura_botao = screen_height * 0.18
    largura_botao = (screen_width - (2 * margem) - (len(rotulos) - 1) * espaco) / len(rotulos)
    y = screen_height * 0.8
    x0 = (screen_width - (len(rotulos)*largura_botao + (len(rotulos)-1)*espaco)) / 2
    botoes = []
    for i, rtl in enumerate(rotulos):
        botao = pygame.Rect(x0 + i * (largura_botao + espaco), y, largura_botao, altura_botao)
        botoes.append((botao, rtl))
    return botoes

def desenhar_botoes_fade(screen, botoes, fonte_base, sel, start_ms, dur_ms, delay_ms):
    now = pygame.time.get_ticks()
    for i, (rect, lbl) in enumerate(botoes):
        
        t_i = now - (start_ms + i * delay_ms)
        if t_i <= 0:
            alpha = 0
        elif t_i >= dur_ms:
            alpha = 255
        else:
            alpha = int(255 * (t_i / dur_ms))

        cor_base = SELECIONADO if i == sel else CINZA
        surf_bg = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        surf_bg.fill((*cor_base, alpha))

        fs = int(rect.height * 0.5)
        font = pygame.font.SysFont(fonte_base, fs, bold=True)
        txt_surf = font.render(lbl, True, BRANCO)
        
        while txt_surf.get_width() > rect.width * 0.8 and fs > 10:
            fs -= 2
            font = pygame.font.SysFont(fonte_base, fs, bold=True)
            txt_surf = font.render(lbl, True, BRANCO)

        txt_surf.set_alpha(alpha)

        x = (rect.width - txt_surf.get_width()) // 2
        y = (rect.height - txt_surf.get_height()) // 2
        surf_bg.blit(txt_surf, (x, y))

        screen.blit(surf_bg, rect.topleft)