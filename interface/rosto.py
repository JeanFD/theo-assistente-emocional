import math

PRETO = (0, 0, 0)
ROSTO_BASE = ["O - O", "^ - ^"]

def desenhar_rosto(screen, fonte, estado, tempo):
    x_off = math.cos(tempo*2) * 10
    y_off = math.sin(tempo*2) * 20
    surf = fonte.render(ROSTO_BASE[estado], True, PRETO)
    screen.blit(surf, surf.get_rect(center=((screen.get_width()//2)+x_off, (screen.get_height()//2)+y_off)))

def atualizar_estado_rosto(tempo, ultimo_tempo_troca, piscando):
    if not piscando and (tempo - ultimo_tempo_troca >= 2.4):
        return 1, tempo, True
    elif piscando and (tempo - ultimo_tempo_troca >= 0.3):
        return 0, tempo, False
    return None
