"""Parametri della fontanella d'angolo (tutte le misure in mm).

Sistema di riferimento (assemblato):
  origine  = spigolo interno delle due pareti, a livello del pavimento
  asse X   = lungo la PARETE A (lato corto, 20 cm)              -> parete A = piano y = 0
  asse Y   = lungo la PARETE B (lato lungo, 25 cm, la FONTANA)  -> parete B = piano x = 0
  asse Z   = verticale, z = 0 pavimento
Guardando la parete B (quella da 25 cm) l'angolo e' a sinistra: il tubo esce dal muro
a PIPE_Y = 95 mm dall'angolo.
"""
import math

# --- Pianta a tre lati -------------------------------------------------------
A = 200.0          # lato lungo la parete A (corta), parte dall'angolo
B = 250.0          # lato lungo la parete B (lunga, dove si fissa la fontana), parte dall'angolo
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

# --- Schienale sulla parete lunga (B) + alzatina sulla parete corta (A) ------
T_W = 20.0         # spessore schienale sulla parete B
T_S = 12.0         # spessore alzatina paraspruzzi sulla parete A
UPSTAND_H = 40.0   # altezza alzatina sopra il bordo vasca
BS_TAIL_H = 30.0   # altezza schienale all'estremita' lontana dall'angolo

# --- Tubo PPR: esce gia' dal muro (parete B) nella zona del lavabo -----------
PIPE_Y = 95.0           # centro del tubo dall'angolo, lungo la parete B
Z_PIPE_IN = 900.0       # quota di uscita del tubo dal muro (DA VERIFICARE in opera; 855..1130)
RISER = (22.0, PIPE_Y)  # asse della salita verticale nella colonnina dello schienale
SPOUT = (100.0, PIPE_Y) # asse del beccuccio (bottiglia centrata qui)
COL_HW = 26.0           # semi-larghezza colonnina (esterno)
CH_HW = 19.5            # semi-larghezza cavedio interno (aperto verso il muro)
ARM_R = 23.0            # raggio esterno braccio
SPOUT_R = 23.0          # raggio esterno canna di uscita (= braccio: estremita' continua)
CH_W = 19.0             # semi-larghezza canale interno
SPOUT_RI = 19.5         # raggio interno canna di uscita

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
TANK_PHI = 30.0
TANK_U0 = 76.0
TANK_L = 102.0
TANK_W = 156.0
TANK_VOFF = 40.0
TANK_Z0 = 578.0
TANK_H = 113.0

# --- Box elettronica (stagno), appeso alla parete B dentro il vano ----------
BOX_ALONG = (115.0, 205.0)   # tratto di parete B occupato (y)
BOX_DEPTH = (WALL, 53.0)     # sporgenza dalla parete (x)
BOX_Z = (710.0, 762.0)

# --- Viteria ----------------------------------------------------------------
INSERT_M4 = 5.6    # foro per inserto filettato a caldo M4
INSERT_M3 = 4.0
MAG_D = 6.3        # magnete 6x3
MAG_H = 3.2

MAX_PRINT = 250.0
