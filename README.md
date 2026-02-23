#  Chess GrandMaster — AI-Powered Chess Coach

> **A fully interactive chess game built with Python & Pygame, powered by a Stockfish chess engine and a Google Gemini LLM coaching assistant.** Play against a world-class AI bot, get real-time move hints, receive natural-language coaching advice, and track your game with timers and move history — all in a beautiful desktop GUI.

---

##  Table of Contents

1.  [What Is This Project?](#-what-is-this-project)
2.  [Features at a Glance](#-features-at-a-glance)
3.  [Project Architecture — The Big Picture](#-project-architecture--the-big-picture)
4.  [File-by-File Breakdown](#-file-by-file-breakdown)
5.  [How Chess Pieces Move — Explained Simply](#-how-chess-pieces-move--explained-simply)
6.  [Special Chess Rules Implemented](#-special-chess-rules-implemented)
7.  [What Is FEN? (Forsyth–Edwards Notation)](#-what-is-fen-forsythedwards-notation)
8.  [What Is UCI? (Universal Chess Interface)](#-what-is-uci-universal-chess-interface)
9.  [How Stockfish Works — The Chess Engine Brain](#-how-stockfish-works--the-chess-engine-brain)
10. [How the LLM (Gemini) Is Integrated — The AI Coach](#-how-the-llm-gemini-is-integrated--the-ai-coach)
11. [The Game Loop — Step by Step](#-the-game-loop--step-by-step)
12. [How a Move Happens — End to End](#-how-a-move-happens--end-to-end)
13. [The Undo System](#-the-undo-system)
14. [The Timer System](#-the-timer-system)
15. [The UI — What You See on Screen](#-the-ui--what-you-see-on-screen)
16. [Setup & Installation](#-setup--installation)
17. [How to Run](#-how-to-run)
18. [Environment Variables](#-environment-variables)
19. [Tech Stack](#-tech-stack)
20. [Folder Structure](#-folder-structure)
21. [Glossary of Terms](#-glossary-of-terms)

---

##  What Is This Project?

Imagine you want to learn chess, but you don't have a coach sitting next to you. This project solves that! It's a **desktop chess application** where:

- You can **play chess** on a beautiful graphical board.
- You can play against **another human** (2-player mode) or against a **super-strong AI bot** (Stockfish engine).
- At any time, you can click **"Get Hint"** and the AI will tell you the single best move to make.
- A **Gemini LLM** (Google's AI language model) will explain *why* that move is good, in simple English — like a real chess coach talking to you.
- You get a **live evaluation bar** that shows who is winning (positive = White is ahead, negative = Black is ahead).
- You have **chess clocks** (timers), **move history**, **undo**, and **board themes**.

**Think of it as:** Chess.com, but running on your own computer, with your own personal AI coach.

---

##  Features at a Glance

| Feature | Description |
|---|---|
|  **Themed Board** | 5 beautiful board themes (Classic Wood, Green & Cream, Grey Slate, Warm Tan, Ocean Blue) |
|  **AI Opponent** | Toggle a Stockfish-powered bot that plays as Black at maximum strength (skill level 20) |
|  **Get Hint** | Ask Stockfish for the best move — it highlights what you should play |
|  **AI Coach (LLM)** | Gemini explains *why* the best move is good, in 1-2 sentences |
|  **Live Evaluation** | Real-time board evaluation score (e.g., `+1.5` means White is slightly better) |
|  **Chess Clocks** | Configurable timers: 5 min, 10 min, or 30 min presets |
|  **Undo Moves** | Press `U` to undo the last move (supports castling, en passant, promotion undo) |
|  **Move History** | A scrollable log of all moves played in the game |
|  **Auto-Promotion** | Pawns that reach the end automatically become Queens |
|  **Full Chess Rules** | Castling, en passant, check, checkmate, stalemate — all implemented |

---

##  Project Architecture — The Big Picture

The project follows a **modular architecture** — each file has ONE clear job. Here's how they connect:

```
┌─────────────────────────────────────────────────────────────┐
│                        main.py                              │
│                   (Game Loop - The Boss)                     │
│  Initializes everything, runs the while-True loop,          │
│  handles events, renders every frame                        │
└─────────┬──────────────┬──────────────┬─────────────────────┘
          │              │              │
          ▼              ▼              ▼
   ┌──────────┐   ┌───────────┐   ┌──────────────┐
   │  state   │   │  engine   │   │ ui_renderer  │
   │ (Global  │   │ (Move     │   │ (Drawing     │
   │  Memory) │   │ Executor) │   │  Everything) │
   └────┬─────┘   └─────┬─────┘   └──────────────┘
        │               │
        ▼               ▼
  ┌───────────┐   ┌───────────────┐
  │  models   │   │  move_logic   │──► move_physics
  │ (Piece &  │   │ (Legal Move   │   (Raw Moves &
  │  Record)  │   │  Validator)   │    Attack Checks)
  └───────────┘   └───────────────┘
                        │
                        ▼
                  ┌───────────────┐
                  │  game_status  │
                  │  (Checkmate,  │
                  │   Stalemate)  │
                  └───────────────┘

  ┌───────────┐   ┌───────────────┐   ┌──────────────┐
  │ ai_agent  │──►│ ai_interface  │──►│  Stockfish   │
  │ (AI Turn  │   │ (Engine &     │   │  (External   │
  │  & Hints) │   │  Gemini API)  │   │   Program)   │
  └───────────┘   └───────────────┘   └──────────────┘
                        │
                        ▼
                  ┌──────────────┐
                  │  Gemini LLM  │
                  │  (Google AI) │
                  └──────────────┘
```

**Data flows like this:**
1. **User clicks** → `input_handler` figures out what was clicked
2. If it's a board square → `move_logic` checks if the move is legal
3. If legal → `engine` executes the move on the board
4. After the move → `uci_utils` generates a FEN string of the new position
5. FEN is sent to **Stockfish** to evaluate & to **Gemini** for coaching advice
6. `ui_renderer` draws everything on screen 60 times per second

---

##  File-by-File Breakdown

### `main.py` — The Game Loop (The Boss of Everything)
**What it does:** This is the entry point. When you run the game, this file starts. It:
1. Imports all other modules
2. Calls `initialize_game_board()` to place all 32 pieces
3. Runs an infinite `while True` loop that:
   - Ticks the chess clock timer
   - Listens for mouse clicks and keyboard presses
   - Checks if the AI has a pending move to play
   - Redraws the entire screen 60 times per second

```python
# The main game loop — runs forever until you close the window
while True:
    dt = throttle.tick(60) / 1000.0  # Cap at 60 FPS, get delta-time in seconds

    # Update chess clocks
    if state.timer_active:
        if state.current_turn_color == 'white':
            state.white_time -= dt       # Subtract elapsed time from White's clock
        else:
            state.black_time -= dt       # Subtract elapsed time from Black's clock

    # Listen for user events (clicks, key presses, window close)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()    # Close the game
        elif event.type == pygame.MOUSEBUTTONDOWN:
            input_handler.handle_mouse_input(pygame.mouse.get_pos(), ui_rects)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_u:
                engine.undo_move()       # Press 'U' to undo

    # If the AI bot calculated a move in the background, play it now
    if state.pending_ai_move is not None:
        start_pos, end_pos = state.pending_ai_move
        state.pending_ai_move = None     # Consume it so we don't replay it
        engine.execute_move(end_pos[0], end_pos[1])

    # Draw everything on screen
    ui_renderer.draw_topbar()            # Theme buttons
    ui_renderer.draw_chess_board()       # The 8x8 grid
    ui_renderer.draw_all_pieces()        # Piece images
    ui_renderer.draw_sidebar()           # AI coach panel, timers, buttons
    ui_renderer.draw_history_panel()     # Move log
    pygame.display.flip()               # Push frame to monitor
```

---

### `constants.py` — Layout & Colors (The Design Blueprint)
**What it does:** Stores all the magic numbers for the UI layout and color palette. Changing a value here changes the entire look of the app.

```python
# Board dimensions
BOARD_PX = 690           # Board is 690 pixels wide/tall
SQUARE_SIZE = BOARD_PX // 8  # Each square = 690/8 = 86 pixels

# 5 board color themes: (light_square_color, dark_square_color)
BOARD_THEMES = [
    ((240, 217, 181), (181, 136, 99)),   # Classic Wood
    ((238, 238, 210), (118, 150,  86)),  # Green & Cream
    ((200, 200, 200), ( 80,  80,  80)),  # Grey Slate
    ((255, 235, 205), (139,  90,  43)),  # Warm Tan
    ((173, 216, 230), ( 70, 130, 180)),  # Ocean Blue
]

# UI palette — dark modern theme
BG_DARK    = ( 22,  22,  30)   # Main background (almost black)
ACCENT     = ( 90, 130, 255)   # Blue accent for buttons and borders
SUCCESS    = ( 70, 200, 120)   # Green for "ready" / positive states
DANGER     = (200,  70,  70)   # Red for errors / negative states
```

---

### `state.py` — Global Game Memory (The Brain's Notebook)
**What it does:** Holds ALL the shared data that every module reads and writes. Think of this as the "notebook" that everyone passes around.

```python
# The 8x8 chess board — a 2D list of ChessPiece objects (or None for empty squares)
board = [[None for _ in range(8)] for _ in range(8)]

# Whose turn is it? Either 'white' or 'black'
current_turn_color = 'white'

# When you click a piece, these track what's selected
active_selected_piece = None      # The ChessPiece object you clicked
active_selected_pos = None        # Its (row, col) on the board
legal_moves_for_selected = []     # Where it can legally go (shown as dots)

# AI state
ai_opponent_enabled = False       # Is the bot playing as Black?
ai_coach_message = "I am your coach. Make a move or click 'Hint'!"
pending_ai_move = None            # Bot's next move, set by background thread

# Timer state
timer_active = False
white_time = 600.0                # 10 minutes in seconds
black_time = 600.0
```

---

### `models.py` — Data Classes (The Blueprint for Pieces & Moves)
**What it does:** Defines two classes:

**`ChessPiece`** — Represents a single chess piece (a pawn, knight, bishop, rook, queen, or king):
```python
class ChessPiece:
    def __init__(self, color, type_name, image_path):
        self.color = color           # 'white' or 'black'
        self.type = type_name        # 'pawn', 'knight', 'bishop', 'rook', 'queen', 'king'
        self.image = pygame.image.load(image_path)  # Load the PNG image
        self.has_moved = False       # Important for castling & pawn double-move rules
```

**`MoveRecord`** — Stores everything needed to UNDO a move:
```python
class MoveRecord:
    def __init__(self, start_pos, end_pos, piece_moved, captured_piece, ...):
        self.start_pos = start_pos           # Where the piece was BEFORE
        self.end_pos = end_pos               # Where the piece went TO
        self.captured_piece = captured_piece  # What was captured (or None)
        self.is_en_passant = is_en_passant   # Was this an en passant capture?
        self.is_castle = is_castle           # Was this a castling move?
        self.is_promotion = is_promotion     # Did a pawn get promoted?
```

---

### `board_manager.py` — Board Setup (The Chess Store)
**What it does:** Places all 32 pieces in their starting positions. Called once when the game starts.

```python
def initialize_game_board():
    # Clear the board
    for r in range(8):
        for c in range(8):
            state.board[r][c] = None

    # Place Pawns — 8 per side, on rows 1 (black) and 6 (white)
    for col in range(8):
        state.board[1][col] = ChessPiece('black', 'pawn', 'src/images/black_pawn.png')
        state.board[6][col] = ChessPiece('white', 'pawn', 'src/images/white_pawn.png')

    # Place the back row: Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook
    # Row 0 = Black's back rank, Row 7 = White's back rank
    state.board[0][0] = ChessPiece('black', 'rook', ...)   # a8
    state.board[0][1] = ChessPiece('black', 'knight', ...) # b8
    # ... and so on for all 32 pieces
```

**The starting board looks like this:**
```
Row 0: ♜ ♞ ♝ ♛ ♚ ♝ ♞ ♜   (Black's pieces)
Row 1: ♟ ♟ ♟ ♟ ♟ ♟ ♟ ♟   (Black's pawns)
Row 2:  .  .  .  .  .  .  .  .   (empty)
Row 3:  .  .  .  .  .  .  .  .   (empty)
Row 4:  .  .  .  .  .  .  .  .   (empty)
Row 5:  .  .  .  .  .  .  .  .   (empty)
Row 6: ♙ ♙ ♙ ♙ ♙ ♙ ♙ ♙   (White's pawns)
Row 7: ♖ ♘ ♗ ♕ ♔ ♗ ♘ ♖   (White's pieces)
       a  b  c  d  e  f  g  h
```

---

### `move_physics.py` — Raw Movement Rules (The Rule Book)
**What it does:** Calculates where each piece *can physically go*, ignoring whether it would put your own king in danger. Think of these as the "physics" of piece movement.

### `move_logic.py` — Legal Move Validator (The Referee)
**What it does:** Takes the raw moves from `move_physics.py` and filters out any move that would leave your own King in check. Also adds **castling** as a legal move when conditions are met.

### `engine.py` — The Move Executor (The Gamemaster)
**What it does:** Actually performs a move on the board. Handles all side effects (captures, castling rook movement, en passant, pawn promotion). Stores each move in history for undo. Triggers the AI's turn if bot mode is on.

### `game_status.py` — Endgame Detection (The Judge)
**What it does:** Checks if the game is over:
- **Checkmate** = King is in check AND no legal moves exist → the player in checkmate LOSES
- **Stalemate** = King is NOT in check AND no legal moves exist → the game is a DRAW

### `input_handler.py` — Click Handler (The Translator)
**What it does:** Converts mouse click coordinates into game actions. Determines if the user clicked a board square, a sidebar button (Hint, Bot Toggle, Timer), or a theme button.

### `uci_utils.py` — FEN & UCI Translator (The Interpreter)
**What it does:** Converts between the game's internal board representation and standard chess notation formats (FEN and UCI).

### `ai_agent.py` — The AI's Brain (The Strategy Module)
**What it does:** Orchestrates AI actions — fetching the best move from Stockfish for the bot, fetching hints, and requesting coaching commentary from Gemini.

### `ai_interface.py` — External AI Connections (The Phone Line)
**What it does:** The actual communication layer with Stockfish (via the `stockfish` Python library) and Google Gemini (via the `google-generativeai` library). Handles thread safety, error handling, and API calls.

### `ui_renderer.py` — The Artist (The Painter)
**What it does:** Draws everything you see: the board, pieces, sidebar, timers, buttons, evaluation score, coach advice text, and move history panel. All Pygame drawing code lives here.

---

##  How Chess Pieces Move — Explained Simply

Each chess piece has its own unique way of moving. Here's how each one works in this game:

###  Pawn (The Foot Soldier)
- **Forward only:** Moves 1 square forward (never backward!)
- **First move bonus:** Can move 2 squares forward on its very first move
- **Captures diagonally:** Can only capture enemies that are 1 square diagonally in front
- **Special: En Passant** — If an enemy pawn jumps 2 squares and lands beside your pawn, you can capture it "in passing"
- **Special: Promotion** — When a pawn reaches the last row, it transforms into a Queen automatically

```python
# Pawn movement in code (from move_physics.py)
if piece.type == 'pawn':
    move_dir = -1 if piece.color == 'white' else 1  # White goes UP (-1), Black goes DOWN (+1)

    # Move forward 1 square (only if the square is empty)
    if state.board[row + move_dir][col] is None:
        moves.append((row + move_dir, col))

        # Move forward 2 squares (only from starting position, both squares must be empty)
        start_row = 6 if piece.color == 'white' else 1
        if row == start_row and state.board[row + 2 * move_dir][col] is None:
            moves.append((row + 2 * move_dir, col))

    # Capture diagonally (left and right)
    for direction_col in [-1, 1]:
        target = state.board[row + move_dir][col + direction_col]
        if target and target.color != piece.color:
            moves.append((row + move_dir, col + direction_col))
```

###  Rook (The Tower)
- Moves any number of squares **horizontally or vertically** (left, right, up, down)
- Cannot jump over other pieces — stops when it hits something
- If it hits an enemy, it can capture it

###  Knight (The Horse)
- Moves in an **L-shape**: 2 squares in one direction + 1 square perpendicular (or vice versa)
- **The ONLY piece that can jump over other pieces!**
- Has exactly 8 possible landing squares from any position

```python
# Knight moves: all 8 L-shaped jumps
if piece.type == 'knight':
    directions = [
        (2,1), (2,-1), (-2,1), (-2,-1),   # 2 rows + 1 column
        (1,2), (1,-2), (-1,2), (-1,-2)    # 1 row + 2 columns
    ]
```

###  Bishop (The Diagonal Runner)
- Moves any number of squares **diagonally** only
- Cannot jump over pieces
- A bishop on a white square can NEVER reach a black square (and vice versa)

###  Queen (The Powerhouse)
- Moves like a **Rook + Bishop combined** — any number of squares in any straight direction (horizontal, vertical, or diagonal)
- The most powerful piece on the board!

###  King (The VIP)
- Moves only **1 square in any direction**
- Cannot move into a square that's attacked by an enemy piece
- **Special: Castling** — Can move 2 squares toward a rook under certain conditions

```python
# Sliding logic — used by Rook, Bishop, and Queen (from move_physics.py)
# The key idea: keep moving in a direction until you hit the edge or another piece
for direction_row, direction_col in directions:
    curr_r, curr_c = row + direction_row, col + direction_col
    while 0 <= curr_r < 8 and 0 <= curr_c < 8:        # Stay on the board
        blocking_p = state.board[curr_r][curr_c]
        if blocking_p is None or blocking_p.color != piece.color:
            moves.append((curr_r, curr_c))              # Empty or enemy = valid
        if not is_sliding or blocking_p:
            break                                        # Stop here if blocked
        curr_r += direction_row                          # Keep sliding
        curr_c += direction_col
```

---

##  Special Chess Rules Implemented

### 1. Castling (King + Rook Team Move)
**What is it?** A special move where the King moves 2 squares toward a Rook, and the Rook jumps over the King to the other side. It's the only move where two pieces move at once!

**Conditions (ALL must be true):**
- ❌ The King has NOT moved yet
- ❌ The Rook has NOT moved yet
- ❌ No pieces between the King and Rook
- ❌ The King is NOT currently in check
- ❌ The King does NOT pass through any attacked square

```python
# Castling check (from move_logic.py)
if piece.type == 'king' and not piece.has_moved and not is_king_in_check(piece.color):
    # Kingside castling (moving right, toward column 7)
    rook = state.board[row][7]
    if rook and rook.type == 'rook' and not rook.has_moved:
        if state.board[row][5] is None and state.board[row][6] is None:  # Path clear?
            if not is_cell_attacked(row, 5, piece.color):                 # Safe path?
                if not is_cell_attacked(row, 6, piece.color):
                    legal_moves.append((row, 6))  # King can castle kingside!
```

### 2. En Passant (The Sneaky Pawn Capture)
**What is it?** If an enemy pawn advances 2 squares from its starting position and lands right beside your pawn, you can capture it on the very next move as if it had only moved 1 square.

**Why does it exist?** To prevent pawns from "sneaking past" your pawn by using the double-move. Without en passant, the double-move would be unfair.

```python
# Setting up en passant target (from engine.py)
# When a pawn moves 2 squares forward, mark the "passed" square
if moving_piece.type == 'pawn' and abs(target_row - start_row) == 2:
    # The en passant target is the square the pawn "skipped over"
    state.pawn_en_passant_target = ((target_row + start_row) // 2, start_col)
```

### 3. Pawn Promotion (The Upgrade)
**What is it?** When a pawn reaches the opposite end of the board (row 0 for White, row 7 for Black), it **transforms into a Queen**.

```python
# Auto-promotion (from engine.py)
if moving_piece.type == 'pawn' and (target_row == 0 or target_row == 7):
    # Replace the pawn with a brand new Queen of the same color
    state.board[target_row][target_col] = ChessPiece(
        moving_piece.color, 'queen', f'src/images/{moving_piece.color}_queen.png'
    )
```

### 4. Check, Checkmate & Stalemate
- **Check:** Your King is being attacked. You MUST get out of check on your next move.
- **Checkmate:** Your King is in check AND there's no way to escape. **You lose.**
- **Stalemate:** Your King is NOT in check BUT you have no legal moves. **The game is a draw.**

```python
# From game_status.py — Simple and elegant!
def is_checkmate(color):
    return has_no_legal_moves(color) and is_king_in_check(color)

def is_stalemate(color):
    return has_no_legal_moves(color) and not is_king_in_check(color)
```

---

##  What Is FEN? (Forsyth–Edwards Notation)

**FEN is a single line of text that describes the ENTIRE state of a chess game.** It's like a "save file" for a chess position. Every chess program in the world understands FEN.

### Example FEN (Starting Position):
```
rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
```

### Breaking It Down (6 Parts, Separated by Spaces):

| Part | Example | Meaning |
|---|---|---|
| **1. Piece Placement** | `rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR` | Each row separated by `/`. Lowercase = black, UPPERCASE = white. Numbers = empty squares. |
| **2. Active Color** | `w` | Whose turn? `w` = White, `b` = Black |
| **3. Castling Rights** | `KQkq` | `K` = White can castle kingside, `Q` = queenside, `k`/`q` = Black. `-` = nobody can castle |
| **4. En Passant Target** | `-` | The square where en passant capture is possible, or `-` if none |
| **5. Halfmove Clock** | `0` | Moves since last pawn move or capture (for the 50-move draw rule) |
| **6. Fullmove Number** | `1` | Current move number (starts at 1, increments after Black's move) |

### Piece Letters:
| Letter | Piece |
|---|---|
| `P` / `p` | Pawn (White / black) |
| `N` / `n` | Knight |
| `B` / `b` | Bishop |
| `R` / `r` | Rook |
| `Q` / `q` | Queen |
| `K` / `k` | King |

### How This Project Generates FEN:

```python
# From uci_utils.py — generate_fen() builds the FEN string
def generate_fen():
    piece_map = {
        ('white', 'pawn'): 'P', ('white', 'knight'): 'N', ('white', 'bishop'): 'B',
        ('white', 'rook'): 'R', ('white', 'queen'): 'Q', ('white', 'king'): 'K',
        ('black', 'pawn'): 'p', ('black', 'knight'): 'n', ('black', 'bishop'): 'b',
        ('black', 'rook'): 'r', ('black', 'queen'): 'q', ('black', 'king'): 'k'
    }

    rows = []
    for r in range(8):                    # Loop through each row
        empty_count = 0
        row_str = ""
        for c in range(8):                # Loop through each column
            p = state.board[r][c]
            if p:
                if empty_count > 0:
                    row_str += str(empty_count)   # Write the number of empty squares
                    empty_count = 0
                row_str += piece_map[(p.color, p.type)]  # Write the piece letter
            else:
                empty_count += 1
        if empty_count > 0:
            row_str += str(empty_count)
        rows.append(row_str)

    return "/".join(rows) + " w KQkq - 0 1"   # (simplified)
```

---

##  What Is UCI? (Universal Chess Interface)

**UCI is a communication protocol** — a standard "language" that chess programs use to talk to chess engines like Stockfish. Think of it like how HTTP lets your browser talk to websites.

### UCI Move Format:
A move is written as **4 characters**: `[start_square][end_square]`

| UCI Move | Meaning |
|---|---|
| `e2e4` | Move from e2 to e4 (common opening pawn move) |
| `g1f3` | Move knight from g1 to f3 |
| `e1g1` | Castling kingside (king goes from e1 to g1) |

### How This Project Converts UCI ↔ Grid Coordinates:

```python
# From uci_utils.py — Convert "e2e4" to grid coordinates ((6,4), (4,4))
def uci_to_grid(uci):
    # 'e' → column 4, '2' → row 6 (because row 0 is rank 8)
    start_c = ord(uci[0]) - ord('a')     # 'e' - 'a' = 4
    start_r = 8 - int(uci[1])            # 8 - 2 = 6
    end_c = ord(uci[2]) - ord('a')       # 'e' - 'a' = 4
    end_r = 8 - int(uci[3])              # 8 - 4 = 4
    return (start_r, start_c), (end_r, end_c)
```

---

##  How Stockfish Works — The Chess Engine Brain

**Stockfish** is the world's strongest open-source chess engine. It has an Elo rating of ~3500 (the best humans are ~2800). Here's how it works at a high level:

### The Core Idea: Search + Evaluation
1. **Search:** Stockfish looks ahead many moves (sometimes 30+ moves deep). It builds a "tree" of all possible future positions.
2. **Evaluate:** For each position at the end of a branch, it assigns a numerical score (positive = good for White, negative = good for Black).
3. **Choose:** It picks the move that leads to the best score, assuming the opponent also plays perfectly.

### Key Techniques Stockfish Uses:

| Technique | What It Does |
|---|---|
| **Alpha-Beta Pruning** | Skips branches of the search tree that can't possibly be better than what's already found. Saves massive computation. |
| **NNUE (Neural Network)** | A neural network trained on millions of games that evaluates positions much more accurately than hand-crafted rules. |
| **Iterative Deepening** | Searches 1 move deep, then 2, then 3, etc. This way it always has a "best guess" even if time runs out. |
| **Transposition Table** | Remembers positions it's already evaluated, so it doesn't repeat work. |
| **Move Ordering** | Looks at the most promising moves first (captures, checks) to make pruning more effective. |

### How This Project Talks to Stockfish:

```python
# From ai_interface.py — Initialize Stockfish
from stockfish import Stockfish

# Load the Stockfish executable (downloaded separately)
engine = Stockfish(path="C:/path/to/stockfish.exe")
engine.set_skill_level(20)  # Max difficulty (0-20 scale)

# Ask for the best move
def get_best_move_from_stockfish(fen):
    with engine_lock:                    # Thread-safe! Only one request at a time
        engine.set_fen_position(fen)     # Tell Stockfish the current position
        move = engine.get_best_move()    # Stockfish thinks and returns e.g. "e2e4"
        return move                      # Return the UCI move string

# Get position evaluation
def get_evaluation_and_move(fen):
    engine.set_fen_position(fen)
    move = engine.get_best_move()
    eval_data = engine.get_evaluation()  # Returns {'type': 'cp', 'value': 150}
    # 'cp' = centipawns (1 pawn = 100). So 150 = White is 1.5 pawns ahead
    # 'mate' = forced checkmate found. value = moves until mate
    score = eval_data['value'] / 100.0   # Convert to pawns: 1.5
    return move, f"{score:+}"            # Returns ("e2e4", "+1.5")
```

### Evaluation Score Explained:
| Score | Meaning |
|---|---|
| `+0.0` | Position is perfectly equal |
| `+1.5` | White is ahead by about 1.5 pawns worth of advantage |
| `-2.3` | Black is ahead by about 2.3 pawns worth of advantage |
| `Mate in 5` | White can force checkmate in 5 moves |
| `Mate in -3` | Black can force checkmate in 3 moves |

---

##  How the LLM (Gemini) Is Integrated — The AI Coach

### What Is an LLM?
An **LLM (Large Language Model)** is an AI that understands and generates human language. Google's **Gemini** is one such model. In this project, it acts as a chess coach that explains moves in plain English.

### How It Works in This Project:

1. **You click "Get Hint"**
2. The app asks **Stockfish** for the best move and evaluation
3. The app sends a **prompt** to **Gemini** with:
   - The current board position (as FEN)
   - The best move Stockfish found
   - The evaluation score
4. Gemini responds with a 1-2 sentence explanation of why that move is good
5. The explanation appears in the "COACH ADVICE" section of the sidebar

### The Prompt Sent to Gemini:

```python
# From ai_interface.py
prompt = f"""
You are a Grandmaster Chess Coach.
Current Board (FEN): {fen}
Stockfish Evaluation: {evaluation}
Best Move (UCI): {best_move}

Provide a concise (maximum 2 sentences) explanation of why this move is good or
what the strategic goal is. Speak like a helpful mentor.
"""

# Send to Gemini and get response
response = model.generate_content(prompt)
coaching_text = response.text.strip()
# Example response: "This move controls the center and opens a line for your bishop.
#                    It also puts pressure on Black's weak e-pawn."
```

### Setup — How Gemini Is Configured:

```python
# From ai_interface.py
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()  # Load API key from .env file

# Configure with your API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Load the model
model = genai.GenerativeModel('gemini-3-flash-preview')
```

### The Flow (Visual):
```
User clicks "GET HINT"
        │
        ▼
  ┌─────────────┐     FEN string      ┌──────────────┐
  │  ai_agent.py │ ──────────────────► │  Stockfish   │
  │  get_ai_hint │                     │  Engine      │
  └──────┬───────┘ ◄────────────────── └──────────────┘
         │           best_move + eval
         │
         │   FEN + move + eval
         ▼
  ┌──────────────┐                     ┌──────────────┐
  │ai_interface  │ ──────────────────► │  Gemini LLM  │
  │coach_comment │                     │  (Google AI) │
  └──────┬───────┘ ◄────────────────── └──────────────┘
         │           coaching text
         ▼
  state.ai_coach_message = "This move controls the center..."
         │
         ▼
  ui_renderer draws the advice in the sidebar
```

### Thread Safety:
All AI operations run in **background threads** so the game doesn't freeze while waiting for Stockfish or Gemini to respond:

```python
# From ai_agent.py — Everything runs in a daemon thread
def perform_ai_turn():
    if state.is_ai_thinking: return     # Don't stack up requests

    state.is_ai_thinking = True
    def fetch_and_move():
        try:
            move_uci = get_best_move_from_stockfish(fen)
            coords = uci_utils.uci_to_grid(move_uci)
            state.pending_ai_move = coords   # Main loop picks this up next frame
        finally:
            state.is_ai_thinking = False

    threading.Thread(target=fetch_and_move, daemon=True).start()
```

---

##  The Game Loop — Step by Step

Every video game has a **game loop** — an infinite loop that runs ~60 times per second. Each iteration is called a **frame**. Here's what happens each frame:

```
┌─────────────────────────────────────────────┐
│ FRAME START                                 │
│                                             │
│ 1.  Tick the clock (subtract time)       │
│ 2.  Check for mouse clicks              │
│ 3.  Check for keyboard presses (Undo)    │
│ 4.  Check if AI has a pending move       │
│ 5.  Clear the screen                     │
│ 6.  Draw the top bar (themes)            │
│ 7.  Draw the chess board (grid)          │
│ 8.  Draw all pieces (images)             │
│ 9.  Draw the sidebar (AI coach, buttons) │
│ 10.  Draw the bottom bar (hint display)   │
│ 11.  Draw the history panel (move log)    │
│ 12.  Push frame to screen (display.flip)  │
│                                             │
│ FRAME END → Go back to FRAME START          │
└─────────────────────────────────────────────┘
```

---

##  How a Move Happens — End to End

Here's the complete journey when you click a piece and then click a target square:

1. **Click #1 — Select a piece:**
   - `input_handler` detects the click coordinates
   - Converts pixel position to board `(row, col)`
   - Checks if there's a piece of the current player's color at that square
   - Calls `move_logic.get_fully_legal_moves()` to compute all legal destination squares
   - Stores the piece, its position, and legal moves in `state`
   - `ui_renderer` draws yellow highlight on the selected square and dots on legal moves

2. **Click #2 — Make the move:**
   - `input_handler` checks if the clicked square is in the `legal_moves_for_selected` list
   - If yes → calls `engine.execute_move(row, col)`
   - `engine` handles:
     - Moving the piece on the board array
     - Capturing enemy pieces
     - Castling (moving the rook too)
     - En passant (removing the captured pawn)
     - Pawn promotion (replacing pawn with queen)
     - Saving the move to `move_history` for undo
     - Logging to `game_move_log` for the history panel
     - Switching turns (`white` ↔ `black`)
     - Starting a background thread to update evaluation
     - Triggering AI's turn if bot is enabled
     - Checking for checkmate or stalemate

---

##  The Undo System

Press **`U`** to undo the last move. The system perfectly reverses everything:

```python
def undo_move():
    move = state.move_history.pop()     # Get the last move record

    # Put the piece back where it was
    state.board[move.start_pos] = move.piece_moved
    state.board[move.end_pos] = move.captured_piece  # Restore captured piece (or None)

    # Reverse special moves
    if move.is_en_passant:   # Put the captured pawn back
    if move.is_castle:       # Put the rook back to its original position
    if move.is_promotion:    # Turn the queen back into a pawn

    # Restore game state
    state.pawn_en_passant_target = move.prev_en_passant
    state.current_turn_color = 'white' if current == 'black' else 'black'
```

---

##  The Timer System

The game has chess clocks (like in tournament chess):
- Each player starts with a set time (default: 10 minutes)
- Time ticks down only during **your** turn
- If your time reaches 0, you lose!
- Presets: **5 min**, **10 min**, **30 min**
- Toggle the clock on/off with the sidebar button

---

##  The UI — What You See on Screen

The window is divided into 4 main areas:

```
┌──────────────────────────┬─────────────┬──────────┐
│       TOP BAR            │             │          │
│  [Classic][Green][Slate] │             │          │
│  [Warm Tan][Ocean]       │             │          │
├──────────────────────────┤  SIDEBAR    │  MOVE    │
│                          │             │ HISTORY  │
│                          │  ♞ AI COACH │          │
│      CHESS BOARD         │  Engine: ✓  │ Move 1   │
│        8 × 8             │  Eval: +0.3 │ Move 2   │
│                          │             │ Move 3   │
│                          │  [GET HINT] │ ...      │
│                          │  [BOT: OFF] │          │
│                          │             │          │
│                          │  COACH:     │          │
│                          │  "Great     │          │
│                          │   move!"    │          │
├──────────────────────────┤             │          │
│ BOTTOM BAR: Best Move: E2-E4          │          │
└──────────────────────────┴─────────────┴──────────┘
```

---

##  Setup & Installation

### Prerequisites
- **Python 3.8+** installed
- **Stockfish** chess engine downloaded ([stockfishchess.org](https://stockfishchess.org/download/))
- **Google Gemini API Key** (free tier available at [aistudio.google.com](https://aistudio.google.com/))

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/Chess-GrandMaster.git
cd Chess-GrandMaster
```

### Step 2: Install Python Dependencies
```bash
pip install pygame stockfish google-generativeai python-dotenv
```

### Step 3: Download Stockfish
1. Go to [stockfishchess.org/download](https://stockfishchess.org/download/)
2. Download the version for your OS
3. Extract it and note the path to the executable (e.g., `C:\stockfish\stockfish.exe`)

### Step 4: Create `.env` File
Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_gemini_api_key_here
STOCKFISH_PATH=C:\path\to\stockfish\stockfish.exe
```

>  **NEVER commit your `.env` file to Git!** It contains your secret API key. The `.gitignore` already blocks it.

---

##  How to Run

```bash
cd src
python main.py
```

The game window will open. Click pieces to move them!

### Controls:
| Control | Action |
|---|---|
| **Left Click** | Select a piece / Make a move |
| **U key** | Undo the last move |
| **Theme buttons** | Change board colors |
| **GET HINT** | Ask AI for the best move |
| **ENABLE BOT** | Let AI play as Black automatically |
| **CLOCK toggle** | Turn chess timer on/off |

---

##  Environment Variables

| Variable | Description | Example |
|---|---|---|
| `GEMINI_API_KEY` | Your Google Gemini API key | `AIzaSy...` |
| `STOCKFISH_PATH` | Full path to Stockfish executable | `C:\stockfish\stockfish.exe` |

---

##  Tech Stack

| Technology | Purpose |
|---|---|
| **Python 3** | Core programming language |
| **Pygame** | Game window, rendering, input handling |
| **Stockfish** | Chess engine for move analysis & bot play |
| **`stockfish` (Python lib)** | Python wrapper to communicate with Stockfish |
| **Google Gemini** | LLM for natural language coaching |
| **`google-generativeai`** | Python SDK for Gemini API |
| **`python-dotenv`** | Load environment variables from `.env` file |

---

##  Folder Structure

```
Chess-GrandMaster/
├── .env                    #  API keys (SECRET — never commit this!)
├── .gitignore              # Files Git should ignore
├── README.md               # This file — you're reading it!
├── requirements.txt        # Python dependencies
└── src/                    # All source code
    ├── main.py             #  Entry point & game loop
    ├── constants.py        #  Layout sizes & color palette
    ├── state.py            #  Global game state (the shared notebook)
    ├── models.py           #  ChessPiece & MoveRecord classes
    ├── board_manager.py    #  Board initialization (place all 32 pieces)
    ├── move_physics.py     #  Raw piece movement calculations
    ├── move_logic.py       #  Legal move validation (prevents self-check)
    ├── engine.py           #  Move execution, undo, turn management
    ├── game_status.py      #  Checkmate & stalemate detection
    ├── input_handler.py    #  Mouse click → game action translator
    ├── uci_utils.py        #  FEN generation & UCI coordinate conversion
    ├── ai_agent.py         #  AI turn orchestration & hint logic
    ├── ai_interface.py     #  Stockfish & Gemini API communication
    ├── ui_renderer.py      #  All Pygame drawing (board, sidebar, etc.)
    ├── test_fen.py         #  Quick FEN generation test script
    └── images/             #  Chess piece PNG images (12 files)
        ├── white_pawn.png
        ├── white_rook.png
        ├── ... (6 white + 6 black piece images)
        └── black_king.png
```

---

##  Glossary of Terms

| Term | Meaning |
|---|---|
| **FEN** | Forsyth–Edwards Notation — a text format to describe a chess position |
| **UCI** | Universal Chess Interface — a protocol for talking to chess engines |
| **Stockfish** | The strongest open-source chess engine in the world |
| **LLM** | Large Language Model — an AI that understands and generates text (like Gemini) |
| **Gemini** | Google's LLM, used here as a chess coaching assistant |
| **Pygame** | A Python library for making games with graphics and sound |
| **Centipawn (cp)** | Unit of evaluation. 100 cp = advantage of 1 pawn |
| **Elo Rating** | A number measuring chess skill. Beginners ~800, GMs ~2700, Stockfish ~3500 |
| **Castling** | Special king+rook move for safety and rook activation |
| **En Passant** | Special pawn capture when an enemy pawn double-moves past yours |
| **Promotion** | A pawn reaching the last rank transforms into a stronger piece |
| **Check** | The king is under attack — must escape immediately |
| **Checkmate** | The king is in check with no escape — game over, you lose |
| **Stalemate** | No legal moves but not in check — game is a draw |
| **Daemon Thread** | A background thread that automatically stops when the main program exits |
| **Thread Lock** | A mechanism preventing two threads from using Stockfish simultaneously |
| **API Key** | A secret password that lets your code access an online service (like Gemini) |
| **`.env` File** | A hidden configuration file that stores sensitive settings like API keys |

---

<p align="center">
  Made  by <strong>Ujjwal Gupta</strong>
</p>
