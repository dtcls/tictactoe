import pygame, sys
import threading 
from AI import AiTicTacToe

pygame.init()
pygame.mixer.init() # Khởi tạo module âm thanh của Pygame

# 1. CẬP NHẬT KÍCH THƯỚC MÀN HÌNH VÀ BẢNG CỜ
WIDTH, HEIGHT = 1280, 720
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Caro Board - Mang tinh yeu den cho moi nha")

N = 9
CELL_SIZE = 55 # Kích thước 1 ô vuông 
BOARD_SIZE = CELL_SIZE * N # Kích thước bảng 9x9 (495x495)
BOARD_X = 600 # Đẩy bảng sang phải một chút cho cân đối
BOARD_Y = 100 # Đẩy bảng xuống dưới

# --- TẢI ẢNH NỀN GIẤY CUỘN CỔ ĐIỂN ---
try:
    BG_IMG = pygame.image.load("assets/vintage_theme.jpg.jpeg")
    BG_IMG = pygame.transform.scale(BG_IMG, (WIDTH, HEIGHT))
except Exception as e:
    print(f"Lỗi tải ảnh nền: {e}")
    BG_IMG = pygame.Surface((WIDTH, HEIGHT))
    BG_IMG.fill((220, 205, 175)) 

# Thu nhỏ X, O cho vừa với ô 60x60
XO_Size = (40, 40)
try:
    X_IMG = pygame.image.load("assets/X.png")
    O_IMG = pygame.image.load("assets/O.png")
    X_IMG = pygame.transform.scale(X_IMG, XO_Size)
    O_IMG = pygame.transform.scale(O_IMG, XO_Size)
except Exception as e:
    print(f"Lỗi tải ảnh X/O: {e}")
    X_IMG = None
    O_IMG = None

# --- TẢI ÂM THANH VÀ NHẠC NỀN ---
try:
    # --- 1. Tải Hiệu ứng âm thanh (Sound Effects) ---
    SOUND_MOVE = pygame.mixer.Sound("assets/move2.wav")   
    SOUND_CLICK = pygame.mixer.Sound("assets/click.wav") 
    SOUND_UNDO = pygame.mixer.Sound("assets/undo.wav")   

    # --- 2. Tải và phát Nhạc nền (Background Music) ---
    # Thay "bgm.mp3" bằng tên file nhạc của bạn
    pygame.mixer.music.load("assets/bgm.wav") 
    
    # Chỉnh âm lượng nhạc nền (0.0 đến 1.0). Để 0.3 cho nhạc phát nhè nhẹ làm nền
    pygame.mixer.music.set_volume(0.2) 
    
    # Phát nhạc. Số -1 có nghĩa là nhạc sẽ lặp lại vô tận (Loop)
    pygame.mixer.music.play(-1) 

except Exception as e:
    print(f"Lỗi tải âm thanh (hãy kiểm tra lại tên file trong thư mục assets): {e}")
    SOUND_MOVE = None
    SOUND_CLICK = None
    SOUND_UNDO = None

def play_sound(sound):
    """Hàm hỗ trợ phát âm thanh để tránh lỗi nếu file không tồn tại"""
    if sound:
        sound.play()

board = [[0 for _ in range(N)] for _ in range(N)]
graphical_board = [[ [None, None] for _ in range(N)] for _ in range(N)]
to_move = -1

# --- KHỞI TẠO CÁC FONT CHỮ ---
classic_font = "Courier New" 

# Sử dụng SysFont để lấy phông có sẵn trong hệ điều hành
FONT = pygame.font.SysFont(classic_font, 42, bold=True)
FONT_SMALL = pygame.font.SysFont(classic_font, 20, bold=True)
FONT_MED = pygame.font.SysFont(classic_font, 24, bold=True) 
FONT_LARGE = pygame.font.SysFont(classic_font, 36, bold=True)

# --- BIẾN TOÀN CỤC CHO UI & GAME LỌGIC ---
ai_thinking = False 
game_finished = False
current_difficulty = "Medium" 
move_history = [] # Lịch sử lưu các nước đi (y, x, người chơi) để dùng cho Undo

btn_easy_rect = None
btn_med_rect = None
btn_hard_rect = None
btn_undo_rect = None

def display_winner(text):
    render_text = FONT.render(text, True, (255, 215, 0)) 
    text_rect = render_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    overlay = pygame.Surface((WIDTH, 150))
    overlay.set_alpha(180) 
    overlay.fill((0, 0, 0))
    SCREEN.blit(overlay, (0, HEIGHT // 2 - 75))
    SCREEN.blit(render_text, text_rect)

# 2. HÀM VẼ NỀN ẢNH VÀ UI BẢNG CỜ ĐƯỢC CHIA Ô
def draw_background_and_ui(surface):
    global to_move, ai_thinking, game_finished
    global btn_easy_rect, btn_med_rect, btn_hard_rect, btn_undo_rect, current_difficulty
    
    surface.blit(BG_IMG, (0, 0))
    
    ink_color = (80, 55, 40)
    parchment_color = (230, 212, 175)
    
    box_bg_color = (240, 220, 190)       
    highlight_bg_color = (255, 255, 235) 
    highlight_border = 4                 
    normal_border = 2                    

    # Bảng UI Menu (Bên trái)
    ui_x = 180
    ui_y = BOARD_Y      
    ui_width = 350
    ui_height = BOARD_SIZE 
    
    pygame.draw.rect(surface, parchment_color, (ui_x, ui_y, ui_width, ui_height))
    pygame.draw.rect(surface, ink_color, (ui_x, ui_y, ui_width, ui_height), 3)

    padding = 15
    box_w = ui_width - 2 * padding
    
    # --- Ô 1: YOU / PLAYER / X ---
    box1_y = ui_y + padding
    box1_h = 100
    
    is_player_turn = (not game_finished and to_move == -1)
    current_box1_bg = highlight_bg_color if is_player_turn else box_bg_color
    current_box1_border = highlight_border if is_player_turn else normal_border
    
    pygame.draw.rect(surface, current_box1_bg, (ui_x + padding, box1_y, box_w, box1_h))
    pygame.draw.rect(surface, ink_color, (ui_x + padding, box1_y, box_w, box1_h), current_box1_border)
    
    surface.blit(FONT_SMALL.render("YOU", True, (120, 100, 80)), (ui_x + padding + 15, box1_y + 15))
    surface.blit(FONT_LARGE.render("Player", True, (20, 100, 20)), (ui_x + padding + 15, box1_y + 45))
    if X_IMG:
        surface.blit(X_IMG, (ui_x + padding + box_w - 60, box1_y + 30))

    # --- Ô 2: BOT / AI / O ---
    box2_y = box1_y + box1_h + padding
    box2_h = 100
    
    is_ai_turn = (not game_finished and to_move == 1)
    current_box2_bg = highlight_bg_color if is_ai_turn else box_bg_color
    current_box2_border = highlight_border if is_ai_turn else normal_border

    pygame.draw.rect(surface, current_box2_bg, (ui_x + padding, box2_y, box_w, box2_h))
    pygame.draw.rect(surface, ink_color, (ui_x + padding, box2_y, box_w, box2_h), current_box2_border)
    
    surface.blit(FONT_SMALL.render("BOT", True, (120, 100, 80)), (ui_x + padding + 15, box2_y + 15))
    surface.blit(FONT_LARGE.render("AI", True, (180, 40, 40)), (ui_x + padding + 15, box2_y + 45))
    if O_IMG:
        surface.blit(O_IMG, (ui_x + padding + box_w - 60, box2_y + 30))

    # --- Ô 3: DIFFICULTY (NÚT BẤM) ---
    box3_y = box2_y + box2_h + padding
    box3_h = 90
    pygame.draw.rect(surface, box_bg_color, (ui_x + padding, box3_y, box_w, box3_h))
    pygame.draw.rect(surface, ink_color, (ui_x + padding, box3_y, box_w, box3_h), normal_border)
    
    surface.blit(FONT_SMALL.render("DIFFICULTY", True, (120, 100, 80)), (ui_x + padding + 15, box3_y + 10))
    
    btn_w = (box_w - 40) // 3 
    btn_h = 35
    btn_start_x = ui_x + padding + 10
    btn_y = box3_y + 40

    difficulties = ["Easy", "Medium", "Hard"]
    rects = []

    for i, diff in enumerate(difficulties):
        rect = pygame.Rect(btn_start_x + i * (btn_w + 10), btn_y, btn_w, btn_h)
        rects.append(rect)
        
        if current_difficulty == diff:
            pygame.draw.rect(surface, ink_color, rect) 
            text_color = (255, 255, 255)
        else:
            pygame.draw.rect(surface, ink_color, rect, 2)
            text_color = ink_color

        render_txt = FONT_MED.render(diff, True, text_color)
        surface.blit(render_txt, (rect.x + (btn_w - render_txt.get_width()) // 2, rect.y + (btn_h - render_txt.get_height()) // 2))

    btn_easy_rect, btn_med_rect, btn_hard_rect = rects[0], rects[1], rects[2]

    # --- Ô 4: TRẠNG THÁI LƯỢT ĐI ---
    box4_y = box3_y + box3_h + padding
    box4_h = 70
    pygame.draw.rect(surface, box_bg_color, (ui_x + padding, box4_y, box_w, box4_h))
    pygame.draw.rect(surface, ink_color, (ui_x + padding, box4_y, box_w, box4_h), normal_border)
    
    status_color = ink_color
    if game_finished:
        status_text = "Game Over!"
    elif to_move == -1:
        status_text = "Your Turn (X)"
        status_color = (20, 100, 20) 
    else:
        status_text = "AI is thinking (O)..."
        status_color = (180, 40, 40) 
        
    render_status = FONT_MED.render(status_text, True, status_color)
    surface.blit(render_status, (ui_x + padding + (box_w - render_status.get_width()) // 2, box4_y + (box4_h - render_status.get_height()) // 2))

    # --- Ô 5: NÚT ĐI LẠI (UNDO) ---
    box5_y = box4_y + box4_h + padding
    box5_h = 50
    btn_undo_rect = pygame.Rect(ui_x + padding, box5_y, box_w, box5_h)
    
    # Kiểm tra điều kiện có được bấm Undo không
    can_undo = not ai_thinking and len(move_history) >= 2
    
    undo_bg = box_bg_color if can_undo else (220, 210, 190)
    undo_txt_color = ink_color if can_undo else (150, 140, 130)

    pygame.draw.rect(surface, undo_bg, btn_undo_rect)
    pygame.draw.rect(surface, ink_color, btn_undo_rect, normal_border)
    
    undo_txt = FONT_MED.render("Undo", True, undo_txt_color)
    surface.blit(undo_txt, (btn_undo_rect.x + (box_w - undo_txt.get_width())//2, btn_undo_rect.y + (box5_h - undo_txt.get_height())//2))

    # Vẽ bảng caro 9x9 bên phải
    for i in range(N + 1):
        pygame.draw.line(surface, ink_color, 
                         (BOARD_X + i * CELL_SIZE, BOARD_Y), 
                         (BOARD_X + i * CELL_SIZE, BOARD_Y + BOARD_SIZE), 2)
        pygame.draw.line(surface, ink_color, 
                         (BOARD_X, BOARD_Y + i * CELL_SIZE), 
                         (BOARD_X + BOARD_SIZE, BOARD_Y + i * CELL_SIZE), 2)
        
# 3. CẬP NHẬT TỌA ĐỘ VẼ X/O
def render_board(board, ximg, oimg):
    global graphical_board
    for i in range(N):
        for j in range(N):
            center_x = BOARD_X + j * CELL_SIZE + CELL_SIZE // 2
            center_y = BOARD_Y + i * CELL_SIZE + CELL_SIZE // 2
            
            if board[i][j] == -1:
                graphical_board[i][j][0] = ximg
                graphical_board[i][j][1] = ximg.get_rect(center=(center_x, center_y))
            elif board[i][j] == 1:
                graphical_board[i][j][0] = oimg
                graphical_board[i][j][1] = oimg.get_rect(center=(center_x, center_y))

# 4. CẬP NHẬT TỌA ĐỘ CLICK CHUỘT LÊN BÀN CỜ
def add_XO(board, graphical_board, to_move):
    current_pos = pygame.mouse.get_pos()
    
    if BOARD_X <= current_pos[0] <= BOARD_X + BOARD_SIZE and BOARD_Y <= current_pos[1] <= BOARD_Y + BOARD_SIZE:
        converted_x = int((current_pos[0] - BOARD_X) / CELL_SIZE)
        converted_y = int((current_pos[1] - BOARD_Y) / CELL_SIZE)
        
        if 0 <= converted_x < N and 0 <= converted_y < N:
            if board[converted_y][converted_x] == 0:
                board[converted_y][converted_x] = to_move 
                last_move = to_move
                render_board(board, X_IMG, O_IMG)
                return board, (1 if to_move == -1 else -1), converted_y, converted_x, last_move
                
    return board, to_move, None, None, None

def ai_task():
    global ai_thinking, to_move, game_finished, winner_text, current_difficulty, move_history
    
    if current_difficulty == "Easy": ai.depth = 2
    elif current_difficulty == "Medium": ai.depth = 3
    elif current_difficulty == "Hard": ai.depth = 4

    move_y, move_x = ai.best_move() 
    
    if move_y != -1 and not game_finished:
        board[move_y][move_x] = 1
        ai.board[move_y][move_x] = 1
        ai.currentI, ai.currentJ = move_y, move_x
        ai.lastPlayed = 1
        ai.emptyCells -= 1
        ai.update_bound(move_y, move_x, ai.next_bound)
        
        # Lưu nước đi của máy vào lịch sử
        move_history.append((move_y, move_x, 1))
        
        # Phát âm thanh khi AI đánh
        play_sound(SOUND_MOVE)
        
        render_board(board, X_IMG, O_IMG)
        
        if ai.isFour(move_y, move_x, 1):
            winner_text = "AI (O) WINS!"
            game_finished = True
        elif ai.emptyCells <= 0:
            winner_text = "TIE GAME!"
            game_finished = True
            
    to_move = -1
    ai_thinking = False

# --- MAIN LOOP ---
ai = AiTicTacToe()
winner_text = ""
clock = pygame.time.Clock()

while True:
    draw_background_and_ui(SCREEN)
    
    for i in range(N):
        for j in range(N):
            if graphical_board[i][j][0] is not None:
                SCREEN.blit(graphical_board[i][j][0], graphical_board[i][j][1])
    
    if game_finished:
        display_winner(winner_text)
    
    if not game_finished and to_move == 1:
        if not ai_thinking:
            ai_thinking = True
            ai_thread = threading.Thread(target=ai_task)
            ai_thread.start()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            
            # --- XỬ LÝ CLICK NÚT UNDO ---
            if btn_undo_rect and btn_undo_rect.collidepoint(mouse_pos):
                if not ai_thinking and len(move_history) >= 2:
                    # Phát âm thanh Undo
                    play_sound(SOUND_UNDO)
                    
                    while len(move_history) > 0 and move_history[-1][2] == 1:
                        move_history.pop()
                    if len(move_history) > 0 and move_history[-1][2] == -1:
                        move_history.pop()
                    
                    board = [[0 for _ in range(N)] for _ in range(N)] 
                    graphical_board = [[ [None, None] for _ in range(N)] for _ in range(N)]
                    ai = AiTicTacToe() 
                    to_move = -1
                    game_finished = False
                    winner_text = ""
                    
                    for hy, hx, hp in move_history:
                        board[hy][hx] = hp
                        ai.board[hy][hx] = hp
                        ai.currentI, ai.currentJ = hy, hx
                        ai.lastPlayed = hp
                        ai.emptyCells -= 1
                        ai.update_bound(hy, hx, ai.next_bound)
                        
                    render_board(board, X_IMG, O_IMG)
                continue 

            # --- XỬ LÝ CLICK CHỌN ĐỘ KHÓ ---
            if not game_finished and to_move == -1 and not ai_thinking:
                if btn_easy_rect and btn_easy_rect.collidepoint(mouse_pos):
                    if current_difficulty != "Easy": play_sound(SOUND_CLICK)
                    current_difficulty = "Easy"
                    continue 
                elif btn_med_rect and btn_med_rect.collidepoint(mouse_pos):
                    if current_difficulty != "Medium": play_sound(SOUND_CLICK)
                    current_difficulty = "Medium"
                    continue
                elif btn_hard_rect and btn_hard_rect.collidepoint(mouse_pos):
                    if current_difficulty != "Hard": play_sound(SOUND_CLICK)
                    current_difficulty = "Hard"
                    continue

            # --- XỬ LÝ CLICK LÊN BÀN CỜ ---
            if game_finished and BOARD_X <= mouse_pos[0] <= BOARD_X + BOARD_SIZE and BOARD_Y <= mouse_pos[1] <= BOARD_Y + BOARD_SIZE:
                board = [[0 for _ in range(N)] for _ in range(N)] 
                graphical_board = [[ [None, None] for _ in range(N)] for _ in range(N)]
                ai = AiTicTacToe() 
                to_move = -1
                game_finished = False
                winner_text = ""
                ai_thinking = False
                move_history = [] 
            elif to_move == -1 and not ai_thinking: 
                board, to_move, y, x, last_move = add_XO(board, graphical_board, to_move)
                if y is not None and x is not None:
                    # Phát âm thanh khi người chơi đánh
                    play_sound(SOUND_MOVE)
                    
                    ai.board[y][x] = -1
                    ai.currentI, ai.currentJ = y, x
                    ai.lastPlayed = -1
                    ai.emptyCells -= 1
                    ai.update_bound(y, x, ai.next_bound)
                    
                    move_history.append((y, x, -1))
                    
                    if ai.isFour(y, x, last_move):
                        winner_text = "PLAYER (X) WINS!"
                        game_finished = True
                    elif ai.emptyCells <= 0:
                        winner_text = "TIE GAME!"
                        game_finished = True

    pygame.display.update()
    clock.tick(60)