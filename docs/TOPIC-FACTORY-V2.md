# Topic Factory V2 — ma trận chủ đề có kiểm chứng

Tài liệu này mô tả lớp "chọn chủ đề" mới của content factory: cách một ý định tìm kiếm đi từ ứng viên
→ kiểm tra trùng lặp → duyệt → hàng đợi cho writer → QA → xuất bản, và vì sao hệ thống có thể mở rộng
tới 20.000–40.000 bài **khi có đủ chủ đề thật** mà không nhân bản tiêu đề.

Nguyên tắc bắt buộc (không được nới lỏng bằng cấu hình):

- Không lấy số lượng thay giá trị. Mỗi hàng được duyệt phải trả lời bằng chữ: *người đọc nhận được thông tin gì mà bài hiện có chưa cung cấp* (`information_gain`).
- Không tạo nhiều bài cùng intent; không dùng hoán vị template (quận × đối tượng × bối cảnh × năm) để tăng bài.
- Không bịa nhu cầu tìm kiếm: khối lượng chỉ lấy từ `data/keyword-metrics.jsonl` (nguồn + ngày đối chiếu), thiếu số liệu thì ghi "không có số liệu".
- Không xoá bài, đổi URL, redirect hay thay kiến trúc production khi chưa được chủ cửa hàng duyệt (xem mục 8).
- Điểm tương đồng là **tín hiệu** cho biên tập; chỉ hoán vị template mới bị loại tự động. Writer không bao giờ tạo hay nới lỏng phê duyệt.

## 1. Thành phần

| Tệp | Vai trò | Ai sửa |
|---|---|---|
| `config/topic-universe.json` | Vũ trụ chủ đề: hub → subtopic → intent cho phép, loại bằng chứng bắt buộc, trục qualifier (quận, đối tượng, bối cảnh, thời lượng, nhóm, năm, từ đệm), stopword/từ đánh dấu intent giữ dấu, ngưỡng trùng lặp, quy tắc ưu tiên và duyệt | Biên tập; đổi tệp này tự động dựng lại chỉ mục |
| `data/topic-matrix.jsonl` | **Ma trận chủ đề chính** — nguồn sự thật duy nhất cho writer. Mỗi dòng = một ý định với vòng đời | `scripts/topic_matrix.py` (discover/approve/set/next); biên tập có thể sửa trường nghiên cứu |
| `data/topic-matrix-published.jsonl` | Dẫn xuất từ `content/posts.json` + `content/articles/`: bài đã xuất bản, quyết định audit (KEEP/REWRITE/MERGE-CANDIDATE/REJECT), trọng số trùng lặp hard/soft | Chỉ `sync` |
| `data/cache/topic-index.sqlite` | Chỉ mục tăng dần (SQLite, stdlib): bag-of-words TF-IDF, khoá cụm, khoá hoán vị, postings có cờ `hard` | Chỉ `sync`/`discover`/`approve`/`set`; gitignore |
| `data/keyword-metrics.jsonl` | Khối lượng/KD/intent theo từ khoá, có `source` và `checked`; dòng không có số liệu vẫn được ghi để không tra lại | Tool SEO (OpenSEO/DataForSEO), không ghi tay |
| `data/seeds/*.jsonl` | Lô ứng viên (mỗi dòng một ý định; dòng `#` là chú thích) | Người đề xuất chủ đề |
| `reports/topic-factory-v2-audit.md`, `reports/slot-audit-N.csv` | Báo cáo audit (bài V1, N slot kế tiếp của bộ lập kế hoạch cũ, ma trận) | `audit` |
| `tests/test_topic_matrix.py` | Kiểm thử chuẩn hoá, 6 tầng trùng lặp, cổng kiểm tra fail-closed, vòng đời, QA bài, khói trên dữ liệu thật | — |

Bộ xưởng V1 (`scripts/content_factory.py`, bộ lập kế hoạch hoán vị, writer template) **không bị sửa** và vẫn tạm dừng
(`STOP_FACTORY`, `enabled: false`). Nó chỉ còn được dùng để audit (`spec_for`) cho tới khi kế hoạch ở mục 8 được duyệt.

## 2. Vũ trụ chủ đề

Industry (thuê xe máy Hà Nội) → Hub (`thue-xe`, `xe-may`, `xe-dien`, `bao-duong`, `du-lich`, `luat-giao-thong`, `kinh-nghiem`; `xe-dap`, `o-to` tắt) → Subtopic → Intent (informational / commercial / transactional / navigational / troubleshooting) → User problem → Article.

Mỗi hub khai báo `requires_sources` và `evidence_types` được chấp nhận (ví dụ `luat-giao-thong`: `law`, `official`;
`thue-xe`: `business-facts`, `owner`; `kinh-nghiem` không bắt buộc nguồn nhưng cấm số liệu không dẫn nguồn).
Các trục qualifier liệt kê từ ngữ **chỉ nhân bản trang** chứ không thêm thông tin (quận, "cho sinh viên", "giờ cao điểm sáng tối", "theo tháng", năm...).

## 3. Hàng trong ma trận

Trường chính: `topic_id` (TM-xxxxx; bài đã xuất bản là PUB-<sha1 url>), `lifecycle`, `origin`, `hub`, `subtopic`, `cluster`, `url`, `slug`,
`title`, `primary_keyword`, `secondary_keywords`, `intent`, `user_problem`, `information_gain`, `evidence[]` (`type`, `source`, `quote`, `verbatim`, `checked`),
`research_status`, `keyword_volume`, `keyword_source`, `keyword_difficulty`, `outline`, `suggested_internal_links`, `content_type`, `schema`, `priority` (P0/P1/P2),
`quality_status`, `editorial_approval` (`by`, `at`, `note`, `override_reason`), `overlap[]`, `legacy_overlap[]`, `cannibalization_risk`, `merge_into`,
`permutation_of`, `decision_hint`, `gate_errors[]`, `approval_blockers[]`, `audit_decision`, `rejected_reason`, `history[]`.

Vòng đời và chuyển trạng thái hợp lệ (mọi chuyển khác bị từ chối):

```
PLANNED  → RESEARCH | APPROVED | REJECTED
RESEARCH → PLANNED  | APPROVED | REJECTED
APPROVED → WRITING  | RESEARCH | REJECTED      (thu hồi duyệt = APPROVED → RESEARCH)
WRITING  → QA       | APPROVED | REJECTED
QA       → PUBLISHED| WRITING  | REJECTED      (PUBLISHED chỉ khi URL đã có trong nguồn bài)
REJECTED → PLANNED                              (mở lại phải qua cổng kiểm tra từ đầu)
```

## 4. Sáu tầng chống trùng lặp

So sánh tiếng Việt **giữ dấu** (NFC, chữ thường); chỉ bỏ dấu khi tạo slug và so khớp qualifier (bỏ dấu làm "đèn đỏ" trùng "đến đó").

| Tầng | Cách so | Kết quả |
|---|---|---|
| 1. Từ khoá | trùng chính xác (`exact_keyword`) hoặc trùng **khoá từ khoá chuẩn hoá** (`keyword_normalized`: bỏ quận/đối tượng/thời lượng/nhóm/năm, giữ bối cảnh) | cao |
| 2. Cụm intent | `intent_class :: token lõi` của phần đầu tiêu đề (bỏ qualifier, stopword, từ đánh dấu) | cao; gần cụm (`intent_cluster_near`, Jaccard lõi ≥ 0,75) → trung bình |
| 3. Ngữ nghĩa | cosine TF-IDF trên unigram+bigram của tiêu đề, từ khoá, user problem, outline; IDF tính **chỉ trên bài hard** | ≥ 0,80 cao, ≥ 0,55 trung bình |
| 4. Tiêu đề / outline | Jaccard trọng số IDF trên token phần hỏi chính (≥ 0,60 cao, ≥ 0,40 trung bình); Jaccard outline ≥ 0,50 → trung bình | |
| 5. Hoán vị / cùng câu hỏi | khoá hoán vị: phần đầu tiêu đề sau khi bỏ **mọi** qualifier; trùng khoá với bất kỳ URL đã có (kể cả bài V1 ẩn) → `permutation` | **REJECT tự động** |
| 6. Đã xuất bản + nháp + kế hoạch | mọi hàng PLANNED/RESEARCH/APPROVED/WRITING/QA được index ngay khi tạo; ứng viên sau trong cùng lô được so với ứng viên trước | như trên |

Hai ngoại lệ có chủ đích:

- **`permutation_with_demand`**: tiêu đề trùng khoá hoán vị nhưng từ khoá chính có khối lượng đo được ≥ ngưỡng P1 (100) *và* chứa từ không có trong bài trùng
  (ví dụ "giờ cao điểm hà nội" 320 lượt/tháng so với bài "Đi xe máy ở Hà Nội"). Đây là ý định riêng, không phải biến thể template → hạ xuống **cao**
  (MERGE-CANDIDATE): biên tập phải `--override` có lý do và `information_gain` phải nêu bài trùng. Không có số liệu = không có ngoại lệ.
- **Cặp lân cận chỉ cần một bên giải thích**: với rủi ro trung bình, blocker "phải nêu URL bài trùng" được coi là thoả nếu hàng kia đã nêu URL hàng này.

Bài V1 (xưởng cũ, đã noindex) là **soft**: không làm tăng rủi ro, không làm loãng IDF, chỉ được liệt kê ở `legacy_overlap` để cân nhắc redirect sau này;
riêng tầng 5 vẫn áp dụng với bài soft (hoán vị của một URL đã tồn tại không tạo thông tin mới).

Rủi ro → gợi ý: hoán vị → REJECT; cao → MERGE-CANDIDATE; trung bình → NEEDS-RESEARCH; không/thấp → KEEP nếu đã có bằng chứng, nếu không NEEDS-RESEARCH.

## 5. Cổng kiểm tra (fail-closed)

`gate_errors` (hàng không thể APPROVED/WRITING khi còn lỗi): thiếu trường bắt buộc; hub tắt hoặc subtopic lạ; URL không ascii/không nằm dưới hub; trùng URL;
tiêu đề > 75 ký tự; tiêu đề không chứa ≥ 60 % từ lõi của từ khoá chính; hoán vị của bài đã có; trùng cao mà chưa có `override_reason`.

`approval_blockers` (điều kiện duyệt): `information_gain` ≥ 60 ký tự; rủi ro trung bình phải nêu URL bài trùng và khác gì; hub yêu cầu nguồn thì cần ≥ 1 bằng chứng
`checked` đúng loại và có `source` (trừ `business-facts`/`owner`); từ khoá chưa có số liệu phải có `keyword_source` (ghi rõ "không có số liệu", không bịa).

`validate` chạy lại toàn bộ đánh giá cho hàng chưa xuất bản và **thoát mã 1** nếu bất kỳ hàng APPROVED/WRITING/QA vi phạm — dùng trong CI.

QA bài viết phạm vi hẹp (`check-article FILE --topic TM-xxxxx`): trùng lặp với toàn bộ chỉ mục (trừ chính URL bài), ≥ 700 từ, ≥ 4 mục, độ dài tiêu đề/excerpt,
không nhắc site chính rentbikehanoi.com, từ ngữ thổi phồng, liên kết nội bộ hỏng, số điện thoại phải khớp `config/business-facts.json`, số liệu không dẫn nguồn (cảnh báo).
Writer chỉ bị QA trên bài mình viết; không QA lại toàn site.

## 6. Quy trình

```
Discover → Validate → Deduplicate → Approve → Queue → Writers (3) → Scoped QA → Publish → Update Index
```

```sh
# Chọn chủ đề (scripts/topic_matrix.py)
python3 scripts/topic_matrix.py sync                                   # dẫn xuất bài đã xuất bản, cập nhật chỉ mục tăng dần (sha256)
python3 scripts/topic_matrix.py discover data/seeds/<lo>.jsonl [--dry-run] [--update]
python3 scripts/topic_matrix.py validate                               # exit 1 nếu hàng đã duyệt vi phạm cổng
python3 scripts/topic_matrix.py approve TM-00017 --by "Nguyễn Hà" --note "..." [--override "lý do"]
python3 scripts/topic_matrix.py set TM-00085 --lifecycle REJECTED --reason "ngoài dịch vụ" --by "Nguyễn Hà"
python3 scripts/topic_matrix.py audit --slots 300 ; status ; export --csv reports/topic-matrix.csv

# Đường xuất bản (scripts/factory_v2.py — điều phối viên duy nhất)
python3 scripts/factory_v2.py queue --writer writer-1 --n 3 [--hub luat-giao-thong] [--topic TM-00017]
        # APPROVED → WRITING; ghi brief content/drafts/TM-00017.brief.json (chủ đề, bằng chứng, luật viết, khuôn nháp)
#   writer viết nháp content/drafts/TM-00017.json theo khuôn (id = topic_id, url/hub như ma trận, factoryVersion 2, sources)
python3 scripts/factory_v2.py qa TM-00017            # QA phạm vi hẹp; đạt → QA, không đạt → vẫn WRITING kèm lý do
python3 scripts/factory_v2.py publish TM-00017 --by "Nguyễn Hà"
        # QA lại (fail-closed) → content/articles/TM-00017.json (factoryVersion 2) → nhật ký data/factory-queue.jsonl (append-only)
        # → content_factory reindex → hàng PUBLISHED → sync chỉ mục trùng lặp. Nháp không đạt chỉ được ghi vào nhật ký, không vào nguồn bài.
python3 scripts/factory_v2.py publish --all --unattended --by github-actions   # chế độ không giám sát: tôn trọng STOP_FACTORY, v2.enabled, max_publish_per_run
python3 scripts/factory_v2.py status
python3 scripts/build.py && python3 scripts/validate_factory_site.py   # shard V2 được index, vào sitemap-posts.xml và chỉ mục tìm kiếm
```

- `discover` là idempotent: seed có cùng khoá từ khoá với hàng đã có thì bị bỏ qua (được liệt kê trong `skipped`); `--update` chỉ làm mới trường nghiên cứu
  (bằng chứng, information_gain, outline, ghi chú) của hàng PLANNED/RESEARCH **cùng tiêu đề**; không chạm hàng đã duyệt hay đã loại.
- Một điều phối viên duy nhất ghi ma trận và nguồn bài: lệnh CLI chạy tuần tự; trên GitHub Actions (`.github/workflows/topic-factory-v2.yml`)
  cùng nhóm `concurrency` với xưởng V1. Writer chỉ đọc brief và viết nháp; writer không gọi `approve`, không đổi vòng đời, không ghi vào `content/articles/`.
- Ba writer = ba hàng đợi (`writer-1..3` trong `config/content-factory.json` → `v2.writers`); hiện writer là phiên Claude Code của routine viết bài hằng ngày
  hoặc chủ cửa hàng — không có API AI hay template trong repo (AGENTS.md).
- `set ... REJECTED` gỡ hàng khỏi chỉ mục ngay để không chặn ứng viên khác; hàng PUBLISHED do bài nguồn (`PUB-…`) đại diện; `validate` sau đó cập nhật lại phân loại các hàng chưa duyệt.
- Hàng chỉ được PUBLISHED khi URL đã tồn tại trong `content/posts.json` hoặc `content/articles/`; `content/drafts/` không phải nguồn bài — build, sitemap, chỉ mục tìm kiếm không đọc.
- `build.py`/`validate_factory_site.py`: cờ `noindex_factory_articles` chỉ còn áp dụng cho shard `factoryVersion < 2`; shard V2 được index trừ khi có trong `config/factory-noindex.json`.

## 7. Năng lực mở rộng và kiến trúc index cho 40.000 URL

Đo trên dữ liệu thật (3.673 bài đã xuất bản + 96 hàng ma trận, máy 1 nhân):

| Việc | Thời gian |
|---|---|
| `sync` dựng lại toàn bộ chỉ mục (khi đổi vũ trụ/mã) | ≈ 24 s |
| `sync` tăng dần, không đổi | ≈ 2 s |
| `discover` 97 ứng viên (6 tầng + cổng) | ≈ 1,1 s (≈ 10 ms/ứng viên) |
| `validate` 96 hàng | ≈ 1 s |
| `audit` 300 slot | ≈ 5 s |

Chỉ mục dùng postings có cờ `hard` + index `(hard, term)` nên ứng viên ngữ nghĩa chỉ lấy từ bài được index; df/IDF cập nhật tăng dần theo từng lần ghi.
Ước tính tuyến tính cho 40.000 bài hard: dựng lại toàn bộ ≈ 5–8 phút (chỉ khi đổi cấu hình), đánh giá một ứng viên ≈ 50–100 ms, một lô 500 ứng viên ≈ 1 phút.
Nếu cần nhanh hơn: giới hạn ứng viên ngữ nghĩa theo hub (cột `hub` đã có trong `docs`).

Kiến trúc index (áp dụng dần theo mục 8, không tự động):

1. **Hub → cluster → bài**: mỗi hub có trang hub; mỗi bài mới phải có ≥ 2 liên kết nội bộ gợi ý (`suggested_internal_links`) tới bài cùng cụm và trang hub, và được liên kết ngược từ bài lân cận (`merge_into`/`overlap` là danh sách gợi ý sẵn).
2. **Sitemap index**: `build.py` đã xuất `sitemap.xml` (index) → `sitemap-pages.xml`. Khi một hub vượt ~5.000 URL, tách `sitemap-<hub>.xml` (≤ 10.000 URL/tệp, `lastmod` thật từ `updated`), giữ một sitemap index duy nhất đăng trong Search Console.
3. **Canonical** tự trỏ về chính URL; breadcrumb Hub → Subtopic → Bài; schema `Article` + `BreadcrumbList`, `FAQPage` chỉ khi bài có mục hỏi–đáp thật.
4. **Không nháp trong sitemap**: chỉ URL có trong nguồn bài mới được build; hàng WRITING/QA không có tệp nguồn.
5. **Không noindex tự động**: quyết định noindex/redirect cho bài V1 chỉ sau audit (`legacy_overlap`, GSC) và được chủ cửa hàng duyệt.
6. **Đánh giá index bằng Search Console**: báo cáo hằng tuần (routine thứ Hai) + `inspect_urls` theo lô ≤ 5 URL; chủ đề chỉ được coi là "thành công" khi URL được index và có hiển thị, không phải khi xuất bản.

## 8. Migration: đã làm gì, còn gì chờ phê duyệt

| Bước | Trạng thái | Thay đổi | Rollback |
|---|---|---|---|
| M1 | **Đã làm** | Writer nhận chủ đề từ ma trận qua `factory_v2.py queue` (chỉ APPROVED); nháp phải qua `qa` + `publish` (fail-closed). Bộ lập kế hoạch hoán vị và writer template V1 vẫn nằm trong `content_factory.py` nhưng chỉ còn dùng để audit; xưởng V1 vẫn tạm dừng (`STOP_FACTORY`, `enabled: false`). | Xoá `scripts/factory_v2.py`, `content/drafts/`; không ảnh hưởng bài cũ |
| M2 | **Đã làm** | Shard V2 nằm cùng thư mục `content/articles/<TM-id>.json` với `factoryVersion: 2`, `topic_id`, `sources`, `publishedAt`; `build.py`/`validate_factory_site.py` chỉ noindex `factoryVersion < 2`; `reindex` và nhật ký hàng đợi dùng chung định dạng V1 (bài V2 có `sequence: null`). | Xoá shard `TM-*.json` + chạy `reindex`, `sync`; cờ cũ vẫn nguyên nghĩa với bài V1 |
| M3 | Chờ | Tách sitemap theo hub khi một hub vượt ~5.000 URL (mục 7.2); hiện `sitemap-posts.xml` đủ cho hàng chục nghìn URL. | Một sitemap-pages.xml |
| M4 | **Chờ phê duyệt** | 3.337 bài V1 noindex giữ nguyên; chỉ sau khi bài mới cùng intent đã index ổn định mới cân nhắc redirect 301, từng hub một. Bảng đối chiếu để chủ cửa hàng duyệt: `reports/redirect-candidates-v1.csv` (mỗi bài V1 được đánh giá 6 tầng so với toàn bộ bài được index; chỉ liệt kê cặp rủi ro cao/trung bình, kèm tầng và điểm). Chưa áp dụng redirect nào. | Không làm nếu không duyệt |
| M5 | **Đã làm (thủ công)** | `.github/workflows/topic-factory-v2.yml`: job `checks` chạy trên mọi pull request (sync, validate, 3 bộ test, build, validate site); job `publish` chỉ chạy khi `workflow_dispatch` với input `publish` và tôn trọng `STOP_FACTORY`/`v2.enabled`. Không có lịch tự động — bật lịch là quyết định của chủ cửa hàng. | Tắt workflow |

Giới hạn hiện tại cần nói rõ: 20.000–40.000 là **năng lực** của hệ thống (chỉ mục, cổng, vòng đời) — số bài xuất bản phụ thuộc vào số chủ đề thật có bằng chứng.
Lô thử nghiệm 97 ứng viên cho thấy tỷ lệ duyệt ngay ≈ 25 %; phần lớn còn lại chờ nguồn (NEEDS-RESEARCH), không phải bị loại.

## 9. Kiểm tra bắt buộc

```sh
python3 tests/test_topic_matrix.py
python3 tests/test_factory_v2.py
python3 scripts/topic_matrix.py validate
python3 scripts/content_factory.py run --dry-run
python3 tests/test_content_factory.py
python3 scripts/build.py
python3 scripts/validate_factory_site.py
```
