"""Parametri della fontanella d'angolo (tutte le misure in mm).

Sistema di riferimento (assemblato):
  origine  = spigolo interno delle due pareti, a livello del pavimento
  asse X   = lungo la PARETE A (lato da 25 cm)  -> la parete A e' il piano y = 0
  asse Y   = lungo la PARETE B (lato da 20 cm)  -> la parete B e' il piano x = 0
  asse Z   = verticale, z = 0 pavimento
"""
import math

# --- Pianta a tre lati -------------------------------------------------------
A = 250.0          # lato lungo la parete A (parte dall'angolo)
B = 200.0          # lato lungo la parete B (parte dall'angolo)
ARC_N = 2.0        # esponente super-ellisse del bordo frontale (2 = quarto d'ellisse)
ARC_PTS = 240      # risoluzione del bordo curvo

# --- Quote verticali (dal pavimento) ----------------------------------------
Z_TOP = 840.0      # bordo superiore vasca (piano a 84 cm)
Z_GRID_TOP = 836.0 # piano griglia (appoggio bottiglia)
GRID_T = 8.0       # spessore griglia
Z_VASCA_BOT = 770.0
Z_CORPO_BOT = 570.0
Z_BS_TOP = 1040.0  # sommita' schienale (giunto con la testa)
Z_OUTLET = 1150.0  # uscita beccuccio (faccia inferiore): 31 cm liberi sopra la griglia
Z_ARM = Z_OUTLET + 40.0      # asse del braccio orizzontale del beccuccio
Z_HEAD_TOP = Z_ARM + 28.0    # sommita' piatta della testa

# --- Schienale / colonna d'angolo -------------------------------------------
T_W = 20.0         # spessore delle ali dello schienale (aderenti alle pareti)
R_C = 65.0         # raggio esterno colonna d'angolo (quarto di cilindro)
R_CH = 58.0        # raggio del vano tecnico (cavedio) per il tubo PPR
BS_TAIL_H = 30.0   # altezza ali all'estremita' (sopra il bordo vasca)

# --- Tubo PPR ----------------------------------------------------------------
RISER = (24.0, 24.0)   # asse della salita verticale PPR DN20
SPOUT = (95.0, 95.0)   # asse del beccuccio (bottiglia centrata qui)
ARM_R = 23.0           # raggio esterno braccio
SPOUT_R = 23.0         # raggio esterno canna di uscita (= braccio: estremita' continua)
CH_W = 19.0            # semi-larghezza canale interno
SPOUT_RI = 19.5        # raggio interno canna di uscita

# --- Vasca -------------------------------------------------------------------
RIM_W = 14.0       # larghezza bordo frontale
NOSE_R = 6.0       # raggio bordo arrotondato
NOSE_SET = 12.0    # arretramento del corpo sotto il bordo (ombra)
LEDGE = 6.0        # battuta griglia
DRAIN_D = 28.0
FUNNEL_SLOPE = 0.22
Z_DRAIN = 790.0

# --- Corpo / vano tecnico ----------------------------------------------------
WALL = 5.0
FLOOR = 5.0
DOOR_A1 = 14.0     # gradi (angolo polare dall'asse X) apertura sportello
DOOR_A2 = 80.0
Z_DOOR_BOT = 580.0
LIP_H = 6.0

# --- Serbatoio (in coordinate u/v ruotate di TANK_PHI) ----------------------
TANK_PHI = 50.0
TANK_U0 = 74.0
TANK_L = 104.0
TANK_W = 124.0
TANK_VOFF = -12.0
TANK_Z0 = 578.0
TANK_H = 113.0

# --- Box elettronica (stagno) -----------------------------------------------
BOX_X = (110.0, 210.0)
BOX_Y = (WALL, 53.0)
BOX_Z = (710.0, 762.0)

# --- Viteria ----------------------------------------------------------------
INSERT_M4 = 5.6    # foro per inserto filettato a caldo M4
INSERT_M3 = 4.0
MAG_D = 6.3        # magnete 6x3
MAG_H = 3.2

MAX_PRINT = 250.0

def ellipse_r(theta_deg, a=A, b=B):
    t = math.radians(theta_deg)
    return 1.0 / math.sqrt((math.cos(t) / a) ** 2 + (math.sin(t) / b) ** 2)
