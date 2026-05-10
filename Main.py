import pygame, sys
import threading # Thêm thư viện đa luồng
from AI import AiTicTacToe

pygame.init()

WIDTH, HEIGHT = 800, 800
XO_Size = (64, 64)
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tic Tac Toe - AI Multithreaded")
BOARD = pygame.image.load("assets/Board.jpg")
BOARD = pygame.transform.scale(BOARD, (800, 800))
X_IMG = pygame.image.load("assets/X.png")
O_IMG = pygame.image.load("assets/O.png")
X_IMG = pygame.transform.scale(X_IMG, XO_Size)
O_IMG = pygame.transform.scale(O_IMG, XO_Size)
N = 9

board = [[0 for _ in range(N)] for _ in range(N)]
graphical_board = [[ [None, None] for _ in range(N)] for _ in range(N)]
to_move = -1
FONT = pygame.font.SysFont("arial", 40)

# --- BIẾN ĐIỀU KHIỂN LUỒNG ---
ai_thinking = False 

def display_winner(text):
    render_text = FONT.render(text, True, (255, 215, 0)) 
    text_rect = render_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    overlay = pygame.Surface((WIDTH, 150))
    overlay.set_alpha(180) 
    overlay.fill((0, 0, 0))
    SCREEN.blit(overlay, (0, HEIGHT // 2 - 75))
    SCREEN.blit(render_text, text_rect)

def render_board(board, ximg, oimg):
    global graphical_board
    for i in range(N):
        for j in range(N):
            if board[i][j] == -1:
                graphical_board[i][j][0] = ximg
                graphical_board[i][j][1] = ximg.get_rect(center=(j*89+44, i*89+44))
            elif board[i][j] == 1:
                graphical_board[i][j][0] = oimg
                graphical_board[i][j][1] = oimg.get_rect(center=(j*89+44, i*89+44))

def add_XO(board, graphical_board, to_move):
    current_pos = pygame.mouse.get_pos()
    converted_x = int((current_pos[0]) / WIDTH * N)
    converted_y = int((current_pos[1]) / HEIGHT * N)
    
    if 0 <= converted_x < N and 0 <= converted_y < N:
        if board[converted_y][converted_x] == 0:
            board[converted_y][converted_x] = to_move 
            last_move = to_move
            render_board(board, X_IMG, O_IMG)
            return board, (1 if to_move == -1 else -1), converted_y, converted_x, last_move
    return board, to_move, None, None, None

# --- HÀM XỬ LÝ AI TRONG LUỒNG RIÊNG ---
def ai_task():
    global ai_thinking, to_move, game_finished, winner_text
    
    # 1. AI tính toán nước đi
    move_y, move_x = ai.best_move() 
    
    if move_y != -1 and not game_finished:
        # 2. Cập nhật dữ liệu
        board[move_y][move_x] = 1
        ai.board[move_y][move_x] = 1
        ai.currentI, ai.currentJ = move_y, move_x
        ai.lastPlayed = 1
        ai.emptyCells -= 1
        ai.update_bound(move_y, move_x, ai.next_bound)
        
        # 3. Cập nhật đồ họa
        render_board(board, X_IMG, O_IMG)
        
        # 4. Kiểm tra kết quả
        if ai.isFour(move_y, move_x, 1):
            winner_text = "AI (O) WINS!"
            game_finished = True
        elif ai.emptyCells <= 0:
            winner_text = "TIE GAME!"
            game_finished = True
            
    # 5. Kết thúc lượt và mở khóa luồng
    to_move = -1
    ai_thinking = False

# Main
game_finished = False
ai = AiTicTacToe()
winner_text = ""
clock = pygame.time.Clock()

while True:
    SCREEN.blit(BOARD, (0, 0))
    
    for i in range(N):
        for j in range(N):
            if graphical_board[i][j][0] is not None:
                SCREEN.blit(graphical_board[i][j][0], graphical_board[i][j][1])
    
    if game_finished:
        display_winner(winner_text)
    
    # --- LOGIC AI ĐA LUỒNG ---
    if not game_finished and to_move == 1:
        if not ai_thinking:
            ai_thinking = True
            # Chạy hàm ai_task trong một thread mới
            ai_thread = threading.Thread(target=ai_task)
            ai_thread.start()
        
        # Vẽ hiệu ứng "AI is thinking..." để người chơi biết
        thinking_text = FONT.render("AI is thinking...", True, (255, 255, 255))
        SCREEN.blit(thinking_text, (20, 20))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Chỉ nhận click nếu game chưa xong và AI không đang nghĩ
            if game_finished:
                board = [[0 for _ in range(N)] for _ in range(N)] 
                graphical_board = [[ [None, None] for _ in range(N)] for _ in range(N)]
                ai = AiTicTacToe() 
                to_move = -1
                game_finished = False
                winner_text = ""
                ai_thinking = False
            elif to_move == -1 and not ai_thinking: 
                board, to_move, y, x, last_move = add_XO(board, graphical_board, to_move)
                if y is not None and x is not None:
                    ai.board[y][x] = -1
                    ai.currentI, ai.currentJ = y, x
                    ai.lastPlayed = -1
                    ai.emptyCells -= 1
                    ai.update_bound(y, x, ai.next_bound)
                    
                    if ai.isFour(y, x, last_move):
                        winner_text = "PLAYER (X) WINS!"
                        game_finished = True
                    elif ai.emptyCells <= 0:
                        winner_text = "TIE GAME!"
                        game_finished = True

    pygame.display.update()
    clock.tick(60)