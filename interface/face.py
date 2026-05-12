"""Rosto do THEO baseado na logo oficial.

Carrega `refs/theo_pequeno1.png`, separa em 4 sprites (folha, olho esquerdo,
olho direito, boca) e os anima individualmente. Quando a expressao e' "feliz",
os 4 sprites ficam exatamente na mesma posicao da logo original — o rosto
e' identico a logo. Para outras expressoes, cada sprite e' escalado/movido
suavemente via interpolacao (lerp).
"""

import os
import math
import pygame
from dataclasses import dataclass, fields


LOGO_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "refs", "theo_pequeno1.png",
)


@dataclass
class ParametrosRosto:
    """Modificacoes (scale/offset/rotacao) aplicadas a cada blob.

    Todos os valores padrao = 0 ou 1, o que reproduz a logo original.
    """
    # Folha verde (top-left)
    folha_scale: float = 1.0
    folha_dx: float = 0.0
    folha_dy: float = 0.0
    folha_rot: float = 0.0
    # Olho esquerdo magenta (top-right)
    olho_esq_sx: float = 1.0
    olho_esq_sy: float = 1.0
    olho_esq_dy: float = 0.0
    # Olho direito amarelo (bottom-left)
    olho_dir_sx: float = 1.0
    olho_dir_sy: float = 1.0
    olho_dir_dy: float = 0.0
    # Boca azul (bottom-right)
    boca_sx: float = 1.0
    boca_sy: float = 1.0
    boca_dy: float = 0.0
    boca_rot: float = 0.0


# SORRINDO = parametros default = logo identica
EXPRESSAO_FELIZ = ParametrosRosto()

EXPRESSOES = {
    "feliz": EXPRESSAO_FELIZ,
    "neutro": ParametrosRosto(
        boca_sx=0.78, boca_sy=0.72,
    ),
    "triste": ParametrosRosto(
        olho_esq_sy=0.92, olho_dir_sy=0.92,
        olho_esq_dy=0.02, olho_dir_dy=0.02,
        boca_sx=0.85, boca_sy=0.65, boca_rot=180,
        folha_rot=14,
    ),
    "ansioso": ParametrosRosto(
        olho_esq_sx=1.18, olho_esq_sy=1.2,
        olho_dir_sx=1.18, olho_dir_sy=1.2,
        boca_sx=0.55, boca_sy=0.65,
    ),
    "irritado": ParametrosRosto(
        olho_esq_sy=0.55, olho_dir_sy=0.55,
        boca_sx=0.8, boca_sy=0.5, boca_rot=180,
    ),
    "surpreso": ParametrosRosto(
        olho_esq_sx=1.3, olho_esq_sy=1.35,
        olho_dir_sx=1.3, olho_dir_sy=1.35,
        boca_sx=0.55, boca_sy=0.95,
    ),
    "dormindo": ParametrosRosto(
        olho_esq_sy=0.05, olho_dir_sy=0.05,
        olho_esq_dy=0.02, olho_dir_dy=0.02,
        boca_sx=0.4, boca_sy=0.4,
        folha_rot=-22,
    ),
}


def _lerp(a, b, t):
    return a + (b - a) * t


def _carregar_logo():
    """Carrega o PNG da logo, garantindo fundo transparente."""
    img = pygame.image.load(LOGO_PATH).convert_alpha()
    # Heuristica: se o canto e' preto opaco, o PNG tem fundo preto solido.
    # Nesse caso aplicamos colorkey para tornar preto transparente.
    corner = img.get_at((0, 0))
    if corner[3] == 255 and max(corner[:3]) < 30:
        plana = img.convert()
        plana.set_colorkey((0, 0, 0))
        return plana
    return img


class Face:
    def __init__(self, screen):
        self.screen = screen
        self._carregar_sprites()
        self._recalcular_layout()
        self.atual = ParametrosRosto()
        self.alvo = ParametrosRosto()
        self.expressao_nome = "feliz"
        self.set_expressao("feliz", instantaneo=True)
        # Animacoes automaticas
        self.ultimo_piscar = 0.0
        self.piscando_ate = 0.0
        self._piscando_intensidade = 0.0
        self._falando_offset = 0.0

    def _carregar_sprites(self):
        logo = _carregar_logo()
        w, h = logo.get_size()
        hw, hh = w // 2, h // 2
        # Quadrantes da logo (1:1 com as 4 cores)
        self.spr_folha = logo.subsurface((0, 0, hw, hh)).copy()
        self.spr_olho_esq = logo.subsurface((hw, 0, hw, hh)).copy()
        self.spr_olho_dir = logo.subsurface((0, hh, hw, hh)).copy()
        self.spr_boca = logo.subsurface((hw, hh, hw, hh)).copy()

    def _recalcular_layout(self):
        w, h = self.screen.get_size()
        self.tela_w = w
        self.tela_h = h
        # Rosto quadrado, grande, centrado na tela
        self.face_size = int(min(h * 0.82, w * 0.62))
        self.face_w = self.face_size
        self.face_h = self.face_size
        # Tamanho de cada quadrante (1/2 do rosto em cada dim)
        self.quad_w = self.face_size // 2
        self.quad_h = self.face_size // 2
        # Centro do rosto = centro da tela
        self.face_cx = w // 2
        self.face_cy = h // 2
        # Posicao do centro de cada quadrante (replica logo 2x2)
        off = self.face_size / 4
        self.pos_folha = (self.face_cx - off, self.face_cy - off)
        self.pos_olho_esq = (self.face_cx + off, self.face_cy - off)
        self.pos_olho_dir = (self.face_cx - off, self.face_cy + off)
        self.pos_boca = (self.face_cx + off, self.face_cy + off)

    def set_expressao(self, nome, instantaneo=False):
        if nome not in EXPRESSOES:
            nome = "feliz"
        self.expressao_nome = nome
        self.alvo = EXPRESSOES[nome]
        if instantaneo:
            for f in fields(self.alvo):
                setattr(self.atual, f.name, getattr(self.alvo, f.name))

    def update(self, dt, tempo, falando=False, dormindo=False):
        if dormindo and self.expressao_nome != "dormindo":
            self.set_expressao("dormindo")
        elif not dormindo and self.expressao_nome == "dormindo":
            self.set_expressao("feliz")

        velocidade = 6.0
        fator = min(1.0, dt * velocidade)
        for f in fields(self.atual):
            v_atual = getattr(self.atual, f.name)
            v_alvo = getattr(self.alvo, f.name)
            setattr(self.atual, f.name, _lerp(v_atual, v_alvo, fator))

        if not dormindo:
            if tempo >= self.ultimo_piscar + 3.2:
                self.piscando_ate = tempo + 0.14
                self.ultimo_piscar = tempo
        self._piscando_intensidade = 0.0
        if tempo < self.piscando_ate:
            t_local = (self.piscando_ate - tempo) / 0.14
            self._piscando_intensidade = math.sin(t_local * math.pi)

        self._falando_offset = 0.0
        if falando and not dormindo:
            self._falando_offset = (math.sin(tempo * 11) + 1) / 2

    def _blit_quadrante(self, sprite, pos_base, offset_face, scale_x, scale_y, dy, rot, dx=0.0):
        target_w = max(2, int(self.quad_w * scale_x))
        target_h = max(2, int(self.quad_h * scale_y))
        s = pygame.transform.smoothscale(sprite, (target_w, target_h))
        if rot:
            s = pygame.transform.rotate(s, rot)
        cx = pos_base[0] + offset_face[0] + dx * self.face_w
        cy = pos_base[1] + offset_face[1] + dy * self.face_h
        rect = s.get_rect(center=(int(cx), int(cy)))
        self.screen.blit(s, rect.topleft)

    def desenhar(self, tempo):
        flutua_x = math.cos(tempo * 1.1) * self.tela_w * 0.010
        flutua_y = math.sin(tempo * 0.9) * self.tela_h * 0.014
        offset_face = (flutua_x, flutua_y)

        p = self.atual
        # Modulacoes em tempo real
        pisca_factor = (1 - 0.92 * self._piscando_intensidade)
        fala_factor = (1 + 0.30 * self._falando_offset)

        # Folha verde (top-left da logo)
        self._blit_quadrante(
            self.spr_folha, self.pos_folha, offset_face,
            scale_x=p.folha_scale, scale_y=p.folha_scale,
            dy=p.folha_dy, dx=p.folha_dx, rot=p.folha_rot,
        )
        # Olho esquerdo magenta (top-right da logo)
        self._blit_quadrante(
            self.spr_olho_esq, self.pos_olho_esq, offset_face,
            scale_x=p.olho_esq_sx, scale_y=p.olho_esq_sy * pisca_factor,
            dy=p.olho_esq_dy, rot=0,
        )
        # Olho direito amarelo (bottom-left da logo)
        self._blit_quadrante(
            self.spr_olho_dir, self.pos_olho_dir, offset_face,
            scale_x=p.olho_dir_sx, scale_y=p.olho_dir_sy * pisca_factor,
            dy=p.olho_dir_dy, rot=0,
        )
        # Boca azul (bottom-right da logo)
        self._blit_quadrante(
            self.spr_boca, self.pos_boca, offset_face,
            scale_x=p.boca_sx, scale_y=p.boca_sy * fala_factor,
            dy=p.boca_dy, rot=p.boca_rot,
        )
