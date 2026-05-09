import pygame, sys
from AI import AiTicTacToe
pygame.init()
 
WIDTH, HEIGHT = 800, 800
XO_Size = (64, 64)
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tic Tac Toe!")
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

def display_winner(text):

    render_text = FONT.render(text, True, (255, 215, 0)) 
    text_rect = render_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    
    overlay = pygame.Surface((WIDTH, 150))
    overlay.set_alpha(180) 
    overlay.fill((0, 0, 0))
    SCREEN.blit(overlay, (0, HEIGHT // 2 - 75))
    
    SCREEN.blit(render_text, text_rect)
    
# render board
def render_board(board, ximg, oimg):
    global graphical_board
    for i in range(9):
        for j in range(9):
            if board[i][j] == -1:
                graphical_board[i][j][0] = ximg
                graphical_board[i][j][1] = ximg.get_rect(center=(j*89+44, i*89+44))
            elif board[i][j] == 1:
                graphical_board[i][j][0] = oimg
                graphical_board[i][j][1] = oimg.get_rect(center=(j*89+44, i*89+44))
# add XO
def add_XO(board, graphical_board, to_move):
    current_pos = pygame.mouse.get_pos()
    
    converted_x = int((current_pos[0]) / WIDTH * N)
    converted_y = int((current_pos[1]) / HEIGHT * N)
    
    if 0 <= converted_x < N and 0 <= converted_y < N:
        if board[converted_y][converted_x] == 0:
            board[converted_y][converted_x] = to_move 
            last_move = to_move
            to_move = 1 if to_move == -1 else -1
            render_board(board, X_IMG, O_IMG)
            return board, to_move, converted_y, converted_x, last_move
    return board, to_move, None, None, None

# Main
# Main
game_finished = False
ai = AiTicTacToe()
winner_text = ""

while True:
    SCREEN.blit(BOARD, (0, 0))
    
    for i in range(N):
        for j in range(N):
            if graphical_board[i][j][0] is not None:
                SCREEN.blit(graphical_board[i][j][0], graphical_board[i][j][1])
    
    if game_finished:
        display_winner(winner_text)
    
    if not game_finished and to_move == 1:
        move_y, move_x = ai.best_move() 
        
        if move_y != -1:
            board[move_y][move_x] = 1
            
            ai.board[move_y][move_x] = 1
            ai.currentI, ai.currentJ = move_y, move_x
            ai.lastPlayed = 1
            ai.emptyCells -= 1
            ai.updateBound(move_y, move_x, ai.nextBound)
            
            render_board(board, X_IMG, O_IMG)
        
            if ai.isFour(move_y, move_x, 1):
                winner_text = "AI (O) WINS!"
                game_finished = True
            
            to_move = -1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_finished:
                # Reset game
                board = [[0 for _ in range(N)] for _ in range(N)] 
                graphical_board = [[ [None, None] for _ in range(N)] for _ in range(N)]
                ai = AiTicTacToe() 
                to_move = -1
                game_finished = False
                winner_text = ""
            elif to_move == -1: 
                board, to_move, y, x, last_move = add_XO(board, graphical_board, to_move)
                if y is not None and x is not None:
                    ai.board[y][x] = -1
                    ai.currentI, ai.currentJ = y, x
                    ai.lastPlayed = -1
                    ai.emptyCells -= 1
                    ai.updateBound(y, x, ai.nextBound)
                    
                    if ai.isFour(y, x, last_move):
                        winner_text = "PLAYER (X) WINS!"
                        game_finished = True

    pygame.display.update()

