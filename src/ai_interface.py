import os
import threading
import logging
from stockfish import Stockfish
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Thread Lock for Stockfish (Mandatory to prevent engine crashes)
engine_lock = threading.Lock()

# Initialize Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Try to find a working model
try:
    # Use gemini-1.5-flash as default, but allow easy fallback
    model_name = 'gemini-3-flash-preview' 
    model = genai.GenerativeModel(model_name)
    print(f"--- Gemini loaded with model: {model_name} ---")
except Exception as e:
    print(f"--- Gemini model {model_name} error, trying fallback... ---")
    model = genai.GenerativeModel('gemini-pro')

AI_STATUS = "Initializing..."

# Initialize Stockfish (Global instance for efficiency)
stockfish_path = os.getenv("STOCKFISH_PATH")
engine = None
try:
    if stockfish_path and os.path.exists(stockfish_path):
        engine = Stockfish(path=stockfish_path)
        engine.set_skill_level(20) # Max skill
        AI_STATUS = "Ready"
        print(f"--- Stockfish initialized successfully ---")
    else:
        AI_STATUS = "Engine Path Error"
        print(f"--- Stockfish path not found: {stockfish_path} ---")
except Exception as e:
    AI_STATUS = f"Engine Error: {str(e)[:20]}"
    print(f"--- Error initializing Stockfish: {e} ---")
    engine = None

def is_engine_ready():
    return engine is not None

def get_best_move_from_stockfish(fen):
    """Asks Stockfish for the best move in UCI format (e.g., 'e2e4')."""
    global AI_STATUS
    if not engine:
        return None
    with engine_lock:
        try:
            old_status = AI_STATUS
            AI_STATUS = "Thinking..."
            logger.info(f"Engine Move Request: {fen}")
            engine.set_fen_position(fen)
            move = engine.get_best_move()
            logger.info(f"Engine Best Move: {move}")
            AI_STATUS = old_status
            return move
        except Exception as e:
            AI_STATUS = "Engine Error"
            logger.error(f"Stockfish Move Error: {e}")
            return None

def get_ai_coach_commentary(fen, best_move, evaluation, callback):
    """
    Non-blocking thread to fetch natural language commentary from Gemini.
    Calls 'callback(commentary)' when finished.
    """
    global AI_STATUS
    if not model:
        callback("Coach is unavailable (Model Init Failed)")
        return

    def run():
        global AI_STATUS
        prompt = f"""
        You are a Grandmaster Chess Coach. 
        Current Board (FEN): {fen}
        Stockfish Evaluation: {evaluation}
        Best Move (UCI): {best_move}
        
        Provide a concise (maximum 2 sentences) explanation of why this move is good or 
        what the strategic goal is. Speak like a helpful mentor.
        """
        try:
            AI_STATUS = "Coach thinking..."
            response = model.generate_content(prompt)
            callback(response.text.strip())
            AI_STATUS = "Ready"
        except Exception as e:
            AI_STATUS = "Coach Error"
            logger.error(f"Gemini Error: {e}")
            callback(f"Coach had an error (See console)")

    threading.Thread(target=run).start()

def get_evaluation_and_move(fen):
    """Returns (best_move, evaluation_score). Perspective is always WHITE."""
    global AI_STATUS
    if not engine:
        return None, "Engine Off"
    with engine_lock:
        try:
            AI_STATUS = "Evaluating..."
            engine.set_fen_position(fen)
            move = engine.get_best_move()
            eval_data = engine.get_evaluation()
            
            # Safe split for FEN
            parts = fen.split(' ')
            is_white_turn = parts[1] == 'w' if len(parts) > 1 else True
            
            if eval_data['type'] == 'cp':
                val = eval_data['value']
                if not is_white_turn:
                    val = -val
                score = val / 100.0
                eval_str = f"{score:+}"
            else:
                # Mate
                val = eval_data['value']
                if not is_white_turn:
                    val = -val
                eval_str = f"Mate in {abs(val)}" if val > 0 else f"Mate in -{abs(val)}"
                
            AI_STATUS = "Ready"
            return move, eval_str
        except Exception as e:
            AI_STATUS = "Eval Error"
            logger.error(f"Stockfish Eval Error: {e}")
            return None, "Error"
