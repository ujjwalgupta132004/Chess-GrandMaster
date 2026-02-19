from main import generate_fen, board, initialize_game_board

initialize_game_board()
print("Starting position FEN:")
print(generate_fen())

# Simulate a move: e2-e4
pawn = board[6][4]
board[4][4] = pawn
board[6][4] = None
pawn.has_moved = True

print("\nAfter e4 move FEN:")
print(generate_fen())
