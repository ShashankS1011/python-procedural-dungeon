# 🕯️ Shadow Depths: The Python Rogue

> An infinite, procedurally generated dungeon crawler built from scratch with Python & Pygame.

![Game Banner or Screenshot Here](assets/image.png)
*(Note: Replace this line with a link to a screenshot of your game!)*

## 📜 The Story
The **Shadow Depths** are not a place—they are a hunger. 

Legends say the caverns shift and change with every soul that enters. No two maps are ever the same. You are a lone adventurer seeking the **Golden Stairs**, descending deeper into the abyss where the darkness grows thicker and the beasts grow stronger.

Armed with your steel blade and the forbidden art of Fire magic, how deep can you go before the void claims you?

## ✨ Key Features

### 🧠 **Procedural Generation (The "Logic" Core)**
Instead of pre-made levels, the game uses the **Drunkard's Walk Algorithm**.
- A virtual "walker" stumbles through a grid, carving out organic, connected cave systems.
- This ensures every floor is unique and fully traversable.

### ⚔️ **Combat & Gameplay**
- **Dual Combat Styles:** Engage in close-quarters melee (Sword) or keep your distance with magic (Fireballs).
- **Infinite Scaling:** There is no end. Every time you find the stairs, the level increases, and enemies gain HP and Damage.
- **Loot System:** Scavenge for potions to survive the increasing difficulty.

### 🎨 **Visual "Juice" & Polish**
- **Dynamic Fog of War:** A lighting system that restricts visibility, forcing cautious exploration.
- **Particle System:** Custom-built physics for blood splatter effects on hit.
- **Screenshake:** Visceral feedback when the player takes damage.
- **Asset Fallback:** The engine features a "Safe Load" system. If sprite images are missing, it automatically generates colored geometric placeholders so the game never crashes.

## 🎮 Controls

| Key | Action |
| :--- | :--- |
| **Arrow Keys** | Move Character |
| **Spacebar** | Sword Attack (Melee) |
| **Z Key** | Fireball (Ranged) |
| **R Key** | Restart (Only on Game Over screen) |

## 🛠️ Tech Stack & Concepts
* **Language:** Python 3.10+
* **Engine:** Pygame (SDL wrapper)
* **Math:** Vector normalization (for AI pathing), Trigonometry (for animations), Collision detection (AABB).

## 🚀 Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/shadow-depths.git](https://github.com/YOUR_USERNAME/shadow-depths.git)
    cd shadow-depths
    ```

2.  **Install Dependencies**
    You only need Pygame!
    ```bash
    pip install pygame
    ```

3.  **Run the Game**
    ```bash
    python main.py
    ```

## 📂 Project Structure

```text
shadow-depths/
├── assets/          # Sprites (png images)
├── main.py          # The game loop, classes, and logic
├── dungeon_gen.py   # The procedural generation algorithm
└── README.md        # This file
