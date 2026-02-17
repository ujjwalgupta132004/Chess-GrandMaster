import pygame
import sys

pygame.init()

#Constants
WIDHT, HEIGHT = 800,800
SQUARE_SIZE = WIDHT//8

#colors
WHITE =(255,255,255)
BLACK = (0,0,0)
BROWN = (139,69,19)
YELLOW = (255,255,0)
LIGHT_GREEN = (144,238,144)

#create the screen

screen = pygame.display.set_mode((WIDHT,HEIGHT))
pygame.display.set_caption("Chess Game") 

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

def draw_chess_board():
    """Renders the grid and highlights the selection and legal moves."""
    for row in range(8):
        for col in range(8):
            # Calculate standard checkerboard color
            square_color = WHITE if (row + col) % 2 == 0 else LIGHT_GREEN
            
            # Highlight the King if it is currently threatened (Check)
            current_square_piece = board[row][col]
            if current_square_piece:
                if current_square_piece.type == 'king' and current_square_piece.color == current_turn_color:
                    if is_king_in_check(current_turn_color):
                        square_color = (255, 100, 100) # Soft Red indicator
                
            pygame.draw.rect(screen, square_color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
    
    # Highlight the selected piece's square in yellow
    if active_selected_pos:
        sel_row, sel_col = active_selected_pos
        pygame.draw.rect(screen, YELLOW, (sel_col * SQUARE_SIZE, sel_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
        
    # Draw dark gray dots on potential target squares
    for move_row, move_col in legal_moves_for_selected:
        center = (move_col * SQUARE_SIZE + SQUARE_SIZE // 2, move_row * SQUARE_SIZE + SQUARE_SIZE // 2)
        pygame.draw.circle(screen, (80, 80, 80), center, SQUARE_SIZE // 8)

def draw_all_pieces():
    """Draws piece images on top of the squares."""
    for row in range(8):
        for col in range(8):
            p = board[row][col]
            if p:
                screen.blit(p.image, (col * SQUARE_SIZE, row * SQUARE_SIZE))

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

# --- Main Gameplay Interactions ---

def execute_move(target_row, target_col):
    """Applies a move to the board, handling captures and special side effects."""
    global current_turn_color, pawn_en_passant_target, active_selected_piece, active_selected_pos
    
    moving_piece = active_selected_piece
    if moving_piece is None or active_selected_pos is None:
        return

    start_row, start_col = active_selected_pos
    
    # --- Side Effect: Castling ---
    if moving_piece.type == 'king' and abs(target_col - start_col) == 2:
        old_rook_col = 7 if target_col == 6 else 0
        new_rook_col = 5 if target_col == 6 else 3
        board[target_row][new_rook_col] = board[target_row][old_rook_col]
        board[target_row][old_rook_col] = None
        moved_rook = board[target_row][new_rook_col]
        if moved_rook:
            moved_rook.has_moved = True

    # --- Side Effect: En Passant Capture ---
    if moving_piece.type == 'pawn' and (target_row, target_col) == pawn_en_passant_target:
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
    if moving_piece.type == 'pawn' and (target_row == 0 or target_row == 7):
        p_color = moving_piece.color
        board[target_row][target_col] = ChessPiece(p_color, 'queen', f'src/images/{p_color}_queen.png')

    # Switch turns
    current_turn_color = 'black' if current_turn_color == 'white' else 'white'
    
    # Check for Checkmate or Stalemate
    if has_no_legal_moves(current_turn_color):
        if is_king_in_check(current_turn_color):
            print(f"CHECKMATE! {current_turn_color.upper()} player has lost.")
        else:
            print("STALEMATE! The game ends in a draw.")

def handle_mouse_input(position):
    """Translates a user click into a selection or a move execution."""
    global active_selected_piece, active_selected_pos, legal_moves_for_selected
    
    col = position[0] // SQUARE_SIZE
    row = position[1] // SQUARE_SIZE

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
    initialize_game_board()
    throttle = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                handle_mouse_input(pygame.mouse.get_pos())

        draw_chess_board()
        draw_all_pieces()
        pygame.display.flip()
        throttle.tick(60)

if __name__ == "__main__":
    start_chess_game()
        