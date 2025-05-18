import math

PRETO = (0, 0, 0)
ROSTO_BASE = ["O -- O", "-- -- --", "O o O", "-- o --"]

class Rosto:
    def __init__(self, fonte, screen, velocidade_fala=6):
        self.fonte = fonte
        self.screen = screen
        self.velocidade_fala = velocidade_fala

        self.ultimo_tempo_troca = 0.0
        self.piscando = False
        self.rosto_atual = ROSTO_BASE[0]


    def update(self, tempo: float, falando: bool):
        if not self.piscando and tempo - self.ultimo_tempo_troca >= 2.4:
            self.piscando = True
            self.ultimo_tempo_troca = tempo
        elif self.piscando and tempo - self.ultimo_tempo_troca >= 0.2:
            self.piscando = False
            self.ultimo_tempo_troca = tempo

        estado = 1 if self.piscando else 0

        
        if falando and ((int(tempo * self.velocidade_fala) % 2) == 0):
            estado += 2

        self.rosto_atual = ROSTO_BASE[estado]


    def desenhar(self, tempo: float):
        x_off = math.cos(tempo * 2) * 10
        y_off = math.sin(tempo * 2) * 20

        surf = self.fonte.render(self.rosto_atual, True, PRETO)
        rect = surf.get_rect(
            center=(self.screen.get_width()//2 + x_off, self.screen.get_height()//2 + y_off)
        )
        self.screen.blit(surf, rect)
