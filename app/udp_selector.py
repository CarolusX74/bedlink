#- ==========================================================
#- Bedlink - UDP Selector (v0.6.2)
#- ----------------------------------------------------------
#- Detecta selección de mundo por índice dentro del MOTD
#- (solo informativo, sin persistencia)
#- ==========================================================
import re

def detect_world_choice(motd_text: str, client_ip: str):
    """
    Detecta si el MOTD contiene un número [n] elegido por el jugador.
    (Actualmente solo retorna el número; no persiste nada)
    """
    match = re.search(r"\[(\d+)\]", motd_text)
    if match:
        return int(match.group(1))
    return None
