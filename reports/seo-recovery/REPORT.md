# Báo cáo SEO recovery thuha.rentbikehanoi.com

Cập nhật 2026-10-31 01:24 (giờ Hà Nội). Sinh tự động từ `reports/seo-recovery/data/` bằng `scripts/seo_recovery_report.py`.

> INDEX_ELIGIBLE (trang cho phép index, có trong sitemap) **không** đồng nghĩa INDEXED trên Google. Trạng thái Google chỉ lấy từ Search Console; URL chưa kiểm tra ghi NOT_VERIFIED.

## 1. Tổng quan trước / sau

| Chỉ số | Giá trị |
|---|---|
| URL render (kiểm kê đầu dự án) | 5048 |
|   trong đó noindex lúc audit | 3747 |
|   index-eligible lúc audit | 1301 |
| URL đã xoá trước dự án (10/10/2026, 404) | 142 |
| Bài V1 đã mở index có kiểm chứng | 33 |
| URL còn trong config/factory-noindex.json | 3325 |


### Phân loại (classification.csv)

| (Nhóm, hành động, trạng thái) | Số URL |
|---|---|
| ('B', 'REWRITE_THEN_INDEX', 'BLOCKED') | 10 |
| ('B', 'REWRITE_THEN_INDEX', 'DONE') | 33 |
| ('C', 'KEEP_NOINDEX', 'BLOCKED') | 2985 |
| ('D', 'KEEP_INDEX', 'DONE_BY_RULE') | 45 |
| ('D', 'KEEP_NOINDEX', 'BLOCKED') | 2 |
| ('D', 'KEEP_NOINDEX', 'DONE_BY_RULE') | 145 |
| ('E', 'KEEP_NOINDEX', 'BLOCKED') | 572 |
| ('INDEXABLE', 'OPTIMIZE_HUB', 'DONE') | 7 |
| ('INDEXABLE', 'OPTIMIZE_ONPAGE', 'BLOCKED') | 2 |
| ('INDEXABLE', 'OPTIMIZE_ONPAGE', 'DONE') | 1 |
| ('INDEXABLE', 'OPTIMIZE_ONPAGE', 'OPEN') | 1246 |


## 2. Audit hai repository

| Hạng mục | Kết quả | Rủi ro | Ghi chú |
|---|---|---|---|
| Repository Rent-Bike-Hanoi/blog | RỖNG trên GitHub (409 Git Repository is empty; 0 branch, 0 PR, 0 commit); clone local không có commit | Không phải nguồn triển khai; không sửa | Kiểm tra 30/10/2026 qua GitHub API + git ls-remote |
| Repository Rent-Bike-Hanoi/thuha | Source of truth: 664 commit (sau unshallow), branch main, GitHub Pages deploy từ main (workflow pages-build-deployment), CNAME thuha.rentbikehanoi.com | Thấp | Lịch sử nhập từ lucynguyen777/thuha (PR #44–48 cũ) rồi PR #1 ở repo mới |
| Live site = main? | Có: last-modified live khớp commit deploy; HTML trong repo = HTML live | Thấp | Build deterministic (0 diff khi rebuild với lịch sử git đầy đủ) |
| Generator | scripts/build.py (Python stdlib) đọc content/posts.json (73 bài tay), content/articles/*.json (3.600 V1 + 1.169 V2), content/pages.json, content/home.json; templates/partials/*.html; scripts/templates.py | Thấp | Shard V2 có topic_id, sources; V1 có intent chuỗi |
| Noindex logic | factory_noindex = (url in factory-noindex.json OR (noindex_factory_articles AND factoryVersion<2)) AND url not in factory-reindex.json | Trung bình: cờ toàn cục ẩn cả 263 bài KEEP | Allowlist mới (commit 9945e332bc) mở index có kiểm chứng |
| Workflows | content-factory.yml (V1, schedule tắt, STOP_FACTORY), topic-factory-v2.yml (checks trên PR + publish thủ công), refresh-site.yml (push main sửa template -> rebuild + commit), facebook-posts.yml (06:17 hằng ngày, 3 bài từ sitemap) | Trung bình: refresh-site tự commit HTML khi sửa build.py/templates trên main | Đã tính: PR lô P0 merge -> refresh-site chạy (rebuild không diff) |
| Branch/PR | Branch làm việc claude/seo-recovery-2026-10-30; PR #2 (P0) merged 30/10/2026 11:18 UTC | Thấp | Rollback = revert merge commit 8df6269c1a |
| Secrets/quyền | Push được bằng credential phiên; GSC đọc qua Windsor.ai (searchconsole) + OpenSEO URL Inspection (bind tạm, đã trả về blog.rentbikehanoi.com) | Thấp | Không có API key trả phí mới |
| Rủi ro đồng bộ | Không có repo thứ hai chứa mã; blog.rentbikehanoi.com là WordPress riêng (không liên quan mã nguồn) | Thấp |  |


## 3. Phục hồi noindex: nguyên nhân và quyết định

| Nguyên nhân noindex lúc audit | Số URL |
|---|---|
| EMPTY_HUB_no_indexable_articles | 2 |
| FACTORY_NOINDEX_LIST | 3337 |
| GLOBAL_FLAG_noindex_factory_articles(V1) | 263 |
| PAGINATION_all_items_noindex | 145 |


### URL đã mở index (lô đã merge/đang merge)

| URL | Lô | QA | GSC hiển thị (8–10/2026) | GSC index (30/10) |
|---|---|---|---|---|
| /kinh-nghiem/deo-o-quy-ho/xe-ga-honda-vision/di-ve-trong-ngay-day-trip-phuot-solo-mot-minh-checklist-chuan-bi/ | B03-live | None | 11 | NOT_VERIFIED |
| /kinh-nghiem/deo-o-quy-ho/xe-may-so-honda-wave/cuoi-tuan-2-ngay-1-dem-phuot-solo-mot-minh-checklist-chuan-bi/ | B03-live | None | 14 | Crawled - currently not indexed |
| /kinh-nghiem/san-may-ta-xua/xe-ga-honda-vision/cuoi-tuan-2-ngay-1-dem-phuot-solo-mot-minh-diem-checkin-am-thuc/ | B03-live | None | 21 | Crawled - currently not indexed |
| /kinh-nghiem/vuon-quoc-gia-ba-vi/xe-ga-honda-vision/hanh-trinh-3-ngay-2-dem-phuot-solo-mot-minh-diem-checkin-am-thuc/ | B03-live | None | 125 | Crawled - currently not indexed |
| /luat-giao-thong/xu-ly-khi-xay-ra-va-cham-nguoi-moi-lay-bang-lai-can-cu-phap-ly-moi-nhat-khi-di-chuyen-trong-dieu-kien-mua-bao-tam-nhin-han-che/ | B03-live | None | 0 | NOT_VERIFIED |
| /xe-dien/xe-may-dien-vinfast-evo-200/khoi-dong-buoi-sang-lanh-nguoi-su-dung-xe-hang-ngay-sau-thoi-gian-dai-khong-su-dung-chi-phi-thuc-te/ | B03-live | None | 61 | Crawled - currently not indexed |
| /xe-dien/xe-may-dien-vinfast-evo-200/xu-ly-ngap-nuoc-sinh-vien-tu-bao-duong-xe-sau-thoi-gian-dai-khong-su-dung-chi-phi-thuc-te/ | B03-live | None | 14 | Submitted and indexed |
| /xe-dien/xe-may-dien-vinfast-feliz-s/khoi-dong-buoi-sang-lanh-sinh-vien-tu-bao-duong-xe-sau-thoi-gian-dai-khong-su-dung-chi-phi-thuc-te/ | B03-live | None | 45 | Crawled - currently not indexed |
| /xe-may/ba-dinh/honda-wave-alpha/lo-trinh-khach-du-lich-trong-nuoc-di-cong-tac-dai-ngay-chay-xe-tren-cac-truc-duong-vanh-dai/ | B03-live | None | 10 | Crawled - currently not indexed |
| /xe-may/xe-con-tay-honda-winner-x/thay-the-bugi-nguoi-su-dung-xe-hang-ngay-mua-dong-thoi-tiet-lanh-gia-dau-hieu-can-kiem-tra/ | B04-live | None | 0 | NOT_VERIFIED |
| /xe-may/xe-may-so-honda-wave/ap-suat-lop-chuan-nguoi-thue-xe-dai-han-sau-thoi-gian-dai-khong-su-dung-lich-trinh-dinh-ky/ | B04-live | None | 0 | NOT_VERIFIED |
| /xe-may/xe-may-so-honda-wave/thay-dau-nhot-tai-xe-cong-nghe-chay-xe-lien-tuc-mua-mua-ngap-ung-do-thi-huong-dan-chi-tiet/ | B04-live | None | 0 | NOT_VERIFIED |
| /xe-may/xe-may-so-honda-wave/thay-loc-gio-dong-co-nguoi-thue-xe-dai-han-moc-bao-duong-dinh-ky-5000-km-lich-trinh-dinh-ky/ | B04-live | None | 0 | NOT_VERIFIED |
| /xe-may/xe-may-so-honda-wave/thay-the-bugi-nhan-vien-van-phong-ban-ron-mua-dong-thoi-tiet-lanh-gia-lich-trinh-dinh-ky/ | B04-live | None | 0 | NOT_VERIFIED |
| /xe-may/xe-so-yamaha-sirius/ap-suat-lop-chuan-nu-gioi-su-dung-xe-ga-sau-thoi-gian-dai-khong-su-dung-dau-hieu-can-kiem-tra/ | B04-live | None | 7 | NOT_VERIFIED |
| /xe-may/xe-so-yamaha-sirius/thay-dau-nhot-nguoi-moi-mua-xe-lan-dau-sau-thoi-gian-dai-khong-su-dung-sai-lam-pho-bien/ | B04-live | None | 0 | NOT_VERIFIED |
| /xe-may/xe-so-yamaha-sirius/thay-loc-gio-dong-co-nu-gioi-su-dung-xe-ga-moc-bao-duong-dinh-ky-5000-km-dau-hieu-can-kiem-tra/ | B04-live | None | 0 | NOT_VERIFIED |
| /xe-may/xe-so-yamaha-sirius/thay-the-bugi-nguoi-moi-mua-xe-lan-dau-sau-thoi-gian-dai-khong-su-dung-lich-trinh-dinh-ky/ | B04-live | None | 0 | NOT_VERIFIED |
| /xe-may/xe-tay-ga-honda-air-blade/ap-suat-lop-chuan-nguoi-thue-xe-dai-han-truoc-chuyen-phuot-di-xa-dau-hieu-can-kiem-tra/ | B04-live | None | 0 | NOT_VERIFIED |
| /xe-may/xe-tay-ga-honda-air-blade/kiem-tra-nuoc-lam-mat-tai-xe-cong-nghe-chay-xe-lien-tuc-moc-bao-duong-dinh-ky-5000-km-dau-hieu-can-kiem-tra/ | B03-live | None | 13 | Submitted and indexed |
| /xe-may/xe-tay-ga-honda-air-blade/thay-dau-nhot-nhan-vien-van-phong-ban-ron-nhung-ngay-nang-nong-dinh-diem-huong-dan-chi-tiet/ | B04-live | None | 0 | NOT_VERIFIED |
| /xe-may/xe-tay-ga-honda-air-blade/thay-nhot-hop-so-lap-nguoi-moi-mua-xe-lan-dau-nhung-ngay-nang-nong-dinh-diem-sai-lam-pho-bien/ | B03-live | None | 5 | NOT_VERIFIED |
| /xe-may/xe-tay-ga-honda-air-blade/thay-the-bugi-nguoi-thue-xe-dai-han-mua-mua-ngap-ung-do-thi-dau-hieu-can-kiem-tra/ | B04-live | None | 0 | NOT_VERIFIED |
| /xe-may/xe-tay-ga-honda-lead/kiem-tra-nuoc-lam-mat-nhan-vien-van-phong-ban-ron-mua-mua-ngap-ung-do-thi-chi-phi-thuc-te/ | B04-live | None | 0 | NOT_VERIFIED |
| /xe-may/xe-tay-ga-honda-lead/thay-day-curoa-nhan-vien-van-phong-ban-ron-truoc-chuyen-phuot-di-xa-dau-hieu-can-kiem-tra/ | B04-live | None | 0 | NOT_VERIFIED |
| /xe-may/xe-tay-ga-honda-lead/thay-nhot-hop-so-lap-nu-gioi-su-dung-xe-ga-truoc-chuyen-phuot-di-xa-dau-hieu-can-kiem-tra/ | B04-live | None | 0 | NOT_VERIFIED |
| /xe-may/xe-tay-ga-honda-vision/ap-suat-lop-chuan-sinh-vien-tu-bao-duong-xe-nhung-ngay-nang-nong-dinh-diem-sai-lam-pho-bien/ | B04-live | None | 0 | NOT_VERIFIED |
| /xe-may/xe-tay-ga-honda-vision/can-chinh-co-phot-nguoi-moi-mua-xe-lan-dau-nhung-ngay-nang-nong-dinh-diem-chi-phi-thuc-te/ | B03-live | None | 16 | Crawled - currently not indexed |
| /xe-may/xe-tay-ga-honda-vision/thay-dau-nhot-nu-gioi-su-dung-xe-ga-mua-dong-thoi-tiet-lanh-gia-sai-lam-pho-bien/ | B04-live | None | 0 | NOT_VERIFIED |
| /xe-may/xe-tay-ga-honda-vision/thay-day-curoa-nguoi-moi-mua-xe-lan-dau-mua-dong-thoi-tiet-lanh-gia-dau-hieu-can-kiem-tra/ | B04-live | None | 0 | NOT_VERIFIED |
| /xe-may/xe-tay-ga-honda-vision/thay-loc-gio-dong-co-nguoi-moi-mua-xe-lan-dau-sau-thoi-gian-dai-khong-su-dung-dau-hieu-can-kiem-tra/ | B04-live | None | 0 | NOT_VERIFIED |
| /xe-may/xe-tay-ga-honda-vision/thay-nhot-hop-so-lap-nu-gioi-su-dung-xe-ga-sau-thoi-gian-dai-khong-su-dung-lich-trinh-dinh-ky/ | B04-live | None | 0 | NOT_VERIFIED |
| /xe-may/xe-tay-ga-honda-vision/thay-the-bugi-nu-gioi-su-dung-xe-ga-mua-dong-thoi-tiet-lanh-gia-lich-trinh-dinh-ky/ | B04-live | None | 0 | NOT_VERIFIED |


### URL giữ noindex có lý do (BLOCKED): 3567

Danh sách đầy đủ trong sheet 03_INDEX_RECOVERY. Theo lý do:

| Lý do (rút gọn) | Số URL |
|---|---|
| audit BO: topic does not fit the vehicle (e.g. engine maintenance on a bicycle/e-bike) | 572 |
| model × generic maintenance topic: model adds no manufacturer-specific information | 60 |
| one rental page per model is enough | 55 |
| template permutation (district x audience x context) of /kinh-nghiem/dao-cat-ba-hai-phong/xe-ga-honda-vision/di-ve-trong | 29 |
| template permutation (district x audience x context) of /kinh-nghiem/ha-noi-pho-co-va-ho-tay/xe-dap-touring-da-ngoai/chu | 29 |
| template permutation (district x audience x context) of /kinh-nghiem/ho-dai-lai/xe-con-tay-honda-winner-x/di-ve-trong-ng | 29 |
| template permutation (district x audience x context) of /kinh-nghiem/pho-co-hoi-an/xe-ga-honda-lead/di-ve-trong-ngay-day | 29 |
| template permutation (district x audience x context) of /kinh-nghiem/ruong-bac-thang-hoang-su-phi/xe-may-phan-khoi-50cc/ | 29 |
| template permutation (district x audience x context) of /kinh-nghiem/ruong-bac-thang-mu-cang-chai/xe-ga-honda-lead/di-ve | 29 |
| template permutation (district x audience x context) of /kinh-nghiem/tam-dao-vinh-phuc/xe-ga-honda-lead/hanh-trinh-3-nga | 29 |
| template permutation (district x audience x context) of /kinh-nghiem/vinh-ha-long/xe-dap-touring-da-ngoai/chuyen-kham-ph | 29 |
| template permutation (district x audience x context) of /kinh-nghiem/cao-nguyen-da-dong-van/xe-ga-honda-air-blade/hanh-t | 28 |
| template permutation (district x audience x context) of /kinh-nghiem/cao-nguyen-moc-chau/xe-may-so-honda-wave/di-ve-tron | 28 |
| template permutation (district x audience x context) of /kinh-nghiem/co-do-hue/xe-con-tay-yamaha-exciter/chuyen-kham-pha | 28 |
| template permutation (district x audience x context) of /kinh-nghiem/deo-thung-khe-hoa-binh/xe-ga-honda-air-blade/hanh-t | 28 |


## 4. Nội dung và trùng lặp

- Bài index-eligible có cặp tương đồng >= 0,60 với bài index khác: 183 (sheet 05).
- Cụm trùng >= 0,80 giữa bài V1: xem sheet 05 (cluster_id).


## 5. Technical SEO

| Hạng mục | Phát hiện | Ảnh hưởng | Trạng thái | Commit |
|---|---|---|---|---|
| robots/meta | 3.747 trang noindex,follow: 3.337 bài V1 trong config/factory-noindex.json (GOP 2.737 + BO 575 + XEM_LAI 25, chủ site duyệt 10–11/10/2026), 263 bài V1 KEEP chỉ bị noindex do cờ toàn cục noindex_factory_articles=true (commit 43394ba465 11/10/2026), 145 trang ph | 3747 | IN_PROGRESS | 9945e332bc |
| x-robots-tag | GitHub Pages không gửi X-Robots-Tag; không có noindex qua HTTP header. | 0 | DONE |  |
| robots.txt | Allow: / cho mọi bot; sitemap index khai báo đúng. | 0 | DONE |  |
| canonical | 100% trang có canonical tự trỏ đúng https://thuha.rentbikehanoi.com<path>; không canonical chéo domain. | 0 | DONE |  |
| sitemap | sitemap.xml (index) -> sitemap-pages.xml 87 URL + sitemap-posts.xml 1.169 URL = 1.256 URL, tất cả index-eligible, có lastmod thật từ git; không chứa URL noindex. | 1256 | DONE |  |
| title | 1.239/1.301 trang index-eligible có thẻ <title> > 65 ký tự vì hậu tố " / Thuê xe máy Nguyễn Hà" (24 ký tự) bị Google cắt. | 1239 | DONE | f8bb56ef58 (PR #2, merge 8df6269c) |
| meta description | 922/1.301 trang index-eligible có meta description > 160 ký tự (tối đa 301). | 922 | DONE | f8bb56ef58 (PR #2) |
| menu / crawl | Header+footer trên 5.048 trang link tới 2 hub noindex rỗng (/xe-dap/, /o-to/) và 9 hub cố định. | 5048 | DONE | f8bb56ef58 (PR #2) |
| homepage | Trang chủ gần như không có nội dung văn bản (0 từ trong article-body), H1 là slogan; GSC: "Crawled - currently not indexed" (29/10). | 1 | DONE | f8bb56ef58 (PR #2) |
| index coverage | GSC URL Inspection 30/10: 9/10 trang tiền "Crawled - currently not indexed" (chỉ /thue-xe-may/long-bien/ indexed); 6/9 hub "URL is unknown to Google"; V2 mẫu: 4 indexed, 3 crawled-not-indexed, 2 discovered, 1 unknown; 4 bài V1 noindex vẫn "Submitted and indexe | 50 | IN_PROGRESS |  |
| pagination | 208 trang phân trang hub (25 bài/trang); 145 trang chỉ chứa bài V1 noindex -> noindex; 45 trang index-eligible nhưng không có trong sitemap (đúng chủ đích). | 208 | DONE_BY_RULE |  |
| redirect / http | http->https 301; không có trailing slash -> 301 có slash; www không phục vụ (không có DNS/cert) — không link tới www ở đâu. | 0 | DONE |  |
| 404 | URL không tồn tại trả 404 với 404.html (noindex); 142 URL mồ côi đã bị xoá ngày 10/10/2026 trước dự án (live 404, GSC unknown). | 142 | DONE_BY_RULE |  |
| schema | Mọi trang có Organization + Blog; bài có BlogPosting (author Person, publisher) + BreadcrumbList; FAQPage khi có FAQ; trang tiền có LocalBusiness (geo, hasMap, giờ); tác giả có ProfilePage. GSC rich results: Breadcrumbs PASS trên mẫu. | 0 | DONE |  |
| images | 0 ảnh thiếu alt; ảnh trong bài có width/height và loading=lazy; 1.294 trang index-eligible dùng og:image mặc định của thương hiệu (chấp nhận được). | 0 | DONE |  |
| performance | HTML 26–50 KB; CSS 28 KB (render-blocking, không font ngoài); JS 19 KB defer; assets/search-index.json 5,6 MB chỉ tải khi mở tìm kiếm/chat (lazy). Chưa đo Lighthouse/CWV thực tế. | 0 | NOT_VERIFIED |  |
| internal links | 0 link nội bộ gãy; 46.643 link ngữ cảnh+liên quan; 1 bài V2 index-eligible không có link vào (/du-lich/phu-quang-cung/, GSC Discovered-not-indexed). | 1 | DONE | 795fcca86d (PR #3) |
| duplicate content | V1: median max-sim TF-IDF 0,82; 2.590/3.600 bài V1 >= 0,80 với bài khác; 148 cụm >= 0,80 (lớn nhất 786 bài). Index-eligible: 183 cặp >= 0,60 (ví dụ /bang-gia/ ~ /thue-xe-may/ha-noi/theo-thang/ 0,73; CBR650R ~ CB650R 0,80). | 2590 | IN_PROGRESS |  |
| cross-domain | blog.rentbikehanoi.com (WordPress, cùng thương hiệu, 1.100 URL) và rentbikehanoi.com nhắm cùng từ khoá "thuê xe máy hà nội"; nội dung KHÔNG sao chép (<4% 6-gram trùng). GBP trỏ về rentbikehanoi.com. | 0 | NEEDS_REVIEW |  |
| build reproducibility | Clone nông (shallow) làm build.py dùng ngày fallback cho lastmod/dateModified của toàn bộ 4.866 trang; sau unshallow build tái tạo 0 diff. | 4866 | DONE |  |
| dates / structured data | Mọi bài trong content/posts.json (73 bài viết tay, gồm 9 trang tiền) lấy datePublished = dateModified = ngày commit gần nhất của posts.json; sửa 1 bài làm cả 73 trang đổi ngày đăng, ngày sửa và sitemap lastmod (tín hiệu tươi mới giả). | 73 | DONE | 3b819fa99f (PR #5, merge 40e52b2e60); bot refresh 0 diff; live 30/10: /bang-gia/ dateModified 2026-10-15, theo-ngay 2026-10-30 |
| business facts | Bảng giá trong quy tắc chung của chủ sở hữu (Wave tháng 900k–1,2tr, Vision tháng 1,8–2tr, Air Blade tháng 1,5tr, Click/Mio, cọc 2–3tr…) khác cách nhóm giá của site (config/business-facts.json: xe số 1–1,2tr/tháng, xe ga 1,2–2tr/tháng, cọc 2–5tr). | 0 | NEEDS_REVIEW |  |


## 6. Changelog và QA

- Changelog: 96 dòng (sheet 09).
- QA: 89 lượt; PASS 78, FAIL 11 (sheet 10).


## 7. GSC

- Tổng 05–27/10/2026: 93 click, 3123 hiển thị (Windsor.ai).

| URL Inspection 30/10 (50 URL mẫu) | Số URL |
|---|---|
| Crawled - currently not indexed | 23 |
| Discovered - currently not indexed | 2 |
| Submitted and indexed | 11 |
| URL is unknown to Google | 14 |


## 8. Checkpoint

```json
{
 "batch_id": "B04 hoàn tất (PR #6, #7)",
 "updated": "2026-10-31T01:23:53+07:00",
 "commit_sha": "57fd310780 (main, merge PR #7); 625c5bee22 (squash PR #6)",
 "completed_urls": [
  "/kinh-nghiem/deo-o-quy-ho/xe-ga-honda-vision/di-ve-trong-ngay-day-trip-phuot-solo-mot-minh-checklist-chuan-bi/",
  "/kinh-nghiem/deo-o-quy-ho/xe-may-so-honda-wave/cuoi-tuan-2-ngay-1-dem-phuot-solo-mot-minh-checklist-chuan-bi/",
  "/kinh-nghiem/san-may-ta-xua/xe-ga-honda-vision/cuoi-tuan-2-ngay-1-dem-phuot-solo-mot-minh-diem-checkin-am-thuc/",
  "/kinh-nghiem/vuon-quoc-gia-ba-vi/xe-ga-honda-vision/hanh-trinh-3-ngay-2-dem-phuot-solo-mot-minh-diem-checkin-am-thuc/",
  "/luat-giao-thong/xu-ly-khi-xay-ra-va-cham-nguoi-moi-lay-bang-lai-can-cu-phap-ly-moi-nhat-khi-di-chuyen-trong-dieu-kien-mua-bao-tam-nhin-han-che/",
  "/xe-dien/xe-may-dien-vinfast-evo-200/khoi-dong-buoi-sang-lanh-nguoi-su-dung-xe-hang-ngay-sau-thoi-gian-dai-khong-su-dung-chi-phi-thuc-te/",
  "/xe-dien/xe-may-dien-vinfast-evo-200/xu-ly-ngap-nuoc-sinh-vien-tu-bao-duong-xe-sau-thoi-gian-dai-khong-su-dung-chi-phi-thuc-te/",
  "/xe-dien/xe-may-dien-vinfast-feliz-s/khoi-dong-buoi-sang-lanh-sinh-vien-tu-bao-duong-xe-sau-thoi-gian-dai-khong-su-dung-chi-phi-thuc-te/",
  "/xe-may/ba-dinh/honda-wave-alpha/lo-trinh-khach-du-lich-trong-nuoc-di-cong-tac-dai-ngay-chay-xe-tren-cac-truc-duong-vanh-dai/",
  "/xe-may/xe-con-tay-honda-winner-x/thay-the-bugi-nguoi-su-dung-xe-hang-ngay-mua-dong-thoi-tiet-lanh-gia-dau-hieu-can-kiem-tra/",
  "/xe-may/xe-may-so-honda-wave/ap-suat-lop-chuan-nguoi-thue-xe-dai-han-sau-thoi-gian-dai-khong-su-dung-lich-trinh-dinh-ky/",
  "/xe-may/xe-may-so-honda-wave/thay-dau-nhot-tai-xe-cong-nghe-chay-xe-lien-tuc-mua-mua-ngap-ung-do-thi-huong-dan-chi-tiet/",
  "/xe-may/xe-may-so-honda-wave/thay-loc-gio-dong-co-nguoi-thue-xe-dai-han-moc-bao-duong-dinh-ky-5000-km-lich-trinh-dinh-ky/",
  "/xe-may/xe-may-so-honda-wave/thay-the-bugi-nhan-vien-van-phong-ban-ron-mua-dong-thoi-tiet-lanh-gia-lich-trinh-dinh-ky/",
  "/xe-may/xe-so-yamaha-sirius/ap-suat-lop-chuan-nu-gioi-su-dung-xe-ga-sau-thoi-gian-dai-khong-su-dung-dau-hieu-can-kiem-tra/",
  "/xe-may/xe-so-yamaha-sirius/thay-dau-nhot-nguoi-moi-mua-xe-lan-dau-sau-thoi-gian-dai-khong-su-dung-sai-lam-pho-bien/",
  "/xe-may/xe-so-yamaha-sirius/thay-loc-gio-dong-co-nu-gioi-su-dung-xe-ga-moc-bao-duong-dinh-ky-5000-km-dau-hieu-can-kiem-tra/",
  "/xe-may/xe-so-yamaha-sirius/thay-the-bugi-nguoi-moi-mua-xe-lan-dau-sau-thoi-gian-dai-khong-su-dung-lich-trinh-dinh-ky/",
  "/xe-may/xe-tay-ga-honda-air-blade/ap-suat-lop-chuan-nguoi-thue-xe-dai-han-truoc-chuyen-phuot-di-xa-dau-hieu-can-kiem-tra/",
  "/xe-may/xe-tay-ga-honda-air-blade/kiem-tra-nuoc-lam-mat-tai-xe-cong-nghe-chay-xe-lien-tuc-moc-bao-duong-dinh-ky-5000-km-dau-hieu-can-kiem-tra/",
  "/xe-may/xe-tay-ga-honda-air-blade/thay-dau-nhot-nhan-vien-van-phong-ban-ron-nhung-ngay-nang-nong-dinh-diem-huong-dan-chi-tiet/",
  "/xe-may/xe-tay-ga-honda-air-blade/thay-nhot-hop-so-lap-nguoi-moi-mua-xe-lan-dau-nhung-ngay-nang-nong-dinh-diem-sai-lam-pho-bien/",
  "/xe-may/xe-tay-ga-honda-air-blade/thay-the-bugi-nguoi-thue-xe-dai-han-mua-mua-ngap-ung-do-thi-dau-hieu-can-kiem-tra/",
  "/xe-may/xe-tay-ga-honda-lead/kiem-tra-nuoc-lam-mat-nhan-vien-van-phong-ban-ron-mua-mua-ngap-ung-do-thi-chi-phi-thuc-te/",
  "/xe-may/xe-tay-ga-honda-lead/thay-day-curoa-nhan-vien-van-phong-ban-ron-truoc-chuyen-phuot-di-xa-dau-hieu-can-kiem-tra/",
  "/xe-may/xe-tay-ga-honda-lead/thay-nhot-hop-so-lap-nu-gioi-su-dung-xe-ga-truoc-chuyen-phuot-di-xa-dau-hieu-can-kiem-tra/",
  "/xe-may/xe-tay-ga-honda-vision/ap-suat-lop-chuan-sinh-vien-tu-bao-duong-xe-nhung-ngay-nang-nong-dinh-diem-sai-lam-pho-bien/",
  "/xe-may/xe-tay-ga-honda-vision/can-chinh-co-phot-nguoi-moi-mua-xe-lan-dau-nhung-ngay-nang-nong-dinh-diem-chi-phi-thuc-te/",
  "/xe-may/xe-tay-ga-honda-vision/thay-dau-nhot-nu-gioi-su-dung-xe-ga-mua-dong-thoi-tiet-lanh-gia-sai-lam-pho-bien/",
  "/xe-may/xe-tay-ga-honda-vision/thay-day-curoa-nguoi-moi-mua-xe-lan-dau-mua-dong-thoi-tiet-lanh-gia-dau-hieu-can-kiem-tra/",
  "/xe-may/xe-tay-ga-honda-vision/thay-loc-gio-dong-co-nguoi-moi-mua-xe-lan-dau-sau-thoi-gian-dai-khong-su-dung-dau-hieu-can-kiem-tra/",
  "/xe-may/xe-tay-ga-honda-vision/thay-nhot-hop-so-lap-nu-gioi-su-dung-xe-ga-sau-thoi-gian-dai-khong-su-dung-lich-trinh-dinh-ky/",
  "/xe-may/xe-tay-ga-honda-vision/thay-the-bugi-nu-gioi-su-dung-xe-ga-mua-dong-thoi-tiet-lanh-gia-lich-trinh-dinh-ky/"
 ],
 "remaining": "33 bài V1 đã mở index có kiểm chứng (B03 12 + B04 21). BLOCKED: B04 10 bài (bản nháp ở reports/seo-recovery/drafts/B04/), NH-00115, B06 (/bang-gia/ vs /theo-thang/). Nhóm C 2.985 + E 572 giữ noindex theo phân loại. Theo dõi GSC: trang tiền/trang chủ 'Crawled - currently not indexed' (crawl 29/10, trước nội dung mới); 6 hub + 9/10 bài B04 'URL is unknown to Google'.",
 "next_task": "Sau 7–14 ngày: kéo GSC (Windsor searchconsole + OpenSEO inspect, bind tạm thuha rồi trả về blog) cho 33 URL đã mở + 7 hub + trang tiền; cập nhật sheet GSC/Dashboard. Ứng viên lô sau: nhóm B còn lại (nếu có dữ liệu chính hãng mới), viết lại vòng 2 cho drafts/B04 nếu có thông số riêng từng mẫu, quyết định của chủ site về B06.",
 "open_errors": [
  "Trang tiền + trang chủ 'Crawled - currently not indexed' (GSC 29/10)",
  "cross-domain blog.rentbikehanoi.com cùng thương hiệu/NAP: NEEDS_REVIEW",
  "bảng giá quy tắc chung khác business-facts.json: NEEDS_REVIEW"
 ],
 "history": [
  {
   "ts": "2026-10-31T00:04:04+07:00",
   "done": [
    "HUB-01 PR #4 merge b69b1b5162, live 7/7",
    "B05 PR #5 merge 40e52b2e60, live: theo-ngay QA 95; ngày thật cho 73 bài viết tay; bot refresh 0 diff",
    "B06 BLOCKED (ghi changelog)"
   ]
  },
  {
   "ts": "2026-10-31T01:23:53+07:00",
   "done": [
    "B04: 31 bài viết lại theo sổ hướng dẫn chính hãng, kiểm chứng đối kháng (3 lỗi nặng + 30 nhẹ đã sửa); greedy QA 21 PASS / 10 BLOCKED; PR #6 squash 625c5bee22; PR #7 đồng bộ ngày 57fd310780; live 21/21 index-eligible + sitemap, 10/10 BLOCKED noindex"
   ]
  }
 ]
}
```
