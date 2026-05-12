"""Rosto do THEO desenhado vetorialmente, inspirado na logo.

Composto por 4 elementos:
  - Folha verde (acima da cabeca)
  - Olho esquerdo magenta
  - Olho direito amarelo
  - Boca azul

Animacoes sao feitas por interpolacao suave (lerp) entre conjuntos de
parametros-alvo. Cada expressao define um conjunto de parametros; ao
trocar de expressao, o rosto transita fluidamente para o novo alvo.
"""

import math
import pygame
from dataclasses import dataclass, fields
from interface.tema import COR_FOLHA, COR_OLHO_ESQ, COR_OLHO_DIR, COR_BOCA


@dataclass
class ParametrosRosto:
    # Olhos: escala relativa ao tamanho base
    olho_esq_w: float = 1.0
    olho_esq_h: float = 1.0
    olho_esq_curva: float = 0.0   # -0.6 = ^, 0 = circular, 0.6 = U
    olho_dir_w: float = 1.0
    olho_dir_h: float = 1.0
    olho_dir_curva: float = 0.0
    # Boca
    boca_w: float = 1.0
    boca_h: float = 1.0
    boca_curva: float = 0.5       # -1 triste, 0 reta/elipse, 1 sorriso
    # Folha
    folha_tilt: float = 0.0       # graus de inclinacao


EXPRESSOES = {
    "feliz": ParametrosRosto(
        boca_w=1.0, boca_h=0.7, boca_curva=0.7,
        olho_esq_curva=0.25, olho_dir_curva=0.25,
        folha_tilt=-8,
    ),
    "neutro": ParametrosRosto(
        boca_w=0.7, boca_h=0.55, boca_curva=0.2,
    ),
    "triste": ParametrosRosto(
        olho_esq_h=0.85, olho_dir_h=0.85,
        boca_w=0.7, boca_h=0.55, boca_curva=-0.55,
        folha_tilt=12,
    ),
    "ansioso": ParametrosRosto(
        olho_esq_w=1.15, olho_esq_h=1.15,
        olho_dir_w=1.15, olho_dir_h=1.15,
        boca_w=0.55, boca_h=0.7, boca_curva=-0.2,
        folha_tilt=6,
    ),
    "irritado": ParametrosRosto(
        olho_esq_w=1.0, olho_esq_h=0.7, olho_esq_curva=-0.35,
        olho_dir_w=1.0, olho_dir_h=0.7, olho_dir_curva=-0.35,
        boca_w=0.8, boca_h=0.5, boca_curva=-0.7,
    ),
    "surpreso": ParametrosRosto(
        olho_esq_w=1.25, olho_esq_h=1.3,
        olho_dir_w=1.25, olho_dir_h=1.3,
        boca_w=0.55, boca_h=0.95, boca_curva=0.0,
        folha_tilt=-4,
    ),
    "dormindo": ParametrosRosto(
        olho_esq_w=1.0, olho_esq_h=0.12, olho_esq_curva=-0.5,
        olho_dir_w=1.0, olho_dir_h=0.12, olho_dir_curva=-0.5,
        boca_w=0.45, boca_h=0.45, boca_curva=0.0,
        folha_tilt=-20,
    ),
}


def _lerp(a, b, t):
    return a + (b - a) * t


def _gerar_blob_curvado(cx, cy, w, h, curva):
    """Gera lista de pontos de um blob horizontal arredondado com curvatura.

    Reutilizado para boca e (com curva negativa/positiva) para os olhos
    quando precisam virar formato ^ ou U.

    - curva > 0: forma de sorriso (centro mais baixo, pontas elevadas)
    - curva < 0: forma de triste / olho sonolento
    - curva = 0: elipse achatada simetrica
    """
    n = 28
    topo = []
    base = []
    half_w = w / 2
    for i in range(n + 1):
        t = (i / n) * 2 - 1  # -1 a 1
        x = cx + t * half_w
        yc = cy + curva * w * 0.18 * (1 - t * t)
        h_local = h * math.sqrt(max(0.0, 1 - t * t))
        topo.append((x, yc - h_local / 2))
        base.append((x, yc + h_local / 2))
    return topo + list(reversed(base))


def _desenhar_blob(surface, cor, pontos):
    if len(pontos) >= 3:
        pygame.draw.polygon(surface, cor, pontos)


def _desenhar_olho(surface, cor, cx, cy, w, h, curva):
    """Desenha olho com tamanho e curvatura especificados."""
    if h < 4:
        h = 4  # garante visibilidade minima
    if abs(curva) < 0.05:
        # Elipse simples (mais limpa que poligono)
        rect = pygame.Rect(int(cx - w / 2), int(cy - h / 2), int(w), int(h))
        pygame.draw.ellipse(surface, cor, rect)
    else:
        pontos = _gerar_blob_curvado(cx, cy, w, h, curva)
        _desenhar_blob(surface, cor, pontos)


def _desenhar_folha(surface, cor, cx, cy, w, h, tilt_graus):
    """Desenha folha verde com pontinha em cima (igual a logo)."""
    # Forma: gota invertida (ponta em cima, base arredondada embaixo)
    pontos = []
    n = 26
    for i in range(n):
        t = i / n
        ang = t * 2 * math.pi
        # Raio variavel: pequeno em cima (pontuda), grande embaixo (redonda)
        # ang = pi/2 (270 graus visualmente) = topo
        fator_y = math.sin(ang)
        if fator_y < 0:
            # Parte de cima: afina e estica
            raio_x = w * 0.32
            raio_y = h * 0.7
        else:
            # Parte de baixo: redonda
            raio_x = w * 0.5
            raio_y = h * 0.55
        x = raio_x * math.cos(ang)
        y = raio_y * fator_y
        # Deslocar pra cima (pontinha)
        if fator_y < -0.6:
            y -= h * 0.15
            x *= 0.4  # afina mais a pontinha
        # Rotaciona
        if tilt_graus:
            rad = math.radians(tilt_graus)
            cos_t, sin_t = math.cos(rad), math.sin(rad)
            x, y = x * cos_t - y * sin_t, x * sin_t + y * cos_t
        pontos.append((cx + x, cy + y))
    _desenhar_blob(surface, cor, pontos)


class Face:
    def __init__(self, screen):
        self.screen = screen
        self._recalcular_layout()
        self.atual = ParametrosRosto()
        self.alvo = ParametrosRosto()
        self.expressao_nome = "neutro"
        self.set_expressao("neutro", instantaneo=True)
        # Animacoes automaticas
        self.ultimo_piscar = 0.0
        self.piscando_ate = 0.0

    def _recalcular_layout(self):
        w, h = self.screen.get_size()
        self.tela_w = w
        self.tela_h = h
        # Tamanho base do rosto: limita pelo menor lado para nao deformar
        self.face_h = int(h * 0.62)
        self.face_w = int(self.face_h * 1.05)
        # Dimensoes base de cada elemento
        self.base_olho_w = self.face_h * 0.20
        self.base_olho_h = self.face_h * 0.20
        self.base_boca_w = self.face_h * 0.48
        self.base_boca_h = self.face_h * 0.18
        self.base_folha_w = self.face_h * 0.30
        self.base_folha_h = self.face_h * 0.32
        # Posicoes relativas ao centro do rosto
        self.off_olho_x = self.face_w * 0.20
        self.off_olho_y = -self.face_h * 0.10
        self.off_boca_y = self.face_h * 0.23
        self.off_folha_y = -self.face_h * 0.48

    def set_expressao(self, nome, instantaneo=False):
        if nome not in EXPRESSOES:
            nome = "neutro"
        self.expressao_nome = nome
        self.alvo = EXPRESSOES[nome]
        if instantaneo:
            self.atual = ParametrosRosto(**{f.name: getattr(self.alvo, f.name) for f in fields(self.alvo)})

    def update(self, dt, tempo, falando=False, dormindo=False):
        # Define expressao baseada em flags simples
        if dormindo:
            self.set_expressao("dormindo")
        elif self.expressao_nome == "dormindo":
            # acordou: volta pro neutro
            self.set_expressao("neutro")

        # Lerp dos parametros em direcao ao alvo (suaviza animacao)
        velocidade = 6.0
        fator = min(1.0, dt * velocidade)
        for f in fields(self.atual):
            v_atual = getattr(self.atual, f.name)
            v_alvo = getattr(self.alvo, f.name)
            setattr(self.atual, f.name, _lerp(v_atual, v_alvo, fator))

        # Piscar automatico (so quando nao esta dormindo)
        if not dormindo:
            if tempo >= self.ultimo_piscar + 3.2:
                self.piscando_ate = tempo + 0.13
                self.ultimo_piscar = tempo
        self._piscando_intensidade = 0.0
        if tempo < self.piscando_ate:
            # Suaviza com curva senoidal
            t_local = (self.piscando_ate - tempo) / 0.13
            self._piscando_intensidade = math.sin(t_local * math.pi)

        # Movimento da boca quando falando
        self._falando_offset = 0.0
        if falando and not dormindo:
            self._falando_offset = (math.sin(tempo * 11) + 1) / 2  # 0..1

    def desenhar(self, tempo):
        cx_face = self.tela_w // 2
        cy_face = self.tela_h // 2
        # Float suave do rosto inteiro
        flutua_x = math.cos(tempo * 1.1) * self.tela_w * 0.012
        flutua_y = math.sin(tempo * 0.9) * self.tela_h * 0.016
        cx = cx_face + int(flutua_x)
        cy = cy_face + int(flutua_y)

        p = self.atual

        # Olhos (aplica piscada por achatamento)
        intens_pisca = self._piscando_intensidade
        # Esquerdo (magenta, do espectador)
        olho_esq_h = self.base_olho_h * p.olho_esq_h * (1 - 0.9 * intens_pisca)
        _desenhar_olho(
            self.screen, COR_OLHO_ESQ,
            cx - self.off_olho_x,
            cy + self.off_olho_y,
            self.base_olho_w * p.olho_esq_w,
            olho_esq_h,
            p.olho_esq_curva,
        )
        # Direito (amarelo)
        olho_dir_h = self.base_olho_h * p.olho_dir_h * (1 - 0.9 * intens_pisca)
        _desenhar_olho(
            self.screen, COR_OLHO_DIR,
            cx + self.off_olho_x,
            cy + self.off_olho_y,
            self.base_olho_w * p.olho_dir_w,
            olho_dir_h,
            p.olho_dir_curva,
        )

        # Boca (com modulacao de fala)
        boca_w = self.base_boca_w * p.boca_w
        boca_h = self.base_boca_h * p.boca_h * (1 + 0.45 * self._falando_offset)
        boca_curva = p.boca_curva
        pontos_boca = _gerar_blob_curvado(
            cx, cy + self.off_boca_y, boca_w, boca_h, boca_curva
        )
        _desenhar_blob(self.screen, COR_BOCA, pontos_boca)

        # Folha por cima (sobreposicao leve na cabeca)
        _desenhar_folha(
            self.screen, COR_FOLHA,
            cx - self.face_w * 0.12,
            cy + self.off_folha_y,
            self.base_folha_w,
            self.base_folha_h,
            p.folha_tilt,
        )
