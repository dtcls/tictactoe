import math
import sys

N = 9
SCORES = {
    "FOUR": 1_000_000,
    "OPEN_THREE": 100_000,
    "BLOCK_THREE": 10_000,
    "OPEN_TWO": 1_000,
    "BLOCK_TWO": 100,
    "OPEN_ONE": 10, 
    "BLOCK_ONE": 1  
}
_EVAL_TABLE = {} 
for _c in range(1, 6):
    for _e in range(0, 3):
        if _c >= 4:
            _EVAL_TABLE[(_c, _e)] = SCORES["FOUR"]
        elif _c == 3:
            _EVAL_TABLE[(_c, _e)] = SCORES["OPEN_THREE"] if _e >= 2 else SCORES["BLOCK_THREE"]
        elif _c == 2:
            _EVAL_TABLE[(_c, _e)] = SCORES["OPEN_TWO"] if _e >= 2 else SCORES["BLOCK_TWO"]
        elif _c == 1:
            _EVAL_TABLE[(_c, _e)] = SCORES["OPEN_ONE"] if _e >= 2 else SCORES["BLOCK_ONE"]
        else:
            _EVAL_TABLE[(_c, _e)] = 0
AXES = [(1, 0), (0, 1), (1, 1), (1, -1)]
class AiTicTacToe():
    def __init__(self, depth = 5):
        self.depth = depth
        self.board = [[0 for j in range(N)] for i in range(N)]
        self.next_bound = set()
        self.patternDict = {}
        self.currentI = -1
        self.currentJ = -1
        self.lastPlayed = 0
        self.emptyCells = N * N
        self.killer_moves = [[] for _ in range(depth + 2)]   
        self.history_table = {}                            
    # check wheter a move is inside board
    def isValid(self, i, j):
        if i < 0 or i >= N or j < 0 or j >= N:
            return False
        if self.board[i][j] != 0:
            return False
        else:
            return True
    def update_bound(self, ni, nj, bound: set, radius = 3):
        bound.discard((ni, nj))
        for di in range(-radius, radius + 1):
            for dj in range(-radius, radius + 1):
                if di == 0 and dj == 0:
                    continue
                row, column = ni + di, nj + dj
                if self.isValid(row, column):
                    bound.add((row, column))
    def line_correct(self, i, j, dirX, dirY, state):
        count = 1
        open_ends = 0
        # forward
        row, col = i + dirY, j + dirX
        while 0 <= row < N and 0 <= col < N and self.board[row][col] == state:
            count += 1
            row += dirY
            col += dirX
        if 0 <= row < N and 0 <= col < N and self.board[row][col] == 0:
            open_ends += 1
        # behind
        row, col = i - dirY, j - dirX
        while 0 <= row < N and 0 <= col < N and self.board[row][col] == state:
            count += 1
            row -= dirY
            col -= dirX
        if 0 <= row < N and 0 <= col < N and self.board[row][col] == 0:
            open_ends += 1
        return count, open_ends
    @staticmethod
    def _eval_line(count, open_ends):
        return _EVAL_TABLE.get((count, open_ends), 0)
 
    def evaluate(self):
        score = 0
        for i in range(N):
            row = self.board[i]
            for j in range(N):
                cell = row[j]
                if cell == 0:
                    continue
                for dirX, dirY in AXES:
                    prev_r = i - dirY
                    prev_c = j - dirX
                    if 0 <= prev_r < N and 0 <= prev_c < N and self.board[prev_r][prev_c] == cell:
                        continue  
                    cnt, ends = self.line_correct(i, j, dirX, dirY, cell)
                    if cnt >= 2:
                        score += cell * _EVAL_TABLE.get((cnt, ends), 0)
        return score
    def scoreMove(self, i, j, depth):
        score = 0
        key = (i, j)
 
        # History heuristic
        score += self.history_table.get(key, 0)
 
        # Killer heuristic
        if depth < len(self.killer_moves) and key in self.killer_moves[depth]:
            score += 500

        axes = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for state in (1, -1):
            self.board[i][j] = state
            for dx, dy in axes:
                cnt, ends = self.line_correct(i, j, dx, dy, state)
                s = self._eval_line(cnt, ends)
                score += s if state == 1 else int(s * 1.2)
            self.board[i][j] = 0
 
        return score
    def orderedMoves(self, bound, depth):
        moves = sorted(
            bound,
            key=lambda pos: self.scoreMove(pos[0], pos[1], depth),
            reverse=True,
        )
        return moves
 
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
    def alpha_beta_pruning(self, depth, bound, alpha, beta, isMaximizing):
        if self.lastPlayed != 0 and self.isFour(self.currentI, self.currentJ, self.lastPlayed) :
            if self.lastPlayed == 1:
                return SCORES['FOUR'] + depth * 100
            if self.lastPlayed == -1:
                return - SCORES['FOUR'] - depth * 100
        if self.emptyCells <= 0:
            return 0
        if depth == 0:
            return self.evaluate()
        moves = self.orderedMoves(bound, depth)

        if isMaximizing:
            best = -math.inf
            for i, j in moves:
                self.board[i][j] = 1
                self.emptyCells -= 1
                old = (self.currentI, self.currentJ, self.lastPlayed)
                self.currentI, self.currentJ, self.lastPlayed = i, j, 1
 
                new_bound = bound - {(i, j)}
                self.update_bound(i, j, new_bound)
 
                val = self.alpha_beta_pruning(depth - 1, new_bound, alpha, beta, False)
 
                self.board[i][j] = 0
                self.emptyCells += 1
                self.currentI, self.currentJ, self.lastPlayed = old
 
                if val > best:
                    best = val
                if val > alpha:
                    alpha = val
                    key = (i, j)
                    self.history_table[key] = self.history_table.get(key, 0) + depth ** 2
                if beta <= alpha:
                    # Killer heuristic: lưu nước gây cutoff
                    key = (i, j)
                    if key not in self.killer_moves[depth]:
                        self.killer_moves[depth].insert(0, key)
                        if len(self.killer_moves[depth]) > 2:
                            self.killer_moves[depth].pop()
                    break
            return best
 
        else:
            best = math.inf
            for i, j in moves:
                self.board[i][j] = -1
                self.emptyCells -= 1
                old = (self.currentI, self.currentJ, self.lastPlayed)
                self.currentI, self.currentJ, self.lastPlayed = i, j, -1
 
                new_bound = bound - {(i, j)}
                self.update_bound(i, j, new_bound)
 
                val = self.alpha_beta_pruning(depth - 1, new_bound, alpha, beta, True)
 
                self.board[i][j] = 0
                self.emptyCells += 1
                self.currentI, self.currentJ, self.lastPlayed = old
 
                if val < best:
                    best = val
                if val < beta:
                    beta = val
                if beta <= alpha:
                    key = (i, j)
                    if key not in self.killer_moves[depth]:
                        self.killer_moves[depth].insert(0, key)
                        if len(self.killer_moves[depth]) > 2:
                            self.killer_moves[depth].pop()
                    break
            return best
    def best_move(self):
        if self.emptyCells == N * N:
            return (N // 2, N // 2)
        self.history_table.clear()
        best_score = -math.inf
        move = (-1, -1)
        bound = set(self.next_bound)
        moves = self.orderedMoves(bound, self.depth)
 
        for i, j in moves:
            self.board[i][j] = 1
            self.emptyCells -= 1
            old = (self.currentI, self.currentJ, self.lastPlayed)
            self.currentI, self.currentJ, self.lastPlayed = i, j, 1
 
            new_bound = bound - {(i, j)}
            self.update_bound(i, j, new_bound)
 
            score = self.alpha_beta_pruning(self.depth - 1, new_bound, -math.inf, math.inf, False)
 
            self.board[i][j] = 0
            self.emptyCells += 1
            self.currentI, self.currentJ, self.lastPlayed = old
 
            if score > best_score:
                best_score = score
                move = (i, j)
 
            if best_score >= SCORES["FOUR"]:
                break
 
        return move