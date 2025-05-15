import math

PRETO = (0, 0, 0)
ROSTO_BASE = ["O -- O", "-- -- --", "O o O", "-- o --"]

def desenhar_rosto(screen, fonte, rosto, tempo):
    x_off = math.cos(tempo*2) * 10
    y_off = math.sin(tempo*2) * 20
    surf = fonte.render(rosto, True, PRETO)
    screen.blit(surf, surf.get_rect(center=((screen.get_width()//2)+x_off, (screen.get_height()//2)+y_off)))

def atualizar_estado_rosto(tempo, ultimo_tempo_troca, piscando, falando, velocidade_fala=6):
    if piscando:
        estado = 1
    else:
        estado = 0

    if not piscando and (tempo - ultimo_tempo_troca >= 2.4):
        estado = 1
        piscando = True
        ultimo_tempo_troca = tempo
    elif piscando and (tempo - ultimo_tempo_troca >= 0.2):
        estado = 0
        piscando = False 
        ultimo_tempo_troca = tempo
    
    if falando:
        falando = (int(tempo * velocidade_fala) % 2) == 0

    if falando:
        estado += 2
    
    return ROSTO_BASE[estado], ultimo_tempo_troca, piscando
