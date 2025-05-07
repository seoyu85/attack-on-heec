import pygame
import sys
import random
import math
import os

# Initialize pygame
pygame.font.init()
pygame.init()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
INVULNERABILITY_TIME = 1000

# Stage configuration
STAGE_ZOMBIE_COUNTS = {
    1: 5,    # Stage 1: 5 zombies
    2: 9,    # Stage 2: 9 zombies + boss
    3: 14,   # Stage 3: 14 zombies + boss
    4: 20,   # Stage 4: 20 zombies
    5: 24    # Stage 5: 24 zombies + boss
}

STAGE_BOSSES = {
    2: "assets/bosses/Boss1",
    3: "assets/bosses/Boss2",
    5: "assets/bosses/boss3"
}

# Player controls
PLAYER1_UP, PLAYER1_DOWN = pygame.K_UP, pygame.K_DOWN
PLAYER1_LEFT, PLAYER1_RIGHT = pygame.K_LEFT, pygame.K_RIGHT
PLAYER1_ATTACK = pygame.K_m
PLAYER2_UP, PLAYER2_DOWN = pygame.K_z, pygame.K_s
PLAYER2_LEFT, PLAYER2_RIGHT = pygame.K_q, pygame.K_d
PLAYER2_ATTACK = pygame.K_a

# Setup screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Attack On Heec")
clock = pygame.time.Clock()

# Game states
MENU, PLAYING, GAME_OVER, STAGE_TRANSITION = 0, 1, 2, 3
current_state = MENU

# Font setup
title_font = pygame.font.SysFont("Arial", 64)
button_font = pygame.font.SysFont("Arial", 32)
font_small = pygame.font.SysFont("Arial", 16)
font_medium = pygame.font.SysFont("Arial", 24)
font_large = pygame.font.SysFont("Arial", 32)

def load_image(path, scale=1.0):
    """Load a single image with optional scaling"""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        abs_path = os.path.join(script_dir, path)
        image = pygame.image.load(abs_path).convert_alpha()
        if scale != 1.0:
            new_size = (int(image.get_width() * scale), 
                       int(image.get_height() * scale))
            image = pygame.transform.scale(image, new_size)
        return image
    except Exception as e:
        print(f"Failed to load image {path}: {e}")
        placeholder = pygame.Surface((50, 50), pygame.SRCALPHA)
        if "zombie1" in path:
            placeholder.fill((100, 200, 100, 255))
        elif "zombie2" in path:
            placeholder.fill((200, 100, 100, 255))
        elif "zombie3" in path:
            placeholder.fill((100, 100, 200, 255))
        else:
            placeholder.fill((150, 150, 150, 255))
        return placeholder

class Weapon:
    def __init__(self, name, price, damage, image_path=None):
        self.name = name
        self.price = price
        self.damage = damage
        self.image = load_image(image_path) if image_path else pygame.Surface((40, 40))

    def draw(self, screen, x, y):
        screen.blit(self.image, (x, y))

    def get_info_text(self, font):
        return font.render(f"{self.name}: {self.damage} DMG - {self.price} Coins", True, WHITE)

class Coin:
    def __init__(self, screen, x, y, coin_type=1):
        self.screen = screen
        self.coin_type = coin_type
        self.value = {1: 150, 2: 100, 3: 50}.get(coin_type, 50)
        self.image = load_image(f"assets/coins/Coin{coin_type}.png")
        self.image = pygame.transform.scale(self.image, (30, 30))
        self.rect = self.image.get_rect(center=(x, y))
        self.lifetime = 10000  # 10 seconds

    def update(self, dt):
        self.lifetime -= dt
        return self.lifetime > 0

    def draw(self):
        self.screen.blit(self.image, self.rect)

class Player:
    def __init__(self, screen, x, y, health, damage, speed, player_num):
        self.screen = screen
        self.rect = pygame.Rect(x, y, 50, 50)
        self.health = health
        self.max_health = health
        self.damage = damage
        self.speed = speed
        self.player_num = player_num
        self.coins = 0
        self.facing_right = True
        self.image = load_image(f"assets/player{player_num}/Idle.png")
        
        # Controls
        if player_num == 1:
            self.up_key = PLAYER1_UP
            self.down_key = PLAYER1_DOWN
            self.left_key = PLAYER1_LEFT
            self.right_key = PLAYER1_RIGHT
            self.attack_key = PLAYER1_ATTACK
        else:
            self.up_key = PLAYER2_UP
            self.down_key = PLAYER2_DOWN
            self.left_key = PLAYER2_LEFT
            self.right_key = PLAYER2_RIGHT
            self.attack_key = PLAYER2_ATTACK
        
        self.attacking = False
        self.attack_cooldown = 500
        self.last_attack_time = 0
        self.invulnerable = False
        self.last_hit_time = 0
        self.flicker = False
        self.flicker_counter = 0
        self.equipped_weapon = None

    def is_vulnerable(self):
        return not self.invulnerable

    def update(self):
        current_time = pygame.time.get_ticks()
        if self.invulnerable and current_time - self.last_hit_time > INVULNERABILITY_TIME:
            self.invulnerable = False
            
        if self.invulnerable:
            self.flicker_counter += 1
            if self.flicker_counter >= 5:
                self.flicker = not self.flicker
                self.flicker_counter = 0
        
        keys = pygame.key.get_pressed()
        moving = False
        
        if keys[self.left_key]:
            self.rect.x -= self.speed
            self.facing_right = False
            moving = True
        if keys[self.right_key]:
            self.rect.x += self.speed
            self.facing_right = True
            moving = True
        if keys[self.up_key]:
            self.rect.y -= self.speed
            moving = True
        if keys[self.down_key]:
            self.rect.y += self.speed
            moving = True
        
        self.rect.clamp_ip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        
        if keys[self.attack_key] and not self.attacking:
            if current_time - self.last_attack_time > self.attack_cooldown:
                self.attacking = True
                self.last_attack_time = current_time
                self.attack()
        
        if self.attacking and current_time - self.last_attack_time > 200:
            self.attacking = False
        
        # Update image facing direction
        if not self.facing_right:
            self.image = pygame.transform.flip(load_image(f"assets/player{self.player_num}/Idle.png"), True, False)
        else:
            self.image = load_image(f"assets/player{self.player_num}/Idle.png")

    def attack(self):
        attack_rect = self.get_attack_rect()
        if not attack_rect:
            return
        
        for zombie in zombies[:]:
            if zombie.rect.colliderect(attack_rect) and zombie.state != "dead":
                zombie.take_damage(self.damage)
                if zombie.health <= 0:
                    coins.append(Coin(screen, zombie.rect.centerx, zombie.rect.centery))
                    zombies.remove(zombie)
    
    def get_attack_rect(self):
        if not self.attacking:
            return None
        
        attack_rect = pygame.Rect(0, 0, 80, 60)
        offset_x = 40 if self.facing_right else -40
        attack_rect.center = (self.rect.centerx + offset_x, self.rect.centery)
        return attack_rect
    
    def take_damage(self, amount):
        if not self.invulnerable:
            self.health -= amount
            if self.health < 0:
                self.health = 0
            self.invulnerable = True
            self.last_hit_time = pygame.time.get_ticks()
    
    def draw(self):
        if not self.invulnerable or (self.invulnerable and self.flicker):
            self.screen.blit(self.image, self.rect)
    
    def equip_weapon(self, weapon):
        self.equipped_weapon = weapon
        self.damage = weapon.damage

class Zombie:
    def __init__(self, screen, x, y, health, damage, speed, zombie_type, is_boss=False):
        self.screen = screen
        self.zombie_type = zombie_type
        self.is_boss = is_boss
        self.health = health
        self.max_health = health
        self.damage = damage
        self.speed = speed
        self.state = "idle"
        self.facing_right = True
        self.image = load_image(f"assets/{zombie_type}/Idle.png", 1.5 if is_boss else 1.0)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.target = None
        self.is_attacking = False
        self.attack_cooldown = 1000
        self.last_attack_time = 0
        self.attack_range = 50 if not is_boss else 70

    def update(self, player1, player2, dt):
        if self.state == "dead":
            return True  # Ready to be removed
            
        # Find closest player
        dist_to_player1 = math.hypot(self.rect.centerx - player1.rect.centerx, 
                                   self.rect.centery - player1.rect.centery)
        dist_to_player2 = math.hypot(self.rect.centerx - player2.rect.centerx,
                                   self.rect.centery - player2.rect.centery)
        
        self.target = player1 if dist_to_player1 <= dist_to_player2 else player2
        distance = min(dist_to_player1, dist_to_player2)
        
        # Movement direction
        dx = self.target.rect.centerx - self.rect.centerx
        dy = self.target.rect.centery - self.rect.centery
        self.facing_right = dx > 0
        
        # Normalize direction
        dist = max(1, math.hypot(dx, dy))
        dx, dy = dx / dist, dy / dist
        
        current_time = pygame.time.get_ticks()
        
        # Combat logic
        if distance <= self.attack_range:
            if not self.is_attacking and current_time - self.last_attack_time > self.attack_cooldown:
                self.is_attacking = True
                self.last_attack_time = current_time
                self.image = load_image(f"assets/{self.zombie_type}/Attack.png", 1.5 if self.is_boss else 1.0)
                
                if distance < self.attack_range * 0.8 and self.target.is_vulnerable():
                    self.target.take_damage(self.damage)
        else:
            self.state = "walk"
            self.rect.x += dx * self.speed
            self.rect.y += dy * self.speed
            self.image = load_image(f"assets/{self.zombie_type}/Walk.png", 1.5 if self.is_boss else 1.0)
        
        # Reset attack state
        if self.is_attacking and current_time - self.last_attack_time > 500:
            self.is_attacking = False
            self.image = load_image(f"assets/{self.zombie_type}/Idle.png", 1.5 if self.is_boss else 1.0)
        
        # Flip image if needed
        if not self.facing_right:
            self.image = pygame.transform.flip(self.image, True, False)
        
        return False

    def take_damage(self, amount):
        if self.state == "dead":
            return False
            
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.state = "dead"
            self.image = load_image(f"assets/{self.zombie_type}/Dead.png", 1.5 if self.is_boss else 1.0)
            return True  # Zombie died
        else:
            self.image = load_image(f"assets/{self.zombie_type}/Hurt.png", 1.5 if self.is_boss else 1.0)
            return False

    def draw(self):
        self.screen.blit(self.image, self.rect)
        
        # Health bar
        if self.state != "dead":
            health_bar_width = 60 if self.is_boss else 40
            health_ratio = self.health / self.max_health
            
            # Background
            pygame.draw.rect(
                self.screen, (60, 60, 60),
                (self.rect.centerx - health_bar_width//2, self.rect.top - 10, 
                 health_bar_width, 5)
            )
            
            # Health level
            health_color = (255, 215, 0) if self.is_boss else (0, 255, 0)
            pygame.draw.rect(
                self.screen, health_color,
                (self.rect.centerx - health_bar_width//2, self.rect.top - 10,
                 int(health_bar_width * health_ratio), 5)
            )
            
            # Border
            pygame.draw.rect(
                self.screen, (255, 255, 255),
                (self.rect.centerx - health_bar_width//2, self.rect.top - 10,
                 health_bar_width, 5), 1
            )

class UI:
    def __init__(self, screen):
        self.screen = screen
    
    def draw_health_bar(self, health, max_health, x, y, label=None):
        bar_width = 200
        bar_height = 20
        
        if label:
            label_text = font_small.render(label, True, WHITE)
            self.screen.blit(label_text, (x, y - 20))
        
        pygame.draw.rect(self.screen, RED, (x, y, bar_width, bar_height))
        health_width = max(0, (health / max_health) * bar_width)
        pygame.draw.rect(self.screen, GREEN, (x, y, health_width, bar_height))
        pygame.draw.rect(self.screen, WHITE, (x, y, bar_width, bar_height), 2)
        
        health_text = font_small.render(f"HP: {health}/{max_health}", True, WHITE)
        self.screen.blit(health_text, (x + 5, y + 2))
    
    def draw_coins(self, coins, x, y):
        coin_text = font_medium.render(f"Coins: {coins}", True, YELLOW)
        self.screen.blit(coin_text, (x, y))
    
    def draw_stage(self, stage, x, y):
        stage_text = font_large.render(f"Stage {stage}", True, WHITE)
        self.screen.blit(stage_text, (x, y))
    
    def draw_stage_transition(self, stage):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        if stage in STAGE_BOSSES:
            text = font_large.render(f"BOSS STAGE!", True, (255, 50, 50))
        else:
            text = font_large.render(f"Stage {stage}", True, WHITE)
        
        text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.screen.blit(text, text_rect)

# Initialize game objects
ui = UI(screen)
player1 = None
player2 = None
zombies = []
coins = []
current_stage = 1
max_stages = 5
player1_coins = 0
player2_coins = 0
spawn_timer = 0
spawn_interval = 2000
zombie_types = ["zombie1", "zombie2", "zombie3"]
zombies_spawned = 0
stage_transition_timer = 0
stage_transition_duration = 2000  # 2 seconds

def init_game():
    global player1, player2, zombies, coins, current_stage, player1_coins, player2_coins, zombies_spawned
    player1 = Player(screen, SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2, 100, 10, 5, 1)
    player2 = Player(screen, 3 * SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2, 100, 10, 5, 2)
    zombies.clear()
    coins.clear()
    current_stage = 1
    player1_coins = 0
    player2_coins = 0
    zombies_spawned = 0

def spawn_zombie():
    global zombies_spawned
    
    if zombies_spawned >= STAGE_ZOMBIE_COUNTS[current_stage]:
        return
    
    # Spawn boss if it's time
    if zombies_spawned == STAGE_ZOMBIE_COUNTS[current_stage] - 1 and current_stage in STAGE_BOSSES:
        spawn_boss()
        zombies_spawned += 1
        return
    
    zombie_type = random.choice(zombie_types)
    side = random.randint(0, 3)
    
    if side == 0:  # Top
        x = random.randint(0, SCREEN_WIDTH)
        y = -50
    elif side == 1:  # Right
        x = SCREEN_WIDTH + 50
        y = random.randint(0, SCREEN_HEIGHT)
    elif side == 2:  # Bottom
        x = random.randint(0, SCREEN_WIDTH)
        y = SCREEN_HEIGHT + 50
    else:  # Left
        x = -50
        y = random.randint(0, SCREEN_HEIGHT)
    
    health = 80 + current_stage * 20
    speed = 1 + current_stage * 0.2
    
    zombies.append(Zombie(screen, x, y, health, 5 + current_stage * 2, speed, zombie_type))
    zombies_spawned += 1

def spawn_boss():
    boss_type = STAGE_BOSSES[current_stage]
    side = random.randint(0, 3)
    
    if side == 0:  # Top
        x = random.randint(100, SCREEN_WIDTH - 100)
        y = -100
    elif side == 1:  # Right
        x = SCREEN_WIDTH + 100
        y = random.randint(100, SCREEN_HEIGHT - 100)
    elif side == 2:  # Bottom
        x = random.randint(100, SCREEN_WIDTH - 100)
        y = SCREEN_HEIGHT + 100
    else:  # Left
        x = -100
        y = random.randint(100, SCREEN_HEIGHT - 100)
    
    health = 300 + current_stage * 50
    damage = 20 + current_stage * 5
    speed = 1.5 + current_stage * 0.1
    
    zombies.append(Zombie(screen, x, y, health, damage, speed, boss_type, is_boss=True))

def check_stage_completion():
    global current_stage, zombies_spawned, stage_transition_timer
    
    if (len(zombies) == 0 and 
        zombies_spawned >= STAGE_ZOMBIE_COUNTS[current_stage] and 
        current_stage < max_stages):
        
        current_stage += 1
        zombies_spawned = 0
        stage_transition_timer = pygame.time.get_ticks()
        return True
    return False

def draw_menu():
    screen.fill(BLACK)
    
    title_shadow = title_font.render("Attack On Heec", True, (50, 50, 50))
    title_text = title_font.render("Attack On Heec", True, (220, 20, 20))
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
    screen.blit(title_shadow, (title_rect.x + 3, title_rect.y + 3))
    screen.blit(title_text, title_rect)
    
    button_text = button_font.render("PLAY", True, WHITE)
    button_rect = button_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    
    pygame.draw.rect(screen, (100, 10, 10), 
                    (button_rect.x - 25, button_rect.y - 15, 
                     button_rect.width + 50, button_rect.height + 30))
    pygame.draw.rect(screen, (150, 20, 20), 
                    (button_rect.x - 20, button_rect.y - 10, 
                     button_rect.width + 40, button_rect.height + 20))
    pygame.draw.rect(screen, (50, 0, 0), 
                    (button_rect.x - 25, button_rect.y - 15, 
                     button_rect.width + 50, button_rect.height + 30), 2)
    
    screen.blit(button_text, button_rect)
    
    return button_rect

def draw_game_over():
    screen.fill(BLACK)
    gameover_text = title_font.render("GAME OVER", True, RED)
    gameover_rect = gameover_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
    screen.blit(gameover_text, gameover_rect)
    
    button_text = button_font.render("PLAY AGAIN", True, WHITE)
    button_rect = button_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    pygame.draw.rect(screen, (50, 50, 50), 
                    (button_rect.x - 20, button_rect.y - 10, 
                     button_rect.width + 40, button_rect.height + 20))
    screen.blit(button_text, button_rect)
    
    return button_rect

# Main game loop
running = True
while running:
    dt = clock.tick(FPS)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            if current_state == MENU:
                button_rect = draw_menu()
                if button_rect.collidepoint(mouse_pos):
                    current_state = PLAYING
                    init_game()
            
            elif current_state == GAME_OVER:
                button_rect = draw_game_over()
                if button_rect.collidepoint(mouse_pos):
                    current_state = PLAYING
                    init_game()
    
    if current_state == MENU:
        draw_menu()
    
    elif current_state == PLAYING:
        # Update game objects
        player1.update()
        player2.update()
        
        # Check for game over
        if player1.health <= 0 and player2.health <= 0:
            current_state = GAME_OVER
        
        # Spawn zombies
        spawn_timer += dt
        if spawn_timer >= spawn_interval and zombies_spawned < STAGE_ZOMBIE_COUNTS[current_stage]:
            spawn_timer = 0
            spawn_zombie()
        
        # Update zombies
        for zombie in list(zombies):
            if zombie.update(player1, player2, dt):
                zombies.remove(zombie)
            
            if zombie.rect.colliderect(player1.rect) and player1.is_vulnerable():
                player1.take_damage(zombie.damage)
            
            if zombie.rect.colliderect(player2.rect) and player2.is_vulnerable():
                player2.take_damage(zombie.damage)
        
        # Update coins
        for coin in list(coins):
            if coin.rect.colliderect(player1.rect):
                player1_coins += coin.value
                coins.remove(coin)
            elif coin.rect.colliderect(player2.rect):
                player2_coins += coin.value
                coins.remove(coin)
            elif not coin.update(dt):
                coins.remove(coin)
        
        # Check stage completion
        if check_stage_completion():
            current_state = STAGE_TRANSITION
    
    elif current_state == STAGE_TRANSITION:
        if pygame.time.get_ticks() - stage_transition_timer > stage_transition_duration:
            current_state = PLAYING
            spawn_interval = max(500, 2000 - (current_stage - 1) * 300)
        
        # Draw everything
        screen.fill(BLACK)
        ui.draw_stage_transition(current_stage)
    
    elif current_state == GAME_OVER:
        draw_game_over()
    
    if current_state == PLAYING:
        # Draw everything
        screen.fill(BLACK)
        
        for coin in coins:
            coin.draw()
        
        for zombie in zombies:
            zombie.draw()
        
        player1.draw()
        player2.draw()
        
        ui.draw_health_bar(player1.health, player1.max_health, SCREEN_WIDTH - 210, SCREEN_HEIGHT - 30, "Player 1")
        ui.draw_health_bar(player2.health, player2.max_health, 10, SCREEN_HEIGHT - 30, "Player 2")
        ui.draw_coins(player1_coins, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 60)
        ui.draw_coins(player2_coins, 10, SCREEN_HEIGHT - 60)
        ui.draw_stage(current_stage, SCREEN_WIDTH // 2 - 50, 10)
    
    pygame.display.flip()

pygame.quit()
sys.exit()