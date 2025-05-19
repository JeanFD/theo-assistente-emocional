import pygame
import time

class Transicao:
    def __init__(self, tempo_fade=1.0):
        self.tempo_fade = tempo_fade
        self.transicionando = False
        self.t0 = 0
        self.de = (255, 255, 255)
        self.para = (0, 0, 0)
        self.fracao = 0.0

    def start(self, cor_atual, cor_destino):
        self.transicionando = True
        self.t0 = time.time()
        self.de = cor_atual
        self.para = cor_destino
        self.fracao = 0.0

    def update(self):
        if not self.transicionando:
            return self.para, False
        dt = time.time() - self.t0
        frac = min(dt / self.tempo_fade, 1.0)
        cor = tuple(
            int(self.de[i] + (self.para[i] - self.de[i]) * frac)
            for i in range(3)
        )
        if frac >= 1.0:
            self.transicionando = False
            return self.para, True
        return cor, False

    def is_active(self):
        return self.transicionando