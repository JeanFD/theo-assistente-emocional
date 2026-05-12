"""Componentes de UI: texto e botoes do THEO.

Design system:
  - Fonte personalizada (JandaManateeSolid) com fallback profissional
  - Botoes arredondados com sombra suave (profundidade)
  - Borda de destaque grossa quando selecionado por teclado
  - Cache de fontes por tamanho (evita recriar a cada frame)
"""

import os
import pygame
from interface.tema import (
    BRANCO, AZUL_MARINHO, BOTAO_PADRAO, BOTAO_SELECIONADO_TECLADO, BOTAO_TEXTO,
    SOMBRA_BOTAO, RAIO_BOTAO, OFFSET_SOMBRA, BORDA_DESTAQUE,
    FONTE_CUSTOM_PATH, FONTE_FALLBACKS,
)


_FONT_CACHE = {}


def fonte(tamanho, bold=True):
    """Carrega fonte custom se existir, senao usa fallback. Cacheia por tamanho."""
    key = (tamanho, bold)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    if os.path.exists(FONTE_CUSTOM_PATH):
        try:
            f = pygame.font.Font(FONTE_CUSTOM_PATH, tamanho)
            _FONT_CACHE[key] = f
            return f
        except Exception:
            pass
    # Fallback: tenta cada nome ate funcionar
    for nome in FONTE_FALLBACKS:
        try:
            f = pygame.font.SysFont(nome, tamanho, bold=bold)
            _FONT_CACHE[key] = f
            return f
        except Exception:
            continue
    f = pygame.font.Font(None, tamanho)
    _FONT_CACHE[key] = f
    return f


def _wrap_lines(fonte_obj, texto, max_width):
    """Quebra texto em linhas respeitando \\n e largura maxima."""
    linhas = []
    for paragrafo in texto.split('\n'):
        words = paragrafo.split(' ')
        line = ''
        while words:
            word = words.pop(0)
            test_line = f"{line} {word}".strip()
            if fonte_obj.size(test_line)[0] <= max_width:
                line = test_line
            else:
                linhas.append(line)
                line = word
        linhas.append(line)
    return linhas


def desenhar_frase(screen, fonte_obj, texto, cor=AZUL_MARINHO, top_ratio=0.13, max_width_ratio=0.86):
    """Desenha texto centralizado no topo com word-wrap e espacamento adequado."""
    if not texto:
        return
    max_width = screen.get_width() * max_width_ratio
    linhas = _wrap_lines(fonte_obj, texto, max_width)
    line_h = int(fonte_obj.get_linesize() * 1.08)
    total_h = line_h * len(linhas)
    y = screen.get_height() * top_ratio - total_h / 2
    for i, l in enumerate(linhas):
        surf = fonte_obj.render(l, True, cor)
        rect = surf.get_rect(center=(screen.get_width() // 2, y + i * line_h + line_h / 2))
        screen.blit(surf, rect)


def criar_botoes(screen_width, screen_height, rotulos):
    """Cria layout dos botoes na parte inferior da tela."""
    if not rotulos:
        return []
    margem = screen_width * 0.09
    espaco = screen_width * 0.022
    altura_botao = screen_height * 0.14
    largura_botao = (screen_width - 2 * margem - (len(rotulos) - 1) * espaco) / len(rotulos)
    y = screen_height * 0.80
    x0 = (screen_width - (len(rotulos) * largura_botao + (len(rotulos) - 1) * espaco)) / 2
    return [
        (pygame.Rect(int(x0 + i * (largura_botao + espaco)), int(y), int(largura_botao), int(altura_botao)), rtl)
        for i, rtl in enumerate(rotulos)
    ]


def _calc_alpha(now, start_ms, index, delay_ms, dur_ms):
    t = now - (start_ms + index * delay_ms)
    if t <= 0:
        return 0
    if t >= dur_ms:
        return 255
    return int(255 * (t / dur_ms))


def _texto_que_cabe(label, max_w, max_h):
    """Encontra o maior tamanho de fonte que faz o texto caber no espaco."""
    fs = int(max_h * 0.46)
    while fs > 12:
        f = fonte(fs, bold=True)
        size = f.size(label)
        if size[0] <= max_w and size[1] <= max_h * 0.85:
            return f, size
        fs -= 2
    return fonte(12, bold=True), fonte(12, bold=True).size(label)


def _desenhar_botao(screen, rect, label, cor_fundo, alpha, selecionado_destaque):
    """Botao com sombra suave, cantos arredondados e texto centralizado."""
    raio = int(min(rect.width, rect.height) * RAIO_BOTAO)

    # Sombra (alphablend separado pois tem alpha proprio)
    sombra_alpha = (SOMBRA_BOTAO[3] * alpha) // 255
    if sombra_alpha > 0:
        sombra_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(
            sombra_surf,
            (SOMBRA_BOTAO[0], SOMBRA_BOTAO[1], SOMBRA_BOTAO[2], sombra_alpha),
            sombra_surf.get_rect(),
            border_radius=raio,
        )
        screen.blit(sombra_surf, (rect.left, rect.top + OFFSET_SOMBRA))

    # Corpo do botao
    corpo = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(corpo, (*cor_fundo, alpha), corpo.get_rect(), border_radius=raio)

    # Borda de destaque (teclado)
    if selecionado_destaque:
        pygame.draw.rect(
            corpo,
            (*BOTAO_SELECIONADO_TECLADO, alpha),
            corpo.get_rect(),
            width=BORDA_DESTAQUE,
            border_radius=raio,
        )

    # Texto
    f, (tw, th) = _texto_que_cabe(label, rect.width * 0.86, rect.height)
    txt = f.render(label, True, BOTAO_TEXTO)
    txt.set_alpha(alpha)
    corpo.blit(txt, ((rect.width - tw) // 2, (rect.height - th) // 2))

    screen.blit(corpo, rect.topleft)


def desenhar_botoes_fade(screen, botoes, fonte_nome, selecionado, fade_start_ms, fade_t_ms, delay_ms,
                         teclado_ativo=False, cores_por_botao=None):
    """Desenha botoes com fade-in escalonado e cores configuraveis por botao."""
    now = pygame.time.get_ticks()
    for i, (rect, label) in enumerate(botoes):
        cor = cores_por_botao[i] if (cores_por_botao and i < len(cores_por_botao)) else BOTAO_PADRAO
        alpha = _calc_alpha(now, fade_start_ms, i, delay_ms, fade_t_ms)
        destaque = teclado_ativo and i == selecionado
        _desenhar_botao(screen, rect, label, cor, alpha, destaque)
