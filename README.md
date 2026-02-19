# ♟️ The Ultimate Chess Engine Tutorial: A Step-by-Step Guide

Hello! This project is a complete Chess game built from scratch. Whether you want to play a game or learn how to code your own engine, this guide is for you.

## 🚀 1. Getting Started

Before we dive into the code, here is how you can run the game on your own computer:

1. **Install Python**: Make sure you have Python installed.
2. **Install Pygame**: Open your terminal and type:
   ```bash
   pip install pygame
   ```
3. **Run the Game**:
   ```bash
   python src/main.py
   ```

---

## 🏗️ 2. The Setup (Imports & Tools)

Every program starts by gathering the tools it needs. In Python, we call these **Imports**.

```python
import pygame  # The "Drawing & Games" toolbox.
import sys     # The "System" toolbox (used to close the game window).

pygame.init()  # This starts the Pygame engine. Think of it as turning on the engine of a car.
```

---

## 🎨 2. The Canvas (Constants & Window)

Before we draw pieces, we need a board and some colors. We use **Constants** (all caps) for values that never change.

```python
WIDHT, HEIGHT = 800, 800     # The window size is 800x800 pixels.
SQUARE_SIZE = WIDHT // 8     # 8 squares in a row, so each square is 100 pixels wide.

# We define colors using RGB (Red, Green, Blue) numbers (0 to 255).
WHITE = (255, 255, 255)      # Pure White
LIGHT_GREEN = (144, 238, 144) # The light squares on the board
YELLOW = (255, 255, 0)       # Used to highlight the piece you clicked
```

Next, we create the actual window:
```python
screen = pygame.display.set_mode((WIDHT, HEIGHT))
pygame.display.set_caption("Chess Game") # Sets the title at the top of the window
```

---

## 🧩 3. The Pieces (Blueprints)

We use a **Class** called `ChessPiece`. Think of a class as a "cookie cutter." Every individual piece (like the White King or Black Pawn) is a "cookie" made from this cutter.

```python
class ChessPiece:
    def __init__(self, color, type, image):
        self.color = color         # 'white' or 'black'
        self.type = type           # 'king', 'queen', etc.
        self.image = pygame.image.load(image) # Load the .png picture
        # Make the image fit perfectly inside a 100x100 square
        self.image = pygame.transform.scale(self.image, (SQUARE_SIZE, SQUARE_SIZE))
        self.has_moved = False     # Needed for Castling (you can't castle if you've moved!)
```

---

## 🗺️ 4. The Map (The Board & State)

The board is a **2D List** (a grid). It's like a list that contains 8 other lists, representing the 8 rows.

```python
board = [[None for _ in range(8)] for _ in range(8)]
```

We also track the **Global State**:
- `current_turn_color`: Whose turn is it?
- `active_selected_piece`: Which piece are you holding?
- `active_selected_pos`: Where was that piece on the grid?
- `legal_moves_for_selected`: Where can that piece legally move?
- `pawn_en_passant_target`: A special square for the En Passant capture rule.

---

## 🧠 5. The Logic: How Pieces Move

This is the most important part of the code! Every piece has a "Raw Move" list (where it can physically go).

### ♟️ The Pawn (Complexity: Medium)
Pawns are unique because they move forward but capture diagonally.
```python
if piece.type == 'pawn':
    move_dir = -1 if piece.color == 'white' else 1
    # Move forward 1 square
    if board[row + move_dir][col] is None:
        moves.append((row + move_dir, col))
        # Move forward 2 squares on the first turn
        if row == start_row and board[row + 2 * move_dir][col] is None:
            moves.append((row + 2 * move_dir, col))
    # Capture Diagonally
    for dc in [-1, 1]:
        if board[row + move_dir][col + dc] is an_enemy:
            moves.append((row + move_dir, col + dc))
```

### 🏇 The Knight (The Jumper)
Knights don't care about pieces in their way. They jump to 8 "L" spots.
```python
directions = [(2,1), (2,-1), (-2,1), (-2,-1), (1,2), (1,-2), (-1,2), (-1,-2)]
# The code checks each of these 8 spots around the Knight.
```

### 🏰 Sliding Pieces (Rook, Bishop, Queen)
These pieces use a `while` loop to slide until they hit a "wall" or another piece.
```python
while square_is_on_board:
    if square_is_empty:
        moves.append(square) # Keep sliding!
    elif square_has_enemy:
        moves.append(square) # Capture and STOP.
        break
    else:
        break # Hit a friend, STOP.
```

### 👑 The King
The King moves 1 square in any direction.
```python
directions = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
```

---

## 🛡️ 6. The "Brain": Legal Moves

In Chess, you **cannot** make a move that puts your own King in danger (Check). The computer uses **Simulation** to prevent this:

```python
for move in raw_moves:
    # 1. TEMPORARILY move the piece on the board
    # 2. ASK: "Is the King being attacked by an enemy right now?"
    # 3. IF NO: Add the move to the "Legal Moves" list.
    # 4. CRITICAL: Move the piece back to where it was (Undo).
```

---

## 🏰 7. Special Side Effects

When you move a piece, sometimes extra things happen. Our `execute_move` function handles these:
1. **Castling**: If the King moves 2 squares, the Rook automatically jumps over him.
2. **En Passant**: If a Pawn captures a "ghost" square, the pawn behind it is removed.
3. **Pawn Promotion**: If a Pawn reaches row 0 or 7, we change it into a **Queen**.
4. **Turn Switching**: After a move, `current_turn_color` swaps from 'white' to 'black'.

---

## 🖱️ 8. Interaction (How Clicking Works)

The `handle_mouse_input` function translates your screen click (pixels) into a grid position (0–7).
- **Click 1**: Picks up a piece and calculates `get_fully_legal_moves`.
- **Click 2**: If the square is in the list, it executes the move.

---

## 🔄 9. The Game Loop

Finally, `start_chess_game` runs forever in a `while True` loop.
1. It listens for clicks.
2. It draws the board (`draw_chess_board`).
3. It draws the pieces (`draw_all_pieces`).
4. It refreshes the screen (`pygame.display.flip`).

---

## � Conclusion

By combining **Math** (coordinates), **Logic** (simulating moves), and **Graphics** (drawing), you've created a complete world! Coding is just giving a computer a very long list of very simple instructions. 🚀
