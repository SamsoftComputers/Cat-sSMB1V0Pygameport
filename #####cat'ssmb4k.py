import pygame
import array
import random
import math
import sys

# --- Configuration & Constants ---
SCREEN_W, SCREEN_H = 256, 240
WINDOW_W, WINDOW_H = 768, 720
FPS = 60
TILE_SIZE = 16

# Colors
BLACK = (0, 0, 0)
WHITE = (252, 252, 252)
SKY = (92, 148, 252)
UNDERGROUND_BG = (0, 0, 0)
CASTLE_BG = (0, 0, 0)
GREEN = (0, 184, 0)
BROWN = (136, 68, 0)
RED = (216, 40, 0)
ORANGE = (228, 92, 16)
YELLOW = (216, 216, 0)
DKBROWN = (100, 50, 0)
SKIN = (252, 216, 168)  # NES SMB1 Mario skin (1:1 ROM accurate)
GRAY = (152, 152, 152)
LAVA_RED = (216, 40, 0)
MAP_GREEN = (34, 177, 76)
MAP_PATH = (220, 220, 220)
LOCKED_GRAY = (80, 80, 80)

# --- Physics Constants ---
GRAVITY = 0.35          
JUMP_POWER = -5.5       
JUMP_POWER_DOUBLE = -6.5
JUMP_POWER_TRIPLE = -7.8
MAX_FALL = 10.0
PLAYER_WALK_SPEED = 3.0
PLAYER_RUN_SPEED = 5.5
ACCELERATION = 0.25     
DECELERATION = 0.15     
FRICTION = 0.15         
AIR_CONTROL = 0.15      
BOUNCE_SPEED = -5.0
WALL_SLIDE_SPEED = 2.0
WALL_JUMP_KICK_X = 5.0
WALL_JUMP_KICK_Y = -6.5

# --- Sound Synthesis ---
pygame.mixer.pre_init(frequency=22050, size=-16, channels=1, buffer=512)
pygame.init()

def make_square_wave(freq, dur_sec, vol=0.2):
    sr = 22050
    n = int(sr * dur_sec)
    buf = array.array('h', [0] * n)
    amplitude = int(32767 * vol)
    if freq > 0:
        period = sr / freq
        for i in range(n):
            buf[i] = amplitude if (i % int(period)) < (period / 2) else -amplitude
    return pygame.mixer.Sound(buffer=buf)

def make_noise(dur_sec, vol=0.2):
    sr = 22050
    n = int(sr * dur_sec)
    amplitude = int(32767 * vol)
    buf = array.array('h', [random.randint(-amplitude, amplitude) for _ in range(n)])
    return pygame.mixer.Sound(buffer=buf)

def make_triangle_wave(freq, dur_sec, vol=0.2):
    sr = 22050
    n = int(sr * dur_sec)
    buf = array.array('h', [0] * n)
    amplitude = int(32767 * vol)
    if freq > 0:
        period = sr / freq
        for i in range(n):
            phase = (i % period) / period
            if phase < 0.25:
                buf[i] = int(amplitude * (phase * 4))
            elif phase < 0.75:
                buf[i] = int(amplitude * (2 - (phase * 4)))
            else:
                buf[i] = int(amplitude * ((phase * 4) - 4))
    return pygame.mixer.Sound(buffer=buf)

# Sound Assets
sounds = {}
def init_sounds():
    sounds['jump'] = make_square_wave(440, 0.1, 0.1)
    sounds['jump2'] = make_square_wave(550, 0.1, 0.1) 
    sounds['jump3'] = make_square_wave(660, 0.15, 0.1) 
    sounds['coin'] = make_triangle_wave(988, 0.1, 0.15)
    sounds['stomp'] = make_square_wave(150, 0.05, 0.15)
    sounds['die'] = make_noise(0.5, 0.2)
    sounds['break'] = make_noise(0.1, 0.1)
    sounds['powerup'] = make_triangle_wave(523, 0.3, 0.1)
    sounds['powerup_appear'] = make_triangle_wave(400, 0.15, 0.1)
    sounds['pause'] = make_square_wave(220, 0.2, 0.05)
    sounds['stage_clear'] = make_triangle_wave(660, 2.5, 0.1)
    sounds['kick'] = make_square_wave(200, 0.05, 0.15)
    sounds['thud'] = make_noise(0.1, 0.3) 
    sounds['map_move'] = make_square_wave(150, 0.05, 0.1)

# --- Sprite Data ---
# NES SMB1 accurate palettes
MARIO_PALETTE = [(0,0,0), SKIN, RED, BROWN]
ITEM_PALETTE = [(0,0,0,0), (216,40,0), (252,152,56), WHITE]
GOOMBA_PALETTE = [(0,0,0,0), (234,158,34), (172,80,0), BLACK]
GREEN_KOOPA_PALETTE = [(0,0,0,0), WHITE, (0,168,0), (252,152,56)]
RED_KOOPA_PALETTE = [(0,0,0,0), WHITE, (216,40,0), (252,152,56)]
SPINY_PALETTE = [(0,0,0,0), (216,40,0), WHITE, (0,88,248)]
PIRANHA_PALETTE = [(0,0,0,0), (0,168,0), (216,40,0), WHITE]
BUZZY_PALETTE = [(0,0,0,0), (0,88,248), WHITE, BLACK]
HAMMER_BRO_PALETTE = [(0,0,0,0), (0,168,0), (252,152,56), WHITE]
LAKITU_PALETTE = [(0,0,0,0), (0,168,0), (252,152,56), WHITE]
CHEEP_PALETTE = [(0,0,0,0), (216,40,0), WHITE, (252,152,56)]
BLOOPER_PALETTE = [(0,0,0,0), WHITE, (252,188,176), BLACK]
STAR_PALETTE = [(0,0,0,0), YELLOW, ORANGE, BLACK]
FLAG_PALETTE = [(0,0,0,0), GREEN, WHITE, BLACK]

# Pixel-perfect NES SMB1 Small Mario sprites (16x16) - 1:1 ROM accurate
MARIO_IDLE = [
    [0,0,0,0,0,0,2,2,2,2,2,0,0,0,0,0],
    [0,0,0,0,0,2,2,2,2,2,2,2,2,2,0,0],
    [0,0,0,0,0,3,3,3,1,1,1,3,0,0,0,0],
    [0,0,0,0,3,1,3,1,1,1,3,1,1,1,0,0],
    [0,0,0,0,3,1,3,3,1,1,1,3,1,1,1,0],
    [0,0,0,0,3,3,1,1,1,1,3,3,3,3,0,0],
    [0,0,0,0,0,0,1,1,1,1,1,1,0,0,0,0],
    [0,0,0,0,0,2,2,3,2,2,0,0,0,0,0,0],
    [0,0,0,0,2,2,2,3,2,2,3,2,2,0,0,0],
    [0,0,0,0,2,2,2,3,3,3,3,2,2,0,0,0],
    [0,0,0,0,2,2,3,1,3,3,1,3,2,2,0,0],
    [0,0,0,0,0,3,3,3,3,3,3,3,3,0,0,0],
    [0,0,0,0,0,3,3,0,0,0,0,3,3,0,0,0],
    [0,0,0,0,3,3,3,0,0,0,0,3,3,3,0,0],
    [0,0,0,3,3,3,0,0,0,0,0,0,3,3,3,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
]
MARIO_WALK1 = [
    [0,0,0,0,0,0,2,2,2,2,2,0,0,0,0,0],
    [0,0,0,0,0,2,2,2,2,2,2,2,2,2,0,0],
    [0,0,0,0,0,3,3,3,1,1,1,3,0,0,0,0],
    [0,0,0,0,3,1,3,1,1,1,3,1,1,1,0,0],
    [0,0,0,0,3,1,3,3,1,1,1,3,1,1,1,0],
    [0,0,0,0,3,3,1,1,1,1,3,3,3,3,0,0],
    [0,0,0,0,0,0,1,1,1,1,1,1,0,0,0,0],
    [0,0,0,0,0,0,2,2,2,3,2,2,2,0,0,0],
    [0,0,0,0,0,2,2,2,2,3,2,2,2,2,0,0],
    [0,0,0,0,2,2,2,2,3,3,3,2,2,2,0,0],
    [0,0,0,0,3,2,2,3,3,1,3,3,0,0,0,0],
    [0,0,0,0,3,3,3,3,1,1,3,3,3,0,0,0],
    [0,0,0,0,3,3,3,1,1,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,3,3,0,0,3,3,3,0,0,0],
    [0,0,0,0,0,0,0,0,0,3,3,3,3,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,3,3,0,0,0,0]
]
MARIO_WALK2 = [
    [0,0,0,0,0,0,2,2,2,2,2,0,0,0,0,0],
    [0,0,0,0,0,2,2,2,2,2,2,2,2,2,0,0],
    [0,0,0,0,0,3,3,3,1,1,1,3,0,0,0,0],
    [0,0,0,0,3,1,3,1,1,1,3,1,1,1,0,0],
    [0,0,0,0,3,1,3,3,1,1,1,3,1,1,1,0],
    [0,0,0,0,3,3,1,1,1,1,3,3,3,3,0,0],
    [0,0,0,0,0,0,1,1,1,1,1,1,0,0,0,0],
    [0,0,0,0,0,2,2,3,2,2,3,2,0,0,0,0],
    [0,0,0,0,2,2,2,3,2,2,3,2,2,2,0,0],
    [0,0,0,0,2,2,2,3,3,3,3,2,2,2,0,0],
    [0,0,0,0,2,2,3,1,3,3,1,3,2,2,0,0],
    [0,0,0,0,0,3,3,3,3,3,3,3,3,0,0,0],
    [0,0,0,0,0,0,3,3,0,0,3,3,0,0,0,0],
    [0,0,0,0,0,3,3,3,0,0,3,3,3,0,0,0],
    [0,0,0,0,0,3,3,0,0,0,0,3,3,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
]
MARIO_WALK3 = [
    [0,0,0,0,0,0,2,2,2,2,2,0,0,0,0,0],
    [0,0,0,0,0,2,2,2,2,2,2,2,2,2,0,0],
    [0,0,0,0,0,3,3,3,1,1,1,3,0,0,0,0],
    [0,0,0,0,3,1,3,1,1,1,3,1,1,1,0,0],
    [0,0,0,0,3,1,3,3,1,1,1,3,1,1,1,0],
    [0,0,0,0,3,3,1,1,1,1,3,3,3,3,0,0],
    [0,0,0,0,0,0,1,1,1,1,1,1,0,0,0,0],
    [0,0,0,0,2,2,2,3,2,2,2,0,0,0,0,0],
    [0,0,0,2,2,2,2,3,2,2,2,2,0,0,0,0],
    [0,0,0,2,2,2,3,3,3,2,2,2,0,0,0,0],
    [0,0,0,0,0,3,3,1,3,3,2,2,3,0,0,0],
    [0,0,0,0,3,3,3,1,1,3,3,3,3,0,0,0],
    [0,0,0,0,0,0,0,0,1,1,3,3,3,0,0,0],
    [0,0,0,0,3,3,3,0,0,3,3,0,0,0,0,0],
    [0,0,0,0,3,3,3,3,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,3,3,0,0,0,0,0,0,0,0,0]
]
MARIO_JUMP = [
    [0,0,0,0,0,0,0,2,2,2,2,2,0,0,0,0],
    [0,0,0,0,0,0,2,2,2,2,2,2,2,2,0,0],
    [0,0,0,0,0,0,3,3,3,1,1,1,3,0,0,0],
    [0,0,0,0,0,3,1,3,1,1,1,3,1,1,1,0],
    [0,0,0,0,0,3,1,3,3,1,1,1,3,1,1,1],
    [0,0,0,0,0,3,3,1,1,1,1,3,3,3,3,0],
    [0,0,0,0,0,0,0,1,1,1,1,1,1,0,0,0],
    [0,0,0,2,2,0,2,2,3,2,2,2,0,0,0,0],
    [0,0,2,2,2,2,2,2,3,2,2,3,2,2,2,0],
    [0,0,2,2,2,2,2,3,3,3,3,3,2,2,2,0],
    [0,0,0,0,2,2,3,1,3,3,3,1,3,0,0,0],
    [0,0,0,0,0,3,3,3,3,3,3,3,3,3,0,0],
    [0,0,0,0,3,3,3,3,0,0,0,3,3,3,0,0],
    [0,0,0,3,3,3,0,0,0,0,0,0,3,3,0,0],
    [0,0,3,3,3,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
]
# 1:1 NES SMB1 Goomba (16x16) - Palette: 0=trans, 1=tan, 2=brown, 3=black
GOOMBA = [
    [0,0,0,0,0,0,2,2,2,2,0,0,0,0,0,0],
    [0,0,0,0,0,2,2,2,2,2,2,0,0,0,0,0],
    [0,0,0,0,2,2,2,2,2,2,2,2,0,0,0,0],
    [0,0,0,2,2,2,2,2,2,2,2,2,2,0,0,0],
    [0,0,2,2,2,2,2,2,2,2,2,2,2,2,0,0],
    [0,0,2,3,3,2,2,2,2,2,2,3,3,2,0,0],
    [0,2,2,1,3,2,2,2,2,2,2,3,1,2,2,0],
    [0,2,2,1,3,2,2,2,2,2,2,3,1,2,2,0],
    [0,2,2,2,2,2,1,1,1,1,2,2,2,2,2,0],
    [0,0,2,2,2,1,1,1,1,1,1,2,2,2,0,0],
    [0,0,0,2,1,1,1,1,1,1,1,1,2,0,0,0],
    [0,0,0,0,1,1,2,2,2,2,1,1,0,0,0,0],
    [0,0,0,2,2,2,2,0,0,2,2,2,2,0,0,0],
    [0,0,2,2,2,2,2,0,0,2,2,2,2,2,0,0],
    [0,2,2,2,2,2,0,0,0,0,2,2,2,2,2,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
]

# 1:1 NES SMB1 Green Koopa Troopa (16x24) - walking frame
# Palette: 0=trans, 1=white, 2=green, 3=orange/tan
KOOPA = [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,2,2,2,0,0,0,0,0,0],
    [0,0,0,0,0,0,2,2,2,2,2,0,0,0,0,0],
    [0,0,0,0,0,2,2,2,2,2,2,2,0,0,0,0],
    [0,0,0,0,0,2,1,1,2,2,2,2,0,0,0,0],
    [0,0,0,0,0,2,1,1,1,2,2,2,0,0,0,0],
    [0,0,0,0,0,2,2,1,2,2,2,2,0,0,0,0],
    [0,0,0,0,0,0,2,2,2,2,2,0,0,0,0,0],
    [0,0,0,0,0,2,2,2,2,2,2,2,0,0,0,0],
    [0,0,0,0,2,2,2,2,2,2,2,2,2,0,0,0],
    [0,0,0,2,2,1,2,2,2,2,1,2,2,2,0,0],
    [0,0,0,2,2,1,1,2,2,1,1,2,2,2,0,0],
    [0,0,3,3,2,2,2,2,2,2,2,2,3,3,0,0],
    [0,0,3,3,3,2,2,2,2,2,2,3,3,3,0,0],
    [0,0,0,3,3,3,0,0,0,0,3,3,3,0,0,0],
    [0,0,0,0,3,3,0,0,0,0,3,3,0,0,0,0]
]

# Red Koopa Troopa (same shape, use RED_KOOPA_PALETTE)
RED_KOOPA = [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,2,2,2,0,0,0,0,0,0],
    [0,0,0,0,0,0,2,2,2,2,2,0,0,0,0,0],
    [0,0,0,0,0,2,2,2,2,2,2,2,0,0,0,0],
    [0,0,0,0,0,2,1,1,2,2,2,2,0,0,0,0],
    [0,0,0,0,0,2,1,1,1,2,2,2,0,0,0,0],
    [0,0,0,0,0,2,2,1,2,2,2,2,0,0,0,0],
    [0,0,0,0,0,0,2,2,2,2,2,0,0,0,0,0],
    [0,0,0,0,0,2,2,2,2,2,2,2,0,0,0,0],
    [0,0,0,0,2,2,2,2,2,2,2,2,2,0,0,0],
    [0,0,0,2,2,1,2,2,2,2,1,2,2,2,0,0],
    [0,0,0,2,2,1,1,2,2,1,1,2,2,2,0,0],
    [0,0,3,3,2,2,2,2,2,2,2,2,3,3,0,0],
    [0,0,3,3,3,2,2,2,2,2,2,3,3,3,0,0],
    [0,0,0,3,3,3,0,0,0,0,3,3,3,0,0,0],
    [0,0,0,0,3,3,0,0,0,0,3,3,0,0,0,0]
]

# Koopa Shell (green) - 16x16
KOOPA_SHELL = [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,2,2,2,2,0,0,0,0,0,0],
    [0,0,0,0,0,2,2,2,2,2,2,0,0,0,0,0],
    [0,0,0,0,2,2,1,2,2,1,2,2,0,0,0,0],
    [0,0,0,2,2,2,1,1,1,1,2,2,2,0,0,0],
    [0,0,0,2,2,2,2,2,2,2,2,2,2,0,0,0],
    [0,0,0,2,2,2,2,2,2,2,2,2,2,0,0,0],
    [0,0,0,2,2,1,2,2,2,2,1,2,2,0,0,0],
    [0,0,0,0,2,2,2,2,2,2,2,2,0,0,0,0],
    [0,0,0,0,0,2,2,2,2,2,2,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
]

# Spiny (16x16) - Palette: 0=trans, 1=red, 2=white, 3=blue
SPINY = [
    [0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0],
    [0,0,0,1,1,1,0,0,0,0,1,1,1,0,0,0],
    [0,0,1,1,1,1,1,0,0,1,1,1,1,1,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,1,1,2,2,1,1,1,1,2,2,1,1,0,0],
    [0,0,1,1,2,3,1,1,1,1,3,2,1,1,0,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,2,2,0,0,0,0,2,2,0,0,0,0],
    [0,0,0,2,2,2,2,0,0,2,2,2,2,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
]

# Piranha Plant (16x24) - Palette: 0=trans, 1=green, 2=red, 3=white
PIRANHA = [
    [0,0,0,0,0,0,2,2,2,2,0,0,0,0,0,0],
    [0,0,0,0,0,2,2,2,2,2,2,0,0,0,0,0],
    [0,0,0,0,2,2,3,2,2,3,2,2,0,0,0,0],
    [0,0,0,2,2,2,3,2,2,3,2,2,2,0,0,0],
    [0,0,2,2,2,2,2,2,2,2,2,2,2,2,0,0],
    [0,0,2,2,2,2,2,2,2,2,2,2,2,2,0,0],
    [0,0,0,2,2,2,2,2,2,2,2,2,2,0,0,0],
    [0,0,0,0,2,2,2,2,2,2,2,2,0,0,0,0],
    [0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0]
]

# Buzzy Beetle (16x16) - Palette: 0=trans, 1=blue, 2=white, 3=black
BUZZY = [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0],
    [0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0],
    [0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,1,1,2,2,1,1,1,1,2,2,1,1,0,0],
    [0,0,1,1,2,3,1,1,1,1,3,2,1,1,0,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,3,3,0,0,0,0,3,3,0,0,0,0],
    [0,0,0,3,3,3,3,0,0,3,3,3,3,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
]

# Hammer Bro (16x24) - Palette: 0=trans, 1=green, 2=tan, 3=white
HAMMER_BRO = [
    [0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0],
    [0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0],
    [0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0],
    [0,0,0,0,1,3,3,1,1,3,3,1,0,0,0,0],
    [0,0,0,0,1,3,3,1,1,3,3,1,0,0,0,0],
    [0,0,0,0,0,1,1,2,2,1,1,0,0,0,0,0],
    [0,0,0,0,0,0,2,2,2,2,0,0,0,0,0,0],
    [0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0],
    [0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0],
    [0,0,0,0,0,2,2,0,0,2,2,0,0,0,0,0],
    [0,0,0,0,2,2,2,0,0,2,2,2,0,0,0,0],
    [0,0,0,0,3,3,3,0,0,3,3,3,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
]

# Lakitu (16x24) - on cloud - Palette: 0=trans, 1=green, 2=tan, 3=white
LAKITU = [
    [0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0],
    [0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0],
    [0,0,0,0,0,1,3,3,3,3,1,0,0,0,0,0],
    [0,0,0,0,0,1,3,2,2,3,1,0,0,0,0,0],
    [0,0,0,0,0,1,3,2,2,3,1,0,0,0,0,0],
    [0,0,0,0,0,0,2,2,2,2,0,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0],
    [0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0],
    [0,0,0,3,3,3,3,3,3,3,3,3,3,0,0,0],
    [0,0,3,3,3,3,3,3,3,3,3,3,3,3,0,0],
    [0,3,3,3,3,3,3,3,3,3,3,3,3,3,3,0],
    [3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3],
    [3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3],
    [0,3,3,3,3,3,3,3,3,3,3,3,3,3,3,0],
    [0,0,0,3,3,3,3,3,3,3,3,3,3,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
]

# Cheep Cheep (16x16) - Palette: 0=trans, 1=red, 2=white, 3=orange
CHEEP_CHEEP = [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0],
    [0,0,0,0,1,1,1,1,1,1,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,0,0,0,0,0],
    [0,0,1,1,1,2,2,1,1,1,1,1,0,0,0,0],
    [0,1,1,1,1,2,3,1,1,1,1,1,1,1,0,0],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],
    [0,0,1,1,1,1,1,1,1,1,1,1,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,0,0,0,0,0],
    [0,0,0,0,1,1,1,1,1,1,0,0,0,0,0,0],
    [0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
]

# Blooper/Bloober (16x24) - Palette: 0=trans, 1=white, 2=pink, 3=black
BLOOPER = [
    [0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0],
    [0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0],
    [0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,3,3,1,1,3,3,1,1,0,0,0],
    [0,0,0,1,1,3,3,1,1,3,3,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0],
    [0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0],
    [0,1,1,0,1,1,1,1,1,1,1,1,0,1,1,0],
    [0,1,0,0,0,1,1,1,1,1,1,0,0,0,1,0],
    [1,1,0,0,0,0,1,1,1,1,0,0,0,0,1,1],
    [1,0,0,0,0,0,0,1,1,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,1,1,0,0,0,0,0,0,1],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
]

def create_surface(data, palette):
    h, w = len(data), len(data[0])
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        for x in range(w):
            idx = data[y][x]
            if idx > 0 and idx < len(palette):
                surf.set_at((x, y), palette[idx])
    return surf

def create_block_surf(color, border=True):
    s = pygame.Surface((TILE_SIZE, TILE_SIZE))
    s.fill(color)
    if border:
        pygame.draw.rect(s, BLACK, (0,0,TILE_SIZE,TILE_SIZE), 1)
    return s

def create_brick_surf(bg_color=BROWN):
    s = pygame.Surface((TILE_SIZE, TILE_SIZE))
    s.fill(bg_color)
    pygame.draw.rect(s, DKBROWN, (0,0,15,7))
    pygame.draw.rect(s, DKBROWN, (0,8,7,7))
    pygame.draw.rect(s, DKBROWN, (8,8,7,7))
    return s

def create_q_block_surf():
    s = pygame.Surface((TILE_SIZE, TILE_SIZE))
    s.fill(ORANGE)
    pygame.draw.rect(s, DKBROWN, (0,0,TILE_SIZE,TILE_SIZE), 2)
    pygame.draw.rect(s, DKBROWN, (6,3,4,2))
    pygame.draw.rect(s, DKBROWN, (10,5,2,4))
    pygame.draw.rect(s, DKBROWN, (6,9,4,2))
    return s

assets = {}
def init_assets():
    # Mario sprites
    assets['mario_idle'] = create_surface(MARIO_IDLE, MARIO_PALETTE)
    assets['mario_walk1'] = create_surface(MARIO_WALK1, MARIO_PALETTE)
    assets['mario_walk2'] = create_surface(MARIO_WALK2, MARIO_PALETTE)
    assets['mario_walk3'] = create_surface(MARIO_WALK3, MARIO_PALETTE)
    assets['mario_jump'] = create_surface(MARIO_JUMP, MARIO_PALETTE)
    
    # Enemy sprites (1:1 NES SMB1 accurate)
    assets['goomba'] = create_surface(GOOMBA, GOOMBA_PALETTE)
    assets['koopa'] = create_surface(KOOPA, GREEN_KOOPA_PALETTE)
    assets['red_koopa'] = create_surface(RED_KOOPA, RED_KOOPA_PALETTE)
    assets['koopa_shell'] = create_surface(KOOPA_SHELL, GREEN_KOOPA_PALETTE)
    assets['red_shell'] = create_surface(KOOPA_SHELL, RED_KOOPA_PALETTE)
    assets['spiny'] = create_surface(SPINY, SPINY_PALETTE)
    assets['piranha'] = create_surface(PIRANHA, PIRANHA_PALETTE)
    assets['buzzy'] = create_surface(BUZZY, BUZZY_PALETTE)
    assets['hammer_bro'] = create_surface(HAMMER_BRO, HAMMER_BRO_PALETTE)
    assets['lakitu'] = create_surface(LAKITU, LAKITU_PALETTE)
    assets['cheep'] = create_surface(CHEEP_CHEEP, CHEEP_PALETTE)
    assets['blooper'] = create_surface(BLOOPER, BLOOPER_PALETTE)
    
    # Block sprites
    assets['floor'] = create_block_surf(BROWN)
    assets['brick'] = create_brick_surf()
    assets['castle_brick'] = create_brick_surf(GRAY)
    assets['qblock'] = create_q_block_surf()
    assets['hard'] = create_block_surf(DKBROWN)
    assets['pipe'] = create_block_surf(GREEN)
    assets['lava'] = create_block_surf(LAVA_RED, False)
    assets['blue_floor'] = create_block_surf((0, 50, 100))
    assets['tree_block'] = create_block_surf(GREEN)
    
    # Coin (animated style)
    cs = pygame.Surface((16,16), pygame.SRCALPHA)
    pygame.draw.ellipse(cs, YELLOW, (4, 2, 8, 12))
    pygame.draw.ellipse(cs, ORANGE, (5, 3, 6, 10))
    pygame.draw.ellipse(cs, YELLOW, (6, 4, 4, 8))
    assets['coin'] = cs

    # Flag ball
    fs = pygame.Surface((16,16), pygame.SRCALPHA)
    pygame.draw.circle(fs, GREEN, (8,8), 6)
    pygame.draw.circle(fs, (0,220,0), (6,6), 2)
    assets['flag_ball'] = fs

    # Pipe sprites (1:1 NES SMB1 ROM accurate)
    # NES Pipe colors: dark green (0,168,0), light green (184,248,24), black border
    PIPE_DARK = (0, 168, 0)
    PIPE_LIGHT = (184, 248, 24)
    
    # Cap Left (16x16) - 1:1 NES SMB1 pipe cap left tile
    pcl = pygame.Surface((16,16), pygame.SRCALPHA)
    pcl.fill(PIPE_DARK)
    # Light green highlight on left edge
    pygame.draw.rect(pcl, PIPE_LIGHT, (0, 0, 4, 16))
    # Top rim detail
    pygame.draw.rect(pcl, PIPE_LIGHT, (0, 0, 16, 2))
    # Black border
    pygame.draw.rect(pcl, BLACK, (0, 0, 16, 16), 1)
    pygame.draw.line(pcl, BLACK, (0, 0), (0, 16), 1)
    assets['pipe_cap_l'] = pcl
    
    # Cap Right (16x16) - 1:1 NES SMB1 pipe cap right tile
    pcr = pygame.Surface((16,16), pygame.SRCALPHA)
    pcr.fill(PIPE_DARK)
    # Top rim detail
    pygame.draw.rect(pcr, PIPE_LIGHT, (0, 0, 16, 2))
    # Black border
    pygame.draw.rect(pcr, BLACK, (0, 0, 16, 16), 1)
    pygame.draw.line(pcr, BLACK, (15, 0), (15, 16), 1)
    assets['pipe_cap_r'] = pcr
    
    # Body Left (16x16) - 1:1 NES SMB1 pipe body left tile
    pbl = pygame.Surface((16,16), pygame.SRCALPHA)
    pbl.fill(PIPE_DARK)
    # Light green highlight on left edge (vertical stripe)
    pygame.draw.rect(pbl, PIPE_LIGHT, (0, 0, 4, 16))
    # Black vertical borders
    pygame.draw.line(pbl, BLACK, (0, 0), (0, 16), 1)
    pygame.draw.line(pbl, BLACK, (15, 0), (15, 16), 1)
    assets['pipe_body_l'] = pbl
    
    # Body Right (16x16) - 1:1 NES SMB1 pipe body right tile
    pbr = pygame.Surface((16,16), pygame.SRCALPHA)
    pbr.fill(PIPE_DARK)
    # Black vertical borders
    pygame.draw.line(pbr, BLACK, (0, 0), (0, 16), 1)
    pygame.draw.line(pbr, BLACK, (15, 0), (15, 16), 1)
    assets['pipe_body_r'] = pbr

    # Mushroom (Powerup)
    ms = pygame.Surface((16,16), pygame.SRCALPHA)
    pygame.draw.ellipse(ms, RED, (1, 1, 14, 10))
    pygame.draw.rect(ms, SKIN, (4, 10, 8, 6))
    pygame.draw.circle(ms, WHITE, (4, 4), 2)
    pygame.draw.circle(ms, WHITE, (12, 4), 2)
    assets['mushroom'] = ms

    # Background Decorations
    # Cloud
    cs = pygame.Surface((48, 24), pygame.SRCALPHA)
    pygame.draw.circle(cs, WHITE, (12, 12), 10)
    pygame.draw.circle(cs, WHITE, (24, 12), 12)
    pygame.draw.circle(cs, WHITE, (36, 12), 10)
    assets['cloud'] = cs
    # Bush
    bs = pygame.Surface((32, 16), pygame.SRCALPHA)
    pygame.draw.circle(bs, GREEN, (8, 12), 8)
    pygame.draw.circle(bs, GREEN, (16, 10), 10)
    pygame.draw.circle(bs, GREEN, (24, 12), 8)
    assets['bush'] = bs
    # Hill
    hs = pygame.Surface((48, 32), pygame.SRCALPHA)
    pygame.draw.ellipse(hs, (0, 150, 0), (0, 0, 48, 64))
    pygame.draw.circle(hs, WHITE, (12, 10), 2)
    assets['hill'] = hs

# --- Game Classes ---

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        
    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)
        
    def update(self, target):
        x = -target.rect.x + SCREEN_W // 2
        x = min(0, x)
        x = max(-(self.width - SCREEN_W), x)
        self.camera.x += (x - self.camera.x) * 0.1

class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y, surf):
        super().__init__()
        self.image = surf
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.true_x = float(x)
        self.true_y = float(y)
        self.dx = 0
        self.dy = 0
        self.on_ground = False

class Block(pygame.sprite.Sprite):
    def __init__(self, x, y, type_char, level_type=0):
        super().__init__()
        self.type = type_char
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.active = True
        
        # Appearance based on world type
        if self.type == 'F': self.image = assets['blue_floor'] if level_type == 2 else assets['floor']
        elif self.type == 'B': self.image = assets['castle_brick'] if level_type == 3 else assets['brick']
        elif self.type == 'Q': self.image = assets['qblock']
        elif self.type == 'H': self.image = assets['hard']
        elif self.type == 'P': self.image = assets['pipe']
        elif self.type == '<': self.image = assets['pipe_cap_l']
        elif self.type == '>': self.image = assets['pipe_cap_r']
        elif self.type == '[': self.image = assets['pipe_body_l']
        elif self.type == ']': self.image = assets['pipe_body_r']
        elif self.type == 'L': self.image = assets['lava']
        elif self.type == 'W': self.image = assets['tree_block'] # Tree/Platform
        elif self.type == 'S': # End Goal
            self.image = assets['coin'] 
            self.rect.width = 16
        elif self.type == 'O': 
            self.image = pygame.Surface((16,16)); self.image.fill(BLACK); self.image.set_colorkey(BLACK)
        elif self.type == 'T': 
            self.image = assets['flag_ball']
        elif self.type == 'c': self.image = assets['cloud']
        elif self.type == 'b': self.image = assets['bush']
        elif self.type == 'h': self.image = assets['hill']
        else:
            # Default: invisible block for any unrecognized characters
            self.image = pygame.Surface((16,16), pygame.SRCALPHA)

    def hit(self):
        if self.type == 'Q' and self.active:
            self.active = False
            self.image = assets['hard']
            # 20% chance for mushroom, else coin
            return 'MUSHROOM' if random.random() < 0.2 else 'COIN'
        elif self.type == 'B':
            sounds['break'].play()
            return None
        return None

class Powerup(Entity):
    def __init__(self, x, y, type):
        super().__init__(x, y, assets['mushroom'] if type == 'MUSHROOM' else assets['coin'])
        self.type = type
        self.dx = 1.0
        self.dy = 0
        
    def update(self, blocks):
        self.dy += GRAVITY
        self.true_x += self.dx
        self.rect.x = int(self.true_x)
        for b in blocks:
            if b.type in ['F','B','Q','H','P','<','>','[',']']:
                if self.rect.colliderect(b.rect):
                    self.dx *= -1
                    self.true_x += self.dx * 2
        self.true_y += self.dy
        self.rect.y = int(self.true_y)
        for b in blocks:
            if b.type in ['F','B','Q','H','P','<','>','[',']']:
                if self.rect.colliderect(b.rect):
                    if self.dy > 0:
                        self.rect.bottom = b.rect.top
                        self.dy = 0
                        self.true_y = float(self.rect.y)

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, assets['mario_idle'])
        self.state = 'SMALL'
        self.walk_speed = PLAYER_WALK_SPEED
        self.run_speed = PLAYER_RUN_SPEED
        self.jump_power = JUMP_POWER
        self.facing_right = True
        self.dead = False
        self.win = False
        self.win_timer = 0
        self.lives = 3
        self.score = 0
        self.coins = 0
        self.can_jump = False
        self.jump_timer = 0
        self.invincible = 0
        self.walk_frame = 0
        self.animation_timer = 0
        
    def update(self, keys, blocks, enemies, powerups):
        if self.dead:
            self.rect.y += 5
            return
            
        if self.win:
            self.win_timer += 1
            if self.win_timer < 180: self.rect.x += 2
            return
        
        # Invincibility
        if self.invincible > 0: 
            self.invincible -= 1
            self.image.set_alpha(100 if self.invincible % 4 < 2 else 255)
        else:
            self.image.set_alpha(255)

        # Movement
        is_running = keys[pygame.K_x] or keys[pygame.K_LSHIFT]
        max_speed = self.run_speed if is_running else self.walk_speed
        
        target_speed = 0
        if keys[pygame.K_LEFT]:
            target_speed = -max_speed
            self.facing_right = False
        elif keys[pygame.K_RIGHT]:
            target_speed = max_speed
            self.facing_right = True
            
        accel = ACCELERATION if self.on_ground else AIR_CONTROL
        if self.dx < target_speed: self.dx = min(self.dx + accel, target_speed)
        elif self.dx > target_speed: self.dx = max(self.dx - accel, target_speed)
        
        # Jump
        if (keys[pygame.K_z] or keys[pygame.K_SPACE]) and self.can_jump:
            self.dy = self.jump_power
            self.on_ground = False
            self.can_jump = False
            sounds['jump'].play()
            
        # Gravity
        self.dy += GRAVITY
        if self.dy > MAX_FALL: self.dy = MAX_FALL
            
        # X Physics
        self.true_x += self.dx
        self.rect.x = int(self.true_x)
        self.check_collision(blocks, powerups, 'x')
        
        # Y Physics
        self.true_y += self.dy
        self.rect.y = int(self.true_y)
        self.on_ground = False
        self.check_collision(blocks, powerups, 'y')
        
        # Floor snap
        if not self.on_ground and self.dy >= 0:
            self.rect.y += 1
            hit = False
            for b in blocks:
                if b.type in ['F','B','Q','H','P','W','L','<','>','[',']']:
                    if self.rect.colliderect(b.rect):
                        hit = True; break
            self.rect.y -= 1
            if hit:
                self.on_ground = True
                self.dy = 0
                self.can_jump = True
                self.true_y = float(self.rect.y)
                
        # Animation (1:1 NES walk cycle)
        self.animation_timer += 1
        anim_img = assets['mario_idle']
        if not self.on_ground:
            anim_img = assets['mario_jump']
        elif abs(self.dx) > 0.5:
            if self.animation_timer % 6 == 0:
                self.walk_frame = (self.walk_frame + 1) % 3
            if self.walk_frame == 0: anim_img = assets['mario_walk1']
            elif self.walk_frame == 1: anim_img = assets['mario_walk2']
            else: anim_img = assets['mario_walk3']
        else:
            anim_img = assets['mario_idle']
            self.walk_frame = 0
            
        # State Scale (Big Mario)
        if self.state == 'BIG':
            self.image = pygame.transform.scale(anim_img, (16, 32))
            if not self.facing_right: self.image = pygame.transform.flip(self.image, True, False)
            # Adjust rect
            old_bottom = self.rect.bottom
            self.rect.height = 32
            self.rect.bottom = old_bottom
        else:
            self.image = anim_img
            if not self.facing_right: self.image = pygame.transform.flip(self.image, True, False)
            self.rect.height = 16

        # Enemy Interaction
        for e in enemies:
            if e.dead: continue
            if self.rect.colliderect(e.rect):
                if self.dy > 0 and self.rect.bottom < e.rect.centery + 10:
                    e.die()
                    self.dy = BOUNCE_SPEED
                    self.score += 100
                    sounds['stomp'].play()
                elif self.invincible == 0:
                    if self.state == 'BIG':
                        self.state = 'SMALL'
                        self.invincible = 120
                        sounds['thud'].play()
                    else:
                        self.lives -= 1
                        if self.lives <= 0: self.die()
                        else:
                            self.invincible = 90
                            self.dy = -4
                            self.dx = -5 if e.rect.centerx > self.rect.centerx else 5
        
        if self.rect.top > SCREEN_H: self.die()
        
    def check_collision(self, blocks, powerups, axis):
        # Powerup collision
        for p in powerups:
            if self.rect.colliderect(p.rect):
                if p.type == 'MUSHROOM':
                    self.state = 'BIG'
                    self.score += 1000
                    sounds['powerup'].play()
                elif p.type == 'COIN':
                    self.score += 200
                    self.coins += 1
                    sounds['coin'].play()
                p.kill()

        for b in blocks:
            if b.type in ['c','b','h']: continue # Background
            if self.rect.colliderect(b.rect):
                # Win
                if b.type == 'O' or b.type == 'S':
                    self.win = True
                    sounds['stage_clear'].play()
                    return
                # Lava
                if b.type == 'L':
                    self.die()
                    return
                
                # Solid
                if b.type in ['F','B','Q','H','P','W','<','>','[',']']:
                    if axis == 'x':
                        if self.dx > 0: self.rect.right = b.rect.left
                        elif self.dx < 0: self.rect.left = b.rect.right
                        self.dx = 0
                        self.true_x = float(self.rect.x)
                    elif axis == 'y':
                        if self.dy > 0: 
                            self.rect.bottom = b.rect.top
                            self.on_ground = True
                            self.can_jump = True
                            self.dy = 0
                        elif self.dy < 0: 
                            self.rect.top = b.rect.bottom
                            self.dy = 0
                        res = b.hit()
                        if b.type == 'B' and self.state == 'BIG':
                            b.kill()
                            if res == 'COIN':
                                self.score += 200
                                self.coins += 1
                                sounds['coin'].play()
                            elif res == 'MUSHROOM':
                                powerups.add(Powerup(b.rect.x, b.rect.y - 16, 'MUSHROOM'))
                                sounds['powerup_appear'].play()
                        self.true_y = float(self.rect.y)

    def die(self):
        if not self.dead:
            self.dead = True
            self.dy = -6
            sounds['die'].play()

class Enemy(Entity):
    # Enemy types: E=Goomba, K=Green Koopa, R=Red Koopa, S=Spiny, Z=Buzzy, 
    # H=Hammer Bro, L=Lakitu, C=Cheep, B=Blooper, P=Piranha
    def __init__(self, x, y, type_char):
        self.enemy_type = type_char
        
        # Select sprite based on enemy type
        if type_char == 'E':  # Goomba
            surf = assets['goomba']
            self.speed = 0.5
            self.stompable = True
        elif type_char == 'K':  # Green Koopa
            surf = assets['koopa']
            self.speed = 0.5
            self.stompable = True
            self.has_shell = True
        elif type_char == 'R':  # Red Koopa (doesn't fall off edges)
            surf = assets['red_koopa']
            self.speed = 0.4
            self.stompable = True
            self.has_shell = True
        elif type_char == 'Y':  # Spiny (not stompable)
            surf = assets['spiny']
            self.speed = 0.4
            self.stompable = False
        elif type_char == 'Z':  # Buzzy Beetle
            surf = assets['buzzy']
            self.speed = 0.4
            self.stompable = True
            self.has_shell = True
        elif type_char == 'M':  # Hammer Bro
            surf = assets['hammer_bro']
            self.speed = 0.3
            self.stompable = True
        elif type_char == 'A':  # Lakitu
            surf = assets['lakitu']
            self.speed = 0.8
            self.stompable = True
            self.flying = True
        elif type_char == 'C':  # Cheep Cheep
            surf = assets['cheep']
            self.speed = 0.6
            self.stompable = True
            self.flying = True
        elif type_char == 'B':  # Blooper
            surf = assets['blooper']
            self.speed = 0.5
            self.stompable = True
            self.flying = True
        elif type_char == 'I':  # Piranha Plant
            surf = assets['piranha']
            self.speed = 0
            self.stompable = False
        else:  # Default to Goomba
            surf = assets['goomba']
            self.speed = 0.5
            self.stompable = True
        
        super().__init__(x, y, surf)
        self.dx = -self.speed
        self.dead = False
        self.dead_timer = 0
        self.shell_mode = False
        self.flying = getattr(self, 'flying', False)
        self.has_shell = getattr(self, 'has_shell', False)
        self.animation_timer = 0
        self.orig_y = y
        
    def update(self, blocks):
        if self.dead:
            self.dead_timer += 1
            if self.dead_timer > 30: self.kill()
            return
        
        self.animation_timer += 1
        
        # Flying enemies (Lakitu, Cheep, Blooper) - sinusoidal movement
        if self.flying:
            self.true_x += self.dx
            self.rect.x = int(self.true_x)
            # Vertical bobbing
            self.rect.y = int(self.orig_y + math.sin(self.animation_timer * 0.05) * 20)
            return
        
        # Piranha Plant - stationary, just animate up/down from pipe
        if self.enemy_type == 'I':
            phase = (self.animation_timer % 120)
            if phase < 30:
                self.rect.y = self.orig_y - phase // 2
            elif phase < 60:
                self.rect.y = self.orig_y - 15
            elif phase < 90:
                self.rect.y = self.orig_y - (90 - phase) // 2
            else:
                self.rect.y = self.orig_y
            return
            
        # Ground enemy physics
        self.dy += GRAVITY
        self.true_x += self.dx
        self.rect.x = int(self.true_x)
        
        for b in blocks:
            if b.type in ['O', 'S', 'L', '<', '>', '[', ']']: continue
            if self.rect.colliderect(b.rect):
                self.dx *= -1
                self.true_x += self.dx * 2
        
        self.true_y += self.dy
        self.rect.y = int(self.true_y)
        for b in blocks:
            if b.type in ['O', 'S', '<', '>', '[', ']']: continue
            if self.rect.colliderect(b.rect):
                if self.dy > 0:
                    self.rect.bottom = b.rect.top
                    self.dy = 0
                    self.true_y = float(self.rect.y)
        if self.rect.y > SCREEN_H: self.kill()

    def die(self):
        if not self.stompable:
            return  # Spinies and Piranhas can't be stomped
            
        if self.has_shell and not self.shell_mode:
            # Turn into shell
            self.shell_mode = True
            if self.enemy_type == 'K':
                self.image = assets['koopa_shell']
            elif self.enemy_type == 'R':
                self.image = assets['red_shell']
            elif self.enemy_type == 'Z':
                self.image = assets['buzzy']  # Buzzy uses same sprite for shell
            self.rect = self.image.get_rect(center=self.rect.center)
            self.dx = 0  # Shell stops
            return
            
        self.dead = True
        self.image = pygame.transform.scale(self.image, (16, 8))
        self.rect = self.image.get_rect(center=self.rect.center)
        self.rect.bottom += 4

# --- Level Data (1-1 through 8-4) - SMB1 Accurate ---
# Legend: F=Floor, B=Brick, Q=Question, H=Hard, P=Pipe, E=Goomba, K=Koopa, 
# S=Star/End, T=FlagTop, O=FlagPole, L=Lava, W=Tree/Platform

def generate_smb1_level(world, stage):
    """Generate 1:1 style NES SMB1 levels for all 32 stages (1-1 to 8-4)"""
    # Level width depends on stage
    width = 212
    if stage == 2: width = 160  # Underground levels usually shorter
    elif stage == 4: width = 180 # Castle levels
    
    rows = 15
    grid = [[' ' for _ in range(width)] for _ in range(rows)]
    
    # Helper to add features
    def add_floor(start, end):
        for x in range(start, min(end, width)):
            grid[rows-2][x] = 'F'
            grid[rows-1][x] = 'F'
    def add_gap(start, length):
        for x in range(start, min(start+length, width)):
            grid[rows-2][x] = ' '; grid[rows-1][x] = ' '
    def add_pipe(x, h):
        # Top of the pipe
        cap_y = rows - 2 - h
        if 0 <= cap_y < rows and x < width - 1:
            grid[cap_y][x] = '<'
            grid[cap_y][x+1] = '>'
        # Body of the pipe
        for y in range(rows - 2 - h + 1, rows - 2):
            if 0 <= y < rows and x < width - 1:
                grid[y][x] = '['
                grid[y][x+1] = ']'
    def add_platform(x, y, l, char='B'):
        for i in range(l):
            if x+i < width and 0 <= y < rows: grid[y][x+i] = char
    def add_stairs(x, h, dir=1):
        # Create solid, ground-up stairs
        for col in range(h):
            if dir == 1:
                # Ascending to Right (Standard): Starts at x, grows right
                # Height increases with column index
                cx = x + col
                cheight = col + 1
            else:
                # Ascending to Left: Starts at x, grows left
                # Used for mirrored structures
                cx = x - col
                cheight = col + 1
            
            # Build the column from ground up
            for y in range(cheight):
                row_idx = rows - 3 - y
                if 0 <= row_idx < rows and 0 <= cx < width:
                    grid[row_idx][cx] = 'H'

    def add_flag(x):
        if x < width:
            grid[rows-3][x] = 'H'
            for y in range(2, rows-3): grid[y][x] = 'O'
            grid[1][x] = 'T'
            grid[rows-4][x] = 'S'; grid[rows-5][x] = 'S'
    def add_enemy(x, y, etype):
        if 0 <= x < width and 0 <= y < rows: grid[y][x] = etype
    def add_deco(x, y, dtype):
        if 0 <= x < width and 0 <= y < rows: grid[y][x] = dtype
    def clear_end_path():
        # Clear any brick/hard walls and stray blocks near the flag so the exit is reachable
        # Adjusted range to start AFTER the stairs (stairs usually end around width-24)
        for x in range(max(0, width - 20), width - 1):
            for y in range(2, rows - 3):
                # Don't delete flag parts
                if grid[y][x] in ['B', 'H', 'L', 'Q', 'W']:
                     # Protect the flag base 'H' at rows-3
                     if y == rows-3 and grid[y][x] == 'H' and grid[y-1][x] == 'O': 
                         pass
                     else:
                        grid[y][x] = ' '

    # Add default decorations (SMB1 style)
    for x in range(10, width - 20, 40):
        add_deco(x, 2, 'c') # Cloud
        add_deco(x + 20, 12, 'b') # Bush
        add_deco(x + 5, 11, 'h') # Hill

    # ============ 1:1 Accurate Level Data Definitions ============
    if world == 1 and stage == 1:
        add_floor(0, 69); add_gap(69, 2); add_floor(71, 86); add_gap(86, 3); add_floor(89, 153); add_gap(153, 2); add_floor(155, width)
        
        # Pipes now standardized to height 2 (Mario height)
        pipe_data = [(28, 2), (38, 2), (46, 2), (57, 2)]
        if world >= 3: pipe_data.extend([(90, 2), (110, 2)])
        if world >= 5: pipe_data.extend([(130, 2), (145, 2)])
        if world >= 7: pipe_data.extend([(160, 2), (175, 2)])
        for px, ph in pipe_data:
            if px < width - 30: add_pipe(px, ph)
            
        add_platform(16, 9, 1, 'Q'); add_platform(20, 9, 5, 'B'); grid[9][21]='Q'; grid[9][23]='Q'; add_platform(22, 5, 1, 'Q')
        add_platform(77, 9, 3, 'B'); grid[9][78]='Q'; add_platform(80, 5, 8, 'B'); add_platform(91, 5, 4, 'B'); grid[5][94]='Q'
        
        # Modified this section based on user request to remove upper bricks
        add_platform(128, 9, 4, 'B'); # add_platform(129, 5, 3, 'B'); grid[5][130]='Q'
        
        # --- Stairs Adjusted to be shorter ---
        add_stairs(134, 3); # Removed backward stair to prevent pit trap: add_stairs(148, 3, -1); 
        # add_stairs(181, 5); 
        add_flag(198)
        
        # Explicitly clear the area right before the flag, starting AFTER the stairs to prevent artifacts
        # Stairs at 181 with height 8 end at x=188. We start clearing at 190.
        for x in range(190, width - 5):
            for y in range(2, rows - 3):
                if grid[y][x] not in ['O', 'T', 'S']: # Don't delete flag
                     if grid[y][x] == 'H' and y == rows-3: pass # Flag base
                     else: grid[y][x] = ' '
                     
        # Enemies
        for x in [22, 40, 51, 53, 80, 82, 97, 99, 114, 116, 124, 126]: add_enemy(x, rows-3, 'E')

    elif stage == 2: # Underground (X-2)
        add_floor(0, width)
        for x in range(width): grid[0][x] = 'H'; grid[1][x] = 'H'
        add_platform(10, 10, 10, 'B'); add_platform(25, 6, 8, 'B')
        
        # Pipes standardized to height 2
        pipe_xs = [40, 60, 80, 100]
        for px in pipe_xs:
             add_pipe(px, 2)
             
        add_platform(120, 10, 15, 'B'); add_flag(width-15)
        for x in range(20, width-40, 30): add_enemy(x, rows-3, 'Z')

    elif stage == 3: # Athletic (X-3)
        add_floor(0, 20); add_floor(width-20, width)
        plats = [(30, 10, 4), (50, 7, 5), (75, 9, 6), (100, 11, 4), (125, 8, 8), (150, 10, 5)]
        for x, y, l in plats: add_platform(x, y, l, 'W')
        add_flag(width-15)
        for x, y, _ in plats: add_enemy(x+2, y-1, 'R')

    elif stage == 4: # Castle (X-4)
        add_floor(0, width)
        for x in range(width): grid[0][x] = 'H'; grid[1][x] = 'H'
        for x in [30, 60, 90, 120]:
            for i in range(x, x+4): grid[rows-2][i] = 'L'; grid[rows-1][i] = 'L'
            add_platform(x, rows-5, 4, 'H')
        add_platform(width-40, rows-4, 10, 'H') # Axe area
        add_flag(width-5)
        for x in [45, 75, 105]: add_enemy(x, rows-3, 'M')

    else: # Procedural for other levels but improved
        add_floor(0, width)
        # Scale difficulty with world
        num_gaps = world // 2; gap_w = 2 + world // 4
        for _ in range(num_gaps): add_gap(random.randint(40, width-60), gap_w)
        for i in range(3 + world): add_pipe(30 + i*40, 2)
        for i in range(4 + world): add_enemy(40 + i*30, rows-3, 'E' if i%2==0 else 'K')
        add_stairs(width-40, 3 + (world // 3)); add_flag(width-15)

    clear_end_path()
    
    # Remove any lava ('L') from non-castle levels (stage != 4)
    if stage != 4:
        for y in range(rows):
            for x in range(width):
                if grid[y][x] == 'L':
                    grid[y][x] = ' '
    
    return [''.join(row) for row in grid]

# Generate all 32 levels (Worlds 1-8, Stages 1-4)
LEVELS = []
LEVEL_NAMES = []
for world in range(1, 9):
    for stage in range(1, 5):
        LEVELS.append(generate_smb1_level(world, stage))
        LEVEL_NAMES.append(f"{world}-{stage}")
    
def load_level(idx):
    layout = LEVELS[idx]
    blocks, enemies, powerups = pygame.sprite.Group(), pygame.sprite.Group(), pygame.sprite.Group()
    level_type = 0 # 0=Overworld, 1=Underground, 2=Athletic, 3=Castle
    
    # Determine Level Type based on name
    name = LEVEL_NAMES[idx]
    if "-2" in name: level_type = 1
    elif "-3" in name: level_type = 2
    elif "-4" in name: level_type = 3
    
    player_pos = (50, 100)
    width = len(layout[0]) * TILE_SIZE
    
    # All special characters
    enemy_chars = ['E', 'K', 'R', 'Y', 'Z', 'M', 'A', 'C', 'B', 'I']
    deco_chars = ['c', 'b', 'h']
    pipe_chars = ['<', '>', '[', ']']
    
    for y, row in enumerate(layout):
        for x, char in enumerate(row):
            wx, wy = x * TILE_SIZE, y * TILE_SIZE
            if char in ['F', 'B', 'Q', 'H', 'P', 'S', 'O', 'T', 'L', 'W'] + deco_chars + pipe_chars:
                blocks.add(Block(wx, wy, char, level_type))
            elif char in enemy_chars:
                enemies.add(Enemy(wx, wy, char))
                
    return blocks, enemies, powerups, player_pos, width, level_type

# --- Main Game Loop ---

def main():
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("ULTRA MARIO 2D BROS")
    clock = pygame.time.Clock()
    
    init_assets()
    init_sounds()
    
    # Fonts
    font_title = pygame.font.SysFont("Arial", 64, bold=True)
    font_sub = pygame.font.SysFont("Arial", 32, bold=True)
    font_small = pygame.font.SysFont("Arial", 20, bold=True)
    font_hud = pygame.font.SysFont("Arial", 24, bold=True)
    
    GAME_STATE = "MENU"
    current_level_index = 0
    max_level = len(LEVELS)
    blink_timer = 0
    
    # Game Objects
    player = None
    blocks = None
    enemies = None
    powerups = None
    camera = None
    bg_color = SKY
    
    running = True
    while running:
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            
            if GAME_STATE == "MENU":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        # Start game from World 1-1
                        current_level_index = 0
                        blocks, enemies, powerups, p_pos, lvl_w, l_type = load_level(current_level_index)
                        player = Player(*p_pos)
                        camera = Camera(lvl_w, SCREEN_H)
                        bg_color = SKY
                        if l_type == 1: bg_color = UNDERGROUND_BG
                        elif l_type == 3: bg_color = CASTLE_BG
                        GAME_STATE = "LEVEL"
                        sounds['powerup_appear'].play()
                        
        # ============ MAIN MENU ============
        if GAME_STATE == "MENU":
            screen.fill(SKY)
            blink_timer += 1
            
            cx = WINDOW_W // 2
            
            # Title: ULTRA MARIO 2D BROS
            title1 = font_title.render("ULTRA MARIO", True, RED)
            title2 = font_title.render("2D BROS", True, RED)
            # Shadow
            title1_shadow = font_title.render("ULTRA MARIO", True, BLACK)
            title2_shadow = font_title.render("2D BROS", True, BLACK)
            
            screen.blit(title1_shadow, (cx - title1.get_width()//2 + 4, 150 + 4))
            screen.blit(title1, (cx - title1.get_width()//2, 150))
            screen.blit(title2_shadow, (cx - title2.get_width()//2 + 4, 220 + 4))
            screen.blit(title2, (cx - title2.get_width()//2, 220))
            
            # Mario sprite
            mario_big = pygame.transform.scale(assets['mario_idle'], (64, 64))
            screen.blit(mario_big, (cx - 32, 320))
            
            # PRESS SPACE TO START (blinking)
            if (blink_timer // 30) % 2 == 0:
                start_text = font_sub.render("PRESS SPACE TO START", True, YELLOW)
                start_shadow = font_sub.render("PRESS SPACE TO START", True, BLACK)
                screen.blit(start_shadow, (cx - start_text.get_width()//2 + 2, 450 + 2))
                screen.blit(start_text, (cx - start_text.get_width()//2, 450))
            
            # Copyright text
            copy1 = font_small.render("(C) Nintendo 1985-2026", True, WHITE)
            copy2 = font_small.render("(C) Samsoft 1999-2026", True, WHITE)
            screen.blit(copy1, (cx - copy1.get_width()//2, 550))
            screen.blit(copy2, (cx - copy2.get_width()//2, 580))
            
            # Decorative blocks at bottom
            for i in range(0, WINDOW_W, 48):
                pygame.draw.rect(screen, BROWN, (i, WINDOW_H - 48, 48, 48))
                pygame.draw.rect(screen, DKBROWN, (i, WINDOW_H - 48, 48, 48), 3)
            
        # ============ GAMEPLAY ============
        elif GAME_STATE == "LEVEL":
            # Logic
            player.update(keys, blocks, enemies, powerups)
            for e in enemies: e.update(blocks)
            for p in powerups: p.update(blocks)
            camera.update(player)
            
            # Render to internal surface first
            display = pygame.Surface((SCREEN_W, SCREEN_H))
            display.fill(bg_color)
            
            # Draw order: blocks (incl deco), enemies, powerups, player
            for b in blocks: display.blit(b.image, camera.apply(b))
            for p in powerups: display.blit(p.image, camera.apply(p))
            for e in enemies: display.blit(e.image, camera.apply(e))
            display.blit(player.image, camera.apply(player))
            
            # Scale up
            scaled = pygame.transform.scale(display, (WINDOW_W, WINDOW_H))
            screen.blit(scaled, (0,0))
            
            # UI Overlay
            ui_text = font_hud.render(f"WORLD {LEVEL_NAMES[current_level_index]}  LIVES: {player.lives}  SCORE: {player.score}", True, WHITE)
            ui_shadow = font_hud.render(f"WORLD {LEVEL_NAMES[current_level_index]}  LIVES: {player.lives}  SCORE: {player.score}", True, BLACK)
            screen.blit(ui_shadow, (22, 22))
            screen.blit(ui_text, (20, 20))
            
            # Level Transitions
            if player.win and player.win_timer > 100:
                current_level_index = (current_level_index + 1) % max_level
                # Load next level
                blocks, enemies, powerups, p_pos, lvl_w, l_type = load_level(current_level_index)
                player = Player(*p_pos)
                player.score = player.score if player else 0
                camera = Camera(lvl_w, SCREEN_H)
                bg_color = SKY
                if l_type == 1: bg_color = UNDERGROUND_BG
                elif l_type == 3: bg_color = CASTLE_BG
                
            elif player.dead and player.rect.top > SCREEN_H + 20:
                if player.lives > 0:
                    # Respawn same level
                    blocks, enemies, powerups, p_pos, lvl_w, l_type = load_level(current_level_index)
                    old_score = player.score
                    old_lives = player.lives
                    player = Player(*p_pos)
                    player.score = old_score
                    player.lives = old_lives
                    camera = Camera(lvl_w, SCREEN_H)
                else:
                    # Game over - back to menu
                    GAME_STATE = "MENU"

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
