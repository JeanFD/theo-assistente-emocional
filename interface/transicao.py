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

    def start(self,)