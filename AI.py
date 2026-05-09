import math
import sys

N = 9

class AiTicTacToe():
    def __init__(self, depth = 5):
        self.depth = depth
        self.board = [[0 for j in range(N)] for i in range(N)]
        self.nextBound = {}
        self.patternDict = {}
        self.currentI = -1
        self.currentJ = -1
        self.lastPlayed = 0
        self.emptyCells = N * N
        self.board_value = 0
    # check wheter a move is inside board
    def isValid(self, i, j, statue = True):
        if i < 0 or i >= N or j < 0 or j >= N:
            return False
        if self.board[i][j] != 0:
            return False
        else:
            return True
    def updateBound(self, new_i, new_j, bound):
        played = (new_i, new_j)
        if played in bound:
            bound.pop(played)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1), (-1, -1), (1, 1)]
        for dir in directions:
            new_col = new_j + dir[0]
            new_row = new_i + dir[1]
            if self.isValid(new_row, new_col) and (new_row, new_col) not in bound:
                bound[new_row, new_col] = 0
    def countDirection(self ,i, j, xdir, ydir, state, board):
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
    def isFour(self, i, j, state):
        # 4 directions: horizontal, vertical, 2 diagonals
        directions = [[(-1, 0), (1, 0)], \
                        [(0, -1), (0, 1)], \
                        [(-1, 1), (1, -1)], \
                        [(-1, -1), (1, 1)]]
        for axis in directions:
            axis_count = 1
            for (xdir, ydir) in axis:
                axis_count += self.countDirection(i, j, xdir, ydir, state, self.board)
                if axis_count >= 4:
                    return True
        return False

    def results(self):
        if self.isFour(self.currentI, self.currentJ, self.lastPlayed) and self.lastPlayed in (-1, 1):
            if self.lastPlayed == -1:
                return 'Humman!'
            elif self.lastPlayed == 1:
                return 'AI!'
        elif self.emptyCells <= 0:
            return 'Tie'
        else:
            return None
    def childNodes(self, bound):
        for pos in sorted(bound.items(), key=lambda el: el[1], reverse=True):
            yield pos[0]
    def alpha_beta_pruning(self, depth, bound, alpha, beta, isMaximizing):
        # 1. Kiểm tra kết quả (Thắng/Thua/Hòa)
        res = self.results()
        if res == 'AI!': return 1000 + depth
        if res == 'Humman!': return -1000 - depth
        if res == 'Tie' or depth <= 0: return 0

        if isMaximizing:
            maxEval = -math.inf
            # Duyệt qua từng tọa độ (i, j)
            for i, j in self.childNodes(bound):
                # --- BƯỚC THỬ ---
                self.board[i][j] = 1 # AI đặt thử quân O
                self.emptyCells -= 1
                # Lưu lại trạng thái cũ để backtrack
                old_i, old_j, old_last = self.currentI, self.currentJ, self.lastPlayed
                self.currentI, self.currentJ, self.lastPlayed = i, j, 1
                
                # Tạo vùng biên mới cho nước đi tiếp theo
                new_bound = dict(bound)
                self.updateBound(i, j, new_bound)
                
                # --- ĐỆ QUY ---
                eval = self.alpha_beta_pruning(depth - 1, new_bound, alpha, beta, False)
                
                # --- BƯỚC HOÀN TÁC (Backtrack) ---
                self.board[i][j] = 0
                self.emptyCells += 1
                self.currentI, self.currentJ, self.lastPlayed = old_i, old_j, old_last
                
                maxEval = max(maxEval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha: break
            return maxEval
        else:
            minEval = math.inf
            for i, j in self.childNodes(bound):
                # --- BƯỚC THỬ ---
                self.board[i][j] = -1 # Người chơi đặt thử quân X
                self.emptyCells -= 1
                old_i, old_j, old_last = self.currentI, self.currentJ, self.lastPlayed
                self.currentI, self.currentJ, self.lastPlayed = i, j, -1
                
                new_bound = dict(bound)
                self.updateBound(i, j, new_bound)
                
                # --- ĐỆ QUY ---
                eval = self.alpha_beta_pruning(depth - 1, new_bound, alpha, beta, True)
                
                # --- BƯỚC HOÀN TÁC ---
                self.board[i][j] = 0
                self.emptyCells += 1
                self.currentI, self.currentJ, self.lastPlayed = old_i, old_j, old_last
                
                minEval = min(minEval, eval) # Đã sửa từ maxEval thành minEval
                beta = min(beta, eval)
                if beta <= alpha: break
            return minEval
    def best_move(self):
        best_score = -math.inf
        move = (-1, -1)
        current_bound = dict(self.nextBound)
        
        for i, j in self.childNodes(current_bound):
            self.board[i][j] = 1 
            self.emptyCells -= 1
            old_i, old_j = self.currentI, self.currentJ
            self.currentI, self.currentJ = i, j
            self.lastPlayed = 1
            
            new_bound = dict(current_bound)
            self.updateBound(i, j, new_bound)
            
            score = self.alpha_beta_pruning(self.depth - 1, new_bound, -math.inf, math.inf, False)
            
            self.board[i][j] = 0
            self.emptyCells += 1
            self.currentI, self.currentJ = old_i, old_j
            
            if score > best_score:
                best_score = score
                move = (i, j)
        
        return move