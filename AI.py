import math
import random
from typing import List, Set, Tuple, Optional

N = 9
Move = Tuple[int, int]

SCORES = {
    "FOUR": 1_000_000,
    "OPEN_THREE": 220_000,
    "BLOCK_THREE": 55_000,
    "OPEN_TWO": 4_500,
    "BLOCK_TWO": 500,
    "OPEN_ONE": 8,
    "BLOCK_ONE": 1,
    "DOUBLE_OPEN_THREE": 850_000,
    "OPEN_THREE_AND_OPEN_TWO": 420_000,
    "DOUBLE_OPEN_TWO": 95_000,
    "TWO_BLOCK_THREES": 120_000,
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

AXES = ((1, 0), (0, 1), (1, 1), (1, -1))

_NEIGHBORS = {
    r: tuple(
        (di, dj)
        for di in range(-r, r + 1)
        for dj in range(-r, r + 1)
        if not (di == 0 and dj == 0)
    )
    for r in (1, 2)
}


def _build_zobrist() -> List[List[List[int]]]:
    rng = random.Random(42)
    return [
        [[rng.getrandbits(64), rng.getrandbits(64)] for _ in range(N)]
        for _ in range(N)
    ]


_ZOBRIST = _build_zobrist()
_SIDE_HASH = 0x9E3779B97F4A7C15


class AiTicTacToe:
    """
    Board values:
        0  = empty
        1  = AI
       -1  = Human

    Main recommended method:
        best_move_transposition()

    Compatibility methods kept:
        best_move()   -> calls best_move_transposition()
        min_Max(...)  -> plain minimax for benchmark
    """

    def __init__(self, depth: int = 3):
        self.depth = depth
        self.board = [[0 for _ in range(N)] for _ in range(N)]
        self.next_bound: Set[Move] = set()

        self.currentI = -1
        self.currentJ = -1
        self.lastPlayed = 0
        self.emptyCells = N * N

        self.killer_moves = [[] for _ in range(max(depth + 10, 16))]
        self.history_table = {}
        self.trans_table = {}
        self.eval_cache = {}

        self._TT_MAX = 120_000
        self._EVAL_CACHE_MAX = 120_000
        self._zhash = 0

        self.nodes = 0
        self.cutoffs = 0

    def sync_state(self) -> None:
        """Rebuild hash, empty count and candidate move set from current board."""
        self._zhash = 0
        self.emptyCells = 0
        self.next_bound.clear()

        has_piece = False
        for i in range(N):
            for j in range(N):
                cell = self.board[i][j]
                if cell == 0:
                    self.emptyCells += 1
                else:
                    has_piece = True
                    self._zhash ^= _ZOBRIST[i][j][0 if cell == 1 else 1]

        if not has_piece:
            self.currentI = -1
            self.currentJ = -1
            self.lastPlayed = 0
            return

        for i in range(N):
            for j in range(N):
                if self.board[i][j] != 0:
                    self.update_bound(i, j, self.next_bound, radius=1)

    def isValid(self, i: int, j: int) -> bool:
        return 0 <= i < N and 0 <= j < N and self.board[i][j] == 0

    def _place(self, i: int, j: int, state: int) -> None:
        self.board[i][j] = state
        self._zhash ^= _ZOBRIST[i][j][0 if state == 1 else 1]
        self.emptyCells -= 1

    def _unplace(self, i: int, j: int, state: int) -> None:
        self.board[i][j] = 0
        self._zhash ^= _ZOBRIST[i][j][0 if state == 1 else 1]
        self.emptyCells += 1

    def update_bound(self, ni: int, nj: int, bound: Set[Move], radius: int = 1) -> None:
        """Add empty cells around a newly played move to the candidate set."""
        bound.discard((ni, nj))
        for di, dj in _NEIGHBORS[1 if radius <= 1 else 2]:
            row, col = ni + di, nj + dj
            if 0 <= row < N and 0 <= col < N and self.board[row][col] == 0:
                bound.add((row, col))
    def countDirection(self, i: int, j: int, xdir: int, ydir: int, state: int, board=None) -> int:
        if board is None:
            board = self.board
        count = 0
        for step in range(1, 4):
            row = i + ydir * step
            col = j + xdir * step
            if row < 0 or row >= N or col < 0 or col >= N:
                break
            if board[row][col] == state:
                count += 1
            else:
                break
        return count

    def isWin(self, i: int, j: int, state: int) -> bool:
        if i < 0 or j < 0 or state not in (-1, 1):
            return False

        for dirX, dirY in AXES:
            total = 1
            total += self.countDirection(i, j, dirX, dirY, state)
            total += self.countDirection(i, j, -dirX, -dirY, state)
            if total >= 4:
                return True
        return False

    def results(self) -> Optional[str]:
        if self.isWin(self.currentI, self.currentJ, self.lastPlayed):
            return "Human!" if self.lastPlayed == -1 else "AI!"
        if self.emptyCells <= 0:
            return "Tie"
        return None

    def line_correct(self, i: int, j: int, dirX: int, dirY: int, state: int) -> Tuple[int, int]:
        count = 1
        open_ends = 0

        row, col = i + dirY, j + dirX
        while 0 <= row < N and 0 <= col < N and self.board[row][col] == state:
            count += 1
            row += dirY
            col += dirX
        if 0 <= row < N and 0 <= col < N and self.board[row][col] == 0:
            open_ends += 1

        row, col = i - dirY, j - dirX
        while 0 <= row < N and 0 <= col < N and self.board[row][col] == state:
            count += 1
            row -= dirY
            col -= dirX
        if 0 <= row < N and 0 <= col < N and self.board[row][col] == 0:
            open_ends += 1

        return count, open_ends

    def pattern_counts_after_move(self, i: int, j: int, state: int) -> Tuple[int, int, int, int]:

        open_three = block_three = open_two = block_two = 0

        for dirX, dirY in AXES:
            count, open_ends = self.line_correct(i, j, dirX, dirY, state)

            if count >= 4:
                continue
            if count == 3:
                if open_ends >= 2:
                    open_three += 1
                elif open_ends == 1:
                    block_three += 1
            elif count == 2:
                if open_ends >= 2:
                    open_two += 1
                elif open_ends == 1:
                    block_two += 1

        return open_three, block_three, open_two, block_two

    def double_threat_score(self, i: int, j: int, state: int) -> int:
        """Score fork threats created by placing `state` at (i, j)."""
        open_three, block_three, open_two, _ = self.pattern_counts_after_move(i, j, state)

        score = 0
        if open_three >= 2:
            score += SCORES["DOUBLE_OPEN_THREE"]

        if open_three >= 1 and open_two >= 1:
            score += SCORES["OPEN_THREE_AND_OPEN_TWO"]
        if open_two >= 2:
            score += SCORES["DOUBLE_OPEN_TWO"]

        if block_three >= 2:
            score += SCORES["TWO_BLOCK_THREES"]

        return score

    def eval_delta(self, i: int, j: int, state: int) -> int:
        total = 0
        for dirX, dirY in AXES:
            count, open_ends = self.line_correct(i, j, dirX, dirY, state)
            total += _EVAL_TABLE.get((count, open_ends), 0)

        total += self.double_threat_score(i, j, state)
        return total

    def evaluate(self) -> int:
        cached = self.eval_cache.get(self._zhash)
        if cached is not None:
            return cached

        score = 0
        board = self.board

        for i in range(N):
            for j in range(N):
                cell = board[i][j]
                if cell == 0:
                    continue

                for dirX, dirY in AXES:
                    prev_i = i - dirY
                    prev_j = j - dirX

                    if 0 <= prev_i < N and 0 <= prev_j < N and board[prev_i][prev_j] == cell:
                        continue

                    count = 1
                    ni = i + dirY
                    nj = j + dirX
                    while 0 <= ni < N and 0 <= nj < N and board[ni][nj] == cell:
                        count += 1
                        ni += dirY
                        nj += dirX

                    open_ends = 0
                    if 0 <= prev_i < N and 0 <= prev_j < N and board[prev_i][prev_j] == 0:
                        open_ends += 1
                    if 0 <= ni < N and 0 <= nj < N and board[ni][nj] == 0:
                        open_ends += 1

                    score += cell * _EVAL_TABLE.get((count, open_ends), 0)

        if len(self.eval_cache) >= self._EVAL_CACHE_MAX:
            self.eval_cache.clear()
        self.eval_cache[self._zhash] = score
        return score

    def scoreMove(self, i: int, j: int, depth: int) -> int:
        score = self.history_table.get((i, j), 0)

        if depth < len(self.killer_moves) and (i, j) in self.killer_moves[depth]:
            score += 10_000

        score += 30 - (abs(i - N // 2) + abs(j - N // 2)) * 3

        for state, weight in ((1, 3.5), (-1, 2.0)):
            self.board[i][j] = state
            try:
                if self.isWin(i, j, state):
                    score += int(SCORES["FOUR"] * weight)
                else:
                    score += int(self.eval_delta(i, j, state) * weight)
            finally:
                self.board[i][j] = 0

        return score

    def orderedMoves(self, bound: Set[Move], depth: int) -> List[Move]:
        moves = sorted(bound, key=lambda pos: self.scoreMove(pos[0], pos[1], depth), reverse=True)

        if depth >= 6:
            return moves[:7]
        if depth == 5:
            return moves[:8]
        if depth == 4:
            return moves[:10]
        if depth == 3:
            return moves[:14]
        if depth == 2:
            return moves[:18]
        return moves[:24]

    def _move_tactical_value(self, i: int, j: int, state: int) -> int:
        self.board[i][j] = state
        try:
            if self.isWin(i, j, state):
                return SCORES["FOUR"]

            open_three, block_three, open_two, _ = self.pattern_counts_after_move(i, j, state)
            value = self.double_threat_score(i, j, state)

            value += open_three * SCORES["OPEN_THREE"]
            value += block_three * SCORES["BLOCK_THREE"]
            value += open_two * SCORES["OPEN_TWO"]
            return value
        finally:
            self.board[i][j] = 0

    def threat(self, bound: Set[Move]) -> Optional[Move]:

        ordered = self.orderedMoves(bound, self.depth)

        for i, j in ordered:
            self.board[i][j] = 1
            win = self.isWin(i, j, 1)
            self.board[i][j] = 0
            if win:
                return (i, j)
        human_wins = []
        for i, j in bound:
            self.board[i][j] = -1
            win = self.isWin(i, j, -1)
            self.board[i][j] = 0
            if win:
                human_wins.append((i, j))

        if human_wins:
            return max(human_wins, key=lambda pos: self.scoreMove(pos[0], pos[1], self.depth))

        ai_forks = []
        for i, j in ordered:
            value = self._move_tactical_value(i, j, 1)
            if value >= SCORES["OPEN_THREE_AND_OPEN_TWO"]:
                ai_forks.append((value, i, j))
        if ai_forks:
            _, i, j = max(ai_forks)
            return (i, j)

        human_forks = []
        for i, j in ordered:
            value = self._move_tactical_value(i, j, -1)
            if value >= SCORES["OPEN_THREE_AND_OPEN_TWO"]:
                human_forks.append((value, i, j))
        if human_forks:
            _, i, j = max(human_forks)
            return (i, j)

        return None

    def _remember_killer(self, depth: int, move: Move) -> None:
        if depth >= len(self.killer_moves):
            return
        if move not in self.killer_moves[depth]:
            self.killer_moves[depth].insert(0, move)
            if len(self.killer_moves[depth]) > 2:
                self.killer_moves[depth].pop()


    def min_Max(self, depth: int, bound: Set[Move], isMaximizing: bool) -> int:
        self.nodes += 1

        if self.lastPlayed != 0 and self.isWin(self.currentI, self.currentJ, self.lastPlayed):
            if self.lastPlayed == 1:
                return SCORES["FOUR"] + depth * 200
            return -SCORES["FOUR"] - depth * 200

        if self.emptyCells <= 0:
            return 0
        if depth <= 0 or not bound:
            return self.evaluate()

        state = 1 if isMaximizing else -1
        best_score = -math.inf if isMaximizing else math.inf

        for i, j in self.orderedMoves(bound, depth):
            saved = (self.currentI, self.currentJ, self.lastPlayed)
            self._place(i, j, state)
            self.currentI, self.currentJ, self.lastPlayed = i, j, state

            new_bound = bound - {(i, j)}
            self.update_bound(i, j, new_bound, radius=1)

            score = self.min_Max(depth - 1, new_bound, not isMaximizing)

            self._unplace(i, j, state)
            self.currentI, self.currentJ, self.lastPlayed = saved

            if isMaximizing:
                if score > best_score:
                    best_score = score
            else:
                if score < best_score:
                    best_score = score

        return best_score
    # Alpha-Beta + Transposition Table
    def alpha_beta_transposition(self, depth: int, bound: Set[Move], alpha: float, beta: float, isMaximizing: bool) -> int:
        self.nodes += 1

        if self.lastPlayed != 0 and self.isWin(self.currentI, self.currentJ, self.lastPlayed):
            if self.lastPlayed == 1:
                return SCORES["FOUR"] + depth * 200
            return -SCORES["FOUR"] - depth * 200

        if self.emptyCells <= 0:
            return 0
        if depth <= 0 or not bound:
            return self.evaluate()

        alpha_orig, beta_orig = alpha, beta
        key_hash = self._zhash ^ (_SIDE_HASH if isMaximizing else 0)
        tt = self.trans_table.get(key_hash)

        if tt and tt[0] >= depth:
            _, tt_score, tt_flag = tt
            if tt_flag == "EXACT":
                return tt_score
            if tt_flag == "LOWER":
                alpha = max(alpha, tt_score)
            elif tt_flag == "UPPER":
                beta = min(beta, tt_score)
            if alpha >= beta:
                return tt_score

        state = 1 if isMaximizing else -1
        best = -math.inf if isMaximizing else math.inf

        for i, j in self.orderedMoves(bound, depth):
            saved = (self.currentI, self.currentJ, self.lastPlayed)
            self._place(i, j, state)
            self.currentI, self.currentJ, self.lastPlayed = i, j, state

            new_bound = bound - {(i, j)}
            self.update_bound(i, j, new_bound, radius=1)

            val = self.alpha_beta_transposition(depth - 1, new_bound, alpha, beta, not isMaximizing)

            self._unplace(i, j, state)
            self.currentI, self.currentJ, self.lastPlayed = saved

            if isMaximizing:
                if val > best:
                    best = val
                if val > alpha:
                    alpha = val
                    self.history_table[(i, j)] = self.history_table.get((i, j), 0) + depth * depth
                if alpha >= beta:
                    self.cutoffs += 1
                    self._remember_killer(depth, (i, j))
                    break
            else:
                if val < best:
                    best = val
                if val < beta:
                    beta = val
                if beta <= alpha:
                    self.cutoffs += 1
                    self._remember_killer(depth, (i, j))
                    break

        if best <= alpha_orig:
            flag = "UPPER"
        elif best >= beta_orig:
            flag = "LOWER"
        else:
            flag = "EXACT"

        if len(self.trans_table) >= self._TT_MAX:
            self.trans_table.clear()
        self.trans_table[key_hash] = (depth, best, flag)

        return best

    def best_move_transposition(self) -> Move:
        self.sync_state()

        if self.emptyCells == N * N:
            return (N // 2, N // 2)

        self.nodes = 0
        self.cutoffs = 0
        self.history_table.clear()
        self.trans_table.clear()
        self.eval_cache.clear()

        bound = set(self.next_bound)
        if not bound:
            for i in range(N):
                for j in range(N):
                    if self.board[i][j] != 0:
                        self.update_bound(i, j, bound, radius=1)

        if not bound:
            return (N // 2, N // 2)

        urgent = self.threat(bound)
        if urgent is not None:
            return urgent

        move: Move = (-1, -1)
        max_depth = max(1, self.depth)

        for d in range(1, max_depth + 1):
            best_score = -math.inf
            best_move: Move = (-1, -1)

            moves = self.orderedMoves(bound, d)
            if move != (-1, -1):
                moves = [move] + [m for m in moves if m != move]

            for i, j in moves:
                saved = (self.currentI, self.currentJ, self.lastPlayed)
                self._place(i, j, 1)
                self.currentI, self.currentJ, self.lastPlayed = i, j, 1

                new_bound = bound - {(i, j)}
                self.update_bound(i, j, new_bound, radius=1)

                score = self.alpha_beta_transposition(d - 1, new_bound, -math.inf, math.inf, False)

                self._unplace(i, j, 1)
                self.currentI, self.currentJ, self.lastPlayed = saved

                if score > best_score:
                    best_score = score
                    best_move = (i, j)

                if best_score >= SCORES["FOUR"]:
                    return best_move

            if best_move != (-1, -1):
                move = best_move

        return move

    def best_move_minimax(self) -> Move:
        self.sync_state()

        if self.emptyCells == N * N:
            return (N // 2, N // 2)

        self.nodes = 0
        self.cutoffs = 0
        self.eval_cache.clear()

        bound = set(self.next_bound)
        if not bound:
            for i in range(N):
                for j in range(N):
                    if self.board[i][j] != 0:
                        self.update_bound(i, j, bound, radius=1)

        if not bound:
            return (N // 2, N // 2)

        urgent = self.threat(bound)
        if urgent is not None:
            return urgent

        best_score = -math.inf
        best_move: Move = (-1, -1)
        d = max(1, self.depth)

        for i, j in self.orderedMoves(bound, d):
            saved = (self.currentI, self.currentJ, self.lastPlayed)
            self._place(i, j, 1)
            self.currentI, self.currentJ, self.lastPlayed = i, j, 1

            new_bound = bound - {(i, j)}
            self.update_bound(i, j, new_bound, radius=1)

            score = self.min_Max(d - 1, new_bound, False)

            self._unplace(i, j, 1)
            self.currentI, self.currentJ, self.lastPlayed = saved

            if score > best_score:
                best_score = score
                best_move = (i, j)

            if best_score >= SCORES["FOUR"]:
                return best_move

        return best_move