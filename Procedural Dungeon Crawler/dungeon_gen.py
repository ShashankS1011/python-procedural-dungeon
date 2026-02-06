import random

# Constants
WIDTH = 50  # Map width in tiles
HEIGHT = 50 # Map height in tiles
FLOOR = 0
WALL = 1

def generate_dungeon():
    # 1. Create a map filled with WALLS
    # List comprehension to make a 2D grid
    dungeon_map = [[WALL for _ in range(WIDTH)] for _ in range(HEIGHT)]

    # 2. Start the "Drunkard" in the middle
    x, y = WIDTH // 2, HEIGHT // 2
    dungeon_map[y][x] = FLOOR 
    
    floor_count = 1
    target_floors = 800 # How many floor tiles we want

    # 3. Walk until we have enough floor
    while floor_count < target_floors:
        # Pick a random direction: (dx, dy)
        direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
        
        # Move
        x += direction[0]
        y += direction[1]

        # Check bounds (don't walk off the map edge!)
        if 1 < x < WIDTH - 1 and 1 < y < HEIGHT - 1:
            if dungeon_map[y][x] == WALL:
                dungeon_map[y][x] = FLOOR
                floor_count += 1
                
    return dungeon_map

# Test it!
if __name__ == "__main__":
    my_map = generate_dungeon()
    # Print it to the console to see the shape
    for row in my_map:
        line = "".join(["#" if tile == WALL else " " for tile in row])
        print(line)