"""
benchmark_ai.py
Benchmark cho AI Caro 9x9 trong file AI.py.

Đo:
- Thời gian chọn nước đi
- Số node/trạng thái đã xét trong alpha-beta
- Số lần gọi hàm evaluate
- Số lần hit transposition table
- Số lần cắt tỉa alpha-beta
- Kích thước transposition table và eval cache

Cách chạy:
    Đặt file này cùng thư mục với AI.py
    python benchmark_ai.py
"""

import csv
import math
import statistics
import time
from copy import deepcopy

from AI import AiTicTacToe, N, SCORES, _SIDE_HASH


class BenchmarkAI(AiTicTacToe):
    """Kế thừa AI gốc để thêm bộ đếm benchmark mà không cần sửa logic chính."""

    def reset_metrics(self):
        self.nodes = 0
        self.eval_calls = 0
        self.tt_hits = 0
        self.alpha_beta_cutoffs = 0
        self.max_ply_reached = 0

    def evaluate(self):
        self.eval_calls += 1
        return super().evaluate()

    def alpha_beta_transposition(self, depth, bound, alpha, beta, isMaximizing):
        # Một lần đi vào hàm alpha-beta được tính là một trạng thái/node đã xét.
        self.nodes += 1
        self.max_ply_reached = max(self.max_ply_reached, self.depth - depth)

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
            self.tt_hits += 1
            _, tt_score, tt_flag = tt

            if tt_flag == "EXACT":
                return tt_score

            if tt_flag == "LOWER":
                alpha = max(alpha, tt_score)
            elif tt_flag == "UPPER":
                beta = min(beta, tt_score)

            if alpha >= beta:
                self.alpha_beta_cutoffs += 1
                return tt_score

        best = -math.inf if isMaximizing else math.inf
        state = 1 if isMaximizing else -1

        for i, j in self.orderedMoves(bound, depth):
            saved = (self.currentI, self.currentJ, self.lastPlayed)

            self._place(i, j, state)
            self.currentI, self.currentJ, self.lastPlayed = i, j, state

            new_bound = bound - {(i, j)}
            self.update_bound(i, j, new_bound, radius=1)

            val = self.alpha_beta_transposition(
                depth - 1,
                new_bound,
                alpha,
                beta,
                not isMaximizing
            )

            self._unplace(i, j, state)
            self.currentI, self.currentJ, self.lastPlayed = saved

            if isMaximizing:
                if val > best:
                    best = val

                if val > alpha:
                    alpha = val
                    self.history_table[(i, j)] = self.history_table.get((i, j), 0) + depth * depth

                if alpha >= beta:
                    self.alpha_beta_cutoffs += 1
                    self._remember_killer(depth, (i, j))
                    break
            else:
                if val < best:
                    best = val

                if val < beta:
                    beta = val

                if beta <= alpha:
                    self.alpha_beta_cutoffs += 1
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


def apply_moves(ai, moves):
    """
    moves: list[(row, col, player)]
    player: -1 = Human/X, 1 = AI/O
    """
    ai.board = [[0 for _ in range(N)] for _ in range(N)]
    ai.currentI = -1
    ai.currentJ = -1
    ai.lastPlayed = 0
    ai.emptyCells = N * N
    ai.next_bound.clear()

    for row, col, player in moves:
        ai.board[row][col] = player
        ai.currentI, ai.currentJ = row, col
        ai.lastPlayed = player

    ai.sync_state()


TEST_CASES = {
    "empty_board": [],

    # X vừa đi trung tâm, AI cần phản ứng.
    "opening": [
        (4, 4, -1),
    ],

    # Thế cờ trung cuộc, chưa có thắng ngay.
    "middle_game": [
        (4, 4, -1), (4, 5, 1),
        (3, 4, -1), (5, 4, 1),
        (3, 3, -1), (5, 5, 1),
        (2, 4, -1), (6, 4, 1),
    ],

    # Human có chuỗi nguy hiểm, AI cần ưu tiên chặn.
    "defense_threat": [
        (4, 3, -1), (3, 3, 1),
        (4, 4, -1), (3, 4, 1),
        (4, 5, -1),
    ],

    # AI có cơ hội thắng/chốt nhanh.
    "ai_winning_chance": [
        (2, 2, 1), (4, 4, -1),
        (2, 3, 1), (5, 4, -1),
        (2, 4, 1),
    ],
}


def benchmark_one_case(case_name, moves, depth, repeats=3):
    rows = []

    for run_id in range(1, repeats + 1):
        ai = BenchmarkAI(depth=depth)
        apply_moves(ai, moves)
        ai.reset_metrics()

        start = time.perf_counter()
        best_move = ai.best_move_transposition()
        elapsed = time.perf_counter() - start

        rows.append({
            "case": case_name,
            "depth": depth,
            "run": run_id,
            "best_move": best_move,
            "time_ms": elapsed * 1000,
            "nodes": ai.nodes,
            "eval_calls": ai.eval_calls,
            "tt_hits": ai.tt_hits,
            "alpha_beta_cutoffs": ai.alpha_beta_cutoffs,
            "trans_table_size": len(ai.trans_table),
            "eval_cache_size": len(ai.eval_cache),
            "max_ply_reached": ai.max_ply_reached,
        })

    return rows


def summarize(rows):
    grouped = {}

    for row in rows:
        key = (row["case"], row["depth"])
        grouped.setdefault(key, []).append(row)

    summary_rows = []

    for (case_name, depth), items in grouped.items():
        summary_rows.append({
            "case": case_name,
            "depth": depth,
            "best_move_last_run": items[-1]["best_move"],
            "avg_time_ms": statistics.mean(x["time_ms"] for x in items),
            "min_time_ms": min(x["time_ms"] for x in items),
            "max_time_ms": max(x["time_ms"] for x in items),
            "avg_nodes": statistics.mean(x["nodes"] for x in items),
            "avg_eval_calls": statistics.mean(x["eval_calls"] for x in items),
            "avg_tt_hits": statistics.mean(x["tt_hits"] for x in items),
            "avg_cutoffs": statistics.mean(x["alpha_beta_cutoffs"] for x in items),
            "avg_trans_table_size": statistics.mean(x["trans_table_size"] for x in items),
            "avg_eval_cache_size": statistics.mean(x["eval_cache_size"] for x in items),
            "max_ply_reached": max(x["max_ply_reached"] for x in items),
        })

    return summary_rows


def print_table(rows):
    headers = [
        "case",
        "depth",
        "best_move_last_run",
        "avg_time_ms",
        "avg_nodes",
        "avg_eval_calls",
        "avg_tt_hits",
        "avg_cutoffs",
        "avg_trans_table_size",
        "avg_eval_cache_size",
    ]

    print("\n=== AI BENCHMARK SUMMARY ===")
    print(" | ".join(headers))
    print("-" * 150)

    for row in rows:
        print(
            f"{row['case']} | "
            f"{row['depth']} | "
            f"{row['best_move_last_run']} | "
            f"{row['avg_time_ms']:.3f} | "
            f"{row['avg_nodes']:.1f} | "
            f"{row['avg_eval_calls']:.1f} | "
            f"{row['avg_tt_hits']:.1f} | "
            f"{row['avg_cutoffs']:.1f} | "
            f"{row['avg_trans_table_size']:.1f} | "
            f"{row['avg_eval_cache_size']:.1f}"
        )


def save_csv(path, rows):
    if not rows:
        return

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main():
    depths = [3, 5, 7]
    repeats = 3

    all_raw_rows = []

    for case_name, moves in TEST_CASES.items():
        for depth in depths:
            all_raw_rows.extend(benchmark_one_case(case_name, moves, depth, repeats=repeats))

    summary_rows = summarize(all_raw_rows)

    print_table(summary_rows)
    save_csv("benchmark_raw.csv", all_raw_rows)
    save_csv("benchmark_summary.csv", summary_rows)

    print("\nĐã lưu:")
    print("- benchmark_raw.csv: kết quả từng lần chạy")
    print("- benchmark_summary.csv: kết quả trung bình")


if __name__ == "__main__":
    main()
