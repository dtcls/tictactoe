# Cờ Caro AI — Minimax & Alpha-Beta Pruning

Bài tập lập trình môn **Cơ sở Trí tuệ Nhân tạo**.  
Chương trình chơi Cờ Caro 9×9, điều kiện thắng: 4 quân liên tiếp.

---

## Yêu cầu

- Python 3.8+
- Cài thư viện:

```bash
pip install -r requirements.txt
```

---

## Chạy game

```bash
python Main.py
```

> Cần có thư mục `assets/` chứa: `vintage_theme.jpg.jpeg`, `x0.png`, `o0.png`, `move2.wav`, `click.wav`, `undo.wav`, `bgm.wav`, `trailer.mp4`, `loading.gif`.

---

## Chạy benchmark (Level 3)

```bash
jupyter notebook benchmark_analysis_level3_depth1_8_seconds.ipynb
```

Kết quả được lưu vào `benchmark_results.csv`.

---

## Cấu trúc thư mục

```
caro-ai/
├── AI.py           # Logic AI: Minimax, Alpha-Beta, hàm đánh giá
├── Main.py         # Giao diện Pygame, vòng lặp game
├── requirements.txt
├── benchmark_analysis_level3_depth1_8_seconds.ipynb
├── benchmark_results.csv
├── report_caro_ai.pdf
└── assets/         # Hình ảnh, âm thanh, video
```

---

## Tính năng

| Tính năng | Mô tả |
|---|---|
| Chế độ chơi | PVE (Người vs Máy), PVP (Người vs Người) |
| Thuật toán AI | Minimax hoặc Alpha-Beta (toggle trên giao diện) |
| Độ khó | Easy (d=4), Medium (d=5), Hard (d=6) |
| Undo | Hủy nước đi vừa đánh |
| Đi trước | Người hoặc máy tùy chọn |

---

## Thành viên nhóm

| MSSV | Họ và Tên |
|---|---|
| ... | ... |
| ... | ... |
| ... | ... |
