import pygame

BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
CINZA = (200, 200, 200)
SELECIONADO = (50, 175, 200)

FADE_T = 0.3
DELAY_BTWN = 0.2

class TextRenderer:
    def __init__(self, screen, fonte, max_width_ratio=0.8, top_ratio=0.2, color=PRETO):
        self.screen = screen
        self.fonte = fonte
        self.max_width_ratio = max_width_ratio
        self.top_ratio = top_ratio
        self.color = color

    def desenhar(self, texto):
        max_width = self.screen.get_width() * self.max_width_ratio
        words, lines, line = texto.split(' '), [], ''
        for word in words:
            test = f"{line} {word}".strip()
            if self.fonte.size(test)[0] <= max_width:
                line = test
            else:
                lines.append(line)
                line = word
        if line: lines.append(line)
            
        line_h = self.fonte.get_linesize()
        total_h = line_h * len(lines)
        y = self.screen.get_height() * self.top_ratio - total_h/2
        for i, l in enumerate(lines):
            surf = self.fonte.render(l, True, self.color)
            rect = surf.get_rect(center=(self.screen.get_width()//2, y + i*line_h))
            self.screen.blit(surf, rect)


class Botao:
    def __init__(self, rect, label, fonte, cor_base, selected_color):
        self.rect = rect
        self.label = label
        self.fonte = fonte
        self.cor_base, self.selected_color = cor_base, selected_color
        self.alpha = 0

    def atualiza_alpha(self, now, start_ms, index, delay_ms, dur_ms):
        t = now - (start_ms + index * delay_ms)
        if t <= 0: self.alpha = 0
        elif t >= dur_ms: self.alpha = 255
        else: self.alpha = int(255 * (t / dur_ms))

    def desenhar(self, screen, fonte_base, selected, alpha):
        cor = self.selected_color if selected else self.cor_base
        surf_bg = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        surf_bg.fill((*cor, alpha))

        fs = int(self.rect.height * 0.5)
        font = pygame.font.SysFont(fonte_base, fs, bold=True)
        txt = font.render(self.label, True, BRANCO)
        while txt.get_width() > self.rect.width * 0.8 and fs > 10:
            fs -= 2
            font = pygame.font.SysFont(fonte_base, fs, bold=True)
            txt = font.render(self.label, True, BRANCO)
        txt.set_alpha(alpha)

        x = (self.rect.width - txt.get_width()) // 2
        y = (self.rect.height - txt.get_height()) // 2
        surf_bg.blit(txt, (x, y))
        screen.blit(surf_bg, self.rect.topleft)
        
        
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

class GrupoBotoes:
    def __init__(self, screen_width, screen_height, labels, font_name,
                 base_color=CINZA, select_color=SELECIONADO,
                 fade_duration=FADE_T*1000, fade_delay=DELAY_BTWN*1000):
        margem, espaco = screen_width*0.05, screen_width*0.02
        btn_h = screen_height*0.18
        btn_w = (screen_width - 2*margem - (len(labels)-1)*espaco)/len(labels)
        y = screen_height*0.8
        x0 = (screen_width - (len(labels)*btn_w + (len(labels)-1)*espaco))/2

        self.buttons = [
            Botao(pygame.Rect(x0+i*(btn_w+espaco), y, btn_w, btn_h),
                   lbl, font_name, base_color, select_color)
            for i,lbl in enumerate(labels)
        ]
        self.start_ms = pygame.time.get_ticks()
        self.fade_dur, self.fade_dly = fade_duration, fade_delay

    def desenhar(self, screen, selected_index):
        now = pygame.time.get_ticks()
        for i, btn in enumerate(self.buttons):
            btn.atualiza_alpha(now, self.start_ms, i, self.fade_dly, self.fade_dur)
            btn.desenhar(screen, btn.fonte, i==selected_index, btn.alpha)