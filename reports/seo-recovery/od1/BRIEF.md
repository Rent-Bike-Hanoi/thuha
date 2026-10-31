# OD-1 BRIEF: viết lại 608 bài (thuha.rentbikehanoi.com)

Ngày bắt đầu: 31/10/2026. Chủ site yêu cầu sửa trực tiếp trên GitHub. Mục tiêu: 608 bài đạt chuẩn SEO, giữ 100% URL và giữ trạng thái được index. Không dùng noindex hàng loạt, không xoá bài.

Danh sách: `reports/seo-recovery/od1/od1_matrix.csv`, gồm cột batch, group, id, url, file, vehicle, topic, audience, context, angle.

## 1. Bất biến (vi phạm thì loại bài)
- Không đổi `id, url, hub, parent, kind, art, tone, intent, factoryVersion` trong shard `content/articles/NH-xxxxx.json`. Không đổi tên file. Không tạo file shard mới.
- Được viết lại: `title`, `excerpt`, `keywords`, `faqTitle`, `sections`, `faq`, `wordCount`, `sources`, `rewrite`. Chủ site đã cho phép đổi title, H1, H2, H3 và meta.
- Không sửa `content/posts.json`, `config/*`, `scripts/*` và không sửa shard ngoài danh sách được giao.
- Thông tin cửa hàng (địa chỉ, giờ, điện thoại, giá, chính sách, đội xe) chỉ lấy từ `config/business-facts.json`.
  - Không nhắc **bảo hiểm** (trừ "mũ bảo hiểm"/"nón bảo hiểm").
  - Không viết "24/7", không viết "miễn phí giao xe", không khuyến mãi.
  - Không nói cửa hàng cho thuê xe đạp, xe côn tay hoặc xe VinFast. Đội xe chỉ gồm những gì business-facts ghi: xe số, xe ga, xe 50cc, xe máy điện Tailg.
- Không bịa trải nghiệm, đánh giá, số liệu hay lời khách hàng. Mọi thông số kỹ thuật, mốc bảo dưỡng, mức phạt, điều luật và giá phải có trong `sources` kèm **trích nguyên văn** lấy từ thư viện `reports/seo-recovery/od1/lib/*.json` hoặc từ trang nguồn bạn mở được thật. Không có nguồn thì không ghi số.
- Không chỉ thay từ đồng nghĩa để qua bước so trùng. Mỗi bài phải trả lời một ý định tìm kiếm riêng có thật.

## 2. Viết đúng chủ đề URL theo loại xe
URL có dạng `/hub/<loại xe>/<chủ đề>-<đối tượng>-<bối cảnh>-<góc>/`. Title và H1 phải phản ánh **chủ đề và loại xe trong URL**, nói đúng sự thật.
- **Chủ đề áp dụng được cho loại xe** (ví dụ áp suất lốp xe đạp, phanh đĩa VinFast): viết bài chuyên sâu, đúng loại xe đó, có thông số của hãng.
- **Chủ đề không áp dụng được** (bugi, kim phun, lọc gió, nhớt máy cho xe đạp hoặc xe điện; xích cho xe tay ga; nước làm mát cho xe làm mát bằng gió; pin xe điện cho xe xăng):
  - Mở bài trả lời thẳng câu hỏi "<xe> có <bộ phận> không" (không có, vì sao, theo tài liệu hãng).
  - Phần còn lại chuyển sang **bộ phận tương đương thật** của xe đó, theo đúng góc nhìn của URL. Ví dụ: nhớt máy → dầu xích (xe đạp); bugi → hệ thống điện, khóa thông minh, khởi động (xe điện); dây curoa → xích tải (Wave); pin xe điện → bình ắc quy 12V (xe xăng); tiết kiệm nhiên liệu → tiết kiệm sức đạp hoặc quãng đường mỗi lần sạc.
  - Tiêu đề mẫu: "Xe đạp touring có bugi không? Việc cần kiểm tra mùa đông thay thế".
- **Đối tượng, bối cảnh, góc viết** (ví dụ "nữ giới dùng xe ga", "mùa mưa ngập", "chi phí thực tế") là điểm tạo khác biệt giữa các biến thể cùng cụm. Phải dùng thật, không chỉ chèn tên.
  - Góc "chi phí thực tế": chỉ ghi giá có nguồn (bảng giá hãng, trang chính thức). Nếu không có nguồn thì nói các khoản cần dự trù, không ghi số.

## 3. Bài luật giao thông
- Căn cứ hiện hành tại 31/10/2026:
  - Luật Trật tự, an toàn giao thông đường bộ 2024 (Luật 36/2024/QH15) và các văn bản sửa đổi/hợp nhất mới nhất.
  - Nghị định 168/2024/NĐ-CP và các văn bản sửa đổi, bổ sung nếu có. Kiểm tra văn bản hợp nhất năm 2026 trên datafiles.chinhphu.vn.
  - Thông tư 38/2024/TT-BGTVT (tốc độ).
  - Thông tư Bộ Công an về sát hạch và cấp giấy phép lái xe.
- Trích **nguyên văn** điều, khoản, điểm. Thư viện nguồn có sẵn: `lib/seed_legal_quotes.json` (448 trích dẫn đã dùng ở bài đã kiểm chứng) và `lib/legal.json`.
- Hạng **A2 không còn** từ 01/01/2025 (hạng A: mô tô trên 125 cm³ hoặc trên 11 kW). Bằng A2 cấp trước đó vẫn dùng theo điều khoản chuyển tiếp. Không trình bày A2 như hạng hiện hành.
- Bài V1 về luật phải là bài **vệ tinh** của bài trụ cột viết tay cùng chủ đề (danh sách trong `site_index.tsv`, kind=hand-written hoặc V2):
  - Chọn góc dài theo đối tượng, bối cảnh và góc viết của URL.
  - Đặt link tới bài trụ cột.
  - Không lặp lại nguyên bảng mức phạt của bài trụ cột.
- Chủ đề bảo hiểm TNDS bắt buộc: business-facts cấm nhắc bảo hiểm. Bài thuộc chủ đề này ghi `feasible=false` và chờ chủ site quyết định (OD-6).

## 4. Chuẩn QA (`scripts/seo_qa.py`, PASS = điểm ≥85 và không có lỗi critical)
- **Cấu trúc**:
  - ≥5 section `[h2, html]` và ≥3 FAQ `[q, a]`.
  - Section đầu là câu trả lời trực tiếp (AEO), dài 25–160 từ.
- **Độ sâu**: ≥1.200 từ là tốt (900–1.199 từ vẫn có thể đạt). Mục tiêu 1.200–1.800 từ, không độn chữ.
- **Meta**:
  - Title 20–65 ký tự (tối đa 70).
  - Excerpt (meta description) 90–160 ký tự.
  - `keywords` là chuỗi phân tách bằng dấu phẩy, từ khoá đầu tiên là từ khoá chính. ≥60% số từ của nó phải nằm trong title cộng H2 đầu.
- **Sự thật**:
  - Chỉ dùng số điện thoại 0334 699 969 và giờ mở cửa 08:00–17:00.
  - Không vi phạm BANNED.
  - Số tiền ngoài ALLOWED_AMOUNTS phải có nguồn (bài có `sources` và có link ngoài).
- **Nguồn**: hub xe-may, xe-dien, luat-giao-thong cần **cả** link ngoài trong thân bài (`<a href="https://...">`) **và** `sources[]`. Hub xe-dap nên làm như vậy.
  - Mỗi mục trong `sources` có dạng `{"type": "manufacturer|law|standard|guide|business-facts", "source": "<URL>", "quote": "<trích nguyên văn>", "checked": "2026-10-31"}`.
- **Link nội bộ**:
  - ≥3 link tới trang đang index, trong đó ≥1 trang tiền: `/thue-xe-may/ha-noi/`, `/thue-xe-dien/ha-noi/`, `/thue-xe-50cc/ha-noi/`, `/bang-gia/`, `/thue-xe-may/ha-noi/theo-thang/`, `/thue-xe-may/ha-noi/theo-ngay/`, `/thue-xe-may/long-bien/`, `/thue-xe-may/hoan-kiem/`, `/lien-he/`.
  - Link phải tới URL có thật trong `site_index.tsv` hoặc tới hub (`/xe-dap/`, `/xe-dien/`, `/xe-may/`, `/luat-giao-thong/`, `/bao-duong/`).
  - Ưu tiên link tới bài trụ cột hoặc bài đã kiểm chứng (kind hand-written, V2, V1-verified). Không link tới bài V1-unverified.
- **Trùng lặp**: độ tương đồng TF-IDF với mọi trang index phải <0,60 (tốt nhất <0,50). Phép đo tính cả các bài **cùng cụm** đã viết trước.
- **Chạy kiểm tra**: `python3 scripts/seo_qa.py content/articles/NH-xxxxx.json` (chạy trong worktree của lô).

## 5. Hình thức HTML trong section
- Dùng `<p>`, `<ul><li>`, `<ol><li>`, `<h3>`, `<strong>`, `<table><tr><th>/<td>`, `<a href>`. Không dùng `<h1>` hoặc `<h2>` trong body (H2 là phần tử đầu của section).
- Section cuối nên là "Nguồn tham khảo", liệt kê link ngoài (tên văn bản hoặc tài liệu kèm link).
- Đoạn liên hệ cửa hàng chỉ nêu điều có thật và liên quan:
  - Ví dụ với bài xe đạp: cửa hàng không cho thuê xe đạp, nhưng có xe máy điện và xe số tại Long Biên.
  - Giờ, điện thoại, địa chỉ: template đã hiển thị, không cần lặp lại.
- Văn phong: tiếng Việt tự nhiên, không lặp chữ ("xe xe", "chuyến chuyến"), không nhồi từ khoá, viết hoa đúng tên riêng (Honda, VinFast, Shimano, Hà Nội).

## 6. Trường `rewrite`
```json
"rewrite": {"rewrittenAt": "<ISO +07:00>", "by": "Claude Code (SEO recovery OD-1)", "batch": "OD1-Bxx", "queries": ["<từ khoá chính>", "..."], "od1": "<sai loại xe | A2 | XEM_LAI>"}
```
`wordCount` = số từ của văn bản thuần (title của section, body và FAQ).

## 7. Mẫu chất lượng
- `content/articles/NH-02292.json`: bugi Honda Vision (B04).
- Các bài trong `config/factory-reindex.json`.
- Bài V2 `content/articles/TM-*.json`.
