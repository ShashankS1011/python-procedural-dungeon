import pygame
import sys
import math
import random
import dungeon_gen

# --- 1. SETUP & CONSTANTS ---
pygame.init()
pygame.font.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
TILE_SIZE = 32
FPS = 60

# Colors
BLACK = (0, 0, 0)
FLOOR_COLOR = (25, 25, 35)      # Darker floor for atmosphere
WALL_COLOR = (80, 80, 100)
PLAYER_COLOR = (50, 200, 50)
ENEMY_COLOR = (200, 50, 50)
FIREBALL_COLOR = (255, 100, 0)
SWORD_COLOR = (255, 255, 255)
STAIRS_COLOR = (255, 215, 0)    # Gold
POTION_COLOR = (255, 50, 50)    # Red potion
PARTICLE_COLOR = (180, 20, 20)  # Blood red

# UI Colors
UI_BG_COLOR = (50, 50, 50)
HP_BAR_COLOR = (100, 0, 0)
HP_BAR_FILL = (0, 200, 0)
TEXT_COLOR = (255, 255, 255)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Ultimate Dungeon Crawler")
clock = pygame.time.Clock()
font = pygame.font.SysFont('Arial', 20, bold=True)
big_font = pygame.font.SysFont('Arial', 60, bold=True)

# --- 2. ASSETS ---
assets = {}

def load_image(name, filename, color_fallback, shape="rect"):
    try:
        img = pygame.image.load(f"assets/{filename}").convert_alpha()
        img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
        assets[name] = img
    except:
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        if shape == "circle":
            pygame.draw.circle(surf, color_fallback, (TILE_SIZE//2, TILE_SIZE//2), TILE_SIZE//2)
        elif shape == "triangle": # For stairs
             pygame.draw.polygon(surf, color_fallback, [(TILE_SIZE//2, 0), (0, TILE_SIZE), (TILE_SIZE, TILE_SIZE)])
        else:
            surf.fill(color_fallback)
        assets[name] = surf

# Load assets (with shapes for clarity if images missing)
load_image("floor", "floor.png", FLOOR_COLOR)
load_image("wall", "wall.png", WALL_COLOR)
load_image("player", "player.png", PLAYER_COLOR)
load_image("enemy", "enemy.png", ENEMY_COLOR)
load_image("fireball", "fireball.png", FIREBALL_COLOR, shape="circle")
load_image("stairs", "stairs.png", STAIRS_COLOR, shape="triangle")
load_image("potion", "potion.png", POTION_COLOR, shape="circle")

# --- 3. CLASSES ---

class Particle:
    """Visual effect for blood splatter"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.dx = random.uniform(-3, 3) # Random direction
        self.dy = random.uniform(-3, 3)
        self.life = random.randint(10, 20) # Frames to live
        self.size = random.randint(2, 5)

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.life -= 1
        self.size = max(0, self.size - 0.1) # Shrink

class Item:
    """Potions on the ground"""
    def __init__(self, x, y, item_type="potion"):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.type = item_type
        self.image = assets["potion"]
        self.bob_offset = 0

    def update(self):
        # Bobbing animation
        self.bob_offset += 0.1
        self.rect.y += math.sin(self.bob_offset) * 0.5

class Stairs:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.image = assets["stairs"]

class Projectile:
    def __init__(self, x, y, dx, dy):
        self.rect = pygame.Rect(x, y, 16, 16)
        self.dx = dx * 8
        self.dy = dy * 8
        self.image = assets["fireball"]
        self.life = 60

    def update(self, map_data, w, h):
        self.rect.x += self.dx
        self.rect.y += self.dy
        self.life -= 1
        if check_collision(self.rect, map_data, w, h):
            self.life = 0

class Enemy:
    def __init__(self, x, y, level):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.speed = random.uniform(1.5, 2.5) # Random speeds
        self.image = assets["enemy"]
        # DIFFICULTY SCALING: Harder enemies on deeper levels
        self.hp = 3 + (level * 2) 
        self.damage = 10 + (level * 2)

    def update(self, target_rect, map_data, w, h):
        dx = target_rect.x - self.rect.x
        dy = target_rect.y - self.rect.y
        dist = math.hypot(dx, dy)

        if 0 < dist < 400: # Only chase if player is close (Optimization)
            move_x = (dx / dist) * self.speed
            move_y = (dy / dist) * self.speed
            
            self.rect.x += int(move_x)
            if check_collision(self.rect, map_data, w, h): self.rect.x -= int(move_x)
            self.rect.y += int(move_y)
            if check_collision(self.rect, map_data, w, h): self.rect.y -= int(move_y)

class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.speed = 5
        self.image = assets["player"]
        self.facing = (1, 0)
        
        self.max_hp = 100
        self.hp = 100
        self.level = 1
        self.xp = 0
        
        self.cooldown = 0
        self.is_attacking = False
        self.invincibility_timer = 0

    def move(self, dx, dy, map_data, w, h):
        if dx != 0 or dy != 0:
            self.facing = (dx/abs(dx) if dx else 0, dy/abs(dy) if dy else 0)

        self.rect.x += dx
        if check_collision(self.rect, map_data, w, h): self.rect.x -= dx 
        self.rect.y += dy
        if check_collision(self.rect, map_data, w, h): self.rect.y -= dy

        if self.cooldown > 0:
            self.cooldown -= 1
            if self.cooldown < 10: self.is_attacking = False
        
        if self.invincibility_timer > 0:
            self.invincibility_timer -= 1

    def take_damage(self, amount):
        if self.invincibility_timer == 0:
            self.hp -= amount
            self.invincibility_timer = 60
            screenshake_trigger(10) # TRIGGER SHAKE!
            if self.hp < 0: self.hp = 0

    def heal(self, amount):
        self.hp += amount
        if self.hp > self.max_hp: self.hp = self.max_hp

    def attack_sword(self, enemies, particles):
        if self.cooldown == 0:
            self.cooldown = 20
            self.is_attacking = True
            attack_rect = pygame.Rect(
                self.rect.x + (self.facing[0] * TILE_SIZE), 
                self.rect.y + (self.facing[1] * TILE_SIZE), 
                TILE_SIZE, TILE_SIZE
            )

            for enemy in enemies[:]:
                if attack_rect.colliderect(enemy.rect):
                    enemy.hp -= 3 # Stronger melee
                    screenshake_trigger(2) # Tiny shake on hit
                    # Spawn blood
                    for _ in range(5):
                        particles.append(Particle(enemy.rect.centerx, enemy.rect.centery))

    def attack_fireball(self, projectiles):
        if self.cooldown == 0:
            self.cooldown = 30
            proj = Projectile(self.rect.centerx, self.rect.centery, self.facing[0], self.facing[1])
            projectiles.append(proj)

# --- 4. GAME FUNCTIONS ---

def check_collision(rect, map_data, width, height):
    left = max(0, rect.left // TILE_SIZE)
    right = min(width, rect.right // TILE_SIZE + 1)
    top = max(0, rect.top // TILE_SIZE)
    bottom = min(height, rect.bottom // TILE_SIZE + 1)

    for y in range(top, bottom):
        for x in range(left, right):
            if map_data[y][x] == dungeon_gen.WALL:
                if rect.colliderect(pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE)):
                    return True
    return False

# Global Screenshake Variable
shake_intensity = 0

def screenshake_trigger(amount):
    global shake_intensity
    shake_intensity = amount

def apply_screenshake():
    global shake_intensity
    if shake_intensity > 0:
        offset_x = random.randint(-shake_intensity, shake_intensity)
        offset_y = random.randint(-shake_intensity, shake_intensity)
        shake_intensity -= 1
        return offset_x, offset_y
    return 0, 0

def generate_level(level_num, player_obj=None):
    game_map = dungeon_gen.generate_dungeon()
    w, h = len(game_map[0]), len(game_map)
    
    # 1. Spawn Player
    start_x, start_y = w // 2, h // 2
    if player_obj:
        player_obj.rect.topleft = (start_x * TILE_SIZE, start_y * TILE_SIZE)
        player_obj.level = level_num
    else:
        player_obj = Player(start_x * TILE_SIZE, start_y * TILE_SIZE)

    # 2. Spawn Enemies (More enemies on higher levels)
    enemies = []
    enemy_count = 5 + (level_num * 2)
    for _ in range(enemy_count):
        while True:
            ex, ey = random.randint(1, w-2), random.randint(1, h-2)
            if game_map[ey][ex] == dungeon_gen.FLOOR:
                # Ensure enemy doesn't spawn ON the player
                if abs(ex - start_x) > 5 or abs(ey - start_y) > 5:
                    enemies.append(Enemy(ex * TILE_SIZE, ey * TILE_SIZE, level_num))
                    break
    
    # 3. Spawn Stairs (Far from player)
    stairs = None
    while True:
        sx, sy = random.randint(1, w-2), random.randint(1, h-2)
        if game_map[sy][sx] == dungeon_gen.FLOOR:
             if abs(sx - start_x) > 10 or abs(sy - start_y) > 10: # Ensure distance
                stairs = Stairs(sx * TILE_SIZE, sy * TILE_SIZE)
                break

    return game_map, w, h, player_obj, enemies, stairs, [], [], [] # items, projectiles, particles

# --- 5. SETUP LIGHTING SURFACE ---
# We create a "Darkness" layer with a transparent hole
light_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
light_surface.fill(BLACK)
# Create a transparent circle (The Torch)
torch_radius = 150 # How far you can see
pygame.draw.circle(light_surface, (20, 20, 20), (SCREEN_WIDTH//2, SCREEN_HEIGHT//2), torch_radius)
# Use special blend mode to make the circle transparent
light_surface.set_colorkey((20, 20, 20))

# --- 6. MAIN LOOP ---
game_map, MAP_W, MAP_H, player, enemies, stairs, items, projectiles, particles = generate_level(1)
game_active = True

while True:
    # A. Input
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        
        if event.type == pygame.KEYDOWN:
            if game_active:
                if event.key == pygame.K_SPACE: player.attack_sword(enemies, particles)
                if event.key == pygame.K_z: player.attack_fireball(projectiles)
            else:
                if event.key == pygame.K_r: # Restart
                    game_map, MAP_W, MAP_H, player, enemies, stairs, items, projectiles, particles = generate_level(1)
                    game_active = True

    if game_active:
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]: dx = -player.speed
        if keys[pygame.K_RIGHT]: dx = player.speed
        if keys[pygame.K_UP]: dy = -player.speed
        if keys[pygame.K_DOWN]: dy = player.speed
        
        player.move(dx, dy, game_map, MAP_W, MAP_H)

        # Update Projectiles
        for p in projectiles[:]:
            p.update(game_map, MAP_W, MAP_H)
            if p.life <= 0: projectiles.remove(p); continue
            for enemy in enemies[:]:
                if p.rect.colliderect(enemy.rect):
                    enemy.hp -= 2
                    # Spawn blood
                    for _ in range(3): particles.append(Particle(enemy.rect.centerx, enemy.rect.centery))
                    if p in projectiles: projectiles.remove(p)
                    break
        
        # Update Enemies
        for enemy in enemies[:]:
            enemy.update(player.rect, game_map, MAP_W, MAP_H)
            if player.rect.colliderect(enemy.rect):
                player.take_damage(enemy.damage)
            
            if enemy.hp <= 0:
                # Chance to drop loot
                if random.random() < 0.3: # 30% chance
                    items.append(Item(enemy.rect.x, enemy.rect.y))
                enemies.remove(enemy)

        # Update Items
        for item in items[:]:
            item.update()
            if player.rect.colliderect(item.rect):
                player.heal(25)
                items.remove(item)

        # Update Particles
        for p in particles[:]:
            p.update()
            if p.life <= 0: particles.remove(p)

        # Check Stairs
        if player.rect.colliderect(stairs.rect):
            # NEXT LEVEL!
            game_map, MAP_W, MAP_H, player, enemies, stairs, items, projectiles, particles = generate_level(player.level + 1, player)

        if player.hp <= 0:
            game_active = False

    # B. Drawing
    screen.fill(BLACK)
    
    # Calculate Camera
    shake_x, shake_y = apply_screenshake()
    cam_x = player.rect.x - (SCREEN_WIDTH // 2) + shake_x
    cam_y = player.rect.y - (SCREEN_HEIGHT // 2) + shake_y

    # Draw Map (Visible Area Only)
    start_col = max(0, cam_x // TILE_SIZE)
    end_col = min(MAP_W, (cam_x + SCREEN_WIDTH) // TILE_SIZE + 1)
    start_row = max(0, cam_y // TILE_SIZE)
    end_row = min(MAP_H, (cam_y + SCREEN_HEIGHT) // TILE_SIZE + 1)

    for row in range(start_row, end_row):
        for col in range(start_col, end_col):
            tile = game_map[row][col]
            draw_x, draw_y = (col * TILE_SIZE) - cam_x, (row * TILE_SIZE) - cam_y
            if tile == dungeon_gen.WALL: screen.blit(assets["wall"], (draw_x, draw_y))
            else: screen.blit(assets["floor"], (draw_x, draw_y))

    # Draw Entities
    screen.blit(stairs.image, (stairs.rect.x - cam_x, stairs.rect.y - cam_y))
    for item in items: screen.blit(item.image, (item.rect.x - cam_x, item.rect.y - cam_y))
    for enemy in enemies: screen.blit(enemy.image, (enemy.rect.x - cam_x, enemy.rect.y - cam_y))
    for p in projectiles: screen.blit(p.image, (p.rect.x - cam_x, p.rect.y - cam_y))
    
    # Draw Player
    if not (player.invincibility_timer > 0 and (player.invincibility_timer // 5) % 2 == 0):
        screen.blit(player.image, (player.rect.x - cam_x, player.rect.y - cam_y))

    # Draw Particles
    for p in particles:
        pygame.draw.rect(screen, PARTICLE_COLOR, (p.x - cam_x, p.y - cam_y, p.size, p.size))

    # Draw Sword Slash
    if player.is_attacking:
        slash_x = (player.rect.x - cam_x) + (player.facing[0] * TILE_SIZE)
        slash_y = (player.rect.y - cam_y) + (player.facing[1] * TILE_SIZE)
        pygame.draw.rect(screen, SWORD_COLOR, (slash_x, slash_y, TILE_SIZE, TILE_SIZE))

    # --- DRAW LIGHTING (FOG OF WAR) ---
    # We blit the light surface ON TOP of the game world
    screen.blit(light_surface, (0, 0))

    # --- UI ---
    if game_active:
        # HP Bar
        pygame.draw.rect(screen, HP_BAR_COLOR, (20, 20, 200, 25))
        pygame.draw.rect(screen, HP_BAR_FILL, (20, 20, (player.hp/player.max_hp)*200, 25))
        pygame.draw.rect(screen, (255,255,255), (20, 20, 200, 25), 2) # Border
        
        # Level Text
        lvl_text = font.render(f"Dungeon Level: {player.level}", True, STAIRS_COLOR)
        screen.blit(lvl_text, (20, 55))
        
        # Instruction
        if player.hp < 30:
            warn = font.render("Low Health! Find potions!", True, (255, 0, 0))
            screen.blit(warn, (20, 80))
    else:
        # Game Over
        text = big_font.render("YOU DIED", True, (200, 0, 0))
        text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 50))
        screen.blit(text, text_rect)
        
        score_text = font.render(f"You reached Level {player.level}", True, TEXT_COLOR)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 20))
        screen.blit(score_text, score_rect)
        
        restart_text = font.render("Press 'R' to Restart", True, (200, 200, 200))
        res_rect = restart_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 60))
        screen.blit(restart_text, res_rect)

    pygame.display.flip()
    clock.tick(FPS)