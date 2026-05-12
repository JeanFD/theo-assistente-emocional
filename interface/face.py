"""Rosto do THEO em pe' (folha no topo, olhos no meio, boca embaixo).

Os sprites vem da logo (refs/theo_pequeno1.png), com fundo preto convertido
para alpha gradiente (preserva bordas suaves) e cortados na bounding box
para evitar deslocamentos.

Animacoes combinam:
  - Lerp suave entre expressoes (parametros de scale/rotacao/offset)
  - Drift contInuo independente por blob (cada um oscila em frequencia
    propria, dando vida ao rosto sem so 'crescer e encolher')
  - Sway da folha como uma planta ao vento
  - Olhos olham levemente em redor durante o idle
  - Boca tem respiracao sutil e pulsa quando falando
"""

import os
import math
import pygame
from dataclasses import dataclass, fields


LOGO_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "refs", "theo_pequeno1.png",
)

# Rotacao base (graus, CCW) aplicada permanentemente a cada blob.
# No logo original os blobs estao em 2x2 apontando para o centro. Aqui
# rotacionamos para a orientacao correta de um rosto em pe'.
BASE_ROT_FOLHA = -30      # folha aponta para cima
BASE_ROT_OLHO_ESQ = 45    # eixo do magenta horizontal
BASE_ROT_OLHO_DIR = -45   # eixo do amarelo horizontal (lado oposto)
BASE_ROT_BOCA = -45       # boca como sorriso horizontal
# Espelha olho direito para virar mirror do esquerdo
FLIP_OLHO_DIR = True


@dataclass
class ParametrosRosto:
    """Modificadores por blob (escala/offset/rotacao). 1.0/0.0 = neutro."""
    folha_scale: float = 1.0
    folha_dy: float = 0.0
    folha_rot: float = 0.0
    olho_esq_sx: float = 1.0
    olho_esq_sy: float = 1.0
    olho_esq_dy: float = 0.0
    olho_dir_sx: float = 1.0
    olho_dir_sy: float = 1.0
    olho_dir_dy: float = 0.0
    boca_sx: float = 1.0
    boca_sy: float = 1.0
    boca_dy: float = 0.0
    boca_rot: float = 0.0


EXPRESSOES = {
    "feliz": ParametrosRosto(
        folha_rot=-5,
        boca_sx=1.05, boca_sy=1.05,
    ),
    "neutro": ParametrosRosto(
        boca_sx=0.78, boca_sy=0.72,
    ),
    "triste": ParametrosRosto(
        olho_esq_sy=0.85, olho_dir_sy=0.85,
        olho_esq_dy=0.02, olho_dir_dy=0.02,
        boca_sx=0.85, boca_sy=0.6, boca_rot=180,
        folha_rot=18,
    ),
    "ansioso": ParametrosRosto(
        olho_esq_sx=1.15, olho_esq_sy=1.18,
        olho_dir_sx=1.15, olho_dir_sy=1.18,
        boca_sx=0.55, boca_sy=0.6,
        folha_rot=8,
    ),
    "irritado": ParametrosRosto(
        olho_esq_sy=0.55, olho_dir_sy=0.55,
        boca_sx=0.8, boca_sy=0.45, boca_rot=180,
        folha_rot=-2,
    ),
    "surpreso": ParametrosRosto(
        olho_esq_sx=1.32, olho_esq_sy=1.35,
        olho_dir_sx=1.32, olho_dir_sy=1.35,
        boca_sx=0.55, boca_sy=1.0,
        folha_rot=-8,
    ),
    "dormindo": ParametrosRosto(
        olho_esq_sy=0.04, olho_dir_sy=0.04,
        olho_esq_dy=0.02, olho_dir_dy=0.02,
        boca_sx=0.42, boca_sy=0.42,
        folha_rot=-25,
    ),
}


def _lerp(a, b, t):
    return a + (b - a) * t


def _converter_fundo_para_alpha(img):
    """Converte o fundo preto em transparencia real (com gradiente nas bordas).

    Para cada pixel, alpha = max(R,G,B). Pixels pretos viram totalmente
    transparentes, pixels coloridos opacos, e bordas anti-aliased ganham
    alpha intermediario — eliminando o halo/serrilhado.
    """
    img = img.convert_alpha()
    w, h = img.get_size()
    raw = pygame.image.tostring(img, "RGBA")
    ba = bytearray(raw)
    n = len(ba)
    i = 0
    while i < n:
        r = ba[i]
        g = ba[i + 1]
        b = ba[i + 2]
        brilho = r if r > g else g
        if b > brilho:
            brilho = b
        if brilho < 16:
            ba[i + 3] = 0
        elif brilho > 96:
            ba[i + 3] = 255
        else:
            ba[i + 3] = int((brilho - 16) * 255 / 80)
        i += 4
    return pygame.image.fromstring(bytes(ba), (w, h), "RGBA")


def _crop_bbox(surface):
    """Corta surface na bounding box do conteudo nao transparente."""
    mask = pygame.mask.from_surface(surface)
    if mask.count() == 0:
        return surface
    rects = mask.get_bounding_rects()
    if not rects:
        return surface
    bbox = max(rects, key=lambda r: r.w * r.h)
    bbox = bbox.inflate(8, 8).clip(surface.get_rect())
    if bbox.w <= 0 or bbox.h <= 0:
        return surface
    return surface.subsurface(bbox).copy()


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
        img = pygame.image.load(LOGO_PATH)
        img = _converter_fundo_para_alpha(img)
        w, h = img.get_size()
        hw, hh = w // 2, h // 2
        # Quadrantes na ordem da logo
        folha_q = img.subsurface((0, 0, hw, hh)).copy()
        magenta_q = img.subsurface((hw, 0, hw, hh)).copy()
        amarelo_q = img.subsurface((0, hh, hw, hh)).copy()
        azul_q = img.subsurface((hw, hh, hw, hh)).copy()
        # Crop bbox + rotacao base (aplicada uma vez, no carregamento)
        folha_c = _crop_bbox(folha_q)
        magenta_c = _crop_bbox(magenta_q)
        amarelo_c = _crop_bbox(amarelo_q)
        azul_c = _crop_bbox(azul_q)
        if FLIP_OLHO_DIR:
            amarelo_c = pygame.transform.flip(amarelo_c, True, False)
        self.spr_folha = _crop_bbox(pygame.transform.rotate(folha_c, BASE_ROT_FOLHA))
        self.spr_olho_esq = _crop_bbox(pygame.transform.rotate(magenta_c, BASE_ROT_OLHO_ESQ))
        self.spr_olho_dir = _crop_bbox(pygame.transform.rotate(amarelo_c, BASE_ROT_OLHO_DIR))
        self.spr_boca = _crop_bbox(pygame.transform.rotate(azul_c, BASE_ROT_BOCA))

    def _recalcular_layout(self):
        w, h = self.screen.get_size()
        self.tela_w = w
        self.tela_h = h
        # Rosto em pe': tamanhos relativos a altura
        self.h_folha = int(h * 0.16)
        self.h_olho = int(h * 0.18)
        self.h_boca = int(h * 0.16)
        # Largura proporcional preservada de cada sprite
        def _largura(spr, altura_alvo):
            ow, oh = spr.get_size()
            return int(altura_alvo * ow / oh)
        self.w_folha = _largura(self.spr_folha, self.h_folha)
        self.w_olho_esq = _largura(self.spr_olho_esq, self.h_olho)
        self.w_olho_dir = _largura(self.spr_olho_dir, self.h_olho)
        self.w_boca = _largura(self.spr_boca, self.h_boca)
        # Posicao base (centro de cada elemento) — componentes proximos
        cx = w // 2
        cy = h // 2
        espaco_olhos = int(w * 0.11)  # distancia entre olhos (mais junto)
        self.pos_folha = (cx, cy - int(h * 0.22))    # folha menos alta
        self.pos_olho_esq = (cx - espaco_olhos, cy - int(h * 0.01))
        self.pos_olho_dir = (cx + espaco_olhos, cy - int(h * 0.01))
        self.pos_boca = (cx, cy + int(h * 0.18))     # boca mais perto

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
            if tempo >= self.ultimo_piscar + 3.4:
                self.piscando_ate = tempo + 0.14
                self.ultimo_piscar = tempo
        self._piscando_intensidade = 0.0
        if tempo < self.piscando_ate:
            t_local = (self.piscando_ate - tempo) / 0.14
            self._piscando_intensidade = math.sin(t_local * math.pi)

        self._falando_offset = 0.0
        if falando and not dormindo:
            self._falando_offset = (math.sin(tempo * 11) + 1) / 2

    def _blit(self, sprite, w_base, h_base, pos_x, pos_y, sx, sy, rot):
        target_w = max(2, int(w_base * sx))
        target_h = max(2, int(h_base * sy))
        s = pygame.transform.smoothscale(sprite, (target_w, target_h))
        if rot:
            s = pygame.transform.rotate(s, rot)
        rect = s.get_rect(center=(int(pos_x), int(pos_y)))
        self.screen.blit(s, rect.topleft)

    def desenhar(self, tempo):
        # Float global do rosto inteiro
        flutua_x = math.cos(tempo * 1.1) * self.tela_w * 0.008
        flutua_y = math.sin(tempo * 0.9) * self.tela_h * 0.010

        p = self.atual
        dormindo = self.expressao_nome == "dormindo"

        # === ANIMACOES INDEPENDENTES POR BLOB (vida sutil, nao so scale) ===
        # Cada um tem frequencia/fase distinta — sensacao organica, vivo
        amp_drift = self.tela_h * 0.006  # amplitude pequena, sutil
        if dormindo:
            amp_drift *= 0.3  # quase parado dormindo

        folha_dx = math.sin(tempo * 1.6 + 0.0) * amp_drift * 0.6
        folha_dy_drift = math.cos(tempo * 1.2 + 0.0) * amp_drift * 0.4
        folha_rot_sway = math.sin(tempo * 1.4) * 4.0  # vai e volta como folha ao vento

        olho_esq_dx = math.sin(tempo * 0.9 + 1.2) * amp_drift * 0.5
        olho_esq_dy_drift = math.cos(tempo * 1.1 + 1.2) * amp_drift * 0.5
        olho_dir_dx = math.sin(tempo * 0.9 + 2.4) * amp_drift * 0.5
        olho_dir_dy_drift = math.cos(tempo * 1.1 + 2.4) * amp_drift * 0.5

        boca_dx_drift = math.sin(tempo * 0.7 + 3.6) * amp_drift * 0.4
        boca_dy_drift = math.cos(tempo * 0.7 + 3.6) * amp_drift * 0.6
        # Respiracao sutil: boca pulsa devagar mesmo parada
        respiracao = 1.0 + math.sin(tempo * 1.8) * 0.025
        # Olhos "respiram" com pequenos squashes (efeito vivo, nao so blink)
        olho_breath = 1.0 + math.sin(tempo * 1.8 + 1.0) * 0.02

        # Olhares ocasionais (cada ~7s, olho se desloca lateralmente por 1s)
        olhar_x_periodo = (tempo % 7.0) - 6.0  # ativo por 1s no fim do ciclo
        if olhar_x_periodo > 0 and not dormindo:
            olhar_offset = math.sin(olhar_x_periodo * math.pi) * self.tela_w * 0.012
            olho_esq_dx += olhar_offset
            olho_dir_dx += olhar_offset

        # === PISCAR e FALAR ===
        pisca_factor = 1 - 0.94 * self._piscando_intensidade
        fala_factor = 1 + 0.35 * self._falando_offset
        # Falando: boca tambem desloca um pouquinho pra cima na pulsacao
        fala_dy = -self._falando_offset * self.tela_h * 0.004

        # === DESENHO ===
        # Folha
        self._blit(
            self.spr_folha, self.w_folha, self.h_folha,
            self.pos_folha[0] + flutua_x + folha_dx,
            self.pos_folha[1] + flutua_y + folha_dy_drift,
            p.folha_scale, p.folha_scale,
            p.folha_rot + folha_rot_sway,
        )
        # Olho esquerdo (magenta)
        self._blit(
            self.spr_olho_esq, self.w_olho_esq, self.h_olho,
            self.pos_olho_esq[0] + flutua_x + olho_esq_dx,
            self.pos_olho_esq[1] + flutua_y + olho_esq_dy_drift + p.olho_esq_dy * self.tela_h,
            p.olho_esq_sx, p.olho_esq_sy * pisca_factor * olho_breath,
            0,
        )
        # Olho direito (amarelo)
        self._blit(
            self.spr_olho_dir, self.w_olho_dir, self.h_olho,
            self.pos_olho_dir[0] + flutua_x + olho_dir_dx,
            self.pos_olho_dir[1] + flutua_y + olho_dir_dy_drift + p.olho_dir_dy * self.tela_h,
            p.olho_dir_sx, p.olho_dir_sy * pisca_factor * olho_breath,
            0,
        )
        # Boca (azul)
        self._blit(
            self.spr_boca, self.w_boca, self.h_boca,
            self.pos_boca[0] + flutua_x + boca_dx_drift,
            self.pos_boca[1] + flutua_y + boca_dy_drift + p.boca_dy * self.tela_h + fala_dy,
            p.boca_sx * respiracao, p.boca_sy * fala_factor * respiracao,
            p.boca_rot,
        )
