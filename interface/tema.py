"""Paleta e tokens visuais do THEO."""

import os

# === Paleta da logo (pixel a pixel) ===
VERDE = (35, 173, 0)
MAGENTA = (232, 54, 198)
AMARELO = (255, 183, 8)
AZUL = (0, 160, 225)
AZUL_MARINHO = (15, 36, 56)

# === Neutros ===
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
FUNDO_OFFWHITE = (248, 250, 253)   # branco quente, mais suave que branco puro
CINZA_CLARO = (236, 240, 245)
CINZA = (190, 200, 215)
CINZA_TEXTO_SECUNDARIO = (110, 124, 145)

# === Sombras e elevacao ===
SOMBRA_BOTAO = (15, 36, 56, 50)    # azul-marinho 20% alpha
SOMBRA_SUTIL = (15, 36, 56, 25)    # azul-marinho 10% alpha

# === Cores semanticas ===
COR_FUNDO = FUNDO_OFFWHITE
COR_TEXTO = AZUL_MARINHO
COR_TEXTO_SECUNDARIO = CINZA_TEXTO_SECUNDARIO

# === Botoes ===
BOTAO_PADRAO = AZUL
BOTAO_SELECIONADO_TECLADO = AZUL_MARINHO
BOTAO_TEXTO = BRANCO

# === Rosto ===
COR_FOLHA = VERDE
COR_OLHO_ESQ = MAGENTA
COR_OLHO_DIR = AMARELO
COR_BOCA = AZUL

# === Cores por emocao ===
COR_FELIZ = AMARELO
COR_TRISTE = AZUL
COR_ANSIOSO = MAGENTA
COR_IRRITADO = (231, 76, 60)

# === Tipografia ===
_FONTE_DIR = os.path.dirname(os.path.abspath(__file__))
FONTE_CUSTOM_PATH = os.path.join(_FONTE_DIR, "JandaManateeSolid.ttf")
FONTE_FALLBACKS = ["Segoe UI Black", "Arial Black", "Verdana", "Arial"]

# === Espacamentos ===
RAIO_BOTAO = 0.45     # fracao do menor lado (mais arredondado, friendly)
OFFSET_SOMBRA = 6     # px
BORDA_DESTAQUE = 5    # px
