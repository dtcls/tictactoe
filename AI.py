import math
import sys
import random
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
# ── Zobrist hashing ────────────────────────────────────────────────────────────
def _build_zobrist() -> list:
    rng = random.Random(42)
    # table[i][j][piece_index]  piece_index: 0 → AI(1), 1 → Human(-1)
    return [
        [[rng.getrandbits(64), rng.getrandbits(64)] for _ in range(N)]
        for _ in range(N)
    ]
 
_ZOBRIST = _build_zobrist()

class AiTicTacToe():
    def __init__(self, depth = 3):
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
        # Transposition table: hash → (depth, score, flag)
        # flag: 'EXACT' | 'LOWER' | 'UPPER'
        self.trans_table: dict[int, tuple] = {}
        self._TT_MAX = 500_000
        # Zobrist
        self._zhash: int = 0                 
    #__Helper__

    # check wheter a move is inside board
    def isValid(self, i, j):
        if i < 0 or i >= N or j < 0 or j >= N:
            return False
        if self.board[i][j] != 0:
            return False
        else:
            return True
    
    def _place(self, i: int, j: int, state: int):
            self.board[i][j] = state
            self._zhash ^= _ZOBRIST[i][j][0 if state == 1 else 1]
            self.emptyCells -= 1
    
    
    def _unplace(self, i: int, j: int, state: int):
        self.board[i][j] = 0
        self._zhash ^= _ZOBRIST[i][j][0 if state == 1 else 1]
        self.emptyCells += 1
    
    # Update bound
    def update_bound(self, ni, nj, bound: set, radius = 3):
        bound.discard((ni, nj))
        for di in range(-radius, radius + 1):
            for dj in range(-radius, radius + 1):
                if di == 0 and dj == 0:
                    continue
                row, column = ni + di, nj + dj
                if self.isValid(row, column):
                    bound.add((row, column))
    
    # Check in line
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
    
    # Eval score in line
    @staticmethod
    def _eval_line(count, open_ends):
        return _EVAL_TABLE.get((count, open_ends), 0)
    
    # Increment Score
    def  eval_delta(self, i, j, state):
        s = 0
        for dirX, dirY in AXES:
            count, open_ends = self.line_correct(i, j, dirX, dirY, state)
            s += self._eval_line(count, open_ends)
        return s
    
    # Evaluate
    def evaluate(self):
        score = 0
        board = self.board
        for i in range(N):
            row = board[i]
            for j in range(N):
                cell = row[j]
                if cell == 0:
                    continue
                for dirX, dirY in AXES:
                    prev_r = i - dirY
                    prev_c = j - dirX
                    if 0 <= prev_r < N and 0 <= prev_c < N and board[prev_r][prev_c] == cell:
                        continue  
                    cnt, ends = self.line_correct(i, j, dirX, dirY, cell)
                    if cnt >= 2:
                        score += cell * _EVAL_TABLE.get((cnt, ends), 0)
        return score
    
    # Check win
    def isWin(self, i, j, state):
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
        if self.isWin(self.currentI, self.currentJ, self.lastPlayed) and self.lastPlayed in (-1, 1):
            if self.lastPlayed == -1:
                return 'Humman!'
            elif self.lastPlayed == 1:
                return 'AI!'
        elif self.emptyCells <= 0:
            return 'Tie'
        else:
            return None
        
    # Move ordering
    def scoreMove(self, i, j, depth):
        score = 0
        key = (i, j)
 
        # History heuristic
        score += self.history_table.get(key, 0)
 
        # Killer heuristic
        if depth < len(self.killer_moves) and key in self.killer_moves[depth]:
            score += 800

        for state in (1, -1):
            self.board[i][j] = state
            s = self.eval_delta(i, j, state)
            score += s if state == 1 else (s * 1.5)
            self.board[i][j] = 0
        return score
    
    # Ordering
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

    def alpha_beta_pruning(self, depth, bound, alpha, beta, isMaximizing):
        if self.lastPlayed != 0 and self.isWin(self.currentI, self.currentJ, self.lastPlayed) :
            if self.lastPlayed == 1:
                return SCORES['FOUR'] + depth * 200
            if self.lastPlayed == -1:
                return - SCORES['FOUR'] - depth * 200
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
        
    # tranposition
    def alpha_beta_transposition(self, depth, bound, alpha, beta, isMaximizing):
 
        if self.lastPlayed != 0 and self.currentI != -1:
            if self.isWin(self.currentI, self.currentJ, self.lastPlayed):
                if self.lastPlayed == 1:
                    return SCORES["FOUR"] + depth * 200
                else:
                    return -SCORES["FOUR"] - depth * 200
 
        if self.emptyCells <= 0:
            return 0
 
        hash = self._zhash
        tran_table = self.trans_table.get(hash)
        if tran_table and tran_table[0] >= depth:
            tt_depth, tt_score, tt_flag = tran_table
            if tt_flag == 'EXACT':
                return tt_score
            if tt_flag == 'LOWER':
                alpha = max(alpha, tt_score)
            elif tt_flag == 'UPPER':
                beta = min(beta, tt_score)
            if alpha >= beta:
                return tt_score
 
        if depth == 0:
            return self.evaluate()
 
        moves = self.orderedMoves(bound, depth)
        best = -math.inf if isMaximizing else math.inf
        flag = 'UPPER'
 
        for i, j in moves:
            state = 1 if isMaximizing else -1
            saved = (self.currentI, self.currentJ, self.lastPlayed)
 
            self._place(i, j, state)
            self.currentI, self.currentJ, self.lastPlayed = i, j, state
 
            new_bound = bound - {(i, j)}
            self.update_bound(i, j, new_bound)
 
            val = self.alpha_beta_transposition(depth - 1, new_bound, alpha, beta, not isMaximizing)
 
            self._unplace(i, j, state)
            self.currentI, self.currentJ, self.lastPlayed = saved
 
            if isMaximizing:
                if val > best:
                    best = val
                if val > alpha:
                    alpha = val
                    flag = 'EXACT'
                    key = (i, j)
                    self.history_table[key] = self.history_table.get(key, 0) + depth * depth
                if alpha >= beta:
                    key = (i, j)
                    if key not in self.killer_moves[depth]:
                        self.killer_moves[depth].insert(0, key)
                        if len(self.killer_moves[depth]) > 2:
                            self.killer_moves[depth].pop()
                    flag = 'LOWER'
                    break
            else:
                if val < best:
                    best = val
                if val < beta:
                    beta = val
                    flag = 'EXACT'
                if beta <= alpha:
                    key = (i, j)
                    if key not in self.killer_moves[depth]:
                        self.killer_moves[depth].insert(0, key)
                        if len(self.killer_moves[depth]) > 2:
                            self.killer_moves[depth].pop()
                    flag = 'LOWER'
                    break
 
        if len(self.trans_table) >= self._TT_MAX:
            self.trans_table.clear()
        self.trans_table[hash] = (depth, best, flag)
 
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
    def best_move_transposition(self):
        if self.emptyCells == N * N:
            return (N // 2, N // 2)
        self.history_table.clear()
        self.trans_table.clear()

        bound = set(self.next_bound)
        move = (-1, -1)

        for d in range(1, self.depth + 1):
            best_score = -math.inf
            best_move =(-1, -1)
            moves = self.orderedMoves(bound, d)
            for i, j in moves:
                saved = (self.currentI, self.currentJ, self.lastPlayed)
                self._place(i , j, 1)
                self.currentI, self.currentJ, self.lastPlayed = i, j ,1
                new_bound = bound - {(i, j)}
                self.update_bound(i, j, new_bound)
                score = self.alpha_beta_transposition(d- 1, new_bound, -math.inf, math.inf, False)
                self._unplace(i, j, 1)
                self.currentI, self.currentJ, self.lastPlayed = saved
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
                if best_score >= SCORES['FOUR']:
                    return best_move
            if best_move != (-1, -1):
                move = best_move
        return move
