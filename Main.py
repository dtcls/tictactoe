import pygame, sys
import threading 
from AI import AiTicTacToe

# --- IMPORT THÊM THƯ VIỆN CHO VIDEO VÀ GIF ---
import cv2
import numpy as np
from PIL import Image, ImageSequence

pygame.init()
pygame.mixer.init()

# 1. KÍCH THƯỚC MÀN HÌNH VÀ BẢNG CỜ
WIDTH, HEIGHT = 1280, 720
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Caro Board - Mang tinh yeu den cho moi nha")

N = 9
CELL_SIZE = 60
BOARD_SIZE = CELL_SIZE * N
BOARD_X = 550
BOARD_Y = 100

# --- TẢI ẢNH NỀN ---
try:
    BG_IMG = pygame.image.load("assets/vintage_theme.jpg.jpeg")
    BG_IMG = pygame.transform.scale(BG_IMG, (WIDTH, HEIGHT))
except Exception as e:
    print(f"Lỗi tải ảnh nền: {e}")
    BG_IMG = pygame.Surface((WIDTH, HEIGHT))
    BG_IMG.fill((220, 205, 175)) 

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
    SOUND_MOVE = pygame.mixer.Sound("assets/move2.wav")   
    SOUND_CLICK = pygame.mixer.Sound("assets/click.wav") 
    SOUND_UNDO = pygame.mixer.Sound("assets/undo.wav")   
    pygame.mixer.music.load("assets/bgm.wav") 
    pygame.mixer.music.set_volume(0.2) 
    pygame.mixer.music.play(-1) 
except Exception as e:
    print(f"Lỗi tải âm thanh: {e}")
    SOUND_MOVE = None; SOUND_CLICK = None; SOUND_UNDO = None

def play_sound(sound):
    if sound: sound.play()


# MOVE CLASSES - HumanMove và AiMove
class HumanMove:
    
    def __init__(self, player_value):

        self.player_value = player_value
    
    def get_move(self, board, mouse_pos):
        """
        Trả về (row, col) nếu click hợp lệ, ngược lại trả về (None, None).
        """
        if (BOARD_X <= mouse_pos[0] <= BOARD_X + BOARD_SIZE and
                BOARD_Y <= mouse_pos[1] <= BOARD_Y + BOARD_SIZE):
            col = int((mouse_pos[0] - BOARD_X) / CELL_SIZE)
            row = int((mouse_pos[1] - BOARD_Y) / CELL_SIZE)
            if 0 <= col < N and 0 <= row < N:
                if board[row][col] == 0:
                    return row, col
        return None, None
    
    def apply_move(self, board, ai_obj, row, col, move_history):
        """Áp dụng nước đi lên board và cập nhật trạng thái AI."""
        board[row][col] = self.player_value
        ai_obj.board[row][col] = self.player_value
        ai_obj.currentI, ai_obj.currentJ = row, col
        ai_obj.lastPlayed = self.player_value
        ai_obj.emptyCells -= 1
        ai_obj.update_bound(row, col, ai_obj.next_bound)
        move_history.append((row, col, self.player_value))
        return board


class AiMove:
    
    def __init__(self, player_value=1):

        self.player_value = player_value
    
    def get_move(self, ai_obj):

        return ai_obj.best_move_transposition()
    
    def apply_move(self, board, ai_obj, row, col, move_history):
        """Áp dụng nước đi AI lên board."""
        board[row][col] = self.player_value
        ai_obj.board[row][col] = self.player_value
        ai_obj.currentI, ai_obj.currentJ = row, col
        ai_obj.lastPlayed = self.player_value
        ai_obj.emptyCells -= 1
        ai_obj.update_bound(row, col, ai_obj.next_bound)
        move_history.append((row, col, self.player_value))
        return board



# TRẠNG THÁI GAME
board = [[0 for _ in range(N)] for _ in range(N)]
graphical_board = [[ [None, None] for _ in range(N)] for _ in range(N)]
to_move = -1  # -1 = lượt X, 1 = lượt O

classic_font = "Courier New" 
FONT = pygame.font.SysFont(classic_font, 42, bold=True)
FONT_SMALL = pygame.font.SysFont(classic_font, 20, bold=True)
FONT_MED = pygame.font.SysFont(classic_font, 24, bold=True) 
FONT_LARGE = pygame.font.SysFont(classic_font, 36, bold=True)

ai_thinking = False 
game_finished = False
current_difficulty = "Medium"
move_history = []


# Các chế độ: "HvA" (Human vs AI), "HvH" (Human vs Human)

game_mode = "HvA"  # Mặc định: Human (X) vs AI (O)

# Khởi tạo move handlers cho từng bên theo chế độ
def create_move_handlers(mode):
    """Tạo move handler cho X và O dựa trên game_mode."""
    if mode == "HvH":
        return HumanMove(-1), HumanMove(1)   # X=Human, O=Human
    else:  # HvA (mặc định)
        return HumanMove(-1), AiMove(1)      # X=Human, O=AI

move_x_handler, move_o_handler = create_move_handlers(game_mode)

btn_easy_rect = None
btn_med_rect = None
btn_hard_rect = None
btn_undo_rect = None
btn_hvA_rect = None
btn_hvH_rect = None


def display_winner(text):
    render_text = FONT.render(text, True, (255, 215, 0)) 
    text_rect = render_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    overlay = pygame.Surface((WIDTH, 150))
    overlay.set_alpha(180) 
    overlay.fill((0, 0, 0))
    SCREEN.blit(overlay, (0, HEIGHT // 2 - 75))
    SCREEN.blit(render_text, text_rect)


# =========================================================================
# HÀM PHÁT VIDEO INTRO
# =========================================================================
def play_intro_video():
    video_path = "assets/trailer.mp4"
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Không tìm thấy video intro, bỏ qua...")
        return

    clock = pygame.time.Clock()
    intro_font = pygame.font.SysFont(classic_font, 40, bold=True)
    text_surface = intro_font.render("Click anywhere to continue", True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))

    running_intro = True
    while running_intro:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                running_intro = False
                play_sound(SOUND_CLICK)

        frame = cv2.resize(frame, (WIDTH, HEIGHT))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_surface = pygame.image.frombuffer(frame.tobytes(), (WIDTH, HEIGHT), "RGB")
        SCREEN.blit(frame_surface, (0, 0))
        
        if (pygame.time.get_ticks() // 600) % 2 == 0:
            bg_text = intro_font.render("Click anywhere to continue", True, (0, 0, 0))
            SCREEN.blit(bg_text, (text_rect.x + 2, text_rect.y + 2))
            SCREEN.blit(text_surface, text_rect)

        pygame.display.flip()
        clock.tick(30)
    cap.release()


# =========================================================================
# HÀM PHÁT LOADING GIF
# =========================================================================
def play_loading_animation():
    gif_path = "assets/loading.gif"
    frames = []
    try:
        pil_gif = Image.open(gif_path)
        for frame in ImageSequence.Iterator(pil_gif):
            frame_rgba = frame.convert("RGBA")
            size = frame_rgba.size
            data = np.array(frame_rgba)
            red, green, blue, alpha = data.T
            white_areas = (red > 240) & (green > 240) & (blue > 240)
            data[..., 3][white_areas.T] = 0
            py_image = pygame.image.frombuffer(data.tobytes(), size, "RGBA")
            py_image = pygame.transform.scale(py_image, (250, int(250 * size[1]/size[0]))) 
            frames.append(py_image)
    except Exception as e:
        print(f"Không thể load GIF: {e}, bỏ qua loading...")
        return

    clock = pygame.time.Clock()
    loading_duration = 3000
    start_time = pygame.time.get_ticks()
    frame_idx = 0
    loading_font = pygame.font.SysFont(classic_font, 35, bold=True)

    while pygame.time.get_ticks() - start_time < loading_duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

        SCREEN.fill((15, 12, 10)) 
        current_frame = frames[frame_idx]
        gif_rect = current_frame.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
        SCREEN.blit(current_frame, gif_rect)
        
        dots = "." * ((pygame.time.get_ticks() // 400) % 4)
        text_surface = loading_font.render(f"Loading Game{dots}", True, (220, 205, 175))
        text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 210))
        SCREEN.blit(text_surface, text_rect)

        pygame.display.flip()
        frame_idx = (frame_idx + 1) % len(frames)
        clock.tick(15)


# =========================================================================
# VẼ UI (có thêm phần chọn Game Mode)
# =========================================================================
def get_player_labels(mode):
    """Trả về (label_x, sublabel_x, label_o, sublabel_o) theo game mode."""
    if mode == "HvH":
        return "Player 1", "Human (X)", "Player 2", "Human (O)"
    else:  # HvA
        return "Player 1", "Human (X)", "BOT", "AI (O)"


def draw_background_and_ui(surface):
    global to_move, ai_thinking, game_finished
    global btn_easy_rect, btn_med_rect, btn_hard_rect, btn_undo_rect, current_difficulty
    global btn_hvA_rect, btn_hvH_rect, game_mode
    
    surface.blit(BG_IMG, (0, 0))
    
    ink_color = (80, 55, 40)
    parchment_color = (230, 212, 175)
    box_bg_color = (240, 220, 190)       
    highlight_bg_color = (255, 255, 235) 
    highlight_border = 4                 
    normal_border = 2                    

    ui_x = 150
    ui_y = BOARD_Y      
    ui_width = 350
    ui_height = 540
    
    pygame.draw.rect(surface, parchment_color, (ui_x, ui_y, ui_width, ui_height))
    pygame.draw.rect(surface, ink_color, (ui_x, ui_y, ui_width, ui_height), 3)

    padding = 15
    box_w = ui_width - 2 * padding

    # --- Ô 1: GAME MODE ---
    box1_y = ui_y + padding
    box1_h = 80
    pygame.draw.rect(surface, box_bg_color, (ui_x + padding, box1_y, box_w, box1_h))
    pygame.draw.rect(surface, ink_color, (ui_x + padding, box1_y, box_w, box1_h), normal_border)
    surface.blit(FONT_SMALL.render("GAME MODE", True, (120, 100, 80)), (ui_x + padding + 15, box1_y + 8))

    mode_btn_w = (box_w - 30) // 2
    mode_btn_h = 32
    mode_btn_start_x = ui_x + padding + 10
    mode_btn_y = box1_y + 36
    modes = [("HvA", "PVE"), ("HvH", "PVP")]
    mode_rects = []

    for i, (mode_key, mode_label) in enumerate(modes):
        rect = pygame.Rect(mode_btn_start_x + i * (mode_btn_w + 10), mode_btn_y, mode_btn_w, mode_btn_h)
        mode_rects.append(rect)
        if game_mode == mode_key:
            pygame.draw.rect(surface, ink_color, rect)
            txt_col = (255, 255, 255)
        else:
            pygame.draw.rect(surface, ink_color, rect, 2)
            txt_col = ink_color
        lbl = FONT_SMALL.render(mode_label, True, txt_col)
        surface.blit(lbl, (rect.x + (mode_btn_w - lbl.get_width()) // 2,
                           rect.y + (mode_btn_h - lbl.get_height()) // 2))
    btn_hvA_rect, btn_hvH_rect = mode_rects[0], mode_rects[1]

    # --- Ô 2: PLAYER X ---
    label_x, sub_x, label_o, sub_o = get_player_labels(game_mode)
    box2_y = box1_y + box1_h + padding
    box2_h = 85
    is_x_turn = (not game_finished and to_move == -1)
    bg2 = highlight_bg_color if is_x_turn else box_bg_color
    border2 = highlight_border if is_x_turn else normal_border
    pygame.draw.rect(surface, bg2, (ui_x + padding, box2_y, box_w, box2_h))
    pygame.draw.rect(surface, ink_color, (ui_x + padding, box2_y, box_w, box2_h), border2)
    surface.blit(FONT_SMALL.render(label_x, True, (120, 100, 80)), (ui_x + padding + 15, box2_y + 10))
    surface.blit(FONT_MED.render(sub_x, True, (20, 100, 20)), (ui_x + padding + 15, box2_y + 40))
    if X_IMG:
        surface.blit(X_IMG, (ui_x + padding + box_w - 60, box2_y + 22))

    # --- Ô 3: PLAYER O ---
    box3_y = box2_y + box2_h + padding
    box3_h = 85
    is_o_turn = (not game_finished and to_move == 1)
    bg3 = highlight_bg_color if is_o_turn else box_bg_color
    border3 = highlight_border if is_o_turn else normal_border
    pygame.draw.rect(surface, bg3, (ui_x + padding, box3_y, box_w, box3_h))
    pygame.draw.rect(surface, ink_color, (ui_x + padding, box3_y, box_w, box3_h), border3)
    surface.blit(FONT_SMALL.render(label_o, True, (120, 100, 80)), (ui_x + padding + 15, box3_y + 10))
    surface.blit(FONT_MED.render(sub_o, True, (180, 40, 40)), (ui_x + padding + 15, box3_y + 40))
    if O_IMG:
        surface.blit(O_IMG, (ui_x + padding + box_w - 60, box3_y + 22))

    # --- Ô 4: DIFFICULTY ---
    box4_y = box3_y + box3_h + padding
    box4_h = 80
    pygame.draw.rect(surface, box_bg_color, (ui_x + padding, box4_y, box_w, box4_h))
    pygame.draw.rect(surface, ink_color, (ui_x + padding, box4_y, box_w, box4_h), normal_border)
    surface.blit(FONT_SMALL.render("DIFFICULTY", True, (120, 100, 80)), (ui_x + padding + 15, box4_y + 8))
    
    btn_w = (box_w - 40) // 3 
    btn_h = 32
    btn_start_x = ui_x + padding + 10
    btn_y = box4_y + 38

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
        render_txt = FONT_SMALL.render(diff, True, text_color)
        surface.blit(render_txt, (rect.x + (btn_w - render_txt.get_width()) // 2,
                                  rect.y + (btn_h - render_txt.get_height()) // 2))
    btn_easy_rect, btn_med_rect, btn_hard_rect = rects[0], rects[1], rects[2]

    # --- Ô 5: TRẠNG THÁI ---
    box5_y = box4_y + box4_h + padding
    box5_h = 60
    pygame.draw.rect(surface, box_bg_color, (ui_x + padding, box5_y, box_w, box5_h))
    pygame.draw.rect(surface, ink_color, (ui_x + padding, box5_y, box_w, box5_h), normal_border)

    status_color = ink_color
    if game_finished:
        status_text = "Game Over! Click board"
    elif ai_thinking:
        status_text = "AI is thinking..."
        status_color = (180, 40, 40)
    elif to_move == -1:
        status_text = "X's Turn"
        status_color = (20, 100, 20)
    else:
        status_text = "O's Turn"
        status_color = (180, 40, 40)

    render_status = FONT_MED.render(status_text, True, status_color)
    surface.blit(render_status, (ui_x + padding + (box_w - render_status.get_width()) // 2,
                                  box5_y + (box5_h - render_status.get_height()) // 2))

    # --- Ô 6: UNDO ---
    box6_y = box5_y + box5_h + padding
    box6_h = 45
    btn_undo_rect = pygame.Rect(ui_x + padding, box6_y, box_w, box6_h)
    can_undo = not ai_thinking and len(move_history) >= 2
    undo_bg = box_bg_color if can_undo else (220, 210, 190)
    undo_txt_color = ink_color if can_undo else (150, 140, 130)
    pygame.draw.rect(surface, undo_bg, btn_undo_rect)
    pygame.draw.rect(surface, ink_color, btn_undo_rect, normal_border)
    undo_txt = FONT_MED.render("Undo", True, undo_txt_color)
    surface.blit(undo_txt, (btn_undo_rect.x + (box_w - undo_txt.get_width()) // 2,
                             btn_undo_rect.y + (box6_h - undo_txt.get_height()) // 2))

    # Vẽ bảng caro
    for i in range(N + 1):
        pygame.draw.line(surface, ink_color, 
                         (BOARD_X + i * CELL_SIZE, BOARD_Y), 
                         (BOARD_X + i * CELL_SIZE, BOARD_Y + BOARD_SIZE), 2)
        pygame.draw.line(surface, ink_color, 
                         (BOARD_X, BOARD_Y + i * CELL_SIZE), 
                         (BOARD_X + BOARD_SIZE, BOARD_Y + i * CELL_SIZE), 2)
        
    pygame.draw.rect(surface, ink_color, (BOARD_X, BOARD_Y, BOARD_SIZE, BOARD_SIZE), 5)


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


def reset_game():
    """Reset toàn bộ trạng thái game."""
    global board, graphical_board, ai, to_move, game_finished, winner_text, ai_thinking
    global move_history, move_x_handler, move_o_handler
    board = [[0 for _ in range(N)] for _ in range(N)]
    graphical_board = [[ [None, None] for _ in range(N)] for _ in range(N)]
    ai = AiTicTacToe()
    to_move = -1
    game_finished = False
    winner_text = ""
    ai_thinking = False
    move_history = []
    move_x_handler, move_o_handler = create_move_handlers(game_mode)


def get_current_handler():
    """Trả về handler của bên đang có lượt đi."""
    return move_x_handler if to_move == -1 else move_o_handler


def ai_task(handler: AiMove):
    global ai_thinking, to_move, game_finished, winner_text, current_difficulty, move_history, board

    if SOUND_MOVE:
        # get_length() trả về thời gian file âm thanh (giây). Nhân 1000 để đổi ra mili giây.
        delay_ms = int(SOUND_MOVE.get_length() * 1000)
        pygame.time.wait(delay_ms)

    if current_difficulty == "Easy":   ai.depth = 3
    elif current_difficulty == "Medium": ai.depth = 4
    elif current_difficulty == "Hard":   ai.depth = 5

    move_y, move_x = handler.get_move(ai)

    if move_y != -1 and not game_finished:
        handler.apply_move(board, ai, move_y, move_x, move_history)
        play_sound(SOUND_MOVE)
        render_board(board, X_IMG, O_IMG)

        if ai.isWin(move_y, move_x, handler.player_value):
            winner_text = f"{'X' if handler.player_value == -1 else 'O'} WINS!"
            game_finished = True
        elif ai.emptyCells <= 0:
            winner_text = "TIE GAME!"
            game_finished = True

    to_move = 1 if to_move == -1 else -1
    ai_thinking = False


# =========================================================================
# GỌI HÀM INTRO VÀ LOADING TRƯỚC KHI VÀO GAME
# =========================================================================
# (Nhạc nền đã bắt đầu phát từ trên cùng file nên nó sẽ kêu suốt lúc intro)
play_intro_video()
play_loading_animation()

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

    # --- XỬ LÝ LƯỢT ĐI TỰ ĐỘNG (AI) ---
    if not game_finished and not ai_thinking:
        current_handler = get_current_handler()
        if isinstance(current_handler, AiMove):
            ai_thinking = True
            ai_thread = threading.Thread(target=ai_task, args=(current_handler,))
            ai_thread.daemon = True
            ai_thread.start()

    # --- XỬ LÝ SỰ KIỆN ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos

            # --- UNDO ---
            if btn_undo_rect and btn_undo_rect.collidepoint(mouse_pos):
                if not ai_thinking and len(move_history) >= 2:
                    play_sound(SOUND_UNDO)
                    # Xóa nước đi gần nhất của 2 bên
                    while len(move_history) > 0 and move_history[-1][2] == (1 if to_move == -1 else -1):
                        move_history.pop()
                    if len(move_history) > 0:
                        move_history.pop()
                    # Tái tạo board từ history
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
                    # Xác định đến lượt ai tiếp theo
                    if move_history:
                        last_player = move_history[-1][2]
                        to_move = 1 if last_player == -1 else -1
                    render_board(board, X_IMG, O_IMG)
                continue

            # --- CHỌN GAME MODE ---
            if not game_finished and not ai_thinking:
                mode_changed = False
                if btn_hvA_rect and btn_hvA_rect.collidepoint(mouse_pos) and game_mode != "HvA":
                    game_mode = "HvA"; mode_changed = True
                elif btn_hvH_rect and btn_hvH_rect.collidepoint(mouse_pos) and game_mode != "HvH":
                    game_mode = "HvH"; mode_changed = True
                if mode_changed:
                    play_sound(SOUND_CLICK)
                    reset_game()
                    continue

                # --- CHỌN ĐỘ KHÓ ---
                if btn_easy_rect and btn_easy_rect.collidepoint(mouse_pos):
                    if current_difficulty != "Easy": play_sound(SOUND_CLICK)
                    current_difficulty = "Easy"; continue
                elif btn_med_rect and btn_med_rect.collidepoint(mouse_pos):
                    if current_difficulty != "Medium": play_sound(SOUND_CLICK)
                    current_difficulty = "Medium"; continue
                elif btn_hard_rect and btn_hard_rect.collidepoint(mouse_pos):
                    if current_difficulty != "Hard": play_sound(SOUND_CLICK)
                    current_difficulty = "Hard"; continue

            # --- CLICK LÊN BÀN CỜ: reset nếu game đã kết thúc ---
            if game_finished:
                if (BOARD_X <= mouse_pos[0] <= BOARD_X + BOARD_SIZE and
                        BOARD_Y <= mouse_pos[1] <= BOARD_Y + BOARD_SIZE):
                    reset_game()
                continue

            # --- HUMAN MOVE: xử lý khi handler hiện tại là HumanMove ---
            if not ai_thinking:
                current_handler = get_current_handler()
                if isinstance(current_handler, HumanMove):
                    row, col = current_handler.get_move(board, mouse_pos)
                    if row is not None:
                        current_handler.apply_move(board, ai, row, col, move_history)
                        play_sound(SOUND_MOVE)
                        render_board(board, X_IMG, O_IMG)

                        if ai.isWin(row, col, current_handler.player_value):
                            winner_text = f"{'X' if current_handler.player_value == -1 else 'O'} WINS!"
                            game_finished = True
                        elif ai.emptyCells <= 0:
                            winner_text = "TIE GAME!"
                            game_finished = True
                        else:
                            to_move = 1 if to_move == -1 else -1

    pygame.display.update()
    clock.tick(60)