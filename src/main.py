import pygame
import sys
import threading
from ai_interface import get_best_move_from_stockfish, get_ai_coach_commentary, get_evaluation_and_move, AI_STATUS

pygame.init()

# --- Layout Constants ---
TOPBAR_HEIGHT = 50      # Header toolbar height
BOTTOM_BAR_HEIGHT = 40  # Bottom hint display height
BOARD_LABEL_SIZE = 22   # Width/height of coordinate labels strip
SIDEBAR_WIDTH = 320

# Board renders inside the label strip, starting offset
BOARD_OFFSET_X = BOARD_LABEL_SIZE
BOARD_OFFSET_Y = TOPBAR_HEIGHT + BOARD_LABEL_SIZE
BOARD_PX = 720          # Board pixel size (divisible by 8)
SQUARE_SIZE = BOARD_PX // 8

WINDOW_W = BOARD_OFFSET_X + BOARD_PX + SIDEBAR_WIDTH
WINDOW_H = TOPBAR_HEIGHT + BOARD_LABEL_SIZE + BOARD_PX + BOTTOM_BAR_HEIGHT

# Alias for sidebar x start
SIDEBAR_X = BOARD_OFFSET_X + BOARD_PX

# --- Color Palette ---
WHITE  = (255, 255, 255)
BLACK  = (  0,   0,   0)
YELLOW = (255, 215,   0)
RED    = (220,  50,  50)

# Board themes: (light_square, dark_square)
BOARD_THEMES = [
    ((240, 217, 181), (181, 136, 99)),   # Classic Wood
    ((238, 238, 210), (118, 150,  86)),  # Green & Cream
    ((200, 200, 200), ( 80,  80,  80)),  # Grey Slate
    ((255, 235, 205), (139,  90,  43)),  # Warm Tan
    ((173, 216, 230), ( 70, 130, 180)),  # Ocean Blue
]
THEME_NAMES = ["Classic", "Green", "Slate", "Warm Tan", "Ocean"]
current_theme_idx = 0

# UI palette
BG_DARK    = ( 22,  22,  30)
BG_SIDEBAR = ( 28,  28,  40)
ACCENT     = ( 90, 130, 255)
SUCCESS    = ( 70, 200, 120)
DANGER     = (200,  70,  70)
TEXT_DIM   = (160, 160, 180)
TEXT_BRIGHT= (240, 240, 255)

# Create the screen
screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
pygame.display.set_caption("Chess AI — Grandmaster Coach")


#Chess piece class

class ChessPiece:
    def __init__(self,color,type,image):
        self.color=color
        self.type = type
        self.image = pygame.image.load(image)
        self.image = pygame.transform.scale(self.image, (SQUARE_SIZE,SQUARE_SIZE))
        self.has_moved = False

# --- Initial Setup ---

# The 8x8 chess board. It stores ChessPiece objects or None for empty squares.
board = [[None for _ in range(8)] for _ in range(8)]

# --- Global Game State ---
current_turn_color = 'white'  # Current player color: 'white' or 'black'
active_selected_piece = None  # The piece object selected by the player
active_selected_pos = None    # The (row, col) position of that piece
legal_moves_for_selected = [] # Highlighted target squares for the UI
pawn_en_passant_target = None # Square targeting an en passant capture
move_history = []             # Stack to store move history for undoing

# --- AI State ---
ai_opponent_enabled = False
ai_coach_message = "I am your coach. Make a move or click 'Hint'!"
ai_eval_score = "0.0"
is_ai_thinking = False
last_hint_move = ""   # e.g. "e2e4" – displayed below board
pending_ai_move = None  # Set by background thread: ((sr,sc),(er,ec))

class MoveRecord:
    """Stores all information needed to reverse a chess move."""
    def __init__(self, start_pos, end_pos, piece_moved, captured_piece, 
                 prev_en_passant, is_en_passant=False, 
                 is_castle=False, rook_move=None, 
                 is_promotion=False, promoted_from=None):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.piece_moved = piece_moved
        self.captured_piece = captured_piece
        self.prev_en_passant = prev_en_passant
        self.is_en_passant = is_en_passant
        self.is_castle = is_castle
        self.rook_move = rook_move # (rook_piece, r_start, r_end)
        self.is_promotion = is_promotion
        self.promoted_from = promoted_from
        
        # Save 'has_moved' states
        self.piece_moved_had_moved = piece_moved.has_moved
        if rook_move:
            self.rook_had_moved = rook_move[0].has_moved

def initialize_game_board():
    """Starts a new game by placing all 32 pieces in their standard positions."""
    global board
    # Reset board to all empty squares first
    for r in range(8):
        for c in range(8):
            board[r][c] = None

    # Place Pawns
    for col in range(8):
        board[1][col] = ChessPiece('black', 'pawn', 'src/images/black_pawn.png')
        board[6][col] = ChessPiece('white', 'pawn', 'src/images/white_pawn.png')

    # Place Rooks
    board[0][0] = board[0][7] = ChessPiece('black', 'rook', 'src/images/black_rook.png')
    board[7][0] = board[7][7] = ChessPiece('white', 'rook', 'src/images/white_rook.png')

    # Place Knights
    board[0][1] = board[0][6] = ChessPiece('black', 'knight', 'src/images/black_knight.png')
    board[7][1] = board[7][6] = ChessPiece('white', 'knight', 'src/images/white_knight.png')

    # Place Bishops
    board[0][2] = board[0][5] = ChessPiece('black', 'bishop', 'src/images/black_bishop.png')
    board[7][2] = board[7][5] = ChessPiece('white', 'bishop', 'src/images/white_bishop.png')

    # Place Queens
    board[0][3] = ChessPiece('black', 'queen', 'src/images/black_queen.png')
    board[7][3] = ChessPiece('white', 'queen', 'src/images/white_queen.png')

    # Place Kings
    board[0][4] = ChessPiece('black', 'king', 'src/images/black_king.png')
    board[7][4] = ChessPiece('white', 'king', 'src/images/white_king.png')

# --- UI Rendering Functions ---

def get_sq_rect(row, col):
    """Returns the pygame.Rect for a board square."""
    x = BOARD_OFFSET_X + col * SQUARE_SIZE
    y = BOARD_OFFSET_Y + row * SQUARE_SIZE
    return pygame.Rect(x, y, SQUARE_SIZE, SQUARE_SIZE)

def draw_topbar():
    """Draws the top toolbar with board theme switcher."""
    pygame.draw.rect(screen, BG_DARK, (0, 0, WINDOW_W, TOPBAR_HEIGHT))
    # Bottom border line
    pygame.draw.line(screen, ACCENT, (0, TOPBAR_HEIGHT - 1), (WINDOW_W, TOPBAR_HEIGHT - 1), 2)

    font = pygame.font.SysFont('Segoe UI', 17, bold=True)
    label = font.render("BOARD THEME:", True, TEXT_DIM)
    screen.blit(label, (10, 15))

    btn_w, btn_h = 80, 28
    btn_y = (TOPBAR_HEIGHT - btn_h) // 2
    x = 150
    for i, name in enumerate(THEME_NAMES):
        color = ACCENT if i == current_theme_idx else (50, 52, 70)
        rect = pygame.Rect(x, btn_y, btn_w, btn_h)
        pygame.draw.rect(screen, color, rect, border_radius=6)
        txt = font.render(name, True, WHITE)
        screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))
        x += btn_w + 8

def draw_chess_board():
    """Renders the grid, highlights, coordinate labels."""
    light, dark = BOARD_THEMES[current_theme_idx]

    for row in range(8):
        for col in range(8):
            sq_rect = get_sq_rect(row, col)
            square_color = light if (row + col) % 2 == 0 else dark

            # Highlight king in check
            p = board[row][col]
            if p and p.type == 'king' and p.color == current_turn_color:
                if is_king_in_check(current_turn_color):
                    square_color = (210, 60, 60)

            pygame.draw.rect(screen, square_color, sq_rect)

    # Selected piece highlight
    if active_selected_pos:
        sel_r, sel_c = active_selected_pos
        sel_rect = get_sq_rect(sel_r, sel_c)
        highlight = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        highlight.fill((255, 215, 0, 120))
        screen.blit(highlight, sel_rect.topleft)

    # Legal move dots
    for move_row, move_col in legal_moves_for_selected:
        sq_r = get_sq_rect(move_row, move_col)
        center = sq_r.center
        pygame.draw.circle(screen, (0, 0, 0, 160), center, SQUARE_SIZE // 7)
        pygame.draw.circle(screen, (255, 255, 255, 80), center, SQUARE_SIZE // 7 - 2)

    # Board border
    board_rect = pygame.Rect(BOARD_OFFSET_X, BOARD_OFFSET_Y, BOARD_PX, BOARD_PX)
    pygame.draw.rect(screen, ACCENT, board_rect, 2)

    # --- Coordinate Labels ---
    lbl_font = pygame.font.SysFont('Segoe UI', 14, bold=True)
    files = 'ABCDEFGH'
    for col in range(8):
        # Column letters (A-H) below board
        sq_r = get_sq_rect(7, col)
        txt = lbl_font.render(files[col], True, TEXT_DIM)
        x = sq_r.centerx - txt.get_width() // 2
        y = BOARD_OFFSET_Y + BOARD_PX + 4
        screen.blit(txt, (x, y))
        # Also draw at top
        txt2 = lbl_font.render(files[col], True, TEXT_DIM)
        screen.blit(txt2, (x, BOARD_OFFSET_Y - BOARD_LABEL_SIZE + 2))

    for row in range(8):
        # Row numbers (8-1 from top) left of board
        sq_r = get_sq_rect(row, 0)
        num = str(8 - row)
        txt = lbl_font.render(num, True, TEXT_DIM)
        x = BOARD_OFFSET_X - txt.get_width() - 3
        y = sq_r.centery - txt.get_height() // 2
        screen.blit(txt, (x, y))

def draw_all_pieces():
    """Draws piece images on top of the squares."""
    for row in range(8):
        for col in range(8):
            p = board[row][col]
            if p:
                sq_rect = get_sq_rect(row, col)
                screen.blit(p.image, sq_rect.topleft)

def draw_bottom_bar():
    """Draws the bottom bar showing the last hint move."""
    bar_y = TOPBAR_HEIGHT + BOARD_LABEL_SIZE + BOARD_PX
    bar_w = BOARD_OFFSET_X + BOARD_PX
    pygame.draw.rect(screen, BG_DARK, (0, bar_y, bar_w, BOTTOM_BAR_HEIGHT))
    pygame.draw.line(screen, ACCENT, (0, bar_y), (bar_w, bar_y), 1)

    font = pygame.font.SysFont('Segoe UI', 16, bold=True)
    if last_hint_move:
        prefix = font.render("Best Move:  ", True, TEXT_DIM)
        move_txt = font.render(last_hint_move.upper(), True, YELLOW)
        screen.blit(prefix, (12, bar_y + 10))
        screen.blit(move_txt, (12 + prefix.get_width(), bar_y + 10))
    else:
        hint_txt = font.render("Click \"GET HINT\" to see the best move.", True, TEXT_DIM)
        screen.blit(hint_txt, (12, bar_y + 10))


def wrap_text(text, font, max_width):
    """Simple word wrap for Pygame surfaces."""
    words = text.split(' ')
    lines = []
    while words:
        line_words = []
        while words:
            line_words.append(words.pop(0))
            fw, _ = font.size(' '.join(line_words + words[:1]))
            if fw > max_width:
                break
        lines.append(' '.join(line_words))
    return lines

def draw_sidebar():
    """Renders the AI coach panel on the right side."""
    sb_y = 0
    sb_h = WINDOW_H
    pygame.draw.rect(screen, BG_SIDEBAR, (SIDEBAR_X, sb_y, SIDEBAR_WIDTH, sb_h))
    pygame.draw.line(screen, ACCENT, (SIDEBAR_X, 0), (SIDEBAR_X, sb_h), 2)

    pad = 16
    font_title  = pygame.font.SysFont('Segoe UI', 26, bold=True)
    font_med    = pygame.font.SysFont('Segoe UI', 18, bold=True)
    font_small  = pygame.font.SysFont('Segoe UI', 15)
    font_hint   = pygame.font.SysFont('Segoe UI', 13)

    y = 12

    # --- Title ---
    title_surf = font_title.render("\u265e  AI COACH", True, ACCENT)
    screen.blit(title_surf, (SIDEBAR_X + pad, y))
    y += title_surf.get_height() + 4
    pygame.draw.line(screen, ACCENT, (SIDEBAR_X + pad, y), (SIDEBAR_X + SIDEBAR_WIDTH - pad, y), 1)
    y += 10

    # --- Engine Status ---
    import ai_interface
    status_text = ai_interface.AI_STATUS
    status_color = SUCCESS if "Ready" in status_text else (DANGER if "Error" in status_text else YELLOW)
    lbl = font_hint.render("ENGINE STATUS", True, TEXT_DIM)
    val = font_med.render(status_text, True, status_color)
    screen.blit(lbl, (SIDEBAR_X + pad, y))
    y += lbl.get_height() + 2
    screen.blit(val, (SIDEBAR_X + pad, y))
    y += val.get_height() + 10

    # --- Evaluation ---
    eval_s = str(ai_eval_score)
    eval_color = SUCCESS if eval_s.startswith('+') else (DANGER if eval_s.startswith('-') else YELLOW)
    lbl = font_hint.render("EVALUATION (White \u2192)", True, TEXT_DIM)
    eval_font = pygame.font.SysFont('Segoe UI', 30, bold=True)
    val = eval_font.render(eval_s, True, eval_color)
    screen.blit(lbl, (SIDEBAR_X + pad, y))
    y += lbl.get_height() + 2
    screen.blit(val, (SIDEBAR_X + pad, y))
    y += val.get_height() + 10
    pygame.draw.line(screen, (50, 55, 80), (SIDEBAR_X + pad, y), (SIDEBAR_X + SIDEBAR_WIDTH - pad, y), 1)
    y += 8

    # --- Mode ---
    bot_active = ai_opponent_enabled
    lbl = font_hint.render("GAME MODE", True, TEXT_DIM)
    screen.blit(lbl, (SIDEBAR_X + pad, y))
    y += lbl.get_height() + 2
    mode_txt = "\u25cf  Bot Playing Black" if bot_active else "\u25cb  Local 2-Player"
    mode_col  = SUCCESS if bot_active else TEXT_DIM
    mode_surf = font_med.render(mode_txt, True, mode_col)
    screen.blit(mode_surf, (SIDEBAR_X + pad, y))
    y += mode_surf.get_height() + 8
    pygame.draw.line(screen, (50, 55, 80), (SIDEBAR_X + pad, y), (SIDEBAR_X + SIDEBAR_WIDTH - pad, y), 1)
    y += 8

    # --- Buttons (right after mode section) ---
    btn_w = SIDEBAR_WIDTH - pad * 2
    btn_h = 40
    btn_x = SIDEBAR_X + pad

    # Hint button
    h_rect = pygame.Rect(btn_x, y, btn_w, btn_h)
    pygame.draw.rect(screen, ACCENT, h_rect, border_radius=10)
    h_txt = font_med.render("\u2192 GET HINT", True, WHITE)
    screen.blit(h_txt, (h_rect.centerx - h_txt.get_width() // 2, h_rect.centery - h_txt.get_height() // 2))
    y += btn_h + 8

    # Bot toggle button
    t_color = DANGER if bot_active else (60, 65, 90)
    t_rect = pygame.Rect(btn_x, y, btn_w, btn_h)
    pygame.draw.rect(screen, t_color, t_rect, border_radius=10)
    t_label = "DISABLE BOT" if bot_active else "ENABLE BOT"
    t_txt = font_med.render(t_label, True, WHITE)
    screen.blit(t_txt, (t_rect.centerx - t_txt.get_width() // 2, t_rect.centery - t_txt.get_height() // 2))
    y += btn_h + 12
    pygame.draw.line(screen, (50, 55, 80), (SIDEBAR_X + pad, y), (SIDEBAR_X + SIDEBAR_WIDTH - pad, y), 1)
    y += 8

    # --- Advice Section ---
    lbl = font_hint.render("GRANDMASTER ADVICE", True, TEXT_DIM)
    screen.blit(lbl, (SIDEBAR_X + pad, y))
    y += lbl.get_height() + 6
    wrapped = wrap_text(ai_coach_message, font_small, SIDEBAR_WIDTH - pad * 2)
    for line in wrapped:
        if y + font_small.get_height() > WINDOW_H - 10:
            break
        surf = font_small.render(line, True, TEXT_BRIGHT)
        screen.blit(surf, (SIDEBAR_X + pad, y))
        y += surf.get_height() + 3

    return h_rect, t_rect

# --- Rules and Movement Helper Functions ---

def is_cell_attacked(target_row, target_col, defender_color):
    """Returns True if the specified square is reachable by ANY enemy piece."""
    opponent_color = 'black' if defender_color == 'white' else 'white'
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece and piece.color == opponent_color:
                # Use raw movement patterns to check for threats without recursion
                if (target_row, target_col) in get_raw_piece_moves(piece, r, c):
                    return True
    return False

def get_raw_piece_moves(piece, row, col):
    """Calculates basic physics-based moves, ignoring specialized rules like 'Check'."""
    moves = []
    
    # Pawn-specific movement logic
    if piece.type == 'pawn':
        move_dir = -1 if piece.color == 'white' else 1
        # Forward move (blocked by any piece)
        if 0 <= row + move_dir < 8 and board[row + move_dir][col] is None:
            moves.append((row + move_dir, col))
            start_row = 6 if piece.color == 'white' else 1
            # Double move from start rank
            if row == start_row and board[row + 2 * move_dir][col] is None:
                moves.append((row + 2 * move_dir, col))
        # Captures
        for dc in [-1, 1]:
            tr, tc = row + move_dir, col + dc
            if 0 <= tr < 8 and 0 <= tc < 8:
                target = board[tr][tc]
                if target and target.color != piece.color:
                    moves.append((tr, tc))
                elif (tr, tc) == pawn_en_passant_target:
                    moves.append((tr, tc))
        return moves

    # Sliding logic for Rooks, Bishops, and Queens
    is_sliding = piece.type in ['rook', 'bishop', 'queen']
    directions = []
    if piece.type in ['rook', 'queen']:
        directions += [(1,0), (-1,0), (0,1), (0,-1)]
    if piece.type in ['bishop', 'queen']:
        directions += [(1,1), (1,-1), (-1,1), (-1,-1)]
    if piece.type == 'knight':
        directions = [(2,1), (2,-1), (-2,1), (-2,-1), (1,2), (1,-2), (-1,2), (-1,-2)]
    if piece.type == 'king':
        directions = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

    for dr, dc in directions:
        curr_r, curr_c = row + dr, col + dc
        while 0 <= curr_r < 8 and 0 <= curr_c < 8:
            blocking_p = board[curr_r][curr_c]
            # Valid if empty or contains an enemy
            if blocking_p is None or blocking_p.color != piece.color:
                moves.append((curr_r, curr_c))
            
            # Stop if the path is blocked OR if piece doesn't slide (Knight/King)
            if not is_sliding or blocking_p:
                break
            curr_r += dr
            curr_c += dc
    return moves

def get_fully_legal_moves(piece, row, col):
    """Refines raw moves with safety checks to ensure the King isn't left in Check."""
    raw_moves = get_raw_piece_moves(piece, row, col)
    legal_moves = []

    # Filter out moves that would cause self-check
    for target_r, target_c in raw_moves:
        original_piece = board[target_r][target_c]
        
        # Simulate move
        board[target_r][target_c] = piece
        board[row][col] = None
        is_safe = not is_king_in_check(piece.color)
        
        if is_safe:
            legal_moves.append((target_r, target_c))
            
        # Revert simulation
        board[row][col] = piece
        board[target_r][target_c] = original_piece

    # Specialized Castling Logic
    if piece.type == 'king' and not piece.has_moved and not is_king_in_check(piece.color):
        # Kingside (Right)
        rook_r = board[row][7]
        if rook_r and rook_r.type == 'rook' and not rook_r.has_moved:
            if board[row][5] is None and board[row][6] is None:
                if not is_cell_attacked(row, 5, piece.color) and not is_cell_attacked(row, 6, piece.color):
                    legal_moves.append((row, 6))
        # Queenside (Left)
        rook_l = board[row][0]
        if rook_l and rook_l.type == 'rook' and not rook_l.has_moved:
            if board[row][1] is None and board[row][2] is None and board[row][3] is None:
                if not is_cell_attacked(row, 2, piece.color) and not is_cell_attacked(row, 3, piece.color):
                    legal_moves.append((row, 2))

    return legal_moves

# --- Status Checks ---

def find_king(color):
    """Utility to quickly find the King's current coordinates."""
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p and p.type == 'king' and p.color == color:
                return (r, c)
    return None

def is_king_in_check(color):
    """Boolean check for whether the current color's King is under threat."""
    k_pos = find_king(color)
    if k_pos:
        return is_cell_attacked(k_pos[0], k_pos[1], color)
    return False

def has_no_legal_moves(color):
    """Determines if the game should end due to lack of valid moves."""
    for r in range(8):
        for col in range(8):
            p = board[r][col]
            if p and p.color == color:
                if get_fully_legal_moves(p, r, col):
                    return False
    return True

def is_stalemate(color):
    """Returns True if the current color is in stalemate (no moves, not in check)."""
    return has_no_legal_moves(color) and not is_king_in_check(color)

def is_checkmate(color):
    """Returns True if the current color is in checkmate (no moves, in check)."""
    return has_no_legal_moves(color) and is_king_in_check(color)

def uci_to_grid(uci):
    """Translates UCI string (e2e4) to ((start_r, start_c), (end_r, end_c))."""
    if len(uci) < 4: return None
    start_c = ord(uci[0]) - ord('a')
    start_r = 8 - int(uci[1])
    end_c = ord(uci[2]) - ord('a')
    end_r = 8 - int(uci[3])
    return (start_r, start_c), (end_r, end_c)

def perform_ai_turn():
    """Fetches move from Stockfish and stores it in pending_ai_move."""
    global is_ai_thinking, pending_ai_move
    if is_ai_thinking: return
    
    fen = generate_fen()
    print(f"--- AI Turn Started ---")
    is_ai_thinking = True
    
    def fetch_and_move():
        global is_ai_thinking, pending_ai_move
        try:
            move_uci = get_best_move_from_stockfish(fen)
            if move_uci:
                print(f"--- Stockfish chose: {move_uci} ---")
                coords = uci_to_grid(move_uci)
                if coords:
                    pending_ai_move = coords  # Main loop picks this up
            else:
                print("--- Stockfish returned no move (Game over?) ---")
        except Exception as e:
            print(f"--- AI Turn Error: {e} ---")
        finally:
            is_ai_thinking = False

    threading.Thread(target=fetch_and_move, daemon=True).start()

def get_ai_hint():
    """Asks for a hint and updates the coach message."""
    global ai_coach_message, ai_eval_score, is_ai_thinking, last_hint_move
    if is_ai_thinking: return
    
    fen = generate_fen()
    print(f"--- Requesting Hint for FEN: {fen} ---")
    is_ai_thinking = True
    
    def fetch_hint():
        global ai_eval_score, ai_coach_message, is_ai_thinking, last_hint_move
        try:
            move, eval_val = get_evaluation_and_move(fen)
            ai_eval_score = eval_val if eval_val else "?"
            if move:
                last_hint_move = move   # Store raw UCI for bottom bar
                # Format as e2-e4 for sidebar
                move_fmt = f"{move[0]}{move[1]}-{move[2]}{move[3]}" if len(move) >= 4 else move
                print(f"--- Best Move: {move_fmt}  |  Eval: {eval_val} ---")
                ai_coach_message = f"Best move is {move_fmt.upper()}. Analyzing..."
                get_ai_coach_commentary(fen, move, eval_val, update_coach_text)
            else:
                ai_coach_message = "No clear best move found."
        except Exception as e:
            print(f"--- Hint Logic Error: {e} ---")
            ai_coach_message = "Coach had an error."
        finally:
            is_ai_thinking = False

    threading.Thread(target=fetch_hint).start()

def update_coach_text(text):
    """Callback to update coach message with LLM commentary + move notation."""
    global ai_coach_message
    if last_hint_move and len(last_hint_move) >= 4:
        move_fmt = f"{last_hint_move[0]}{last_hint_move[1]}-{last_hint_move[2]}{last_hint_move[3]}".upper()
        ai_coach_message = f"{text}\n\nBest Move: {move_fmt}"
    else:
        ai_coach_message = text

def generate_fen():
    """Generates the FEN string for the current board state."""
    fen_parts = []
    
    # 1. Piece placement
    piece_map = {
        ('white', 'pawn'): 'P', ('white', 'knight'): 'N', ('white', 'bishop'): 'B',
        ('white', 'rook'): 'R', ('white', 'queen'): 'Q', ('white', 'king'): 'K',
        ('black', 'pawn'): 'p', ('black', 'knight'): 'n', ('black', 'bishop'): 'b',
        ('black', 'rook'): 'r', ('black', 'queen'): 'q', ('black', 'king'): 'k'
    }
    
    rows = []
    for r in range(8):
        empty_count = 0
        row_str = ""
        for c in range(8):
            p = board[r][c]
            if p:
                if empty_count > 0:
                    row_str += str(empty_count)
                    empty_count = 0
                row_str += piece_map[(p.color, p.type)]
            else:
                empty_count += 1
        if empty_count > 0:
            row_str += str(empty_count)
        rows.append(row_str)
    fen_parts.append("/".join(rows))
    
    # 2. Side to move
    fen_parts.append('w' if current_turn_color == 'white' else 'b')
    
    # 3. Castling ability
    castling = ""
    # White
    wk = board[7][4]
    if wk and wk.type == 'king' and wk.color == 'white' and not wk.has_moved:
        # Kingside
        wr_k = board[7][7]
        if wr_k and wr_k.type == 'rook' and wr_k.color == 'white' and not wr_k.has_moved:
            castling += "K"
        # Queenside
        wr_q = board[7][0]
        if wr_q and wr_q.type == 'rook' and wr_q.color == 'white' and not wr_q.has_moved:
            castling += "Q"
    # Black
    bk = board[0][4]
    if bk and bk.type == 'king' and bk.color == 'black' and not bk.has_moved:
        # Kingside
        br_k = board[0][7]
        if br_k and br_k.type == 'rook' and br_k.color == 'black' and not br_k.has_moved:
            castling += "k"
        # Queenside
        br_q = board[0][0]
        if br_q and br_q.type == 'rook' and br_q.color == 'black' and not br_q.has_moved:
            castling += "q"
    
    fen_parts.append(castling if castling else "-")
    
    # 4. En passant target square
    if pawn_en_passant_target:
        r, c = pawn_en_passant_target
        col_char = chr(ord('a') + c)
        row_char = str(8 - r)
        fen_parts.append(f"{col_char}{row_char}")
    else:
        fen_parts.append("-")
    
    # 5. Halfmove clock
    fen_parts.append("0")
    
    # 6. Fullmove number
    fen_parts.append("1")
    
    return " ".join(fen_parts)

# --- Main Gameplay Interactions ---

def execute_move(target_row, target_col):
    """Applies a move to the board, handling captures and special side effects."""
    global current_turn_color, pawn_en_passant_target, active_selected_piece, active_selected_pos
    
    moving_piece = active_selected_piece
    if moving_piece is None or active_selected_pos is None:
        return

    # --- Execute the Move ---
    start_row, start_col = active_selected_pos
    captured_piece = board[target_row][target_col]
    prev_en_passant = pawn_en_passant_target
    is_en_passant = False
    is_castle_move = False
    rook_move_info = None

    # --- Side Effect: Castling ---
    if moving_piece.type == 'king' and abs(target_col - start_col) == 2:
        is_castle_move = True
        old_rook_col = 7 if target_col == 6 else 0
        new_rook_col = 5 if target_col == 6 else 3
        rook = board[target_row][old_rook_col]
        rook_move_info = (rook, (target_row, old_rook_col), (target_row, new_rook_col))
        
        board[target_row][new_rook_col] = board[target_row][old_rook_col]
        board[target_row][old_rook_col] = None
        if rook:
            rook.has_moved = True

    # --- Side Effect: En Passant Capture ---
    if moving_piece.type == 'pawn' and (target_row, target_col) == pawn_en_passant_target:
        is_en_passant = True
        captured_piece = board[start_row][target_col] # The captured pawn
        board[start_row][target_col] = None

    # --- Setup next turn's En Passant state ---
    pawn_en_passant_target = None
    if moving_piece.type == 'pawn' and abs(target_row - start_row) == 2:
        pawn_en_passant_target = ((target_row + start_row) // 2, start_col)

    # --- Finalize the Move ---
    board[target_row][target_col] = moving_piece
    board[start_row][start_col] = None
    moving_piece.has_moved = True

    # --- Auto-Promotion to Queen ---
    promoted_from = None
    is_promo = False
    if moving_piece.type == 'pawn' and (target_row == 0 or target_row == 7):
        is_promo = True
        promoted_from = moving_piece
        p_color = moving_piece.color
        board[target_row][target_col] = ChessPiece(p_color, 'queen', f'src/images/{p_color}_queen.png')

    # --- Store Move for Undo ---
    move_rec = MoveRecord(
        (start_row, start_col), (target_row, target_col), 
        board[target_row][target_col], # Could be promoted piece
        captured_piece, 
        prev_en_passant,
        is_en_passant=is_en_passant,
        is_castle=is_castle_move,
        rook_move=rook_move_info,
        is_promotion=is_promo,
        promoted_from=promoted_from
    )
    move_history.append(move_rec)

    # Switch turns
    current_turn_color = 'black' if current_turn_color == 'white' else 'white'
    
    # Update Board Evaluation (Live)
    def update_eval():
        global ai_eval_score
        _, eval_val = get_evaluation_and_move(generate_fen())
        ai_eval_score = eval_val

    threading.Thread(target=update_eval).start()

    # Trigger AI if enabled
    if ai_opponent_enabled and current_turn_color == 'black':
        perform_ai_turn()

    # Check for Checkmate or Stalemate
    if is_checkmate(current_turn_color):
        print(f"CHECKMATE! {current_turn_color.upper()} player has lost.")
    elif is_stalemate(current_turn_color):
        print("STALEMATE! The game ends in a draw.")

def undo_move():
    """Reverses the last move made using the move history stack."""
    global current_turn_color, pawn_en_passant_target, move_history
    if not move_history:
        print("No moves to undo.")
        return

    move = move_history.pop()
    sr, sc = move.start_pos
    tr, tc = move.end_pos

    # Restore piece position
    board[sr][sc] = move.piece_moved
    board[tr][tc] = move.captured_piece
    move.piece_moved.has_moved = move.piece_moved_had_moved

    # Restore En Passant capture
    if move.is_en_passant:
        # The captured pawn was at (sr, tc)
        board[sr][tc] = move.captured_piece
        board[tr][tc] = None

    # Restore Castling Rook
    if move.is_castle:
        rook, r_start, r_end = move.rook_move
        board[r_start[0]][r_start[1]] = rook
        board[r_end[0]][r_end[1]] = None
        if rook:
            rook.has_moved = move.rook_had_moved

    # Restore Promotion
    if move.is_promotion:
        board[sr][sc] = move.promoted_from

    # Restore global state
    pawn_en_passant_target = move.prev_en_passant
    current_turn_color = 'white' if current_turn_color == 'black' else 'black'
    print(f"Undo successful. Now it's {current_turn_color}'s turn.")

# Sidebar button rects – updated each frame by draw_sidebar
_hint_btn_rect   = pygame.Rect(0, 0, 1, 1)
_toggle_btn_rect = pygame.Rect(0, 0, 1, 1)

def handle_mouse_input(position):
    """Translates a user click into a selection or a move execution."""
    global active_selected_piece, active_selected_pos, legal_moves_for_selected
    global ai_opponent_enabled, ai_eval_score, current_theme_idx

    mx, my = position

    # 1. Top-bar theme clicks
    if my < TOPBAR_HEIGHT:
        btn_w, btn_h = 80, 28
        btn_y = (TOPBAR_HEIGHT - btn_h) // 2
        x = 150
        for i in range(len(THEME_NAMES)):
            rect = pygame.Rect(x, btn_y, btn_w, btn_h)
            if rect.collidepoint(mx, my):
                current_theme_idx = i
                return
            x += btn_w + 8
        return

    # 2. Sidebar button clicks
    if _hint_btn_rect.collidepoint(mx, my):
        get_ai_hint()
        return
    if _toggle_btn_rect.collidepoint(mx, my):
        ai_opponent_enabled = not ai_opponent_enabled
        if ai_opponent_enabled and current_turn_color == 'black':
            perform_ai_turn()
        active_selected_piece = None
        active_selected_pos = None
        legal_moves_for_selected = []
        return

    # 3. Board coordinate calculation (accounting for offsets)
    if mx < SIDEBAR_X and my >= BOARD_OFFSET_Y and my < BOARD_OFFSET_Y + BOARD_PX:
        col = (mx - BOARD_OFFSET_X) // SQUARE_SIZE
        row = (my - BOARD_OFFSET_Y) // SQUARE_SIZE

        if not (0 <= row < 8 and 0 <= col < 8):
            return

        # Phase 1: Picking up a piece
        if active_selected_piece is None:
            p = board[row][col]
            if p and p.color == current_turn_color:
                active_selected_piece = p
                active_selected_pos = (row, col)
                legal_moves_for_selected = get_fully_legal_moves(p, row, col)
        
        # Phase 2: Placing the selected piece
        else:
            if (row, col) in legal_moves_for_selected:
                execute_move(row, col)
            
            # Reset selection state
            active_selected_piece = None
            active_selected_pos = None
            legal_moves_for_selected = []

# --- Main Runtime Loop ---

def start_chess_game():
    """Initializes and runs the main game loop."""
    global _hint_btn_rect, _toggle_btn_rect
    initialize_game_board()
    throttle = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                handle_mouse_input(pygame.mouse.get_pos())
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_u:
                    undo_move()

        # --- Poll for pending AI move (set by background thread) ---
        global pending_ai_move, active_selected_piece, active_selected_pos, legal_moves_for_selected
        if pending_ai_move is not None:
            start_pos, end_pos = pending_ai_move
            pending_ai_move = None          # Consume it immediately
            piece = board[start_pos[0]][start_pos[1]]
            if piece and piece.color == 'black':
                active_selected_piece = piece
                active_selected_pos = start_pos
                legal_moves_for_selected = []
                execute_move(end_pos[0], end_pos[1])
                active_selected_piece = None
                active_selected_pos = None
                print(f"--- AI moved: {start_pos} -> {end_pos} ---")

        # Draw everything
        screen.fill(BG_DARK)
        draw_topbar()
        draw_chess_board()
        draw_all_pieces()
        draw_bottom_bar()
        rects = draw_sidebar()
        if rects:
            _hint_btn_rect, _toggle_btn_rect = rects
        pygame.display.flip()
        throttle.tick(60)

if __name__ == "__main__":
    start_chess_game()

        