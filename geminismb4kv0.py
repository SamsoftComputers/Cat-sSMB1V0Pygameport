import pygame
import array
import random
import math
import sys

# --- Configuration & Constants ---
SCREEN_W, SCREEN_H = 256, 240  # NES resolution
WINDOW_W, WINDOW_H = 768, 720  # 3x scale
FPS = 60
TILE_SIZE = 16

# Colors (Famicom/NES palette)
BLACK = (0, 0, 0)
WHITE = (252, 252, 252)
SKY = (92, 148, 252)
NIGHT_SKY = (0, 0, 0)
CAVE_BG = (32, 32, 32)
GREEN = (0, 184, 0)
BROWN = (136, 68, 0)
RED = (216, 40, 0)
ORANGE = (228, 92, 16)
YELLOW = (216, 216, 0)
DKBROWN = (100, 50, 0)
SKIN = (255, 206, 150)
GRAY = (152, 152, 152)
HUD_YELLOW = (255, 255, 0)
HUD_SHADOW = (0, 0, 0)
LAVA = (255, 0, 0)
MAP_GREEN = (34, 177, 76)
MAP_PATH = (200, 200, 200)

# --- SM63 / Flash Game Physics Constants ---
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
    sounds['boss_hit'] = make_noise(0.2, 0.2)
    sounds['star_spawn'] = make_triangle_wave(880, 0.5, 0.1)

# --- Sprite Data & Graphics ---
MARIO_PALETTE = [(0,0,0), SKIN, RED, BROWN]
ENEMY_PALETTE = [(0,0,0,0), WHITE, BLACK, BROWN]
KOOPA_PALETTE = [(0,0,0,0), WHITE, GREEN, BLACK]
PIRANHA_PALETTE = [(0,0,0,0), GREEN, RED, BLACK]
BRICK_PALETTE = [(0,0,0,0), DKBROWN, ORANGE, BLACK]
FLAG_PALETTE = [(0,0,0,0), GREEN, WHITE, BLACK]
STAR_PALETTE = [(0,0,0,0), YELLOW, ORANGE, BLACK]

# Small Mario (16x16)
MARIO_IDLE = [[0,0,0,0,0,0,2,2,2,2,2,0,0,0,0,0],[0,0,0,0,0,2,2,2,2,2,2,2,2,2,0,0],[0,0,0,0,0,3,3,3,1,1,1,3,0,0,0,0],[0,0,0,0,3,1,3,1,1,1,3,1,1,1,0,0],[0,0,0,0,3,1,3,3,1,1,1,3,1,1,1,0],[0,0,0,0,3,3,1,1,1,1,3,3,3,3,0,0],[0,0,0,0,0,0,1,1,1,1,1,1,0,0,0,0],[0,0,0,0,0,2,2,3,2,2,0,0,0,0,0,0],[0,0,0,0,2,2,2,3,2,2,3,2,2,0,0,0],[0,0,0,0,2,2,2,3,3,3,3,2,2,0,0,0],[0,0,0,0,2,2,3,1,3,3,1,3,2,2,0,0],[0,0,0,0,0,3,3,3,3,3,3,3,3,0,0,0],[0,0,0,0,0,3,3,0,0,0,0,3,3,0,0,0],[0,0,0,0,3,3,3,0,0,0,0,3,3,3,0,0],[0,0,0,3,3,3,0,0,0,0,0,0,3,3,3,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]
MARIO_WALK1 = [[0,0,0,0,0,0,2,2,2,2,2,0,0,0,0,0],[0,0,0,0,0,2,2,2,2,2,2,2,2,2,0,0],[0,0,0,0,0,3,3,3,1,1,1,3,0,0,0,0],[0,0,0,0,3,1,3,1,1,1,3,1,1,1,0,0],[0,0,0,0,3,1,3,3,1,1,1,3,1,1,1,0],[0,0,0,0,3,3,1,1,1,1,3,3,3,3,0,0],[0,0,0,0,0,0,1,1,1,1,1,1,0,0,0,0],[0,0,0,0,0,2,2,3,2,2,2,0,0,0,0,0],[0,0,0,0,2,2,2,3,2,2,2,2,0,0,0,0],[0,0,0,0,2,2,2,2,3,3,3,2,2,0,0,0],[0,0,0,0,2,2,3,1,3,3,1,3,2,0,0,0],[0,0,0,0,0,3,3,3,3,3,3,3,3,0,0,0],[0,0,0,0,0,0,3,3,3,0,0,0,0,0,0,0],[0,0,0,0,0,3,3,3,0,0,0,0,0,0,0,0],[0,0,0,0,3,3,3,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]
MARIO_WALK2 = [[0,0,0,0,0,0,2,2,2,2,2,0,0,0,0,0],[0,0,0,0,0,2,2,2,2,2,2,2,2,2,0,0],[0,0,0,0,0,3,3,3,1,1,1,3,0,0,0,0],[0,0,0,0,3,1,3,1,1,1,3,1,1,1,0,0],[0,0,0,0,3,1,3,3,1,1,1,3,1,1,1,0],[0,0,0,0,3,3,1,1,1,1,3,3,3,3,0,0],[0,0,0,0,0,0,1,1,1,1,1,1,0,0,0,0],[0,0,0,0,0,2,2,3,2,2,3,2,0,0,0,0],[0,0,0,0,2,2,2,3,2,2,3,2,2,2,0,0],[0,0,0,0,2,2,2,3,3,3,3,2,2,2,0,0],[0,0,0,0,2,2,3,1,3,3,1,3,2,2,0,0],[0,0,0,0,0,3,3,3,3,3,3,3,3,0,0,0],[0,0,0,0,0,0,3,3,0,0,3,3,0,0,0,0],[0,0,0,0,0,3,3,3,0,0,3,3,3,0,0,0],[0,0,0,0,0,3,3,0,0,0,0,3,3,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]
MARIO_WALK3 = [[0,0,0,0,0,0,2,2,2,2,2,0,0,0,0,0],[0,0,0,0,0,2,2,2,2,2,2,2,2,2,0,0],[0,0,0,0,0,3,3,3,1,1,1,3,0,0,0,0],[0,0,0,0,3,1,3,1,1,1,3,1,1,1,0,0],[0,0,0,0,3,1,3,3,1,1,1,3,1,1,1,0],[0,0,0,0,3,3,1,1,1,1,3,3,3,3,0,0],[0,0,0,0,0,0,1,1,1,1,1,1,0,0,0,0],[0,0,0,0,0,2,2,3,2,2,2,0,0,0,0,0],[0,0,0,0,2,2,2,3,2,2,2,2,0,0,0,0],[0,0,0,0,2,2,2,3,3,3,3,2,2,0,0,0],[0,0,0,0,0,3,3,1,3,3,2,2,3,0,0,0],[0,0,0,0,3,3,3,1,1,3,3,3,3,0,0,0],[0,0,0,0,0,0,0,0,1,1,3,3,3,0,0,0],[0,0,0,0,3,3,3,0,0,3,3,0,0,0,0,0],[0,0,0,0,3,3,3,3,0,0,0,0,0,0,0,0],[0,0,0,0,0,3,3,0,0,0,0,0,0,0,0,0]]
MARIO_JUMP = [[0,0,0,0,0,0,0,2,2,2,2,2,0,0,0,0],[0,0,0,0,0,0,2,2,2,2,2,2,2,2,0,0],[0,0,0,0,0,0,3,3,3,1,1,1,3,0,0,0],[0,0,0,0,0,3,1,3,1,1,1,3,1,1,1,0],[0,0,0,0,0,3,1,3,3,1,1,1,3,1,1,1],[0,0,0,0,0,3,3,1,1,1,1,3,3,3,3,0],[0,0,0,0,0,0,0,1,1,1,1,1,1,0,0,0],[0,0,0,2,2,0,2,2,3,2,2,2,0,0,0,0],[0,0,2,2,2,2,2,2,3,2,2,3,2,2,2,0],[0,0,2,2,2,2,2,3,3,3,3,3,2,2,2,0],[0,0,0,0,2,2,3,1,3,3,3,1,3,0,0,0],[0,0,0,0,0,3,3,3,3,3,3,3,3,3,0,0],[0,0,0,0,3,3,3,3,0,0,0,3,3,3,0,0],[0,0,0,3,3,3,0,0,0,0,0,0,3,3,0,0],[0,0,3,3,3,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]

# Big Mario (16x32)
BIG_MARIO_TOP = [[0,0,0,0,0,0,2,2,2,2,2,0,0,0,0,0],[0,0,0,0,0,2,2,2,2,2,2,2,2,2,0,0],[0,0,0,0,0,3,3,3,1,1,1,3,0,0,0,0],[0,0,0,0,3,1,3,1,1,1,3,1,1,1,0,0],[0,0,0,0,3,1,3,3,1,1,1,3,1,1,1,0],[0,0,0,0,3,3,1,1,1,1,3,3,3,3,0,0],[0,0,0,0,0,0,1,1,1,1,1,1,0,0,0,0],[0,0,0,0,0,2,2,3,2,2,0,0,0,0,0,0],[0,0,0,0,2,2,2,3,2,2,3,2,2,0,0,0],[0,0,0,0,2,2,2,3,3,3,3,2,2,0,0,0],[0,0,0,0,2,2,3,1,3,3,1,3,2,2,0,0],[0,0,0,0,0,3,3,3,3,3,3,3,3,0,0,0],[0,0,0,0,0,3,3,0,0,0,0,3,3,0,0,0],[0,0,0,0,3,3,3,0,0,0,0,3,3,3,0,0],[0,0,0,3,3,3,0,0,0,0,0,0,3,3,3,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]
BIG_MARIO_BOT = [[0,0,0,0,0,0,2,2,2,2,0,0,0,0,0,0],[0,0,0,0,0,2,2,3,2,2,0,0,0,0,0,0],[0,0,0,0,2,2,2,3,2,2,3,2,2,0,0,0],[0,0,0,0,2,2,2,3,3,3,3,2,2,0,0,0],[0,0,0,0,2,2,3,1,3,3,1,3,2,2,0,0],[0,0,0,0,0,3,3,3,3,3,3,3,3,0,0,0],[0,0,0,0,0,3,3,0,0,0,0,3,3,0,0,0],[0,0,0,0,3,3,3,0,0,0,0,3,3,3,0,0],[0,0,0,3,3,3,0,0,0,0,0,0,3,3,3,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]

GOOMBA_SPRITE = [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,3,3,3,3,0,0,0,0,0,0],[0,0,0,0,0,3,3,3,3,3,3,0,0,0,0,0],[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,0,3,1,1,3,3,3,3,1,1,3,0,0,0],[0,0,0,3,1,2,3,3,3,3,2,1,3,0,0,0],[0,0,3,3,3,3,3,3,3,3,3,3,3,3,0,0],[0,3,3,3,3,3,3,3,3,3,3,3,3,3,3,0],[0,0,3,3,3,3,3,3,3,3,3,3,3,3,0,0],[0,0,0,3,3,0,0,3,3,0,0,3,3,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]

KOOPA_SPRITE = [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,2,2,2,2,0,0,0,0,0,0],[0,0,0,0,0,2,2,2,2,2,2,0,0,0,0,0],[0,0,0,0,0,2,1,1,2,2,2,0,0,0,0,0],[0,0,0,0,0,2,1,3,2,2,2,0,0,0,0,0],[0,0,0,0,2,2,2,2,2,2,2,2,0,0,0,0],[0,0,0,2,2,2,2,2,2,2,2,2,2,0,0,0],[0,0,2,2,2,2,2,2,2,2,2,2,2,2,0,0],[0,0,2,2,2,2,2,2,2,2,2,2,2,2,0,0]]

PIRANHA_SPRITE = [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,2,2,2,2,2,2,0,0,0,0,0],[0,0,0,0,2,2,1,2,2,1,2,2,0,0,0,0],[0,0,0,0,2,2,1,2,2,1,2,2,0,0,0,0],[0,0,0,0,2,2,2,2,2,2,2,2,0,0,0,0],[0,0,0,0,0,2,2,1,1,2,2,0,0,0,0,0],[0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0],[0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0],[0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0]]

MUSHROOM_SPRITE = [[0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0],[0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0],[0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0],[0,0,0,1,1,1,2,2,2,2,1,1,1,0,0,0],[0,0,1,1,1,2,2,2,2,2,2,1,1,1,0,0],[0,1,1,1,2,2,2,2,2,2,2,2,1,1,1,0],[0,1,1,1,2,2,2,2,2,2,2,2,1,1,1,0],[0,1,1,1,2,2,2,2,2,2,2,2,1,1,1,0],[0,1,1,1,2,2,2,2,2,2,2,2,1,1,1,0],[0,0,1,1,1,2,2,2,2,2,2,1,1,1,0,0],[0,0,0,1,1,1,2,2,2,2,1,1,1,0,0,0],[0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0],[0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0],[0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]

STAR_SPRITE = [
    [0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,1,2,2,1,0,0,0,0,0,0],
    [0,0,0,0,0,0,1,2,2,1,0,0,0,0,0,0],
    [0,0,0,0,0,1,1,2,2,1,1,0,0,0,0,0],
    [0,1,1,1,1,1,2,2,2,2,1,1,1,1,1,0],
    [0,1,2,2,2,2,2,2,2,2,2,2,2,2,1,0],
    [0,0,1,2,2,2,2,2,2,2,2,2,2,1,0,0],
    [0,0,0,1,2,2,2,2,2,2,2,2,1,0,0,0],
    [0,0,0,0,1,2,2,2,2,2,2,1,0,0,0,0],
    [0,0,0,1,2,2,2,1,1,2,2,2,1,0,0,0],
    [0,0,1,2,2,2,1,0,0,1,2,2,2,1,0,0],
    [0,1,2,2,2,1,0,0,0,0,1,2,2,2,1,0],
    [0,1,2,2,1,0,0,0,0,0,0,1,2,2,1,0],
    [0,1,1,1,0,0,0,0,0,0,0,0,1,1,1,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
]

FLAG_BALL = [[0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0],[0,0,0,1,1,1,1,1,1,1,1,0,0,0,0,0],[0,0,1,1,1,1,1,1,1,1,1,1,0,0,0,0],[0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],[1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],[1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],[1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],[0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[0,0,1,1,1,1,1,1,1,1,1,1,0,0,0,0],[0,0,0,1,1,1,1,1,1,1,1,0,0,0,0,0],[0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0],[0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0]]
FLAG_POLE = [[0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0]] * 8
FLAG_CLOTH = [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],[0,1,1,1,2,2,1,1,1,1,1,1,1,1,0,0],[0,1,1,2,1,1,2,1,1,1,1,1,1,1,0,0],[0,1,1,2,1,1,2,1,1,1,1,1,1,1,0,0],[0,1,1,1,2,2,1,1,1,1,1,1,1,1,0,0],[0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],[0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],[0,0,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[0,0,1,1,1,1,1,1,1,1,1,1,0,0,0,0],[0,0,0,1,1,1,1,1,1,1,1,0,0,0,0,0],[0,0,0,0,1,1,1,1,1,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]

def create_surface(data, palette):
    h = len(data)
    w = len(data[0])
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        for x in range(w):
            idx = data[y][x]
            if idx > 0 and idx < len(palette):
                color = palette[idx]
                surf.set_at((x, y), color)
    return surf

def create_block_surf(color, border=True):
    s = pygame.Surface((TILE_SIZE, TILE_SIZE))
    s.fill(color)
    if border:
        pygame.draw.rect(s, BLACK, (0,0,TILE_SIZE,TILE_SIZE), 1)
        pygame.draw.line(s, BLACK, (0,0), (TILE_SIZE, TILE_SIZE), 1)
    return s

def create_brick_surf():
    s = pygame.Surface((TILE_SIZE, TILE_SIZE))
    s.fill(BROWN)
    pygame.draw.rect(s, DKBROWN, (0,0,15,7))
    pygame.draw.rect(s, DKBROWN, (0,8,7,7))
    pygame.draw.rect(s, DKBROWN, (8,8,7,7))
    return s

def create_q_block_surf():
    s = pygame.Surface((TILE_SIZE, TILE_SIZE))
    s.fill(ORANGE)
    pygame.draw.rect(s, DKBROWN, (0,0,TILE_SIZE,TILE_SIZE), 2)
    # Draw ?
    pygame.draw.rect(s, DKBROWN, (6,3,4,2))
    pygame.draw.rect(s, DKBROWN, (10,5,2,4))
    pygame.draw.rect(s, DKBROWN, (6,9,4,2))
    pygame.draw.rect(s, DKBROWN, (6,12,4,2))
    return s

def create_cloud_sprite():
    surf = pygame.Surface((32, 24), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, WHITE, (0, 8, 32, 16))
    pygame.draw.ellipse(surf, WHITE, (8, 0, 24, 24))
    return surf

def create_bush_sprite():
    surf = pygame.Surface((32, 16), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, GREEN, (0, 4, 12, 12))
    pygame.draw.ellipse(surf, GREEN, (8, 0, 16, 16))
    pygame.draw.ellipse(surf, GREEN, (20, 4, 12, 12))
    return surf

def create_coin_sprite():
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    pygame.draw.circle(surf, YELLOW, (8, 8), 6)
    pygame.draw.circle(surf, ORANGE, (8, 8), 4)
    pygame.draw.circle(surf, YELLOW, (8, 8), 2)
    return surf

assets = {}

def init_assets():
    assets['mario_idle'] = create_surface(MARIO_IDLE, MARIO_PALETTE)
    assets['mario_walk1'] = create_surface(MARIO_WALK1, MARIO_PALETTE)
    assets['mario_walk2'] = create_surface(MARIO_WALK2, MARIO_PALETTE)
    assets['mario_walk3'] = create_surface(MARIO_WALK3, MARIO_PALETTE)
    assets['mario_jump'] = create_surface(MARIO_JUMP, MARIO_PALETTE)
    assets['goomba'] = create_surface(GOOMBA_SPRITE, ENEMY_PALETTE)
    assets['koopa'] = create_surface(KOOPA_SPRITE, KOOPA_PALETTE)
    assets['piranha'] = create_surface(PIRANHA_SPRITE, PIRANHA_PALETTE)
    assets['mushroom'] = create_surface(MUSHROOM_SPRITE, [(0,0,0), RED, WHITE, BLACK])
    assets['star'] = create_surface(STAR_SPRITE, STAR_PALETTE)
    
    # Create Big Mario Sprites (Combinations)
    s_top = create_surface(BIG_MARIO_TOP, MARIO_PALETTE)
    s_bot = create_surface(BIG_MARIO_BOT, MARIO_PALETTE)
    big_surf = pygame.Surface((16, 32), pygame.SRCALPHA)
    big_surf.blit(s_top, (0, 0))
    big_surf.blit(s_bot, (0, 16))
    assets['big_mario_idle'] = big_surf
    
    assets['floor'] = create_block_surf(BROWN)
    assets['brick'] = create_brick_surf()
    assets['qblock'] = create_q_block_surf()
    assets['hard'] = create_block_surf(DKBROWN)
    assets['pipe'] = create_block_surf(GREEN)
    assets['flag_ball'] = create_surface(FLAG_BALL, FLAG_PALETTE)
    assets['flag_pole'] = create_surface(FLAG_POLE, FLAG_PALETTE)
    assets['flag_cloth'] = create_surface(FLAG_CLOTH, FLAG_PALETTE)
    assets['cloud'] = create_cloud_sprite()
    assets['bush'] = create_bush_sprite()
    assets['coin'] = create_coin_sprite()

# --- Game Classes ---

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.target_x = 0
        
    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)
        
    def apply_rect(self, rect):
        return rect.move(self.camera.topleft)
        
    def update(self, target):
        x = -target.rect.x + SCREEN_W // 2
        x = min(0, x)
        x = max(-(self.width - SCREEN_W), x)
        self.target_x = x
        self.camera.x += (self.target_x - self.camera.x) * 0.1
        self.camera.x = int(self.camera.x)

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

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, assets['mario_idle'])
        self.walk_speed = PLAYER_WALK_SPEED
        self.run_speed = PLAYER_RUN_SPEED
        self.max_speed = PLAYER_RUN_SPEED
        self.jump_power = JUMP_POWER
        self.facing_right = True
        self.dead = False
        self.win = False
        self.win_timer = 0
        self.is_running = False
        self.walk_frame = 0
        self.animation_timer = 0
        self.can_jump = False
        self.jump_timer = 0
        self.max_jump_time = 16
        self.coins = 0
        self.stars = 0 # Star counter
        self.score = 0
        self.lives = 8 # Health Points (POW)
        self.max_hp = 8
        self.world = 1
        self.stage = 1
        self.is_big = False
        self.invincible = 0
        
        # SM63 Physics State
        self.jump_combo = 0       # 0=Single, 1=Double, 2=Triple
        self.jump_combo_timer = 0 # Time window to chain jump
        self.wall_slide = False
        self.ground_pound = False
        
    def grow(self):
        if not self.is_big:
            self.is_big = True
            self.image = assets['big_mario_idle']
            self.rect = self.image.get_rect(center=self.rect.center)
            self.rect.bottom = int(self.true_y) + 16 # Adjust for height diff
            self.true_y -= 16
            sounds['powerup'].play()

    def shrink(self, force=True):
        if self.is_big:
            self.is_big = False
            self.image = assets['mario_idle']
            self.rect = self.image.get_rect(center=self.rect.center)
            self.rect.bottom = int(self.true_y) + 32
            self.true_y += 16
            sounds['break'].play()
        elif force:
            self.die()

    def update(self, keys, blocks, enemies, coins, powerups):
        if self.dead:
            self.dy += GRAVITY
            self.rect.y += self.dy
            return
            
        if self.win:
            self.win_timer += 1
            if self.win_timer < 180:
                self.rect.y = min(self.rect.y + 1, 13 * TILE_SIZE - self.rect.height)
            return
        
        # Invincibility frame flickering
        if self.invincible > 0: 
            self.invincible -= 1
            if self.invincible % 4 < 2:
                self.image.set_alpha(100)
            else:
                self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)

        if self.jump_combo_timer > 0: self.jump_combo_timer -= 1
        else: self.jump_combo = 0 # Reset combo if time runs out

        self.is_running = keys[pygame.K_x] or keys[pygame.K_LSHIFT]
        self.max_speed = self.run_speed if self.is_running else self.walk_speed
        
        # --- Flash-like Momentum Physics ---
        target_speed = 0
        # Disable input if getting knocked back (briefly) or allow air control?
        # Standard: Allow some air control
        if self.invincible < 75: # Disable input briefly after hit
            if keys[pygame.K_LEFT]:
                target_speed = -self.max_speed
                self.facing_right = False
            elif keys[pygame.K_RIGHT]:
                target_speed = self.max_speed
                self.facing_right = True
            
        # Ground Pound Logic
        if not self.on_ground and keys[pygame.K_DOWN] and not self.ground_pound and not self.wall_slide:
            self.ground_pound = True
            self.dy = 12.0  # Instant fast fall
            self.dx = 0     # Halt momentum
            
        if self.ground_pound:
            self.dx = 0 # Lock horizontal movement
        else:
            # Acceleration / Deceleration
            if target_speed != 0:
                # Accelerate
                accel = ACCELERATION if self.on_ground else AIR_CONTROL
                if self.dx < target_speed:
                    self.dx = min(self.dx + accel, target_speed)
                elif self.dx > target_speed:
                    self.dx = max(self.dx - accel, target_speed)
            else:
                # Friction
                friction = FRICTION if self.on_ground else 0.05
                if self.dx > 0: self.dx = max(0, self.dx - friction)
                elif self.dx < 0: self.dx = min(0, self.dx + friction)

        # --- Jumping Logic (Triple & Wall) ---
        if (keys[pygame.K_z] or keys[pygame.K_SPACE]) and self.invincible < 75:
            if not self.can_jump: # Pressed just now
                if self.wall_slide:
                    # Wall Jump
                    self.dy = WALL_JUMP_KICK_Y
                    self.dx = WALL_JUMP_KICK_X if not self.facing_right else -WALL_JUMP_KICK_X
                    self.facing_right = not self.facing_right
                    self.wall_slide = False
                    self.jump_combo = 0
                    sounds['jump2'].play()
                    self.can_jump = True
                    
                elif self.on_ground:
                    # Ground Jump
                    if self.jump_combo == 0:
                        self.dy = JUMP_POWER
                        sounds['jump'].play()
                    elif self.jump_combo == 1:
                        self.dy = JUMP_POWER_DOUBLE
                        sounds['jump2'].play()
                    elif self.jump_combo == 2:
                        self.dy = JUMP_POWER_TRIPLE
                        sounds['jump3'].play()
                    
                    self.jump_combo = (self.jump_combo + 1) % 3
                    self.jump_combo_timer = 45 # Time to land and jump again
                    
                    self.on_ground = False
                    self.can_jump = True
                    self.jump_timer = 0
            
            elif self.can_jump and self.jump_timer < self.max_jump_time and not self.wall_slide:
                # Variable jump height
                self.dy -= 0.2
                self.jump_timer += 1
        else:
            self.can_jump = False
            
        # Gravity
        self.dy += GRAVITY
        if self.dy > MAX_FALL: self.dy = MAX_FALL
            
        # X Movement & Collision
        self.true_x += self.dx
        self.rect.x = int(self.true_x)
        self.check_collision(blocks, 'x')
        
        # Wall Slide Detection
        self.wall_slide = False
        if not self.on_ground and self.dy > 0: # Falling
            self.rect.x += 2 # Peek right
            wall_right = pygame.sprite.spritecollideany(self, blocks)
            self.rect.x -= 4 # Peek left
            wall_left = pygame.sprite.spritecollideany(self, blocks)
            self.rect.x += 2 # Reset
            
            # Must press into wall to slide
            if (wall_left and keys[pygame.K_LEFT]) or (wall_right and keys[pygame.K_RIGHT]):
                self.wall_slide = True
                if self.dy > WALL_SLIDE_SPEED:
                    self.dy = WALL_SLIDE_SPEED
                self.ground_pound = False # Cancel GP if hitting wall

        # Y Movement & Collision
        self.true_y += self.dy
        self.rect.y = int(self.true_y)
        self.on_ground = False
        self.check_collision(blocks, 'y')
        
        # Ground Pound Landing
        if self.on_ground and self.ground_pound:
            self.ground_pound = False
            sounds['thud'].play()
            self.jump_combo = 0 # Reset combo on pound
        
        # Pixel-perfect ground snap
        if not self.on_ground and self.dy >= 0:
            self.rect.y += 1
            hit = False
            for block in blocks:
                if block.type not in ['F', 'O', 'T'] and self.rect.colliderect(block.rect):
                    hit = True
                    break
            self.rect.y -= 1
            if hit:
                self.on_ground = True
                self.dy = 0
                self.true_y = float(self.rect.y)
        
        # Powerup Collisions
        for p in powerups:
            if self.rect.colliderect(p.rect):
                p.kill()
                self.grow()
                self.score += 1000

        # Enemy collisions
        for e in enemies:
            if e.dead: continue
            if self.rect.colliderect(e.rect):
                # Standard Stomp or Ground Pound
                # Check if Mario is effectively "above" the enemy
                if (self.dy > 0 and self.rect.bottom < e.rect.centery + 10) or self.ground_pound:
                    e.die()
                    self.dy = BOUNCE_SPEED
                    self.score += 100
                    sounds['stomp'].play()
                    self.ground_pound = False
                elif self.invincible == 0:
                    # Take Damage Logic
                    self.lives -= 1
                    if self.lives <= 0:
                        self.die()
                    else:
                        sounds['thud'].play()
                        self.invincible = 90 # 1.5 seconds i-frames
                        
                        # Knockback Physics
                        self.dy = -4 # Pop up
                        # Knock away from enemy center
                        if e.rect.centerx > self.rect.centerx:
                            self.dx = -5
                        else:
                            self.dx = 5
                        
                        # Apply immediate push to prevent sticking
                        self.true_x += self.dx
                        self.rect.x = int(self.true_x)
                        self.on_ground = False
                        
                        # Optional: Shrink if big (classic mechanics mixed with health)
                        # We will keep size but just lose HP to follow the "HP" request strictly,
                        # but shrinking adds good feedback. Let's toggle shrink but not die.
                        if self.is_big:
                            self.shrink(force=False)
                    
        for coin in coins:
            if self.rect.colliderect(coin.rect):
                coin.collect()
                self.coins += 1
                self.score += 200
                if self.coins % 100 == 0:
                    self.lives = min(self.lives + 1, self.max_hp)
                    
        self.animation_timer += 1
        if self.is_big:
            # Simple big animation toggle
            if self.wall_slide: self.image = assets['big_mario_idle']
            elif self.on_ground:
                if abs(self.dx) > 0.1:
                    self.image = assets['big_mario_idle']
                else:
                    self.image = assets['big_mario_idle']
            else:
                self.image = assets['big_mario_idle']
        else:
            if self.wall_slide:
                self.image = assets['mario_walk1'] # Use a frame that looks like sliding
            elif self.on_ground:
                is_moving_input = keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]
                if abs(self.dx) > 0.1 or is_moving_input:
                    if self.animation_timer % 6 == 0:
                        self.walk_frame = (self.walk_frame + 1) % 3
                    if self.walk_frame == 0: self.image = assets['mario_walk1']
                    elif self.walk_frame == 1: self.image = assets['mario_walk2']
                    else: self.image = assets['mario_walk3']
                else:
                    self.image = assets['mario_idle']
                    self.walk_frame = 0
            else:
                self.image = assets['mario_jump']
            
        if not self.facing_right:
            self.image = pygame.transform.flip(self.image, True, False)
            
        if self.rect.top > SCREEN_H:
            self.lives = 0 # Force death if pit
            self.die()
            
        for block in blocks:
            # STAR / FLAG COLLISION
            if (block.type == 'O' or block.type == 'S') and self.rect.colliderect(block.rect) and not self.win:
                self.win = True; self.dx = 0; self.dy = 0; self.rect.right = block.rect.left
                self.score += 5000; self.stars += 1; sounds['stage_clear'].play()
                
    def check_collision(self, blocks, axis):
        for block in blocks:
            if self.rect.colliderect(block.rect):
                if block.type in ['F', 'O', 'T', 'S']: continue
                if axis == 'x':
                    if self.dx > 0: self.rect.right = block.rect.left
                    elif self.dx < 0: self.rect.left = block.rect.right
                    self.dx = 0
                    self.true_x = float(self.rect.x)
                elif axis == 'y':
                    if self.dy > 0: 
                        self.rect.bottom = block.rect.top
                        self.on_ground = True
                        self.dy = 0
                    elif self.dy < 0: 
                        self.rect.top = block.rect.bottom
                        self.dy = 0
                        spawn_item = block.hit()
                        if spawn_item:
                            return spawn_item # Signal to main loop to spawn
                    self.true_y = float(self.rect.y)
        return None

    def die(self):
        if not self.dead:
            self.dead = True
            self.dy = -6
            sounds['die'].play()

class Enemy(Entity):
    def __init__(self, x, y, surf=None):
        if surf is None: surf = assets['goomba']
        super().__init__(x, y, surf)
        self.dx = -0.5
        self.dead = False
        self.timer = 0
        self.squish_height = 8

    def update(self, blocks):
        if self.dead:
            self.timer += 1
            if self.timer > 30: self.kill()
            return
        self.dy += GRAVITY
        self.true_x += self.dx
        self.rect.x = int(self.true_x)
        for b in blocks:
            if b.type in ['F', 'O', 'T', 'S']: continue
            if self.rect.colliderect(b.rect):
                if self.dx > 0: self.rect.right = b.rect.left
                elif self.dx < 0: self.rect.left = b.rect.right
                self.dx *= -1
                self.true_x = float(self.rect.x)
        self.true_y += self.dy
        self.rect.y = int(self.true_y)
        for b in blocks:
            if b.type in ['F', 'O', 'T', 'S']: continue
            if self.rect.colliderect(b.rect):
                if self.dy > 0:
                    self.rect.bottom = b.rect.top
                    self.dy = 0
                    self.true_y = float(self.rect.y)
        if self.rect.y > SCREEN_H: self.kill()

    def die(self):
        self.dead = True
        self.image = pygame.transform.scale(self.image, (16, self.squish_height))
        self.rect = self.image.get_rect(center=self.rect.center)
        self.rect.bottom += 4

class Koopa(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, assets['koopa'])
        self.shell = False
    
    def die(self):
        if not self.shell:
            self.shell = True
            # Become shell
            self.image = pygame.transform.scale(assets['koopa'], (16, 12))
            self.rect = self.image.get_rect(center=self.rect.center)
            self.rect.bottom += 6
            self.dx = 0
            sounds['stomp'].play()
        else:
            # Kick logic could go here or in collision
            if self.dx == 0:
                self.dx = 3.0
                sounds['kick'].play()
            else:
                self.dx = 0

class Piranha(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, assets['piranha'])
        self.orig_y = y
        self.dy = -0.5
        self.timer = 0
        self.state = 'up'
    
    def update(self, blocks):
        self.timer += 1
        if self.state == 'up':
            self.rect.y += self.dy
            if self.rect.bottom < self.orig_y - 24:
                self.state = 'wait_top'
                self.timer = 0
        elif self.state == 'wait_top':
            if self.timer > 60:
                self.state = 'down'
        elif self.state == 'down':
            self.rect.y -= self.dy
            if self.rect.y > self.orig_y:
                self.state = 'wait_bot'
                self.timer = 0
        elif self.state == 'wait_bot':
            if self.timer > 60:
                self.state = 'up'
    
    def die(self):
        pass # Invincible to stomp

class Powerup(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, assets['mushroom'])
        self.dx = 1.0
        sounds['powerup_appear'].play()
        
    def update(self, blocks):
        self.dy += GRAVITY
        self.true_x += self.dx
        self.rect.x = int(self.true_x)
        for b in blocks:
            if b.type in ['F', 'O', 'T']: continue
            if self.rect.colliderect(b.rect):
                self.dx *= -1
                self.true_x = float(self.rect.x)
        self.true_y += self.dy
        self.rect.y = int(self.true_y)
        for b in blocks:
            if b.type in ['F', 'O', 'T']: continue
            if self.rect.colliderect(b.rect):
                if self.dy > 0:
                    self.rect.bottom = b.rect.top
                    self.dy = 0
                    self.true_y = float(self.rect.y)

class Block(pygame.sprite.Sprite):
    def __init__(self, x, y, type_char):
        super().__init__()
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.type = type_char
        if type_char == 'G': self.image = assets['floor']
        elif type_char == 'B': self.image = assets['brick']
        elif type_char == '?': self.image = assets['qblock']
        elif type_char == 'H': self.image = assets['hard']
        elif type_char == 'P': self.image = assets['pipe']
        elif type_char == 'F': self.image = assets['flag_cloth']
        elif type_char == 'O': self.image = assets['flag_pole']
        elif type_char == 'T': self.image = assets['flag_ball']
        elif type_char == 'S': self.image = assets['star'] # End Star
        else: self.image = assets['floor']
        self.orig_y = y
        self.bouncing = 0
        self.used = False

    def hit(self):
        spawn = None
        if (self.type == '?' or self.type == 'B') and not self.used:
            self.used = True
            self.bouncing = 5
            if self.type == '?':
                sounds['coin'].play()
                self.type = 'H'
                self.image = assets['hard']
                # Chance to spawn mushroom
                if random.random() < 0.3:
                    spawn = 'mushroom'
            else:
                sounds['break'].play()
                self.kill()
        return spawn

    def update(self):
        if self.bouncing > 0:
            self.rect.y -= 2
            self.bouncing -= 1
        elif self.rect.y < self.orig_y:
            self.rect.y += 2

class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = assets['coin']
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.collected = False
        self.timer = 0
    def update(self):
        if self.collected:
            self.timer += 1
            if self.timer > 10: self.kill()
    def collect(self):
        if not self.collected:
            self.collected = True
            sounds['coin'].play()

class BackgroundObject:
    def __init__(self, x, y, type_obj):
        self.x = x
        self.y = y
        self.type = type_obj
        if type_obj == 'cloud': self.image = assets['cloud']
        else: self.image = assets['bush']
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

# --- Map System ---
class MapNode:
    def __init__(self, x, y, world, stage, name):
        self.rect = pygame.Rect(x - 8, y - 8, 16, 16)
        self.x = x
        self.y = y
        self.world = world
        self.stage = stage
        self.name = name
        self.paths = []

class Overworld:
    def __init__(self):
        self.nodes = []
        self.create_nodes()
        self.current_node = self.nodes[0]
        self.mario_rect = pygame.Rect(0, 0, 16, 16)
        self.mario_rect.center = (self.current_node.x, self.current_node.y)
        self.target_node = None
        self.moving = False
        self.speed = 4
        
    def create_nodes(self):
        # Pseudo-3D Layout: Zig-zagging up the screen "Rainbow Road" style
        n1 = MapNode(WINDOW_W//2, 600, 1, 1, "Start")
        n2 = MapNode(WINDOW_W//2 + 100, 500, 1, 2, "Cave")
        n3 = MapNode(WINDOW_W//2 - 100, 400, 1, 3, "Hills")
        n4 = MapNode(WINDOW_W//2, 300, 1, 4, "Castle")
        
        n1.paths = [n2]
        n2.paths = [n1, n3]
        n3.paths = [n2, n4]
        n4.paths = [n3]
        
        self.nodes = [n1, n2, n3, n4]
        
    def update(self):
        if self.moving and self.target_node:
            # Move towards target
            tx, ty = self.target_node.x, self.target_node.y
            mx, my = self.mario_rect.centerx, self.mario_rect.centery
            
            dx = tx - mx
            dy = ty - my
            dist = math.hypot(dx, dy)
            
            if dist < self.speed:
                self.mario_rect.center = (tx, ty)
                self.current_node = self.target_node
                self.target_node = None
                self.moving = False
            else:
                angle = math.atan2(dy, dx)
                self.mario_rect.centerx += math.cos(angle) * self.speed
                self.mario_rect.centery += math.sin(angle) * self.speed

    def draw(self, screen):
        # Draw "3D" Horizon
        screen.fill(SKY)
        pygame.draw.rect(screen, MAP_GREEN, (0, WINDOW_H//2, WINDOW_W, WINDOW_H//2))
        
        # Draw checkerboard pattern for pseudo-3D
        for y in range(WINDOW_H//2, WINDOW_H, 40):
            for x in range(0, WINDOW_W, 40):
                if (x + y) % 80 == 0:
                    offset = (y - WINDOW_H//2) * 0.5 # Perspective spread
                    rect = pygame.Rect(x - offset, y, 40 + offset, 40)
                    pygame.draw.rect(screen, (0, 150, 0), rect)

        # Draw Paths
        for node in self.nodes:
            for next_node in node.paths:
                pygame.draw.line(screen, MAP_PATH, (node.x, node.y), (next_node.x, next_node.y), 4)

        # Draw Nodes
        for node in self.nodes:
            color = RED if node == self.current_node else YELLOW
            pygame.draw.circle(screen, BLACK, (node.x, node.y), 12)
            pygame.draw.circle(screen, color, (node.x, node.y), 10)
            
            # Label
            font = pygame.font.Font(None, 24)
            text = font.render(f"{node.world}-{node.stage}", True, WHITE)
            screen.blit(text, (node.x - 15, node.y - 30))

        # Draw Mario
        screen.blit(assets['mario_idle'], self.mario_rect)

# --- Level Data & Generator ---
# Level themes: 'overworld', 'underground', 'athletic', 'castle'
LEVEL_THEMES = {
    (1,1): 'overworld', (1,2): 'underground', (1,3): 'athletic', (1,4): 'castle',
    (2,1): 'overworld', (2,2): 'underground', (2,3): 'athletic', (2,4): 'castle',
    (3,1): 'overworld', (3,2): 'underground', (3,3): 'athletic', (3,4): 'castle',
    (4,1): 'overworld', (4,2): 'underground', (4,3): 'athletic', (4,4): 'castle',
    (5,1): 'overworld', (5,2): 'underground', (5,3): 'athletic', (5,4): 'castle',
    (6,1): 'overworld', (6,2): 'underground', (6,3): 'athletic', (6,4): 'castle',
    (7,1): 'overworld', (7,2): 'underground', (7,3): 'athletic', (7,4): 'castle',
    (8,1): 'overworld', (8,2): 'underground', (8,3): 'athletic', (8,4): 'castle',
}

def get_theme_colors(theme):
    if theme == 'overworld': return SKY, GREEN, BROWN
    elif theme == 'underground': return CAVE_BG, GRAY, DKBROWN
    elif theme == 'athletic': return SKY, GREEN, ORANGE
    elif theme == 'castle': return BLACK, GRAY, RED
    return SKY, GREEN, BROWN

def generate_level(world, stage):
    level_seed = world * 100 + stage
    random.seed(level_seed)
    
    theme = LEVEL_THEMES.get((world, stage), 'overworld')
    bg_color, ground_tint, block_tint = get_theme_colors(theme)
    
    grid = [['.' for _ in range(210)] for _ in range(15)]
    enemy_positions = []
    
    # World 1-1: Classic SMB1 layout (1:1 accurate)
    if world == 1 and stage == 1:
        # Floor with authentic gaps
        for x in range(210):
            if not (69 <= x <= 70 or 86 <= x <= 88 or 153 <= x <= 154):
                grid[13][x] = 'G'; grid[14][x] = 'G'
        # ? Blocks
        for x in [16, 21, 23, 78, 94, 106, 109, 112, 129, 130, 170]: grid[9][x] = '?'
        grid[5][22] = '?'  # Hidden mushroom block
        # Bricks
        for x in [20, 22, 24, 77, 79, 80, 100, 118, 121, 122, 123, 128, 129, 130, 131, 168, 169, 171]:
            if grid[9][x] == '.': grid[9][x] = 'B'
        for i in range(80, 88): grid[5][i] = 'B'
        for i in range(91, 94): grid[5][i] = 'B'
        # Pipes
        for x, h in [(28,2), (38,3), (46,4), (57,4), (163,2), (179,2)]:
            for y in range(13-h, 13): grid[y][x] = 'P'; grid[y][x+1] = 'P'
        # Stairs at end
        for i in range(8):
            for j in range(i+1): grid[12-i][181+j] = 'H'
        enemy_positions = [22, 40, 51, 53, 80, 82, 97, 99, 114, 116, 124, 126, 174, 176]
        
    # World 1-2: Underground
    elif world == 1 and stage == 2:
        for x in range(210): grid[13][x] = 'G'; grid[14][x] = 'G'
        for x in range(210): grid[0][x] = 'H'; grid[1][x] = 'H'  # Ceiling
        for x in [25, 30, 35, 45, 55, 65, 80, 95, 110, 130, 150, 165]: grid[9][x] = '?'
        for x in range(40, 50): grid[9][x] = 'B'
        for x in range(70, 80): grid[5][x] = 'B'
        for x in range(100, 115): grid[9][x] = 'B'
        for x, h in [(60, 3), (90, 2), (140, 4)]:
            for y in range(13-h, 13): grid[y][x] = 'P'; grid[y][x+1] = 'P'
        enemy_positions = [28, 42, 58, 75, 88, 105, 125, 145, 160, 175]
        
    # World 1-3: Athletic (platforms)
    elif world == 1 and stage == 3:
        for x in range(0, 20): grid[13][x] = 'G'; grid[14][x] = 'G'
        for x in range(185, 210): grid[13][x] = 'G'; grid[14][x] = 'G'
        # Floating platforms
        for start, length, row in [(25, 8, 10), (40, 6, 8), (55, 10, 11), (75, 5, 7),
                                   (90, 8, 9), (110, 6, 10), (130, 10, 8), (155, 8, 11)]:
            for x in range(start, start+length): grid[row][x] = 'B'
        for x in [30, 60, 95, 135, 160]: grid[6][x] = '?'
        enemy_positions = [28, 58, 78, 115, 138, 162]
        
    # World 1-4: Castle & GOOMBERT BOSS
    elif world == 1 and stage == 4:
        for x in range(210): grid[13][x] = 'G'; grid[14][x] = 'G'
        for x in range(210): grid[0][x] = 'H'; grid[1][x] = 'H'
        # Lava pits
        for x in range(50, 55): grid[13][x] = '.'; grid[14][x] = '.'
        for x in range(80, 88): grid[13][x] = '.'; grid[14][x] = '.'
        for x in range(120, 126): grid[13][x] = '.'; grid[14][x] = '.'
        # Platforms over lava
        for x in range(51, 54): grid[11][x] = 'H'
        for x in range(82, 86): grid[10][x] = 'H'
        for x in range(121, 125): grid[11][x] = 'H'
        enemy_positions = [30, 45, 65, 95, 110, 140, 160, 175]
        
    # Worlds 2-8: Procedural with increasing difficulty
    else:
        difficulty = world + (stage - 1) * 0.25
        gap_count = int(2 + difficulty)
        enemy_count = int(8 + difficulty * 2)
        pipe_count = int(3 + world // 2)
        block_count = int(10 + difficulty * 2)
        
        # Base floor
        for x in range(210): grid[13][x] = 'G'; grid[14][x] = 'G'
        
        # Add ceiling for underground/castle
        if theme in ['underground', 'castle']:
            for x in range(210): grid[0][x] = 'H'; grid[1][x] = 'H'
        
        # Gaps
        gap_positions = sorted(random.sample(range(40, 170, 10), min(gap_count, 12)))
        for gx in gap_positions:
            gap_width = random.randint(2, 3 + world // 3)
            for x in range(gx, min(gx + gap_width, 170)):
                grid[13][x] = '.'; grid[14][x] = '.'
        
        # Pipes
        pipe_xs = sorted(random.sample(range(25, 175, 12), min(pipe_count, 10)))
        for px in pipe_xs:
            if grid[13][px] == 'G' and grid[13][px+1] == 'G':
                h = random.randint(2, 4)
                for y in range(13-h, 13): grid[y][px] = 'P'; grid[y][px+1] = 'P'
        
        # ? Blocks
        q_xs = random.sample(range(20, 180), min(block_count, 15))
        for qx in q_xs:
            row = random.choice([5, 9]) if theme != 'athletic' else random.randint(5, 10)
            if grid[row][qx] == '.': grid[row][qx] = '?'
        
        # Brick blocks
        for _ in range(block_count):
            bx = random.randint(20, 180)
            row = random.choice([5, 9])
            if grid[row][bx] == '.': grid[row][bx] = 'B'
        
        # Brick platforms for athletic
        if theme == 'athletic':
            for x in range(0, 25): grid[13][x] = 'G'; grid[14][x] = 'G'
            for x in range(180, 210): grid[13][x] = 'G'; grid[14][x] = 'G'
            for _ in range(6 + world):
                px = random.randint(30, 170)
                py = random.randint(6, 11)
                plen = random.randint(4, 10)
                for x in range(px, min(px + plen, 175)):
                    if grid[py][x] == '.': grid[py][x] = 'B'
        
        # Stairs near end
        for i in range(min(8, 4 + world)):
            for j in range(i + 1): grid[12-i][175+j] = 'H'
        
        # Enemies
        for _ in range(enemy_count):
            ex = random.randint(25, 185)
            if any(grid[13][ex] == 'G' for _ in [1]) or theme == 'athletic':
                enemy_positions.append(ex)
    
    # Flag pole (always at end) - Except Boss
    if True: # Modified: Always generate flag, even for stage 4
        grid[12][198] = 'H'
        for y in range(2, 12): grid[y][198] = 'O'
        grid[1][198] = 'T'
        for x in range(196, 198):
            for y in range(2, 4): grid[y][x] = 'F'
    
    # Coins
    coin_positions = []
    for x in range(25, 180, 8):
        if random.random() < 0.3:
            coin_positions.append((x, random.choice([4, 5, 8, 9])))
    
    # Background objects
    bg_objects = []
    if theme == 'overworld' or theme == 'athletic':
        for i in range(8):
            bx = i * 30 * TILE_SIZE + random.randint(0, 100)
            by = random.randint(50, 120)
            bg_objects.append(BackgroundObject(bx, by, 'cloud'))
        for i in range(5):
            bx = i * 45 * TILE_SIZE + random.randint(0, 150)
            bg_objects.append(BackgroundObject(bx, 11 * TILE_SIZE, 'bush'))
    
    return grid, enemy_positions, coin_positions, bg_objects, bg_color

# --- UI Functions ---

def draw_main_menu(screen, selection, menu_options, in_submenu, submenu_title, submenu_lines):
    screen.fill(SKY)
    font_large = pygame.font.Font(None, 64)
    font_med = pygame.font.Font(None, 48)
    font_small = pygame.font.Font(None, 32)
    cx = WINDOW_W // 2
    
    if in_submenu:
        title = font_large.render(submenu_title, True, YELLOW)
        screen.blit(title, (cx - title.get_width() // 2, 100))
        for i, line in enumerate(submenu_lines):
            line_surf = font_small.render(line, True, WHITE)
            screen.blit(line_surf, (cx - line_surf.get_width() // 2, 250 + i * 40))
        back_text = font_small.render("PRESS ESC TO BACK", True, RED)
        screen.blit(back_text, (cx - back_text.get_width() // 2, WINDOW_H - 100))
    else:
        cy = WINDOW_H // 3
        title_text = font_large.render("ULTRA MARIO", True, RED)
        title_text2 = font_large.render("2D BROS", True, RED)
        title_shadow = font_large.render("ULTRA MARIO", True, BLACK)
        title_shadow2 = font_large.render("2D BROS", True, BLACK)
        screen.blit(title_shadow, (cx - title_text.get_width() // 2 + 4, cy - 80 + 4))
        screen.blit(title_text, (cx - title_text.get_width() // 2, cy - 80))
        screen.blit(title_shadow2, (cx - title_text2.get_width() // 2 + 4, cy - 20 + 4))
        screen.blit(title_text2, (cx - title_text2.get_width() // 2, cy - 20))
        
        for i, option in enumerate(menu_options):
            color = WHITE
            prefix = ""
            if i == selection:
                color = YELLOW
                prefix = "> "
            opt_text = font_med.render(prefix + option, True, color)
            shadow_text = font_med.render(prefix + option, True, BLACK)
            screen.blit(shadow_text, (cx - opt_text.get_width() // 2 + 2, cy + 100 + i * 50 + 2))
            screen.blit(opt_text, (cx - opt_text.get_width() // 2, cy + 100 + i * 50))
        copy_text = font_small.render("(C) 2026 NINTENDO CLONE", True, WHITE)
        screen.blit(copy_text, (cx - copy_text.get_width() // 2, WINDOW_H - 50))

def draw_hud(screen, player, camera):
    font = pygame.font.Font(None, 32)
    shadow_offset = 2
    def draw_text_with_shadow(text, x, y, color=WHITE):
        shadow = font.render(text, True, BLACK)
        surface = font.render(text, True, color)
        screen.blit(shadow, (x + shadow_offset, y + shadow_offset))
        screen.blit(surface, (x, y))

    # SM63 Style Circular Power Meter (Top Center)
    center_x = WINDOW_W // 2
    center_y = 50
    radius = 30
    s = pygame.Surface((radius*2 + 4, radius*2 + 4), pygame.SRCALPHA)
    pygame.draw.circle(s, (0, 0, 0, 128), (radius+2, radius+2), radius)
    screen.blit(s, (center_x - radius - 2, center_y - radius - 2))
    
    max_lives = 8
    current_lives = min(player.lives, max_lives)
    for i in range(max_lives):
        start_angle = math.radians(i * (360/max_lives) - 90)
        end_angle = math.radians((i + 1) * (360/max_lives) - 90)
        color = (255, 0, 0) if player.lives == 1 else HUD_YELLOW
        if i >= current_lives: color = (100, 100, 100)
        p1 = (center_x, center_y)
        p2 = (center_x + math.cos(start_angle) * radius, center_y + math.sin(start_angle) * radius)
        p3 = (center_x + math.cos(end_angle) * radius, center_y + math.sin(end_angle) * radius)
        pygame.draw.polygon(screen, color, [p1, p2, p3])
        pygame.draw.line(screen, BLACK, p1, p2, 2)
        
    pygame.draw.circle(screen, BLACK, (center_x, center_y), radius, 2)
    # Centered "POW" text
    pow_text = "POW"
    text_w, text_h = font.size(pow_text)
    draw_text_with_shadow(pow_text, center_x - text_w // 2, center_y + 35)
    
    # Coin Counter (Bottom Right)
    coin_img = pygame.transform.scale(assets['coin'], (24, 24))
    screen.blit(coin_img, (WINDOW_W - 100, WINDOW_H - 40))
    draw_text_with_shadow(f"x {player.coins:02d}", WINDOW_W - 70, WINDOW_H - 36, HUD_YELLOW)

    # Star Counter (Top Right - SMBX Style)
    draw_text_with_shadow(f"STARS x {player.stars:02d}", WINDOW_W - 150, 24, HUD_YELLOW)

    # Score (Top Left)
    draw_text_with_shadow(f"SCORE: {player.score:06d}", 20, 24)
    draw_text_with_shadow(f"WORLD {player.world}-{player.stage}", 20, 54)

def draw_game_over(screen, player):
    font_large = pygame.font.Font(None, 48)
    font_small = pygame.font.Font(None, 32)
    game_over_text = font_large.render("GAME OVER", True, RED)
    score_text = font_small.render(f"FINAL SCORE: {player.score:06d}", True, WHITE)
    restart_text = font_small.render("PRESS R TO RETURN TO MENU", True, YELLOW)
    cx, cy = WINDOW_W // 2, WINDOW_H // 2
    screen.blit(game_over_text, (cx - game_over_text.get_width() // 2, cy - 50))
    screen.blit(score_text, (cx - score_text.get_width() // 2, cy))
    screen.blit(restart_text, (cx - restart_text.get_width() // 2, cy + 50))

def draw_win_screen(screen, player):
    font_large = pygame.font.Font(None, 48)
    font_small = pygame.font.Font(None, 32)
    win_text = font_large.render("COURSE CLEAR!", True, GREEN)
    score_text = font_small.render(f"SCORE: {player.score:06d}", True, WHITE)
    next_text = font_small.render("NEXT LEVEL...", True, YELLOW)
    cx, cy = WINDOW_W // 2, WINDOW_H // 2
    screen.blit(win_text, (cx - win_text.get_width() // 2, cy - 50))
    screen.blit(score_text, (cx - score_text.get_width() // 2, cy))
    screen.blit(next_text, (cx - next_text.get_width() // 2, cy + 50))

# --- Main Game Loop ---

def main():
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Ultra Mario 2D Bros")
    clock = pygame.time.Clock()
    display = pygame.Surface((SCREEN_W, SCREEN_H))

    init_sounds()
    init_assets()
    
    current_world = 1
    current_stage = 1
    
    def reset_game(world, stage, existing_player=None):
        grid, enemy_positions, coin_positions, bg_objects, bg_color = generate_level(world, stage)
        all_sprites = pygame.sprite.Group()
        blocks = pygame.sprite.Group()
        enemies = pygame.sprite.Group()
        coins_group = pygame.sprite.Group()
        powerups = pygame.sprite.Group()

        for y in range(15):
            for x in range(210):
                char = grid[y][x]
                if char != '.':
                    b = Block(x * TILE_SIZE, y * TILE_SIZE, char)
                    blocks.add(b)
                    all_sprites.add(b)

        for ex in enemy_positions:
            e_type = random.choice(['goomba', 'goomba', 'koopa']) # Simple weight
            if e_type == 'goomba': e = Enemy(ex * TILE_SIZE, 10 * TILE_SIZE)
            else: e = Koopa(ex * TILE_SIZE, 10 * TILE_SIZE)
            enemies.add(e)
            all_sprites.add(e)
            
        for cx, cy in coin_positions:
            coin = Coin(cx * TILE_SIZE, cy * TILE_SIZE)
            coins_group.add(coin)
            all_sprites.add(coin)
            
        if existing_player:
            player = existing_player
            player.rect.x = 100; player.rect.y = 100
            player.true_x = 100.0; player.true_y = 100.0
            player.dx = 0; player.dy = 0
            player.win = False; player.win_timer = 0
        else:
            player = Player(100, 100)
            
        player.world = world; player.stage = stage
        all_sprites.add(player)
        camera = Camera(210 * TILE_SIZE, SCREEN_H)
        
        return all_sprites, blocks, enemies, coins_group, powerups, player, camera, bg_objects, bg_color
    
    all_sprites = None
    blocks = None
    enemies = None
    coins_group = None
    powerups = None
    player = None
    camera = None
    bg_objects = None
    bg_color = SKY
    
    paused = False
    running = True
    game_state = "menu"
    overworld = Overworld() # Initialize Map
    menu_options = ["PLAY GAME", "HOW TO PLAY", "CREDITS", "ABOUT", "EXIT GAME"]
    selected_option = 0
    in_submenu = False
    submenu_title = ""
    submenu_lines = []
    
    while running:
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.KEYDOWN:
                if game_state == "menu":
                    if not in_submenu:
                        if event.key == pygame.K_UP: selected_option = (selected_option - 1) % len(menu_options)
                        elif event.key == pygame.K_DOWN: selected_option = (selected_option + 1) % len(menu_options)
                        elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                            if selected_option == 0:
                                game_state = "overworld" # Go to map first
                            elif selected_option == 1:
                                in_submenu = True; submenu_title = "HOW TO PLAY"
                                submenu_lines = ["ARROWS: Move", "Z / SPACE: Jump", "X / SHIFT: Run", "ESC: Pause", "Goal: Touch the Flag!"]
                            elif selected_option == 2:
                                in_submenu = True; submenu_title = "CREDITS"
                                submenu_lines = ["Nintendo Team (Original)", "Catsan & Mr.Samsoft", "Assets: SMB1 (NES)"]
                            elif selected_option == 3:
                                in_submenu = True; submenu_title = "ABOUT"
                                submenu_lines = ["Ultra Mario 2D Bros", "A fan-made engine test", "written in Python/Pygame."]
                            elif selected_option == 4: running = False
                    else:
                        if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN: in_submenu = False
                
                elif game_state == "overworld":
                    if not overworld.moving:
                        target = None
                        if event.key == pygame.K_UP:
                            # Simple logic: Find node with lower Y
                            for n in overworld.current_node.paths: 
                                if n.y < overworld.current_node.y: target = n
                        elif event.key == pygame.K_DOWN:
                            for n in overworld.current_node.paths: 
                                if n.y > overworld.current_node.y: target = n
                        elif event.key == pygame.K_LEFT:
                            for n in overworld.current_node.paths: 
                                if n.x < overworld.current_node.x: target = n
                        elif event.key == pygame.K_RIGHT:
                            for n in overworld.current_node.paths: 
                                if n.x > overworld.current_node.x: target = n
                        elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                            # Enter Level
                            current_world = overworld.current_node.world
                            current_stage = overworld.current_node.stage
                            all_sprites, blocks, enemies, coins_group, powerups, player, camera, bg_objects, bg_color = reset_game(current_world, current_stage, player)
                            game_state = "playing"
                            
                        if target:
                            overworld.target_node = target
                            overworld.moving = True
                            sounds['map_move'].play()

                elif game_state == "playing":
                    if event.key == pygame.K_ESCAPE:
                        paused = not paused
                        if paused: sounds['pause'].play()
                elif game_state == "game_over":
                     if event.key == pygame.K_r: game_state = "menu"

        if game_state == "menu":
             draw_main_menu(screen, selected_option, menu_options, in_submenu, submenu_title, submenu_lines)
             pygame.display.flip(); clock.tick(FPS); continue

        if game_state == "overworld":
            overworld.update()
            overworld.draw(screen)
            pygame.display.flip(); clock.tick(FPS); continue

        if paused:
            display.fill(bg_color)
            for sprite in all_sprites: display.blit(sprite.image, camera.apply(sprite))
            pygame.transform.scale(display, (WINDOW_W, WINDOW_H), screen)
            s = pygame.Surface((WINDOW_W, WINDOW_H)); s.set_alpha(128); s.fill(BLACK); screen.blit(s, (0,0))
            font = pygame.font.Font(None, 72)
            pause_text = font.render("PAUSED", True, WHITE)
            screen.blit(pause_text, (WINDOW_W // 2 - pause_text.get_width() // 2, WINDOW_H // 2 - pause_text.get_height() // 2))
            pygame.display.flip(); clock.tick(FPS); continue
        
        if game_state == "playing":
            spawn_item = None
            
            # Capture collision return val
            collision_result = player.check_collision(blocks, 'y') 
            if collision_result == 'mushroom':
                # Spawn mushroom above player
                mx = player.rect.centerx
                my = player.rect.top - 16
                p = Powerup(mx, my)
                powerups.add(p)
                all_sprites.add(p)

            player.update(keys, blocks, enemies, coins_group, powerups)
            camera.update(player)
            
            for e in enemies:
                if abs(e.rect.x - player.rect.x) < SCREEN_W: 
                    e.update(blocks)
                         
            for p in powerups: p.update(blocks)
            
            blocks.update()
            coins_group.update()
            
            if player.win and player.win_timer > 150:
                # Return to map
                game_state = "overworld"
                player.win = False
                player.win_timer = 0
                
            if player.dead and player.rect.y > SCREEN_H + 50:
                # Standard respawn or Game Over
                # Reset HP on respawn
                player.rect.x = 100
                player.rect.y = 100
                player.true_x = 100.0; player.true_y = 100.0
                player.dx = 0; player.dy = 0; player.dead = False
                player.lives = 8 # Full Health
                player.is_big = False 
                # If you want true Game Over logic:
                # if player.lives <= 0: game_state = "game_over" 
                # But since we use lives as HP, once HP hits 0 -> Dead -> Respawn with full HP (Infinite Continues)
            
            display.fill(bg_color)
            for bg_obj in bg_objects:
                bg_rect = camera.apply_rect(bg_obj.rect)
                if bg_rect.colliderect(pygame.Rect(0, 0, SCREEN_W, SCREEN_H)): display.blit(bg_obj.image, camera.apply_rect(bg_obj.rect))
            for sprite in all_sprites: display.blit(sprite.image, camera.apply(sprite))
            pygame.transform.scale(display, (WINDOW_W, WINDOW_H), screen)
            draw_hud(screen, player, camera)
            if player.win: draw_win_screen(screen, player)
            
        elif game_state == "game_over":
            pygame.transform.scale(display, (WINDOW_W, WINDOW_H), screen)
            draw_game_over(screen, player)
        
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
