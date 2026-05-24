import math
import pygame
from pygame import mixer
from pygame import font
import asyncio
import os
import sys

# Ensure src/ is on the path (for fighter module)
_src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from fighter import Fighter

# Helper Function for Bundled Assets
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        # Use the directory where this main.py file lives
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

mixer.init()
pygame.init()

# Constants
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h
FPS = 60
ROUND_OVER_COOLDOWN = 3000

# Colors
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)

# Initialize Game Window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
pygame.display.set_caption("Street Fighter")
clock = pygame.time.Clock()

# Load Assets
MAP_FILES = ["assets/images/bg.jpg", "assets/images/bg1.jpg", "assets/images/bg2.jpg"]
loaded_maps = [pygame.image.load(resource_path(m)).convert() for m in MAP_FILES]
current_map_index = 1
bg_image = loaded_maps[current_map_index]
victory_img = pygame.image.load(resource_path("assets/images/victory.png")).convert_alpha()
warrior_victory_img = pygame.image.load(resource_path("assets/images/warrior.png")).convert_alpha()
wizard_victory_img = pygame.image.load(resource_path("assets/images/wizard.png")).convert_alpha()
# Try to load ryu victory image, fallback to warrior
try:
    ryu_victory_img = pygame.image.load(resource_path("assets/images/ryu.png")).convert_alpha()
except FileNotFoundError:
    ryu_victory_img = warrior_victory_img

# Try to load goku victory image
try:
    goku_victory_img = pygame.image.load(resource_path("assets/images/goku_grid.png")).convert_alpha()
except FileNotFoundError:
    goku_victory_img = warrior_victory_img

# Fonts
menu_font = pygame.font.Font(resource_path("assets/fonts/turok.ttf"), 50)
menu_font_title = pygame.font.Font(resource_path("assets/fonts/turok.ttf"), 100)  # Larger font for title
count_font = pygame.font.Font(resource_path("assets/fonts/turok.ttf"), 80)
score_font = pygame.font.Font(resource_path("assets/fonts/turok.ttf"), 30)

# Music and Sounds
pygame.mixer.music.load(resource_path("assets/audio/music.ogg"))
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1, 0.0, 5000)
sword_fx = pygame.mixer.Sound(resource_path("assets/audio/sword.ogg"))
sword_fx.set_volume(0.5)
magic_fx = pygame.mixer.Sound(resource_path("assets/audio/magic.ogg"))
magic_fx.set_volume(0.75)
try:
    boom_fx = pygame.mixer.Sound(resource_path("assets/audio/boom.ogg"))
    boom_fx.set_volume(0.9)
except:
    boom_fx = None

# Load Fighter Spritesheets
warrior_sheet = pygame.image.load(resource_path("assets/images/warrior.png")).convert_alpha()
wizard_sheet = pygame.image.load(resource_path("assets/images/wizard.png")).convert_alpha()
try:
    ryu_sheet = pygame.image.load(resource_path("assets/images/ryu.png")).convert_alpha()
except FileNotFoundError:
    ryu_sheet = warrior_sheet
# Try to load goku sheet
try:
    goku_sheet = pygame.image.load(resource_path("assets/images/goku.png")).convert_alpha()
except FileNotFoundError:
    goku_sheet = warrior_sheet

# Load Lightning Effect
lightning_sheet = pygame.image.load(resource_path("assets/images/lightning.jpg")).convert_alpha()
# Slice lightning sheet into 7 frames
LIGHTNING_FRAMES = 7
lightning_width = lightning_sheet.get_width() // LIGHTNING_FRAMES
lightning_height = lightning_sheet.get_height()
lightning_animation_list = []
for x in range(LIGHTNING_FRAMES):
    temp_img = lightning_sheet.subsurface(x * lightning_width, 0, lightning_width, lightning_height)
    # Scale it down slightly so it's not too huge, keep aspect ratio
    temp_img = pygame.transform.scale(temp_img, (int(lightning_width * 0.8), int(lightning_height * 0.8)))
    lightning_animation_list.append(temp_img)

def remove_top_artifacts(surface):
    w, h = surface.get_size()
    gap_start = -1
    in_gap = False
    for y in range(min(h, 50)):
        row_pixels = sum(1 for x in range(w) if surface.get_at((x, y)).a > 10)
        if row_pixels == 0:
            if not in_gap:
                in_gap = True
                gap_start = y
        else:
            if in_gap:
                if gap_start > 0:
                    surface.fill((0, 0, 0, 0), pygame.Rect(0, 0, w, y))
                break

def load_sliced_effect(sprite_sheet_path, cols, rows, target_height, start_frame=0, max_frames=None):
    try:
        sheet = pygame.image.load(resource_path(sprite_sheet_path)).convert_alpha()
        w, h = sheet.get_size()
        frame_w = w // cols
        frame_h = h // rows
        anim_list = []
        frames_loaded = 0
        current_frame = 0
        for r in range(rows):
            for c in range(cols):
                if max_frames is not None and frames_loaded >= max_frames:
                    return anim_list
                if current_frame < start_frame:
                    current_frame += 1
                    continue
                rect = pygame.Rect(c * frame_w, r * frame_h, frame_w, frame_h)
                sub = sheet.subsurface(rect)
                remove_top_artifacts(sub)
                bbox = sub.get_bounding_rect()
                if bbox.width > 0:  # Skip completely empty frames
                    ratio = target_height / frame_h
                    scaled_w = int(frame_w * ratio)
                    anim_list.append(pygame.transform.scale(sub, (scaled_w, target_height)))
                    frames_loaded += 1
                current_frame += 1
        return anim_list
    except FileNotFoundError:
        return lightning_animation_list

blueboom_anim = load_sliced_effect("assets/images/blueboom.png", cols=2, rows=7, target_height=250)
blueframe_anim = load_sliced_effect("assets/images/blueframe.png", cols=4, rows=3, target_height=300, max_frames=9)
yellowflame_anim = load_sliced_effect("assets/images/yellowflame.png", cols=3, rows=8, target_height=300, start_frame=12, max_frames=6)
fire_anim = load_sliced_effect("assets/images/fire.png", cols=6, rows=4, target_height=550)

# Define Animation Steps
WARRIOR_ANIMATION_STEPS = [10, 8, 1, 7, 7, 3, 7]
WIZARD_ANIMATION_STEPS = [8, 8, 1, 8, 8, 3, 7]

# Fighter Data
WARRIOR_SIZE = 162
WARRIOR_SCALE = 4
WARRIOR_OFFSET = [72, 46]
WARRIOR_DATA = [WARRIOR_SIZE, WARRIOR_SCALE, WARRIOR_OFFSET]
WIZARD_SIZE = 250
WIZARD_SCALE = 3
WIZARD_OFFSET = [112, 97]
WIZARD_DATA = [WIZARD_SIZE, WIZARD_SCALE, WIZARD_OFFSET]

# Ryu data based on 1080x754 grid (approx 108x108 per frame)
RYU_SIZE = [108, 108]
RYU_SCALE = 3.5
RYU_OFFSET = [45, 32]
RYU_DATA = [RYU_SIZE, RYU_SCALE, RYU_OFFSET]
RYU_ANIMATION_STEPS = [8, 8, 1, 7, 7, 3, 7, 7]  # idle, walk/run, jump, attack1, attack2, hit, death, combo
RYU_ROW_MAP = [0, 1, 2, 3, 4, 5, 6, 4]

# Goku data based on new sprite sheet 60x60
GOKU_SIZE = [60, 60]
GOKU_SCALE = 3.5
GOKU_OFFSET = [18, 0]  # Lowered Y offset from 4 to 0 so Goku stands perfectly on ground
GOKU_DATA = [GOKU_SIZE, GOKU_SCALE, GOKU_OFFSET]
GOKU_ANIMATION_STEPS = [4, 8, 8, 4, 4, 4, 4, 5]  # idle, run, jump, attack1, attack2, hit, death, combo
GOKU_ROW_MAP = [0, 1, 2, 3, 3, 6, 7, 5]
GOKU_COL_MAP = [3, 0, 0, 0, 4, 0, 0, 0]

kame_rect = pygame.Rect(295, 290, 177, 58)
try:
    kame_beam_img = goku_sheet.subsurface(kame_rect)
    kame_beam_img = pygame.transform.scale(kame_beam_img, (int(177 * GOKU_SCALE), int(58 * GOKU_SCALE)))
except:
    kame_beam_img = None

# Helper function to load custom Goku animations
def load_custom_goku_animation(path, cols):
    frames = []
    try:
        sheet = pygame.image.load(resource_path(path)).convert_alpha()
        w, h = sheet.get_size()
        frame_w = w // cols
        frame_h = h
        scale = 3.5 * (50 / 115)  # Align with original 60x60 cell scale height
        for c in range(cols):
            rect = pygame.Rect(c * frame_w, 0, frame_w, frame_h)
            sub = sheet.subsurface(rect).copy()
            
            # Remove bleeding from adjacent frames using connected components
            left_bleed = any(sub.get_at((0, y))[3] > 0 for y in range(frame_h))
            right_bleed = any(sub.get_at((frame_w-1, y))[3] > 0 for y in range(frame_h))
            
            if left_bleed or right_bleed:
                visited = set()
                islands = []
                for y in range(frame_h):
                    for x in range(frame_w):
                        if sub.get_at((x, y))[3] > 0 and (x, y) not in visited:
                            island = [(x, y)]
                            visited.add((x, y))
                            idx = 0
                            while idx < len(island):
                                cx, cy = island[idx]
                                idx += 1
                                for dx, dy in [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]:
                                    nx, ny = cx + dx, cy + dy
                                    if 0 <= nx < frame_w and 0 <= ny < frame_h:
                                        if (nx, ny) not in visited and sub.get_at((nx, ny))[3] > 0:
                                            visited.add((nx, ny))
                                            island.append((nx, ny))
                            islands.append(island)
                if islands:
                    islands.sort(key=len, reverse=True)
                    # Keep the largest island (main body), delete smaller islands touching edges
                    for island in islands[1:]:
                        touches_edge = any(x == 0 or x == frame_w - 1 for x, y in island)
                        if touches_edge:
                            for x, y in island:
                                sub.set_at((x, y), (0, 0, 0, 0))

            bbox = sub.get_bounding_rect()
            if bbox.width > 0:
                cropped = sub.subsurface(bbox)
                scaled_w = int(bbox.width * scale)
                scaled_h = int(bbox.height * scale)
                scaled = pygame.transform.scale(cropped, (scaled_w, scaled_h))
                out_surf = pygame.Surface((210, 210), pygame.SRCALPHA)
                draw_x = (210 - scaled_w) // 2
                draw_y = 210 - scaled_h
                out_surf.blit(scaled, (draw_x, draw_y))
                frames.append(out_surf)
            else:
                frames.append(pygame.Surface((210, 210), pygame.SRCALPHA))
    except Exception as e:
        print(f"Error loading {path}: {e}")
    return frames

def load_goku_combo_animation(path):
    frames = []
    try:
        sheet = pygame.image.load(resource_path(path)).convert_alpha()
        w, h = sheet.get_size()
        
        # Find distinct regions separated by empty space
        empty_cols = []
        for x in range(w):
            empty_cols.append(not any(sheet.get_at((x, y))[3] > 0 for y in range(h)))
            
        regions = []
        in_region = False
        start_x = 0
        for x in range(w):
            if not empty_cols[x] and not in_region:
                in_region = True
                start_x = x
            elif empty_cols[x] and in_region:
                in_region = False
                regions.append((start_x, x))
        if in_region:
            regions.append((start_x, w))
            
        final_regions = []
        for i, (sx, ex) in enumerate(regions):
            if i == 1 and ex - sx > 400:  # Region 1 contains 4 frames merged together
                final_regions.append((sx, sx + 120))
                final_regions.append((sx + 120, sx + 240))
                final_regions.append((sx + 240, sx + 380))
                final_regions.append((sx + 380, ex))
            else:
                final_regions.append((sx, ex))
            
        scale = 3.5 * (50 / 115)
        for sx, ex in final_regions:
            sub = sheet.subsurface(pygame.Rect(sx, 0, ex-sx, h)).copy()
            bbox = sub.get_bounding_rect()
            if bbox.width > 0:
                cropped = sub.subsurface(bbox)
                scaled_w = int(bbox.width * scale)
                scaled_h = int(bbox.height * scale)
                scaled = pygame.transform.scale(cropped, (scaled_w, scaled_h))
                
                # Create a surface wide enough for the beam, but minimum 210
                surf_w = max(210, scaled_w + 36) # 36 is 18*2 for left padding logic
                out_surf = pygame.Surface((surf_w, 210), pygame.SRCALPHA)
                
                # The body is at the left edge of the region. Place it at x=18
                draw_x = 18 
                draw_y = 210 - scaled_h
                out_surf.blit(scaled, (draw_x, draw_y))
                frames.append(out_surf)
    except Exception as e:
        print(f"Error loading {path}: {e}")
    return frames

goku_custom_idle = load_custom_goku_animation("assets/images/gokustand-removebg-preview.png", 5)
goku_custom_run = load_custom_goku_animation("assets/images/gokumove-removebg-preview.png", 8)
goku_custom_jump = load_custom_goku_animation("assets/images/gokujumb-removebg-preview.png", 3)
goku_custom_attack1 = load_custom_goku_animation("assets/images/gokuc1-removebg-preview.png", 4)
goku_custom_attack2 = load_custom_goku_animation("assets/images/gokuc2-removebg-preview.png", 8)
goku_custom_combo = load_goku_combo_animation("assets/images/gokuc3-removebg-preview.png")

goku_custom_hit = []
for frame in goku_custom_idle:
    red_frame = frame.copy()
    red_frame.fill((255, 100, 100, 255), special_flags=pygame.BLEND_RGBA_MULT)
    goku_custom_hit.append(red_frame)

# Game Variables
score = [0, 0]  # Player Scores: [P1, P2]

class DamageText:
    def __init__(self, x, y, damage, color):
        self.x = x
        self.y = y
        self.damage = str(damage)
        self.color = color
        self.counter = 0

    def update(self):
        self.y -= 3  # Float up
        self.counter += 1
        return self.counter <= 40

    def draw(self):
        draw_text(f"-{self.damage}", score_font, self.color, self.x, self.y)

damage_text_group = []

class Effect:
    def __init__(self, x, y, animation_list, scale, offset_y=0, offset_x=0, flip=False):
        self.animation_list = animation_list
        self.frame_index = 0
        self.image = self.animation_list[self.frame_index]
        self.update_time = pygame.time.get_ticks()
        self.rect = self.image.get_rect()
        self.rect.centerx = x + offset_x
        self.rect.bottom = y + offset_y
        self.flip = flip
        self.finished = False

    def update(self):
        animation_cooldown = 70
        self.image = self.animation_list[self.frame_index]
        if pygame.time.get_ticks() - self.update_time > animation_cooldown:
            self.frame_index += 1
            self.update_time = pygame.time.get_ticks()
        if self.frame_index >= len(self.animation_list):
            self.finished = True

    def draw(self, surface):
        if not self.finished:
            img = pygame.transform.flip(self.image, self.flip, False)
            # We use BLEND_RGB_ADD to make lightning glow and hide dark background naturally
            surface.blit(img, self.rect, special_flags=pygame.BLEND_RGB_ADD)

active_effects = []

def draw_text(text, font, color, x, y):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))


def draw_bg(image, is_game_started=False):
    scaled_bg = pygame.transform.scale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    screen.blit(scaled_bg, (0, 0))
    if not is_game_started:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))


def draw_button(text, font, text_col, button_col, x, y, width, height):
    pygame.draw.rect(screen, button_col, (x, y, width, height))
    pygame.draw.rect(screen, WHITE, (x, y, width, height), 2)
    text_img = font.render(text, True, text_col)
    text_rect = text_img.get_rect(center=(x + width // 2, y + height // 2))
    screen.blit(text_img, text_rect)
    return pygame.Rect(x, y, width, height)


async def victory_screen(winner_img, winner_text):
    while True:
        draw_bg(bg_image)
        
        # Draw victory logo
        resized_victory_img = pygame.transform.scale(victory_img, (victory_img.get_width() * 2, victory_img.get_height() * 2))
        screen.blit(resized_victory_img, (SCREEN_WIDTH // 2 - resized_victory_img.get_width() // 2,
                                          SCREEN_HEIGHT // 4 - 50))

        # Draw winner text
        win_text = f"{winner_text} WINS!"
        draw_text(win_text, menu_font_title, YELLOW, SCREEN_WIDTH // 2 - menu_font_title.size(win_text)[0] // 2, SCREEN_HEIGHT // 2 - 50)

        # Draw buttons
        button_width = 300
        button_height = 60
        play_again_btn = draw_button("PLAY AGAIN", menu_font, BLACK, GREEN, SCREEN_WIDTH // 2 - button_width // 2, SCREEN_HEIGHT - 200, button_width, button_height)
        main_menu_btn = draw_button("MAIN MENU", menu_font, BLACK, GREEN, SCREEN_WIDTH // 2 - button_width // 2, SCREEN_HEIGHT - 120, button_width, button_height)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_again_btn.collidepoint(event.pos):
                    return "PLAY_AGAIN"
                if main_menu_btn.collidepoint(event.pos):
                    return "MAIN_MENU"
        
        clock.tick(FPS)
        await asyncio.sleep(0)


def draw_gradient_text(text, font, x, y, colors):
    """
    Draws a gradient text by layering multiple text surfaces with slight offsets.
    """
    offset = 2
    for i, color in enumerate(colors):
        img = font.render(text, True, color)
        screen.blit(img, (x + i * offset, y + i * offset))


async def main_menu():
    animation_start_time = pygame.time.get_ticks()

    while True:
        draw_bg(bg_image, is_game_started=False)

        elapsed_time = (pygame.time.get_ticks() - animation_start_time) / 1000
        scale_factor = 1 + 0.05 * math.sin(elapsed_time * 2 * math.pi)  # Slight scaling
        scaled_font = pygame.font.Font(resource_path("assets/fonts/turok.ttf"), int(100 * scale_factor))

        title_text = "STREET FIGHTER"
        colors = [BLUE, GREEN, YELLOW]
        shadow_color = BLACK
        title_x = SCREEN_WIDTH // 2 - scaled_font.size(title_text)[0] // 2
        title_y = SCREEN_HEIGHT // 6

        shadow_offset = 5
        draw_text(title_text, scaled_font, shadow_color, title_x + shadow_offset, title_y + shadow_offset)
        draw_gradient_text(title_text, scaled_font, title_x, title_y, colors)

        button_width = 280
        button_height = 60
        button_spacing = 30

        start_button_y = SCREEN_HEIGHT // 2 - (button_height + button_spacing) * 2 + 50
        controls_button_y = SCREEN_HEIGHT // 2 - (button_height + button_spacing) * 1 + 50
        scores_button_y = SCREEN_HEIGHT // 2 + (button_height + button_spacing) * 0 + 50
        exit_button_y = SCREEN_HEIGHT // 2 + (button_height + button_spacing) * 1 + 50

        start_button = draw_button("START GAME", menu_font, BLACK, GREEN, SCREEN_WIDTH // 2 - button_width // 2,
                                   start_button_y, button_width, button_height)
        controls_button = draw_button("CONTROLS", menu_font, BLACK, GREEN, SCREEN_WIDTH // 2 - button_width // 2,
                                     controls_button_y, button_width, button_height)
        scores_button = draw_button("SCORES", menu_font, BLACK, GREEN, SCREEN_WIDTH // 2 - button_width // 2,
                                    scores_button_y, button_width, button_height)
        exit_button = draw_button("EXIT", menu_font, BLACK, GREEN, SCREEN_WIDTH // 2 - button_width // 2,
                                  exit_button_y, button_width, button_height)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.collidepoint(event.pos):
                    return "START"
                if controls_button.collidepoint(event.pos):
                    return "CONTROLS"
                if scores_button.collidepoint(event.pos):
                    return "SCORES"
                if exit_button.collidepoint(event.pos):
                    pygame.quit()
                    exit()

        pygame.display.update()
        clock.tick(FPS)
        await asyncio.sleep(0)


async def map_selection_screen():
    global current_map_index, bg_image
    
    while True:
        # Show the actual map clearly
        draw_bg(loaded_maps[current_map_index], is_game_started=True)
        
        # Draw semi-transparent overlay for better UI readability
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        title_text = "CHOOSE YOUR ARENA"
        draw_text(title_text, menu_font_title, YELLOW, SCREEN_WIDTH // 2 - menu_font_title.size(title_text)[0] // 2, 50)
        
        button_width = 300
        button_height = 60
        spacing = 30
        
        start_y = 200
        
        dojo_btn = draw_button("MAP 1: DOJO", menu_font, BLACK, GREEN if current_map_index == 0 else WHITE, SCREEN_WIDTH // 2 - button_width // 2, start_y, button_width, button_height)
        forest_btn = draw_button("MAP 2: FOREST", menu_font, BLACK, GREEN if current_map_index == 1 else WHITE, SCREEN_WIDTH // 2 - button_width // 2, start_y + button_height + spacing, button_width, button_height)
        city_btn = draw_button("MAP 3: CITY", menu_font, BLACK, GREEN if current_map_index == 2 else WHITE, SCREEN_WIDTH // 2 - button_width // 2, start_y + (button_height + spacing) * 2, button_width, button_height)
        
        fight_btn = draw_button("FIGHT!", count_font, BLACK, RED, SCREEN_WIDTH // 2 - button_width // 2, start_y + (button_height + spacing) * 3 + 50, button_width, 100)
        back_btn = draw_button("BACK TO MENU", menu_font, BLACK, WHITE, SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT - 100, 400, 50)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if dojo_btn.collidepoint(event.pos):
                    current_map_index = 0
                    bg_image = loaded_maps[0]
                if forest_btn.collidepoint(event.pos):
                    current_map_index = 1
                    bg_image = loaded_maps[1]
                if city_btn.collidepoint(event.pos):
                    current_map_index = 2
                    bg_image = loaded_maps[2]
                if fight_btn.collidepoint(event.pos):
                    return "START"
                if back_btn.collidepoint(event.pos):
                    return "BACK"
        
        clock.tick(FPS)
        await asyncio.sleep(0)


async def pause_screen():
    # Draw semi-transparent overlay
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))
    
    title_text = "GAME PAUSED"
    draw_text(title_text, menu_font_title, YELLOW, SCREEN_WIDTH // 2 - menu_font_title.size(title_text)[0] // 2, 200)
    
    button_width = 300
    button_height = 60
    
    resume_btn = draw_button("RESUME", menu_font, BLACK, GREEN, SCREEN_WIDTH // 2 - button_width // 2, 400, button_width, button_height)
    main_menu_btn = draw_button("MAIN MENU", menu_font, BLACK, RED, SCREEN_WIDTH // 2 - button_width // 2, 500, button_width, button_height)
    
    pygame.display.update()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "RESUME"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if resume_btn.collidepoint(event.pos):
                    return "RESUME"
                if main_menu_btn.collidepoint(event.pos):
                    return "MAIN_MENU"
        clock.tick(FPS)
        await asyncio.sleep(0)


async def mode_selection_screen():
    while True:
        draw_bg(bg_image, is_game_started=False)
        
        # Draw semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        title_text = "SELECT GAME MODE"
        draw_text(title_text, menu_font_title, YELLOW, SCREEN_WIDTH // 2 - menu_font_title.size(title_text)[0] // 2, 100)
        
        button_width = 400
        button_height = 80
        spacing = 50
        
        start_y = 300
        
        player_vs_bot_btn = draw_button("PLAYER VS BOT", menu_font, BLACK, GREEN, SCREEN_WIDTH // 2 - button_width // 2, start_y, button_width, button_height)
        player_vs_player_btn = draw_button("PLAYER VS PLAYER", menu_font, BLACK, GREEN, SCREEN_WIDTH // 2 - button_width // 2, start_y + button_height + spacing, button_width, button_height)
        
        back_btn = draw_button("BACK TO MENU", menu_font, BLACK, WHITE, SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT - 100, 400, 50)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if player_vs_bot_btn.collidepoint(event.pos):
                    return "BOT"
                if player_vs_player_btn.collidepoint(event.pos):
                    return "PLAYER"
                if back_btn.collidepoint(event.pos):
                    return "BACK"
        
        clock.tick(FPS)
        await asyncio.sleep(0)

async def character_selection_screen():
    p1_selected = "warrior"
    p2_selected = "wizard"
    
    while True:
        draw_bg(bg_image, is_game_started=False)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        title_text = "CHARACTER SELECTION"
        draw_text(title_text, menu_font_title, YELLOW, SCREEN_WIDTH // 2 - menu_font_title.size(title_text)[0] // 2, 50)
        
        # P1 Selection
        draw_text(f"P1: {p1_selected.upper()}", menu_font, BLUE, 200, 150)
        p1_warrior_btn = draw_button("WARRIOR", menu_font, BLACK, WHITE if p1_selected == "warrior" else GRAY, 150, 220, 250, 50)
        p1_wizard_btn = draw_button("WIZARD", menu_font, BLACK, WHITE if p1_selected == "wizard" else GRAY, 150, 290, 250, 50)
        p1_ryu_btn = draw_button("RYU", menu_font, BLACK, WHITE if p1_selected == "ryu" else GRAY, 150, 360, 250, 50)
        p1_goku_btn = draw_button("GOKU", menu_font, BLACK, WHITE if p1_selected == "goku" else GRAY, 150, 430, 250, 50)
        
        # P2 Selection
        draw_text(f"P2: {p2_selected.upper()}", menu_font, RED, SCREEN_WIDTH - 450, 150)
        p2_warrior_btn = draw_button("WARRIOR", menu_font, BLACK, WHITE if p2_selected == "warrior" else GRAY, SCREEN_WIDTH - 450, 220, 250, 50)
        p2_wizard_btn = draw_button("WIZARD", menu_font, BLACK, WHITE if p2_selected == "wizard" else GRAY, SCREEN_WIDTH - 450, 290, 250, 50)
        p2_ryu_btn = draw_button("RYU", menu_font, BLACK, WHITE if p2_selected == "ryu" else GRAY, SCREEN_WIDTH - 450, 360, 250, 50)
        p2_goku_btn = draw_button("GOKU", menu_font, BLACK, WHITE if p2_selected == "goku" else GRAY, SCREEN_WIDTH - 450, 430, 250, 50)
        
        continue_btn = draw_button("CONTINUE", count_font, BLACK, GREEN, SCREEN_WIDTH // 2 - 150, 550, 300, 80)
        back_btn = draw_button("BACK TO MENU", menu_font, BLACK, WHITE, SCREEN_WIDTH // 2 - 150, 650, 300, 50)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if p1_warrior_btn.collidepoint(event.pos): p1_selected = "warrior"
                if p1_wizard_btn.collidepoint(event.pos): p1_selected = "wizard"
                if p1_ryu_btn.collidepoint(event.pos): p1_selected = "ryu"
                if p1_goku_btn.collidepoint(event.pos): p1_selected = "goku"
                
                if p2_warrior_btn.collidepoint(event.pos): p2_selected = "warrior"
                if p2_wizard_btn.collidepoint(event.pos): p2_selected = "wizard"
                if p2_ryu_btn.collidepoint(event.pos): p2_selected = "ryu"
                if p2_goku_btn.collidepoint(event.pos): p2_selected = "goku"
                
                if continue_btn.collidepoint(event.pos):
                    return p1_selected, p2_selected
                if back_btn.collidepoint(event.pos):
                    return None, None
        
        clock.tick(FPS)
        await asyncio.sleep(0)


async def scores_screen():
    while True:
        draw_bg(bg_image)

        scores_title = "SCORES"
        draw_text(scores_title, menu_font_title, RED, SCREEN_WIDTH // 2 - menu_font_title.size(scores_title)[0] // 2, 50)

        score_font_large = pygame.font.Font(resource_path("assets/fonts/turok.ttf"), 60)  # Increased size for scores
        p1_text = f"P1: {score[0]}"
        p2_text = f"P2: {score[1]}"
        shadow_offset = 5

        p1_text_x = SCREEN_WIDTH // 2 - score_font_large.size(p1_text)[0] // 2
        p1_text_y = SCREEN_HEIGHT // 2 - 50
        draw_text(p1_text, score_font_large, BLACK, p1_text_x + shadow_offset, p1_text_y + shadow_offset)  # Shadow
        draw_gradient_text(p1_text, score_font_large, p1_text_x, p1_text_y, [BLUE, GREEN])  # Gradient

        p2_text_x = SCREEN_WIDTH // 2 - score_font_large.size(p2_text)[0] // 2
        p2_text_y = SCREEN_HEIGHT // 2 + 50
        draw_text(p2_text, score_font_large, BLACK, p2_text_x + shadow_offset, p2_text_y + shadow_offset)  # Shadow
        draw_gradient_text(p2_text, score_font_large, p2_text_x, p2_text_y, [RED, YELLOW])  # Gradient

        return_button = draw_button("RETURN TO MAIN MENU", menu_font, BLACK, GREEN, SCREEN_WIDTH // 2 - 220, 700, 500, 50)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if return_button.collidepoint(event.pos):
                    return

        pygame.display.update()
        clock.tick(FPS)
        await asyncio.sleep(0)


async def controls_screen():
    while True:
        draw_bg(bg_image)

        # Title
        controls_title = "CONTROLS GUIDE"
        draw_text(controls_title, menu_font_title, GREEN, SCREEN_WIDTH // 2 - menu_font_title.size(controls_title)[0] // 2, 50)
        
        # Controls information
        controls_font = pygame.font.Font(resource_path("assets/fonts/turok.ttf"), 35)
        small_font = pygame.font.Font(resource_path("assets/fonts/turok.ttf"), 25)
        
        # Movement controls
        draw_text("P1 MOVEMENT:", controls_font, WHITE, 100, 150)
        draw_text("A - Move Left", small_font, BLUE, 100, 190)
        draw_text("D - Move Right", small_font, BLUE, 100, 220)
        draw_text("W - Jump", small_font, BLUE, 100, 250)
        
        # Attack controls
        draw_text("P1 ATTACKS:", controls_font, WHITE, 100, 300)
        draw_text("R - Close Attack", small_font, RED, 100, 340)
        draw_text("T - Long Attack", small_font, RED, 100, 370)
        draw_text("Y - Combo Attack", small_font, YELLOW, 100, 400)
        
        # P2 Movement controls
        draw_text("P2 MOVEMENT:", controls_font, WHITE, 400, 150)
        draw_text("Left Arrow - Move Left", small_font, (255, 100, 0), 400, 190)
        draw_text("Right Arrow - Move Right", small_font, (255, 100, 0), 400, 220)
        draw_text("Up Arrow - Jump", small_font, (255, 100, 0), 400, 250)
        
        # P2 Attack controls
        draw_text("P2 ATTACKS:", controls_font, WHITE, 400, 300)
        draw_text("B - Close Attack", small_font, RED, 400, 340)
        draw_text("N - Long Attack", small_font, RED, 400, 370)
        draw_text("M - Combo Attack", small_font, YELLOW, 400, 400)
        
        # Game info
        draw_text("GAME INFO:", controls_font, WHITE, 750, 150)
        draw_text("• P1 is WARRIOR (left)", small_font, YELLOW, 750, 190)
        draw_text("• P2 is WIZARD (right)", small_font, (255, 100, 0), 750, 220)
        draw_text("• Normal attack = 10 dmg (+5 Mana)", small_font, WHITE, 750, 250)
        draw_text("• Combo attack = 15x2 dmg (20 Mana)", small_font, WHITE, 750, 280)
        
        # Tips
        draw_text("TIPS:", controls_font, WHITE, 800, 330)
        draw_text("• Jump to avoid attacks", small_font, GREEN, 800, 370)
        draw_text("• Use close attacks near", small_font, GREEN, 800, 400)
        draw_text("• Use long attacks far", small_font, GREEN, 800, 430)
        
        # Return button
        return_button = draw_button("RETURN TO MAIN MENU", menu_font, BLACK, GREEN, SCREEN_WIDTH // 2 - 220, 550, 500, 50)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if return_button.collidepoint(event.pos):
                    return

        pygame.display.update()
        clock.tick(FPS)
        await asyncio.sleep(0)


def reset_game(ai_enabled, p1_char="warrior", p2_char="wizard"):
    global fighter_1, fighter_2
    
    chars = {
        "warrior": {"data": WARRIOR_DATA, "sheet": warrior_sheet, "steps": WARRIOR_ANIMATION_STEPS, "sound": sword_fx, "type": "melee", "row_map": None, "skill3_sound": boom_fx},
        "wizard": {"data": WIZARD_DATA, "sheet": wizard_sheet, "steps": WIZARD_ANIMATION_STEPS, "sound": magic_fx, "type": "melee", "row_map": None, "skill3_sound": boom_fx},
        "ryu": {"data": RYU_DATA, "sheet": ryu_sheet, "steps": RYU_ANIMATION_STEPS, "sound": magic_fx, "type": "ranged", "row_map": RYU_ROW_MAP, "align_bottom": 92, "skill3_sound": boom_fx},
        "goku": {"data": GOKU_DATA, "sheet": goku_sheet, "steps": GOKU_ANIMATION_STEPS, "sound": magic_fx, "type": "hybrid", "row_map": GOKU_ROW_MAP, "col_map": GOKU_COL_MAP, "skill_image": kame_beam_img, "skill3_sound": boom_fx}
    }
    
    c1 = chars[p1_char]
    c2 = chars[p2_char]
    fighter_1 = Fighter(1, 200, 310, False, c1["data"], c1["sheet"], c1["steps"], c1["sound"], fighter_type=c1["type"], row_map=c1.get("row_map"), col_map=c1.get("col_map"), align_bottom=c1.get("align_bottom"), skill_image=c1.get("skill_image"), skill3_sound=c1.get("skill3_sound"))
    if p1_char == "goku":
        if goku_custom_idle: fighter_1.animation_list[0] = goku_custom_idle
        if goku_custom_run: fighter_1.animation_list[1] = goku_custom_run
        if goku_custom_jump: fighter_1.animation_list[2] = goku_custom_jump
        if goku_custom_attack1: fighter_1.animation_list[3] = goku_custom_attack1
        if goku_custom_attack2: fighter_1.animation_list[4] = goku_custom_attack2
        if goku_custom_hit: fighter_1.animation_list[5] = goku_custom_hit
        if goku_custom_combo: fighter_1.animation_list[7] = goku_custom_combo

    fighter_2 = Fighter(2, 700, 310, True, c2["data"], c2["sheet"], c2["steps"], c2["sound"], fighter_type=c2["type"], row_map=c2.get("row_map"), col_map=c2.get("col_map"), align_bottom=c2.get("align_bottom"), skill_image=c2.get("skill_image"), skill3_sound=c2.get("skill3_sound"))
    if p2_char == "goku":
        if goku_custom_idle: fighter_2.animation_list[0] = goku_custom_idle
        if goku_custom_run: fighter_2.animation_list[1] = goku_custom_run
        if goku_custom_jump: fighter_2.animation_list[2] = goku_custom_jump
        if goku_custom_attack1: fighter_2.animation_list[3] = goku_custom_attack1
        if goku_custom_attack2: fighter_2.animation_list[4] = goku_custom_attack2
        if goku_custom_hit: fighter_2.animation_list[5] = goku_custom_hit
        if goku_custom_combo: fighter_2.animation_list[7] = goku_custom_combo
        
    fighter_2.ai_enabled = ai_enabled


MAX_HEALTH = 250
MAX_MANA = 20

def draw_health_bar(health, x, y):
    bar_width = 400
    bar_height = 30
    pygame.draw.rect(screen, BLACK, (x, y, bar_width, bar_height))
    if health > 0:
        ratio = health / MAX_HEALTH
        pygame.draw.rect(screen, RED, (x, y, bar_width * ratio, bar_height))
    pygame.draw.rect(screen, WHITE, (x, y, bar_width, bar_height), 2)

def draw_mana_bar(mana, x, y):
    bar_width = 400
    bar_height = 15
    pygame.draw.rect(screen, BLACK, (x, y, bar_width, bar_height))
    if mana > 0:
        ratio = mana / MAX_MANA
        pygame.draw.rect(screen, BLUE, (x, y, bar_width * ratio, bar_height))
    pygame.draw.rect(screen, WHITE, (x, y, bar_width, bar_height), 2)


async def countdown():
    countdown_font = pygame.font.Font(resource_path("assets/fonts/turok.ttf"), 100)
    countdown_texts = ["3", "2", "1", "FIGHT!"]

    for text in countdown_texts:
        draw_bg(bg_image, is_game_started=True)

        text_img = countdown_font.render(text, True, RED)
        text_width = text_img.get_width()
        x_pos = (SCREEN_WIDTH - text_width) // 2

        draw_text(text, countdown_font, RED, x_pos, SCREEN_HEIGHT // 2 - 50)

        pygame.display.update()
        await asyncio.sleep(1)


async def game_loop(ai_enabled, p1_char, p2_char):
    global score, active_effects, damage_text_group
    active_effects.clear()
    damage_text_group.clear()
    reset_game(ai_enabled, p1_char, p2_char)
    round_over = False
    winner_img = None
    winner_text = ""
    game_started = True

    await countdown()

    while True:
        draw_bg(bg_image, is_game_started=game_started)

        draw_text(f"P1: {score[0]}", score_font, RED, 20, 20)
        draw_text(f"P2: {score[1]}", score_font, RED, SCREEN_WIDTH - 420, 20)
        
        # Add player identification labels
        player_label_font = pygame.font.Font(resource_path("assets/fonts/turok.ttf"), 25)
        draw_text("PLAYER 1", player_label_font, BLUE, 20, 110)
        draw_text("PLAYER 2", player_label_font, (255, 100, 0), SCREEN_WIDTH - 420, 110)
        
        draw_health_bar(fighter_1.health, 20, 50)
        draw_mana_bar(fighter_1.mana, 20, 85)
        
        draw_health_bar(fighter_2.health, SCREEN_WIDTH - 420, 50)
        draw_mana_bar(fighter_2.mana, SCREEN_WIDTH - 420, 85)

        exit_button = draw_button("MAIN MENU", menu_font, BLACK, YELLOW, SCREEN_WIDTH // 2 - 150, 20, 300, 50)

        if not round_over:
            fighter_1.move(SCREEN_WIDTH, SCREEN_HEIGHT, fighter_2, round_over)
            fighter_2.move(SCREEN_WIDTH, SCREEN_HEIGHT, fighter_1, round_over)

            fighter_1.update(fighter_2)
            fighter_2.update(fighter_1)

            # Check for hits to spawn damage text
            if fighter_1.just_hit:
                damage_text_group.append(DamageText(fighter_1.rect.centerx, fighter_1.rect.y, fighter_1.last_damage_taken, RED))
                fighter_1.just_hit = False

            if fighter_2.just_hit:
                damage_text_group.append(DamageText(fighter_2.rect.centerx, fighter_2.rect.y, fighter_2.last_damage_taken, RED))
                fighter_2.just_hit = False
                
            # Trigger Combo Effects
            if fighter_1.combo_finished:
                fighter_1.combo_finished = False
                if p1_char == "warrior":
                    eff_list = blueframe_anim
                    eff_offset = 20
                    eff_offset_x = 0
                    eff_flip = False
                elif p1_char == "ryu":
                    eff_list = blueboom_anim
                    eff_offset = 50
                    eff_offset_x = 0
                    eff_flip = False
                elif p1_char == "wizard":
                    eff_list = fire_anim
                    eff_offset = 20
                    # fire is a symmetric explosion now, no flip or offset needed
                    eff_flip = False
                    eff_offset_x = 0
                elif p1_char == "goku":
                    eff_list = None
                else:
                    eff_list = lightning_animation_list
                    eff_offset = 10
                    eff_offset_x = 0
                    eff_flip = False
                
                if eff_list:
                    active_effects.append(Effect(fighter_2.rect.centerx, fighter_2.rect.bottom, eff_list, 1, offset_y=eff_offset, offset_x=eff_offset_x, flip=eff_flip))

            if fighter_2.combo_finished:
                fighter_2.combo_finished = False
                if p2_char == "warrior":
                    eff_list = blueframe_anim
                    eff_offset = 20
                    eff_offset_x = 0
                    eff_flip = False
                elif p2_char == "ryu":
                    eff_list = blueboom_anim
                    eff_offset = 50
                    eff_offset_x = 0
                    eff_flip = False
                elif p2_char == "wizard":
                    eff_list = fire_anim
                    eff_offset = 20
                    eff_flip = False
                    eff_offset_x = 0
                elif p2_char == "goku":
                    eff_list = None
                else:
                    eff_list = lightning_animation_list
                    eff_offset = 10
                    eff_offset_x = 0
                    eff_flip = False
                
                if eff_list:
                    active_effects.append(Effect(fighter_1.rect.centerx, fighter_1.rect.bottom, eff_list, 1, offset_y=eff_offset, offset_x=eff_offset_x, flip=eff_flip))

            if not fighter_1.alive:
                score[1] += 1
                round_over = True
                winner_img = wizard_victory_img if p2_char == "wizard" else (warrior_victory_img if p2_char == "warrior" else (ryu_victory_img if p2_char == "ryu" else goku_victory_img))
                winner_text = "PLAYER 2"
            elif not fighter_2.alive:
                score[0] += 1
                round_over = True
                winner_img = warrior_victory_img if p1_char == "warrior" else (wizard_victory_img if p1_char == "wizard" else (ryu_victory_img if p1_char == "ryu" else goku_victory_img))
                winner_text = "PLAYER 1"
        else:
            action = await victory_screen(winner_img, winner_text)
            return action

        fighter_1.draw(screen)
        fighter_2.draw(screen)

        # Update and draw damage text
        remaining_texts = []
        for text in damage_text_group:
            if text.update():
                text.draw()
                remaining_texts.append(text)
        damage_text_group[:] = remaining_texts

        # Update and draw active effects
        remaining_effects = []
        for effect in active_effects:
            effect.update()
            if not effect.finished:
                effect.draw(screen)
                remaining_effects.append(effect)
        active_effects[:] = remaining_effects

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    action = await pause_screen()
                    if action == "MAIN_MENU":
                        return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                if exit_button.collidepoint(event.pos):
                    return None

        pygame.display.update()
        clock.tick(FPS)
        await asyncio.sleep(0)


async def main():
    while True:
        menu_selection = await main_menu()

        if menu_selection == "START":
            mode_selection = await mode_selection_screen()
            if mode_selection in ["BOT", "PLAYER"]:
                ai_enabled = (mode_selection == "BOT")
                
                p1_char, p2_char = await character_selection_screen()
                if p1_char and p2_char:
                    map_selection = await map_selection_screen()
                    if map_selection == "START":
                        while True:
                            result = await game_loop(ai_enabled, p1_char, p2_char)
                            if result != "PLAY_AGAIN":
                                break
        elif menu_selection == "CONTROLS":
            await controls_screen()
        elif menu_selection == "SCORES":
            await scores_screen()

if __name__ == "__main__":
    asyncio.run(main())
