# Kế hoạch 14/10/2026: liên kết nội bộ, nâng cấp bài cũ, volume từ khoá

Bối cảnh: site đạt ~1004 bài indexable (PR #35 merge 14/10). Dừng sản xuất hàng loạt; chuyển sang chất lượng.
Mọi thay đổi đi qua PR, giữ URL, slug, canonical; không đổi title/H1/meta hàng loạt; không sửa rentbikehanoi.com.

## Số liệu khảo sát (build 14/10, 1.028 URL trong sitemap)

- Link trong thân bài: trung vị 11 link/trang. Chỉ 4 trang không có link vào (trang chủ, /cam-nang/, /gioi-thieu/, /chinh-sach-bao-mat/: được nối qua menu, bình thường).
- 1 link gãy: `/du-lich/chua-huyen-thien-hang-khoai/` (bài chưa xuất bản).
- 7 bài chỉ có 1 link vào: den-do-co-duoc-re-phai, sac-binh-ac-quy-xe-may-tai-nha, thue-xe-may-theo-thang-hay-mua-xe, sac-xe-may-dien-o-tram-sac-cong-cong-vinfast, kymco-sky-town-150, di-xe-may-ngay-o-nhiem-bui-min-o-ha-noi, bao-tang-yen-bai.
- Trang tiền: /thue-xe-may/ha-noi/ 874 link vào, /bang-gia/ 464, /thue-xe-dien/ha-noi/ 77, /thue-xe-may/long-bien/ 68, /thue-xe-50cc/ha-noi/ 31, **/thue-xe-may/ha-noi/theo-thang/ chỉ 14**.
- Khối "Bài liên quan" trong `scripts/build.py` lấy 3 bài đầu cùng hub theo thứ tự cố định: 666 bài du lịch gần như cùng trỏ về vài bài giống nhau.

## A. Liên kết nội bộ

| # | Việc | Cách làm | Xong khi |
|---|---|---|---|
| A1 | Sửa link gãy | Bỏ thẻ `<a>` tới chùa Huyền Thiên (giữ chữ) trong bài chứa nó | 0 link gãy |
| A2 | Bài liên quan theo chủ đề | `build.py`: chấm điểm bài cùng hub theo từ khoá chung (keywords + slug), ưu tiên cùng subtopic/tỉnh; giữ 3 thẻ; ổn định (không ngẫu nhiên) | Mỗi bài du lịch có liên quan khác nhau; test + validate PASS; rebuild không diff |
| A3 | Đẩy trang tiền yếu | Thêm 1 câu ngữ cảnh có link /thue-xe-may/ha-noi/theo-thang/ vào bài có ý định thuê dài (sinh viên, đi làm, ở lâu, so sánh thuê/mua), /thue-xe-may/long-bien/ vào bài khu Long Biên – Gia Lâm, /thue-xe-50cc/ha-noi/ vào bài 50cc/học sinh | theo-thang ≥ 40 link vào; chỉ chèn nơi đúng ngữ cảnh |
| A4 | Bài ít link vào | Mỗi bài trong 7 bài trên: thêm link từ 2–3 bài cùng chủ đề | Không bài nào < 3 link vào |
| A5 | Kiểm tra lặp lại | Script kiểm link gãy + đếm link vào chạy mỗi lần build (scratchpad, đưa vào validate nếu ổn định) | Báo cáo số trước/sau |

## B. Nâng cấp bài cũ (data/upgrade-backlog.jsonl)

Thứ tự: UB-018, UB-019, UB-020 (P1, trang tiền, chỉ dùng business-facts) → UB-021 → UB-015 (Bắc Ninh, Quảng Ninh là thành phố trực thuộc TW; đọc nghị quyết trước) → UB-022, UB-023, UB-024 (theo sách hướng dẫn nhà sản xuất, có nguồn).
UB-017 (P0) cần chủ cửa hàng xác nhận mẫu xe: không tự sửa, chỉ hỏi.
Mỗi mục xong: status DONE + `result` trong backlog.

## C. Volume từ khoá

Trạng thái 14/10: OpenSEO còn 11 credit, không đủ cho một lần gọi 10 từ khoá; Semrush hết API unit; Ubersuggest 3 báo cáo/ngày; HarborRank cần đăng nhập lại.
- Cần chủ site: nạp credit OpenSEO (hoặc đăng nhập lại HarborRank để đọc Search Console).
- Khi có: lấy volume cho ~150 từ khoá ưu tiên (trang tiền + cụm thuê xe + bài có hiển thị trong GSC), ghi vào `data/keyword-metrics.jsonl` (ngày + nguồn), xếp thứ tự nâng cấp theo nhu cầu.
- Trong lúc chờ: dùng 3 báo cáo Ubersuggest/ngày cho từ khoá trang tiền.

## Kiểm tra mỗi PR

`content_factory.py run --dry-run`, 4 bộ test, `topic_matrix.py validate`, `build.py` (rebuild không diff), `validate_factory_site.py`.
