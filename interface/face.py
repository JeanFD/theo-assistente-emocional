"""Rosto do THEO desenhado vetorialmente, inspirado na logo.

Composto pelos 4 elementos da logo:
  - Folha verde (acima da cabeca)
  - Olho esquerdo magenta
  - Olho direito amarelo
  - Boca azul

Tecnica de renderizacao: supersampling (desenha em buffer 2x e faz
smoothscale para a tela) para eliminar serrilhado e dar acabamento
arredondado e suave.

Animacoes sao feitas por interpolacao suave (lerp) entre conjuntos de
parametros-alvo. Cada expressao define um conjunto de parametros; ao
trocar de expressao, o rosto transita fluidamente para o novo alvo.
"""

import math
import pygame
from dataclasses import dataclass, fields
from interface.tema import COR_FOLHA, COR_OLHO_ESQ, COR_OLHO_DIR, COR_BOCA


SCALE = 2  # fator de supersampling


@dataclass
class ParametrosRosto:
    # Olhos: escala relativa ao tamanho base
    olho_esq_w: float = 1.0
    olho_esq_h: float = 1.0
    olho_esq_curva: float = 0.0   # -0.6 = ^, 0 = elipse, 0.6 = U
    olho_esq_dy: float = 0.0
    olho_dir_w: float = 1.0
    olho_dir_h: float = 1.0
    olho_dir_curva: float = 0.0
    olho_dir_dy: float = 0.0
    # Boca
    boca_w: float = 1.0
    boca_h: float = 1.0
    boca_curva: float = 0.4       # -1 triste, 0 reta, 1 sorriso
    # Folha
    folha_tilt: float = -5.0


EXPRESSOES = {
    "feliz": ParametrosRosto(
        boca_w=1.1, boca_h=0.85, boca_curva=0.7,
        olho_esq_curva=0.2, olho_dir_curva=0.2,
        folha_tilt=-8,
    ),
    "neutro": ParametrosRosto(
        boca_w=0.85, boca_h=0.7, boca_curva=0.25,
        folha_tilt=-5,
    ),
    "triste": ParametrosRosto(
        olho_esq_h=0.9, olho_dir_h=0.9,
        olho_esq_dy=0.05, olho_dir_dy=0.05,
        boca_w=0.8, boca_h=0.65, boca_curva=-0.5,
        folha_tilt=14,
    ),
    "ansioso": ParametrosRosto(
        olho_esq_w=1.15, olho_esq_h=1.2,
        olho_dir_w=1.15, olho_dir_h=1.2,
        boca_w=0.6, boca_h=0.7, boca_curva=-0.15,
        folha_tilt=6,
    ),
    "irritado": ParametrosRosto(
        olho_esq_w=1.05, olho_esq_h=0.75, olho_esq_curva=-0.3,
        olho_dir_w=1.05, olho_dir_h=0.75, olho_dir_curva=-0.3,
        boca_w=0.85, boca_h=0.55, boca_curva=-0.6,
        folha_tilt=2,
    ),
    "surpreso": ParametrosRosto(
        olho_esq_w=1.25, olho_esq_h=1.3,
        olho_dir_w=1.25, olho_dir_h=1.3,
        boca_w=0.6, boca_h=1.0, boca_curva=0.0,
        folha_tilt=-4,
    ),
    "dormindo": ParametrosRosto(
        olho_esq_w=1.0, olho_esq_h=0.08, olho_esq_curva=-0.45,
        olho_dir_w=1.0, olho_dir_h=0.08, olho_dir_curva=-0.45,
        olho_esq_dy=0.05, olho_dir_dy=0.05,
        boca_w=0.4, boca_h=0.5, boca_curva=0.0,
        folha_tilt=-22,
    ),
}


def _lerp(a, b, t):
    return a + (b - a) * t


def _pontos_blob_curvado(cx, cy, w, h, curva, n=64):
    """Gera blob horizontal arredondado com curvatura suave.

    - curva > 0: sorriso (centro mais baixo, pontas elevadas)
    - curva < 0: triste / olho sonolento
    - curva = 0: elipse achatada simetrica
    """
    half_w = w / 2
    topo = []
    base = []
    for i in range(n + 1):
        t = (i / n) * 2 - 1  # -1 a 1
        x = cx + t * half_w
        yc = cy + curva * w * 0.18 * (1 - t * t)
        h_local = h * math.sqrt(max(0.0, 1 - t * t))
        topo.append((x, yc - h_local / 2))
        base.append((x, yc + h_local / 2))
    return topo + list(reversed(base))


def _pontos_elipse(cx, cy, rx, ry, n=64):
    """Gera pontos de uma elipse cheia."""
    pontos = []
    for i in range(n):
        t = i / n * 2 * math.pi
        pontos.append((cx + rx * math.cos(t), cy + ry * math.sin(t)))
    return pontos


def _pontos_folha(cx, cy, w, h, tilt_graus, n=80):
    """Gera pontos da folha (formato de gota com pontinha em cima)."""
    pontos = []
    rad = math.radians(tilt_graus)
    cos_t, sin_t = math.cos(rad), math.sin(rad)
    for i in range(n):
        t = i / n
        ang = t * 2 * math.pi
        # ang = -pi/2 (3pi/2) = topo (ponta da folha)
        # ang = pi/2 = base arredondada
        fator_y = math.sin(ang)
        if fator_y < 0:
            # Metade de cima: estica e afina (ponta)
            taper = (-fator_y) ** 1.5  # 0 na lateral, 1 na ponta
            raio_x = w * 0.5 * (1 - 0.7 * taper)
            raio_y = h * 0.7
            x = raio_x * math.cos(ang)
            y = raio_y * fator_y - h * 0.05 * taper
        else:
            # Metade de baixo: bem redonda
            raio_x = w * 0.5
            raio_y = h * 0.55
            x = raio_x * math.cos(ang)
            y = raio_y * fator_y
        # Rotacao
        xr = x * cos_t - y * sin_t
        yr = x * sin_t + y * cos_t
        pontos.append((cx + xr, cy + yr))
    return pontos


def _draw_smooth_polygon(surface, cor, pontos):
    """Polygon desenhado com gfxdraw para usar AA do smoothscale ao final."""
    if len(pontos) >= 3:
        pygame.draw.polygon(surface, cor, pontos)


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
        self._piscando_intensidade = 0.0
        self._falando_offset = 0.0
        # Buffer offscreen para supersampling (suaviza serrilhado)
        bw = self.tela_w * SCALE
        bh = self.tela_h * SCALE
        self.buffer = pygame.Surface((bw, bh), pygame.SRCALPHA)

    def _recalcular_layout(self):
        w, h = self.screen.get_size()
        self.tela_w = w
        self.tela_h = h
        # Rosto bem grande, ocupa maioria da tela
        self.face_h = int(h * 0.80)
        self.face_w = int(self.face_h * 1.10)
        # Dimensoes base de cada elemento (grandes e arredondados)
        self.base_olho_w = self.face_h * 0.24
        self.base_olho_h = self.face_h * 0.24
        self.base_boca_w = self.face_h * 0.58
        self.base_boca_h = self.face_h * 0.22
        self.base_folha_w = self.face_h * 0.36
        self.base_folha_h = self.face_h * 0.40
        # Posicoes relativas ao centro do rosto
        self.off_olho_x = self.face_w * 0.22
        self.off_olho_y = -self.face_h * 0.08
        self.off_boca_y = self.face_h * 0.24
        self.off_folha_y = -self.face_h * 0.46
        self.off_folha_x = -self.face_w * 0.12

    def set_expressao(self, nome, instantaneo=False):
        if nome not in EXPRESSOES:
            nome = "neutro"
        self.expressao_nome = nome
        self.alvo = EXPRESSOES[nome]
        if instantaneo:
            for f in fields(self.alvo):
                setattr(self.atual, f.name, getattr(self.alvo, f.name))

    def update(self, dt, tempo, falando=False, dormindo=False):
        if dormindo and self.expressao_nome != "dormindo":
            self.set_expressao("dormindo")
        elif not dormindo and self.expressao_nome == "dormindo":
            self.set_expressao("neutro")

        # Lerp suave em direcao ao alvo
        velocidade = 6.0
        fator = min(1.0, dt * velocidade)
        for f in fields(self.atual):
            v_atual = getattr(self.atual, f.name)
            v_alvo = getattr(self.alvo, f.name)
            setattr(self.atual, f.name, _lerp(v_atual, v_alvo, fator))

        # Piscar automatico
        if not dormindo:
            if tempo >= self.ultimo_piscar + 3.2:
                self.piscando_ate = tempo + 0.14
                self.ultimo_piscar = tempo
        self._piscando_intensidade = 0.0
        if tempo < self.piscando_ate:
            t_local = (self.piscando_ate - tempo) / 0.14
            self._piscando_intensidade = math.sin(t_local * math.pi)

        # Boca pulsa quando falando
        self._falando_offset = 0.0
        if falando and not dormindo:
            self._falando_offset = (math.sin(tempo * 11) + 1) / 2

    def _desenhar_face_buffer(self, cx, cy):
        """Desenha no buffer offscreen (em escala SCALE)."""
        s = SCALE
        p = self.atual
        cx_b = int(cx * s)
        cy_b = int(cy * s)

        # Folha (atras do rosto, mas como esta acima dos olhos da impressao
        # de estar saindo da cabeca)
        folha_w = self.base_folha_w * s
        folha_h = self.base_folha_h * s
        folha_cx = cx_b + int(self.off_folha_x * s)
        folha_cy = cy_b + int(self.off_folha_y * s)
        pontos_folha = _pontos_folha(folha_cx, folha_cy, folha_w, folha_h, p.folha_tilt)
        _draw_smooth_polygon(self.buffer, COR_FOLHA, pontos_folha)

        # Olhos
        intens_pisca = self._piscando_intensidade

        olho_esq_w = self.base_olho_w * p.olho_esq_w * s
        olho_esq_h = self.base_olho_h * p.olho_esq_h * s * (1 - 0.9 * intens_pisca)
        olho_esq_cx = cx_b - int(self.off_olho_x * s)
        olho_esq_cy = cy_b + int((self.off_olho_y + p.olho_esq_dy * self.face_h) * s)
        if abs(p.olho_esq_curva) < 0.05 and olho_esq_h > 8:
            # Elipse simples (rapido)
            pontos_olho_esq = _pontos_elipse(olho_esq_cx, olho_esq_cy, olho_esq_w / 2, olho_esq_h / 2)
        else:
            pontos_olho_esq = _pontos_blob_curvado(
                olho_esq_cx, olho_esq_cy, olho_esq_w, max(olho_esq_h, 4), p.olho_esq_curva
            )
        _draw_smooth_polygon(self.buffer, COR_OLHO_ESQ, pontos_olho_esq)

        olho_dir_w = self.base_olho_w * p.olho_dir_w * s
        olho_dir_h = self.base_olho_h * p.olho_dir_h * s * (1 - 0.9 * intens_pisca)
        olho_dir_cx = cx_b + int(self.off_olho_x * s)
        olho_dir_cy = cy_b + int((self.off_olho_y + p.olho_dir_dy * self.face_h) * s)
        if abs(p.olho_dir_curva) < 0.05 and olho_dir_h > 8:
            pontos_olho_dir = _pontos_elipse(olho_dir_cx, olho_dir_cy, olho_dir_w / 2, olho_dir_h / 2)
        else:
            pontos_olho_dir = _pontos_blob_curvado(
                olho_dir_cx, olho_dir_cy, olho_dir_w, max(olho_dir_h, 4), p.olho_dir_curva
            )
        _draw_smooth_polygon(self.buffer, COR_OLHO_DIR, pontos_olho_dir)

        # Boca
        boca_w = self.base_boca_w * p.boca_w * s
        boca_h = self.base_boca_h * p.boca_h * s * (1 + 0.45 * self._falando_offset)
        boca_cx = cx_b
        boca_cy = cy_b + int(self.off_boca_y * s)
        pontos_boca = _pontos_blob_curvado(boca_cx, boca_cy, boca_w, boca_h, p.boca_curva)
        _draw_smooth_polygon(self.buffer, COR_BOCA, pontos_boca)

    def desenhar(self, tempo):
        # Float suave do rosto
        flutua_x = math.cos(tempo * 1.1) * self.tela_w * 0.010
        flutua_y = math.sin(tempo * 0.9) * self.tela_h * 0.014
        cx = self.tela_w / 2 + flutua_x
        cy = self.tela_h / 2 + flutua_y

        # Limpa buffer e desenha
        self.buffer.fill((0, 0, 0, 0))
        self._desenhar_face_buffer(cx, cy)

        # Smoothscale para a tela: usa o algoritmo de filtragem do pygame
        # para gerar imagem suave (anti-aliasing por supersampling)
        suave = pygame.transform.smoothscale(self.buffer, (self.tela_w, self.tela_h))
        self.screen.blit(suave, (0, 0))
