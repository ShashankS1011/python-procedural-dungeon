import pygame
import sys
import math
import random

# --- 1. SETUP & CONSTANTS ---
pygame.init()
pygame.font.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
TILE_SIZE = 32
FPS = 60

# Map Constants (Formerly in dungeon_gen.py)
WALL = "#"
FLOOR = "."

# Colors
BLACK = (0, 0, 0)
FLOOR_COLOR = (25, 25, 35)      
WALL_COLOR = (80, 80, 100)
PLAYER_COLOR = (50, 200, 50)
ENEMY_COLOR = (200, 50, 50)
FIREBALL_COLOR = (255, 100, 0)
SWORD_COLOR = (255, 255, 255)
STAIRS_COLOR = (255, 215, 0)    
POTION_COLOR = (255, 50, 50)    
PARTICLE_COLOR = (180, 20, 20)  

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

# --- 2. MAP GENERATOR FUNCTION (Moved here!) ---
def generate_dungeon(width=50, height=50):
    # 1. Fill map with walls
    game_map = [[WALL for _ in range(width)] for _ in range(height)]
    
    # 2. Drunkard's Walk Settings
    max_steps = 800  # How much floor to dig
    x, y = width // 2, height // 2 # Start in middle
    
    # 3. Start walking
    for _ in range(max_steps):
        game_map[y][x] = FLOOR # Dig a floor here
        
        # Pick random direction
        direction = random.choice(['N', 'S', 'E', 'W'])
        if direction == 'N' and y > 1: y -= 1
        elif direction == 'S' and y < height - 2: y += 1
        elif direction == 'E' and x < width - 2: x += 1
        elif direction == 'W' and x > 1: x -= 1
            
    return game_map

# --- 3. ASSETS ---
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
        elif shape == "triangle": 
             pygame.draw.polygon(surf, color_fallback, [(TILE_SIZE//2, 0), (0, TILE_SIZE), (TILE_SIZE, TILE_SIZE)])
        else:
            surf.fill(color_fallback)
        assets[name] = surf

load_image("floor", "floor.png", FLOOR_COLOR)
load_image("wall", "wall.png", WALL_COLOR)
load_image("player", "player.png", PLAYER_COLOR)
load_image("enemy", "enemy.png", ENEMY_COLOR)
load_image("fireball", "fireball.png", FIREBALL_COLOR, shape="circle")
load_image("stairs", "stairs.png", STAIRS_COLOR, shape="triangle")
load_image("potion", "potion.png", POTION_COLOR, shape="circle")

# --- 4. CLASSES ---

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.dx = random.uniform(-3, 3) 
        self.dy = random.uniform(-3, 3)
        self.life = random.randint(10, 20) 
        self.size = random.randint(2, 5)

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.life -= 1
        self.size = max(0, self.size - 0.1) 

class Item:
    def __init__(self, x, y, item_type="potion"):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.type = item_type
        self.image = assets["potion"]
        self.bob_offset = 0

    def update(self):
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
        self.speed = random.uniform(1.5, 2.5) 
        self.image = assets["enemy"]
        self.hp = 3 + (level * 2) 
        self.damage = 10 + (level * 2)

    def update(self, target_rect, map_data, w, h):
        dx = target_rect.x - self.rect.x
        dy = target_rect.y - self.rect.y
        dist = math.hypot(dx, dy)

        if 0 < dist < 400: 
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
            screenshake_trigger(10) 
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
                    enemy.hp -= 3 
                    screenshake_trigger(2) 
                    for _ in range(5):
                        particles.append(Particle(enemy.rect.centerx, enemy.rect.centery))

    def attack_fireball(self, projectiles):
        if self.cooldown == 0:
            self.cooldown = 30
            proj = Projectile(self.rect.centerx, self.rect.centery, self.facing[0], self.facing[1])
            projectiles.append(proj)

# --- 5. GAME FUNCTIONS ---

def check_collision(rect, map_data, width, height):
    left = max(0, rect.left // TILE_SIZE)
    right = min(width, rect.right // TILE_SIZE + 1)
    top = max(0, rect.top // TILE_SIZE)
    bottom = min(height, rect.bottom // TILE_SIZE + 1)

    for y in range(top, bottom):
        for x in range(left, right):
            if map_data[y][x] == WALL:
                if rect.colliderect(pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE)):
                    return True
    return False

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
    game_map = generate_dungeon()
    w, h = len(game_map[0]), len(game_map)
    
    start_x, start_y = w // 2, h // 2
    if player_obj:
        player_obj.rect.topleft = (start_x * TILE_SIZE, start_y * TILE_SIZE)
        player_obj.level = level_num
    else:
        player_obj = Player(start_x * TILE_SIZE, start_y * TILE_SIZE)

    enemies = []
    enemy_count = 5 + (level_num * 2)
    for _ in range(enemy_count):
        while True:
            ex, ey = random.randint(1, w-2), random.randint(1, h-2)
            if game_map[ey][ex] == FLOOR:
                if abs(ex - start_x) > 5 or abs(ey - start_y) > 5:
                    enemies.append(Enemy(ex * TILE_SIZE, ey * TILE_SIZE, level_num))
                    break
    
    stairs = None
    while True:
        sx, sy = random.randint(1, w-2), random.randint(1, h-2)
        if game_map[sy][sx] == FLOOR:
             if abs(sx - start_x) > 10 or abs(sy - start_y) > 10: 
                stairs = Stairs(sx * TILE_SIZE, sy * TILE_SIZE)
                break

    return game_map, w, h, player_obj, enemies, stairs, [], [], [] 

# --- 6. LIGHTING ---
light_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
light_surface.fill(BLACK)
pygame.draw.circle(light_surface, (20, 20, 20), (SCREEN_WIDTH//2, SCREEN_HEIGHT//2), 150)
light_surface.set_colorkey((20, 20, 20))

# --- 7. MAIN LOOP ---
game_map, MAP_W, MAP_H, player, enemies, stairs, items, projectiles, particles = generate_level(1)
game_active = True

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        
        if event.type == pygame.KEYDOWN:
            if game_active:
                if event.key == pygame.K_SPACE: player.attack_sword(enemies, particles)
                if event.key == pygame.K_z: player.attack_fireball(projectiles)
            else:
                if event.key == pygame.K_r: 
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

        for p in projectiles[:]:
            p.update(game_map, MAP_W, MAP_H)
            if p.life <= 0: projectiles.remove(p); continue
            for enemy in enemies[:]:
                if p.rect.colliderect(enemy.rect):
                    enemy.hp -= 2
                    for _ in range(3): particles.append(Particle(enemy.rect.centerx, enemy.rect.centery))
                    if p in projectiles: projectiles.remove(p)
                    break
        
        for enemy in enemies[:]:
            enemy.update(player.rect, game_map, MAP_W, MAP_H)
            if player.rect.colliderect(enemy.rect):
                player.take_damage(enemy.damage)
            
            if enemy.hp <= 0:
                if random.random() < 0.3: 
                    items.append(Item(enemy.rect.x, enemy.rect.y))
                enemies.remove(enemy)

        for item in items[:]:
            item.update()
            if player.rect.colliderect(item.rect):
                player.heal(25)
                items.remove(item)

        for p in particles[:]:
            p.update()
            if p.life <= 0: particles.remove(p)

        if player.rect.colliderect(stairs.rect):
            game_map, MAP_W, MAP_H, player, enemies, stairs, items, projectiles, particles = generate_level(player.level + 1, player)

        if player.hp <= 0:
            game_active = False

    screen.fill(BLACK)
    
    shake_x, shake_y = apply_screenshake()
    cam_x = player.rect.x - (SCREEN_WIDTH // 2) + shake_x
    cam_y = player.rect.y - (SCREEN_HEIGHT // 2) + shake_y

    start_col = max(0, cam_x // TILE_SIZE)
    end_col = min(MAP_W, (cam_x + SCREEN_WIDTH) // TILE_SIZE + 1)
    start_row = max(0, cam_y // TILE_SIZE)
    end_row = min(MAP_H, (cam_y + SCREEN_HEIGHT) // TILE_SIZE + 1)

    for row in range(start_row, end_row):
        for col in range(start_col, end_col):
            tile = game_map[row][col]
            draw_x, draw_y = (col * TILE_SIZE) - cam_x, (row * TILE_SIZE) - cam_y
            if tile == WALL: screen.blit(assets["wall"], (draw_x, draw_y))
            else: screen.blit(assets["floor"], (draw_x, draw_y))

    screen.blit(stairs.image, (stairs.rect.x - cam_x, stairs.rect.y - cam_y))
    for item in items: screen.blit(item.image, (item.rect.x - cam_x, item.rect.y - cam_y))
    for enemy in enemies: screen.blit(enemy.image, (enemy.rect.x - cam_x, enemy.rect.y - cam_y))
    for p in projectiles: screen.blit(p.image, (p.rect.x - cam_x, p.rect.y - cam_y))
    
    if not (player.invincibility_timer > 0 and (player.invincibility_timer // 5) % 2 == 0):
        screen.blit(player.image, (player.rect.x - cam_x, player.rect.y - cam_y))

    for p in particles:
        pygame.draw.rect(screen, PARTICLE_COLOR, (p.x - cam_x, p.y - cam_y, p.size, p.size))

    if player.is_attacking:
        slash_x = (player.rect.x - cam_x) + (player.facing[0] * TILE_SIZE)
        slash_y = (player.rect.y - cam_y) + (player.facing[1] * TILE_SIZE)
        pygame.draw.rect(screen, SWORD_COLOR, (slash_x, slash_y, TILE_SIZE, TILE_SIZE))

    screen.blit(light_surface, (0, 0))

    if game_active:
        pygame.draw.rect(screen, HP_BAR_COLOR, (20, 20, 200, 25))
        pygame.draw.rect(screen, HP_BAR_FILL, (20, 20, (player.hp/player.max_hp)*200, 25))
        pygame.draw.rect(screen, (255,255,255), (20, 20, 200, 25), 2) 
        
        lvl_text = font.render(f"Dungeon Level: {player.level}", True, STAIRS_COLOR)
        screen.blit(lvl_text, (20, 55))
        
        if player.hp < 30:
            warn = font.render("Low Health! Find potions!", True, (255, 0, 0))
            screen.blit(warn, (20, 80))
    else:
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