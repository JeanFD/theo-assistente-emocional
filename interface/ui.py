"""Componentes de UI: texto e botoes do THEO."""

import pygame
from interface.tema import (
    BRANCO, PRETO, AZUL_MARINHO,
    BOTAO_PADRAO, BOTAO_SELECIONADO_TECLADO, BOTAO_TEXTO,
)


def _wrap_lines(fonte, texto, max_width):
    """Quebra texto em linhas respeitando \\n e largura maxima."""
    linhas = []
    for paragrafo in texto.split('\n'):
        words = paragrafo.split(' ')
        line = ''
        while words:
            word = words.pop(0)
            test_line = f"{line} {word}".strip()
            if fonte.size(test_line)[0] <= max_width:
                line = test_line
            else:
                linhas.append(line)
                line = word
        linhas.append(line)
    return linhas


def desenhar_frase(screen, fonte, texto, cor=AZUL_MARINHO, top_ratio=0.18, max_width_ratio=0.85):
    """Desenha texto centralizado no topo com word-wrap."""
    if not texto:
        return
    max_width = screen.get_width() * max_width_ratio
    linhas = _wrap_lines(fonte, texto, max_width)
    line_h = fonte.get_linesize()
    total_h = line_h * len(linhas)
    y = screen.get_height() * top_ratio - total_h / 2
    for i, l in enumerate(linhas):
        surf = fonte.render(l, True, cor)
        rect = surf.get_rect(center=(screen.get_width() // 2, y + i * line_h + line_h / 2))
        screen.blit(surf, rect)


def criar_botoes(screen_width, screen_height, rotulos):
    """Cria layout dos botoes na parte inferior da tela."""
    if rotulos is None or len(rotulos) == 0:
        return []
    margem = screen_width * 0.08
    espaco = screen_width * 0.025
    altura_botao = screen_height * 0.16
    largura_botao = (screen_width - (2 * margem) - (len(rotulos) - 1) * espaco) / len(rotulos)
    y = screen_height * 0.78
    x0 = (screen_width - (len(rotulos) * largura_botao + (len(rotulos) - 1) * espaco)) / 2
    botoes = []
    for i, rtl in enumerate(rotulos):
        botao = pygame.Rect(int(x0 + i * (largura_botao + espaco)), int(y), int(largura_botao), int(altura_botao))
        botoes.append((botao, rtl))
    return botoes


def _calc_alpha(now, start_ms, index, delay_ms, dur_ms):
    t = now - (start_ms + index * delay_ms)
    if t <= 0:
        return 0
    if t >= dur_ms:
        return 255
    return int(255 * (t / dur_ms))


def _desenhar_botao(screen, rect, label, fonte_nome, cor_fundo, alpha, selecionado_destaque):
    """Desenha um botao arredondado com texto centralizado."""
    surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    raio = int(min(rect.width, rect.height) * 0.35)
    cor = (*cor_fundo, alpha)
    pygame.draw.rect(surf, cor, surf.get_rect(), border_radius=raio)

    # Borda de destaque para selecao por teclado
    if selecionado_destaque:
        borda_cor = (*BOTAO_SELECIONADO_TECLADO, alpha)
        pygame.draw.rect(surf, borda_cor, surf.get_rect(), width=max(4, rect.height // 16), border_radius=raio)

    # Texto
    fs = int(rect.height * 0.42)
    font = pygame.font.SysFont(fonte_nome, fs, bold=True)
    txt = font.render(label, True, BOTAO_TEXTO)
    while txt.get_width() > rect.width * 0.85 and fs > 10:
        fs -= 2
        font = pygame.font.SysFont(fonte_nome, fs, bold=True)
        txt = font.render(label, True, BOTAO_TEXTO)
    txt.set_alpha(alpha)
    x = (rect.width - txt.get_width()) // 2
    y = (rect.height - txt.get_height()) // 2
    surf.blit(txt, (x, y))

    screen.blit(surf, rect.topleft)


def desenhar_botoes_fade(screen, botoes, fonte_nome, selecionado, fade_start_ms, fade_t_ms, delay_ms,
                         teclado_ativo=False, cores_por_botao=None):
    """Desenha botoes com fade-in escalonado.

    cores_por_botao: opcional, lista de cores RGB. Se fornecido, cada botao usa sua cor.
    Caso contrario, todos usam BOTAO_PADRAO (azul).
    """
    now = pygame.time.get_ticks()
    for i, (rect, label) in enumerate(botoes):
        if cores_por_botao and i < len(cores_por_botao):
            cor = cores_por_botao[i]
        else:
            cor = BOTAO_PADRAO
        alpha = _calc_alpha(now, fade_start_ms, i, delay_ms, fade_t_ms)
        destaque = teclado_ativo and i == selecionado
        _desenhar_botao(screen, rect, label, fonte_nome, cor, alpha, destaque)
