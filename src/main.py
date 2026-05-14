import math
import pygame
from pygame import mixer
from pygame import font
import cv2
import numpy as np
import os
import sys
from fighter import Fighter

# Helper Function for Bundled Assets
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        # When running from src directory, look in parent directory for assets
        if os.path.basename(os.getcwd()) == "src":
            base_path = os.path.abspath("..")
        else:
            base_path = os.path.abspath(".")

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

# Initialize Game Window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
pygame.display.set_caption("Street Fighter")
clock = pygame.time.Clock()

# Load Assets
MAP_FILES = ["assets/images/bg.jpg", "assets/images/bg1.jpg", "assets/images/bg2.jpg"]
loaded_maps = [cv2.imread(resource_path(m)) for m in MAP_FILES]
current_map_index = 1
bg_image = loaded_maps[current_map_index]
victory_img = pygame.image.load(resource_path("assets/images/victory.png")).convert_alpha()
warrior_victory_img = pygame.image.load(resource_path("assets/images/warrior.png")).convert_alpha()
wizard_victory_img = pygame.image.load(resource_path("assets/images/wizard.png")).convert_alpha()

# Fonts
menu_font = pygame.font.Font(resource_path("assets/fonts/turok.ttf"), 50)
menu_font_title = pygame.font.Font(resource_path("assets/fonts/turok.ttf"), 100)  # Larger font for title
count_font = pygame.font.Font(resource_path("assets/fonts/turok.ttf"), 80)
score_font = pygame.font.Font(resource_path("assets/fonts/turok.ttf"), 30)

# Music and Sounds
pygame.mixer.music.load(resource_path("assets/audio/music.mp3"))
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1, 0.0, 5000)
sword_fx = pygame.mixer.Sound(resource_path("assets/audio/sword.wav"))
sword_fx.set_volume(0.5)
magic_fx = pygame.mixer.Sound(resource_path("assets/audio/magic.wav"))
magic_fx.set_volume(0.75)

# Load Fighter Spritesheets
warrior_sheet = pygame.image.load(resource_path("assets/images/warrior.png")).convert_alpha()
wizard_sheet = pygame.image.load(resource_path("assets/images/wizard.png")).convert_alpha()

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

def draw_text(text, font, color, x, y):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))


def blur_bg(image):
    image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    blurred_image = cv2.GaussianBlur(image_bgr, (15, 15), 0)
    return cv2.cvtColor(blurred_image, cv2.COLOR_BGR2RGB)


def draw_bg(image, is_game_started=False):
    if not is_game_started:
        blurred_bg = blur_bg(image)
        blurred_bg = pygame.surfarray.make_surface(np.transpose(blurred_bg, (1, 0, 2)))
        blurred_bg = pygame.transform.scale(blurred_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(blurred_bg, (0, 0))
    else:
        image = pygame.surfarray.make_surface(np.transpose(image, (1, 0, 2)))
        image = pygame.transform.scale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(image, (0, 0))


def draw_button(text, font, text_col, button_col, x, y, width, height):
    pygame.draw.rect(screen, button_col, (x, y, width, height))
    pygame.draw.rect(screen, WHITE, (x, y, width, height), 2)
    text_img = font.render(text, True, text_col)
    text_rect = text_img.get_rect(center=(x + width // 2, y + height // 2))
    screen.blit(text_img, text_rect)
    return pygame.Rect(x, y, width, height)


def victory_screen(winner_img, winner_text):
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


def draw_gradient_text(text, font, x, y, colors):
    """
    Draws a gradient text by layering multiple text surfaces with slight offsets.
    """
    offset = 2
    for i, color in enumerate(colors):
        img = font.render(text, True, color)
        screen.blit(img, (x + i * offset, y + i * offset))


def main_menu():
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


def map_selection_screen():
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


def pause_screen():
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


def mode_selection_screen():
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


def scores_screen():
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


def controls_screen():
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
        draw_text("• Normal attack = 10 dmg", small_font, WHITE, 750, 250)
        draw_text("• Combo attack = 15x2 dmg", small_font, WHITE, 750, 280)
        
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


def reset_game(ai_enabled):
    global fighter_1, fighter_2
    fighter_1 = Fighter(1, 200, 310, False, WARRIOR_DATA, warrior_sheet, WARRIOR_ANIMATION_STEPS, sword_fx)
    fighter_2 = Fighter(2, 700, 310, True, WIZARD_DATA, wizard_sheet, WIZARD_ANIMATION_STEPS, magic_fx)
    fighter_2.ai_enabled = ai_enabled


MAX_HEALTH = 250

def draw_health_bar(health, x, y):
    bar_width = 400
    bar_height = 30
    pygame.draw.rect(screen, BLACK, (x, y, bar_width, bar_height))
    if health > 0:
        ratio = health / MAX_HEALTH
        pygame.draw.rect(screen, RED, (x, y, bar_width * ratio, bar_height))
    pygame.draw.rect(screen, WHITE, (x, y, bar_width, bar_height), 2)


def countdown():
    countdown_font = pygame.font.Font(resource_path("assets/fonts/turok.ttf"), 100)
    countdown_texts = ["3", "2", "1", "FIGHT!"]

    for text in countdown_texts:
        draw_bg(bg_image, is_game_started=True)

        text_img = countdown_font.render(text, True, RED)
        text_width = text_img.get_width()
        x_pos = (SCREEN_WIDTH - text_width) // 2

        draw_text(text, countdown_font, RED, x_pos, SCREEN_HEIGHT // 2 - 50)

        pygame.display.update()
        pygame.time.delay(1000)


def game_loop(ai_enabled):
    global score
    reset_game(ai_enabled)
    round_over = False
    winner_img = None
    winner_text = ""
    game_started = True

    countdown()

    while True:
        draw_bg(bg_image, is_game_started=game_started)

        draw_text(f"P1: {score[0]}", score_font, RED, 20, 20)
        draw_text(f"P2: {score[1]}", score_font, RED, SCREEN_WIDTH - 420, 20)
        
        # Add player identification labels
        player_label_font = pygame.font.Font(resource_path("assets/fonts/turok.ttf"), 25)
        draw_text("PLAYER 1", player_label_font, BLUE, 20, 95)
        draw_text("PLAYER 2", player_label_font, (255, 100, 0), SCREEN_WIDTH - 420, 95)
        
        draw_health_bar(fighter_1.health, 20, 50)
        draw_health_bar(fighter_2.health, SCREEN_WIDTH - 420, 50)

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

            if not fighter_1.alive:
                score[1] += 1
                round_over = True
                winner_img = wizard_victory_img
                winner_text = "PLAYER 2"
            elif not fighter_2.alive:
                score[0] += 1
                round_over = True
                winner_img = warrior_victory_img
                winner_text = "PLAYER 1"
        else:
            action = victory_screen(winner_img, winner_text)
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

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    action = pause_screen()
                    if action == "MAIN_MENU":
                        return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                if exit_button.collidepoint(event.pos):
                    return None

        pygame.display.update()
        clock.tick(FPS)


while True:
    menu_selection = main_menu()

    if menu_selection == "START":
        mode_selection = mode_selection_screen()
        if mode_selection in ["BOT", "PLAYER"]:
            ai_enabled = (mode_selection == "BOT")
            map_selection = map_selection_screen()
            if map_selection == "START":
                while True:
                    result = game_loop(ai_enabled)
                    if result != "PLAY_AGAIN":
                        break
    elif menu_selection == "CONTROLS":
        controls_screen()
    elif menu_selection == "SCORES":
        scores_screen()
