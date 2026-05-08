import pygame, sys
 
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

board = [[(i * N + j + 1) for j in range(N)] for i in range(N)]

graphical_board = [[ [None, None] for _ in range(N)] for _ in range(N)]
to_move = 'X'
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
            if board[i][j] == 'X':
                graphical_board[i][j][0] = ximg
                graphical_board[i][j][1] = ximg.get_rect(center=(j*89+44, i*89+44))
            elif board[i][j] == 'O':
                graphical_board[i][j][0] = oimg
                graphical_board[i][j][1] = oimg.get_rect(center=(j*89+44, i*89+44))
# add XO
def add_XO(board, graphical_board, to_move):
    current_pos = pygame.mouse.get_pos()
    
    converted_x = int((current_pos[0]) / WIDTH * N)
    converted_y = int((current_pos[1]) / HEIGHT * N)
    
    if 0 <= converted_x < N and 0 <= converted_y < N:
        if board[converted_y][converted_x] not in ['O', 'X']:
            board[converted_y][converted_x] = to_move 
            last_move = to_move
            to_move = 'O' if to_move == 'X' else 'X'
            render_board(board, X_IMG, O_IMG)
            return board, to_move, converted_y, converted_x, last_move
    return board, to_move, None, None, None
# Check
def countDirection(i, j, xdir, ydir, state):
        count = 0
        for step in range(1, 4): 
            if xdir != 0 and (j + xdir*step < 0 or j + xdir*step >= N): # ensure move inside the board
                break
            if ydir != 0 and (i + ydir*step < 0 or i + ydir*step >= N):
                break
            if board[i + ydir*step][j + xdir*step] == state:
                count += 1
            else:
                break
        return count

    # Check whether there are 5 pieces connected (in all 4 directions)
def isFour(i, j, state):
    # 4 directions: horizontal, vertical, 2 diagonals
    directions = [[(-1, 0), (1, 0)], \
                    [(0, -1), (0, 1)], \
                    [(-1, 1), (1, -1)], \
                    [(-1, -1), (1, 1)]]
    for axis in directions:
        axis_count = 1
        for (xdir, ydir) in axis:
            axis_count += countDirection(i, j, xdir, ydir, state)
            if axis_count >= 4:
                return True
    return False

# Main
game_finished = False
while True:
    SCREEN.blit(BOARD, (0, 0))
    for i in range(N):
        for j in range(N):
            if graphical_board[i][j][0] is not None:
                SCREEN.blit(graphical_board[i][j][0], graphical_board[i][j][1])
    if game_finished:
            display_winner(winner_text)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_finished:
                board = [[(i * N + j + 1) for j in range(N)] for i in range(N)]
                graphical_board = [[ [None, None] for _ in range(N)] for _ in range(N)]
                to_move = 'X'
                game_finished = False
                winner_text = ""
            else:
                board, to_move, y, x, last_move= add_XO(board, graphical_board, to_move)
                if y is not None and x is not None:
                    if isFour(y, x, last_move):
                        winner_text = f"PLAYER {last_move} WINS!"
                        game_finished = True
                else:
                    print("Vui lòng nhập vị trí khác!")
    pygame.display.update() 

