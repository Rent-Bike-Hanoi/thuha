# Audit Topic Factory V2

Ngày: 2026-10-12. Nguồn: content/posts.json (73 bài viết tay), content/articles/ (3600 bài xưởng V1).

## 1. Bài xưởng V1: ý định tìm kiếm thực so với số bài

| Họ bài | Số bài | Ý định lõi | Trùng (hoán vị) | Tỷ lệ trùng | KEEP | REWRITE | MERGE-CANDIDATE | REJECT |
|---|---|---|---|---|---|---|---|---|
| du-lich | 731 | 25 | 706 | 96.6% | 25 | 0 | 706 | 0 |
| luat | 346 | 25 | 321 | 92.8% | 0 | 25 | 321 | 0 |
| thue-xe | 1471 | 120 | 1351 | 91.8% | 120 | 0 | 1351 | 0 |
| xe-info | 1052 | 260 | 792 | 75.3% | 118 | 0 | 359 | 575 |
| **Tổng** | 3600 | 430 | 3170 | 88.1% | 263 | 25 | 2737 | 575 |

Cách đọc: "ý định lõi" là các trục mang thông tin thật (chủ đề × loại xe, hoặc điểm đến, hoặc lỗi luật). Quận, đối tượng, bối cảnh, thời lượng, nhóm chỉ nhân bản trang. Toàn bộ bài V1 hiện là noindex và được coi là "trùng mềm": không chặn chủ đề mới, chỉ được ghi lại để cân nhắc chuyển hướng sau khi bài mới xuất bản.

## 2. 300 slot kế tiếp của bộ lập kế hoạch cũ (sequence 3678–3977)

Phân loại theo ý định lõi: {'MERGE-CANDIDATE': 267, 'REJECT': 33}. Ý định mới xuất hiện: **0**.
Cổng V2 chạy trên 300 tiêu đề: 296/300 slot trùng với bài V1 đã có (trùng mềm); 68 slot còn trùng cả với bài viết tay/bài được index.
Chi tiết: reports/slot-audit-300.csv.

## 3. Ma trận chủ đề (data/topic-matrix.jsonl)

Số hàng: 96. Vòng đời: {'REJECTED': 23, 'APPROVED': 24, 'RESEARCH': 49}. Phân loại: {'REJECT': 23, 'KEEP': 59, 'NEEDS-RESEARCH': 13, 'MERGE-CANDIDATE': 1}. Rủi ro trùng lặp: {'none': 53, 'high': 19, 'medium': 24}.

| Hub | PLANNED | RESEARCH | APPROVED | WRITING | QA | PUBLISHED | REJECTED |
|---|---|---|---|---|---|---|---|
| bao-duong | 0 | 17 | 1 | 0 | 0 | 0 | 0 |
| du-lich | 0 | 9 | 0 | 0 | 0 | 0 | 4 |
| kinh-nghiem | 0 | 0 | 7 | 0 | 0 | 0 | 3 |
| luat-giao-thong | 0 | 12 | 11 | 0 | 0 | 0 | 8 |
| thue-xe | 0 | 2 | 3 | 0 | 0 | 0 | 5 |
| xe-dien | 0 | 5 | 1 | 0 | 0 | 0 | 1 |
| xe-may | 0 | 4 | 1 | 0 | 0 | 0 | 2 |

## 4. Bài viết tay

73 bài, tất cả KEEP; đây là lớp phủ hiện tại mà mọi chủ đề mới phải so sánh.

