# Báo cáo SEO recovery thuha.rentbikehanoi.com

Cập nhật 2026-10-31 14:37 (giờ Hà Nội). Sinh tự động từ `reports/seo-recovery/data/` bằng `scripts/seo_recovery_report.py`.

> INDEX_ELIGIBLE (trang cho phép index, có trong sitemap) **không** đồng nghĩa INDEXED trên Google. Trạng thái Google chỉ lấy từ Search Console; URL chưa kiểm tra ghi NOT_VERIFIED.

## 1. Tổng quan trước / sau

| Chỉ số | Giá trị |
|---|---|
| URL render (kiểm kê đầu dự án) | 5048 |
|   trong đó noindex lúc audit | 3747 |
|   index-eligible lúc audit | 1301 |
| URL đã xoá trước dự án (10/10/2026, 404) | 142 |
| Bài V1 đã mở index có kiểm chứng | 33 |
| URL còn trong config/factory-noindex.json | 0 |


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


### URL từng BLOCKED (phân loại 30/10): 3567, nay đã mở index theo quyết định chủ site 31/10 (xem mục 9)

Lý do phân loại cũ:

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
| sau mở index 31/10 | T08: Hub /xe-dap/ trở lại menu toàn site nhưng không có nội dung giới thiệu biên tập (content/hubs.json không có mục xe-dap) | 10 | OWNER_DECISION |  |
| sau mở index 31/10 | T09: 121/242 bài V1 trong hub xe-dap có tiêu đề/H1 về bộ phận hoặc loại xe máy (bugi, dây curoa, nhớt, nước làm mát, kim phun, xe ga) | 121 | OWNER_DECISION |  |
| sau mở index 31/10 | T11: Trùng title/meta description trong 4.857 URL sitemap: 147 cặp title (294 URL), 246 cặp description (492 URL), nhóm lớn nhất 2 URL | 492 | OWNER_DECISION |  |
| sau mở index 31/10 | T14: Chỉ mục chatbot/tìm kiếm (giới hạn 2.500) loại 20/33 bài V1 đã viết lại + kiểm chứng nhưng giữ 1.240 bài V1 chưa kiểm chứng | 20 | OPEN |  |
| sau mở index 31/10 | T12: assets/search-index.json tăng từ 5,78MB lên 14,4MB (gzip 2,49MB) sau mở index; site.js chỉ chờ tải 8 giây | 2500 | OPEN |  |
| sau mở index 31/10 | T06: 3.406/3.567 bài V1 mới mở có <title> > 65 ký tự (54/60 trong mẫu live) | 3406 | OPEN |  |
| sau mở index 31/10 | T10: 21/27 mục menu con dạng /hub/#muc-N có nhãn không khớp H2 của section đích (menu hiện trên 4.857 trang) | 6 | OPEN |  |
| sau mở index 31/10 | T02: lastmod của sitemap.xml (index) không đổi dù sitemap-posts.xml tăng 1.202 → 4.769 URL | 3567 | OPEN |  |
| sau mở index 31/10 | T03: 190 trang phân trang chuyên mục (144 trang trước đây noindex) nay index được, không có trong sitemap, description trùng trong cùng hub | 190 | OPEN |  |
| nội dung (sau mở index) | 3.566/3.567 bài V1 có bài V1 khác tương đồng TF-IDF ≥0,60 (trung vị 0,818); 2.624 bài ≥0,80; 89 cụm ≥0,86 (199 URL). Trung vị 77,6% ký tự mỗi bài là câu lặp ở ≥20 bài. | 3566 | OWNER_DECISION |  |
| nội dung (sau mở index) | 572 bài BO (chủ site duyệt bỏ 10/10) nay được index; 552 bài có hướng dẫn kỹ thuật sai loại xe (bugi/nhớt/curoa cho xe đạp, xe điện). | 572 | OWNER_DECISION |  |
| business facts (sau mở index) | Câu khung sai sự thật trên bài V1: giờ 09:00–21:00, tốc độ 50cc, 50cc đòi GPLX, giá sai loại xe, cam kết bảo hiểm/đổi xe/hoàn cọc/24/7, xe đạp điện phạt như xe cơ giới. | 2835 | DONE | ea3d59d7fc (PR #10) |


## 6. Changelog và QA

- Changelog: 98 dòng (sheet 09).
- QA: 89 lượt; PASS 78, FAIL 11 (sheet 10).


## 7. GSC

- Tổng 05–27/10/2026: 93 click, 3123 hiển thị (Windsor.ai).

| URL Inspection 30/10 (50 URL mẫu) | Số URL |
|---|---|
| Crawled - currently not indexed | 23 |
| Discovered - currently not indexed | 2 |
| Submitted and indexed | 11 |
| URL is unknown to Google | 14 |


## 8. Mở index toàn bộ (31/10/2026) và kiểm tra sau mở

Quyết định chủ site: “Giờ mở hết index ra rồi làm bước tiếp theo kiểm 😅 index toàn bộ”.

| Hạng mục | Kết quả |
|---|---|
| PR mở index | #9 (b7de944439) |
| Trang noindex trước / sau | 3713 / 2 (/o-to/, /404.html) |
| URL sitemap trước / sau | 1289 / 4857 |
| Kiểm tra live | 4.857/4.857 HTTP 200, không noindex, canonical tự trỏ (live_crawl_after_open_index_2026-10-31.json) |
| GSC mẫu | 10 URL mới mở: 9 "URL is unknown to Google", 1 "Excluded by noindex" (crawl 12/10, trước khi mở) — NOT_VERIFIED cho tới khi Google crawl lại |
| Kiểm tra rủi ro | 9 agent: 4 kiểm toán (legal, facts, cannibal, technical) + 4 kiểm chứng đối kháng + 1 rà soát độ phủ |
| B07 sửa sự thật | #10 (ea3d59d7fc): 2835 URL, 31 quy tắc |
| Lỗi facts seo_qa trên V1 trước / sau B07 | 2377 / 181 URL (181 URL chỉ còn nhắc bảo hiểm TNDS trong ngữ cảnh luật (OD-6)) |
| Kiểm tra B07 | title/canonical/robots/description/H1/H2 không đổi trên 2.835 trang; 91/91 URL mẫu (3 URL/quy tắc) đạt trên production |


### Phát hiện và trạng thái

| Mảng | ID | Mức | URL | Phát hiện | Kiểm chứng | Trạng thái |
|---|---|---|---|---|---|---|
| legal | LEGAL-50CC-TOC-DO | critical | 83 | Bài xe 50cc khuyên chạy 40–50 km/h hoặc 35–45 km/h, vượt mức tối đa 40 km/h của xe gắn máy | confirmed | FIXED_B07 |
| legal | LEGAL-A2-175CC | critical | 13 | 13 bài trình bày 'bằng lái A2 cho mô tô trên 175cc' như quy định hiện hành, dù hạng A2 đã bị bỏ từ 01/01/2025 | confirmed | OWNER_DECISION |
| legal | LEGAL-50CC-GPLX | high | 126 | Bài xe 50cc ghi người lái phải có giấy phép lái xe, trái Luật 36/2024 và business-facts | confirmed | FIXED_B07 |
| legal | LEGAL-XEMLAI-24 | high | 24 | 24 bài XEM_LAI (chờ rà pháp lý) nay đã index mà chưa được rà lại; 12 bài có câu sai đối chiếu được | confirmed | OWNER_DECISION |
| legal | LEGAL-XE-DAP-DIEN-PHAT | medium | 116 | Câu khung 'xe đạp điện chịu mức phạt tương đương xe cơ giới' sai so với NĐ 168 Điều 9 | confirmed | FIXED_B07 |
| legal | LEGAL-KHONG-CAN-CU-CHU-DE | medium | 291 | Bài luật V1 hứa 'căn cứ pháp lý mới nhất' và 'mức phạt' nhưng không trích Điều/khoản, hoặc không nêu mức phạt của chính lỗi trong chủ đề | confirmed | OPEN |
| legal | LEGAL-NONG-DO-CON-CHUA-KC | medium | 88 | Mức phạt nồng độ cồn (8–10 triệu, tước bằng 22–24 tháng; mức thấp nhất 2–3 triệu): chưa kiểm chứng | partially_wrong | OPEN |
| legal | LEGAL-TRU-DIEM-CHUA-KC | medium | 224 | Số điểm bằng lái bị trừ (4 điểm vượt đèn đỏ hoặc dùng điện thoại; 2 điểm ngược chiều hoặc đi vỉa hè): chưa kiểm chứng | partially_wrong | OPEN |
| legal | LEGAL-TNDS-CHUA-KC | medium | 96 | Mức phạt thiếu bảo hiểm TNDS (200.000–300.000đ): chưa kiểm chứng, và trái quy tắc 'không nêu bảo hiểm' của business-facts | partially_wrong | OWNER_DECISION |
| legal | LEGAL-MUC-PHAT-KHOP | low | 224 | Mức phạt đã khớp NĐ 168 (vượt đèn đỏ, ngược chiều, đi vỉa hè, dùng điện thoại): không cần sửa phần tiền | count_wrong | PASS |
| legal | LEGAL-VB-HET-HIEU-LUC | low | 0 | Không bài V1 nào dẫn văn bản đã hết hiệu lực theo số hiệu | confirmed | PASS |
| legal | LEGAL-XE-DIEN-PHAN-LOAI-CHUA-KC | low | 200 | Bài xe điện VinFast ghi 'giấy phép lái xe phù hợp với phân khối' hoặc khuyên chạy 40–50 km/h, trong khi chưa xác định xe là xe gắn máy hay xe mô tô | count_wrong | OPEN |
| legal | LEGAL-DANG-KIEM-XE-MAY-CHUA-KC | low | 231 | Câu khung ngụ ý xe máy bị 'từ chối đăng kiểm' vì phạt nguội: chưa kiểm chứng | not_checked | OPEN |
| legal | LEGAL-CHO-2-NGUOI-CHUA-KC | low | 93 | Ngoại lệ được chở 2 người (trẻ em dưới 12 tuổi, người già yếu, người khuyết tật): chưa kiểm chứng | not_checked | OPEN |
| legal | LEGAL-DIEU-89-CHUA-KC | low | 13 | Điều khoản chuyển tiếp 'giấy phép cấp trước 01/01/2025 tiếp tục sử dụng theo Điều 89' trong 13 bài A2: chưa kiểm chứng | not_checked | OPEN |
| facts | F01_hours | critical | 1584 | Giờ mở cửa sai 09:00–21:00 trong khối liên hệ thân bài (mâu thuẫn với template 08:00–17:00 trên cùng trang) | confirmed | FIXED_B07 |
| facts | F03_price_tier | high | 490 | Bảng giá sai loại xe: bài xe điện VinFast và xe 50cc dùng giá xe số | confirmed | FIXED_B07 |
| facts | F04_con_tay | high | 474 | Bài về xe côn tay (Winner X, Exciter) khẳng định cửa hàng cho thuê và niêm yết giá, trong khi cửa hàng không cho thuê côn tay | confirmed | OWNER_DECISION |
| facts | F02_damage | high | 715 | Cam kết sửa xe và đổi xe trái business-facts ("chịu toàn bộ chi phí", "đổi xe mới trong vòng 2 giờ", "đổi xe ngay trong ngày") | confirmed | FIXED_B07 |
| facts | F08_insurance_store | high | 619 | Cửa hàng cam kết hoặc ngụ ý xe thuê có bảo hiểm (business-facts: không nêu bảo hiểm) | partially_wrong | FIXED_B07 |
| facts | F05_out_of_hanoi | high | 640 | Bài phượt ra ngoài Hà Nội khuyên dùng giá tuần và không nêu điều kiện thuê từ 48 giờ | partially_wrong | PARTIAL_B07 (F05a 307 URL đã sửa; câu thiếu điều kiện 48 giờ còn lại) |
| facts | F12_rental_conditions_50cc | high | 82 | Điều kiện thuê xe 50cc sai: đòi giấy phép lái xe (business-facts: không yêu cầu bằng A1, nhận khách từ 18 tuổi) | confirmed | FIXED_B07 |
| facts | F07_deposit_refund | medium | 719 | Cam kết hoàn cọc "ngay lập tức" mà không nêu khấu trừ | confirmed | FIXED_B07 |
| facts | F06_delivery | medium | 1057 | Giao xe tận nơi không nêu điều kiện hợp đồng, phí 50.000đ/lượt và bán kính 10 km | partially_wrong | PARTIAL_B07 (F06a 626 URL đã sửa; câu giao theo quận chờ chủ site xác nhận bán kính) |
| facts | F10_247 | medium | 686 | Cụm "24/7" (bị BANNED chặn; dễ hiểu là phục vụ 24/7) | confirmed | FIXED_B07 |
| facts | F13_unsupported_amount | medium | 402 | Con số tiết kiệm "từ một đến hai triệu đồng mỗi tháng" không có trong business-facts và không có nguồn (seo_qa không bắt vì viết bằng chữ) | confirmed | FIXED_B07 |
| facts | F15_fleet_vinfast | medium | 684 | Bài mời thuê xe điện VinFast (Evo 200, Feliz S, Klara S) trong khi business-facts chỉ xác nhận xe điện Tailg | confirmed | OWNER_DECISION |
| facts | F05c_daytrip_vs_48h | medium | 135 | Kịch bản "đi về trong ngày" ra ngoài Hà Nội kèm lời mời thuê xe, trái điều kiện thuê từ 48 giờ | not_checked | OPEN |
| facts | F11_airport_false_positive | low | 493 | Câu về sân bay Nội Bài ĐÚNG với business-facts nhưng regex BANNED của seo_qa.py bắt nhầm | not_checked | FIXED_B07 |
| facts | F09_insurance_legal | low | 182 | Nhắc bảo hiểm TNDS bắt buộc trong ngữ cảnh pháp luật (không phải cam kết của cửa hàng) nhưng bị BANNED chặn | not_checked | OWNER_DECISION |
| facts | F12_rental_conditions_incomplete | low | 461 | Thủ tục thuê ghi "chỉ cần" giấy tờ, bỏ sót điều kiện từ 20 tuổi; "không giữ giấy tờ tùy thân" ghi vô điều kiện | not_checked | FIXED_B07 |
| facts | F14_superlative | low | 488 | Khẳng định "mức giá cạnh tranh hàng đầu thị trường" không có trong business-facts | not_checked | PARTIAL_B07 (77 bài côn tay chờ quyết định F04) |
| cannibal | CANN-07 | high | 880 | Anchor "bảng giá thuê xe máy theo tháng" trong 534 bài V1 trỏ /bang-gia/, trong khi GSC owner của "giá thuê xe máy theo tháng" là /thue-xe-may/ha-noi/ | confirmed | OPEN |
| cannibal | CANN-11 | high | 265 | 345 bài luật V1 mới index trùng chủ đề với bài luật viết tay đang có hiển thị GSC: 265 bài ≥0,5 (0 bài ≥0,6); 24 bài XEM_LAI (khung luật cũ) nay cũng  | partially_wrong | OWNER_DECISION |
| cannibal | CANN-03 | medium | 246 | Cụm "thuê xe máy long biên" / "thuê xe máy phố cổ/hoàn kiếm": 246 bài V1 theo quận cạnh tranh với 2 trang tiền quận | confirmed | OPEN |
| cannibal | CANN-04 | medium | 1224 | 10 quận KHÔNG có trang tiền riêng, chỉ có bài V1 nhắm "thuê <mẫu xe> <quận>": 1.224 bài (cơ hội, chưa có số liệu nhu cầu) | confirmed | OWNER_DECISION |
| cannibal | CANN-05 | medium | 328 | Cụm "thuê xe máy theo tháng": 328 bài V1 có "thuê theo tháng"/"thuê dài hạn" trong title/kw1, cạnh tranh /thue-xe-may/ha-noi/theo-thang/ | count_wrong | OPEN |
| cannibal | CANN-06 | medium | 146 | 146 bài V1 "thuê theo tuần": 130 bài được template gắn link "Thuê xe máy theo tháng Hà Nội", 60 bài không có link về /thue-xe-may/ha-noi/theo-ngay/ | partially_wrong | OPEN |
| cannibal | CANN-08 | medium | 122 | 122 bài V1 /thue-xe/<quận>/xe-may-50cc/ có H2 chứa nguyên cụm "thuê xe máy 50cc" — cạnh tranh /thue-xe-50cc/ha-noi/ và /thue-xe-50cc/ha-noi/kinh-nghie | confirmed | OWNER_DECISION |
| cannibal | CANN-09 | medium | 368 | 368 bài V1 /xe-dien/<quận>/vinfast-*/ nhắm "thuê xe điện VinFast <quận>" — cạnh tranh /thue-xe-dien/ha-noi/; mẫu xe không có trong fleet của business- | confirmed | OWNER_DECISION |
| cannibal | CANN-12 | medium | 1 | Bài V1 luật 50cc/xe điện đã viết lại (B03) nhưng không có trong factory-reindex: sim 0,597 với /luat-giao-thong/xe-50cc-co-can-bang-lai/ (351 hiển thị | confirmed | OPEN |
| cannibal | CANN-10 | low | 147 | Cụm "giá thuê xe máy": 147 bài V1 có "chi phí"/"giá thuê" trong title (intent thuê xe) — cạnh tranh nhẹ với /bang-gia/ | confirmed | MONITOR |
| cannibal | CANN-13 | low | 5 | 5 bài V1 Honda Vision theo quận ≥0,5 với bài viết tay /xe-may/honda/vision/chon-xe-thue/ | confirmed | OPEN |
| cannibal | CANN-14 | low | 245 | 245 bài V1 intent thuê xe theo quận cho xe côn tay (Honda Winner X, Yamaha Exciter) — cửa hàng không cho thuê côn tay | confirmed | OWNER_DECISION |
| cannibal | CANN-15 | low | 68 | Chưa có dữ liệu GSC sau khi mở index (31/10/2026): file cannibalization không có URL V1 nào | not_checked | NOT_VERIFIED |
| cannibal | CANN-01 | low | 0 | TF-IDF (seo_qa.Uniq) giữa 3.567 V1 và 9 trang tiền: 0 bài ≥0,6, 0 bài ≥0,5 | not_checked | PASS |
| cannibal | CANN-02 | low | 1 | Tương đồng V1 với 7 hub: 0 bài ≥0,6; 1 bài ≥0,5 (hub /luat-giao-thong/) | not_checked | PASS |
| technical | T08 | high | 10 | Hub /xe-dap/ trở lại menu toàn site nhưng không có nội dung giới thiệu biên tập (content/hubs.json không có mục xe-dap) | confirmed | OWNER_DECISION |
| technical | T09 | high | 121 | 121/242 bài V1 trong hub xe-dap có tiêu đề/H1 về bộ phận hoặc loại xe máy (bugi, dây curoa, nhớt, nước làm mát, kim phun, xe ga) | confirmed | OWNER_DECISION |
| technical | T11 | medium | 492 | Trùng title/meta description trong 4.857 URL sitemap: 147 cặp title (294 URL), 246 cặp description (492 URL), nhóm lớn nhất 2 URL | confirmed | OWNER_DECISION |
| technical | T14 | medium | 20 | Chỉ mục chatbot/tìm kiếm (giới hạn 2.500) loại 20/33 bài V1 đã viết lại + kiểm chứng nhưng giữ 1.240 bài V1 chưa kiểm chứng | confirmed | OPEN |
| technical | T12 | medium | 2500 | assets/search-index.json tăng từ 5,78MB lên 14,4MB (gzip 2,49MB) sau mở index; site.js chỉ chờ tải 8 giây | confirmed | OPEN |
| technical | T06 | medium | 3406 | 3.406/3.567 bài V1 mới mở có <title> > 65 ký tự (54/60 trong mẫu live) | partially_wrong | OPEN |
| technical | T10 | medium | 6 | 21/27 mục menu con dạng /hub/#muc-N có nhãn không khớp H2 của section đích (menu hiện trên 4.857 trang) | confirmed | OPEN |
| technical | T02 | low | 3567 | lastmod của sitemap.xml (index) không đổi dù sitemap-posts.xml tăng 1.202 → 4.769 URL | confirmed | OPEN |
| technical | T03 | low | 190 | 190 trang phân trang chuyên mục (144 trang trước đây noindex) nay index được, không có trong sitemap, description trùng trong cùng hub | confirmed | OPEN |
| technical | T01 | low | 4857 | ĐẠT: robots.txt + sitemap.xml/sitemap-pages.xml/sitemap-posts.xml hợp lệ; 4.857/4.857 URL live 200, không redirect, không noindex | confirmed | PASS |
| technical | T04 | low | 2 | ĐẠT: /o-to/ và /404.html vẫn noindex,follow và không có trong sitemap | confirmed | PASS |
| technical | T05 | low | 60 | ĐẠT (trừ độ dài title): mẫu 60 bài V1 mới mở, 10 bài/hub rải đều | confirmed | PASS |
| technical | T07 | low | 4857 | ĐẠT: quét toàn bộ 4.857 trang sitemap (HTML repo) — description, H1, JSON-LD, FAQPage | not_checked | PASS |
| technical | T13 | low | 1 | ĐẠT: assets/navigation.json 5.463 byte (gzip 1.226) | not_checked | PASS |


### Rủi ro do bước rà soát độ phủ bổ sung

| URL | Rủi ro |
|---|---|
| 3566 | Không kiểm toán nào đo nội dung trùng lặp hoặc mỏng giữa các bài V1 với nhau. Tôi đã tự kiểm, và đây là rủi ro lớn nhất: gần như toàn bộ V1 vượt ngưỡng trùng lặp mà chính seo_qa.py coi là lỗi critical. |
| 688 | Thông tin kỹ thuật bảo dưỡng sai loại xe ngoài hub xe-dap. T09 chỉ đếm 121 title xe đạp. Hub xe-dien, hub xe-may và thân bài chưa được kiểm. Tôi đã tự kiểm. |
| 572 | Mở index toàn bộ đã đảo ngược quyết định BO mà chủ site duyệt ngày 10/10/2026. Không kiểm toán nào nêu nhóm này thành một phát hiện riêng. |
| 766 | Ngôn ngữ máy và lỗi ghép khuôn trong title và thân bài. T06 chỉ đo độ dài title; chất lượng câu chữ chưa được kiểm. |
| 3567 | Hình ảnh và E-E-A-T: V1 không có ảnh nội dung, và schema gán tác giả cá nhân cho 3.567 bài máy sinh, kể cả bài luật YMYL chưa kiểm chứng. |
| 3567 | Ngân sách crawl và đánh giá chất lượng toàn site: chưa có số liệu sau khi mở index. Ngay trước khi mở, Google đã không index hầu hết trang tiền. |
| 4857 | IndexNow có thể đẩy toàn bộ sitemap, gồm cả V1 đang sai sự thật, lên Bing/Yandex. Chưa rõ đã gửi hay chưa. Riêng Facebook đã kiểm và không có rủi ro. |
| 0 | Đầu vào của bước phản biện bị cắt. Tôi không nhận được phán quyết đối kháng cho 3 kiểm toán facts, cannibal và technical. |


### Cần chủ site quyết định

| ID | Ưu tiên | URL | Câu hỏi | Bằng chứng |
|---|---|---|---|---|
| OD-1 | P0 | 608 | Gắn lại noindex,follow cho 572 bài BO (nội dung sai loại xe: bugi, nhớt, curoa cho xe đạp/xe điện; chủ site đã duyệt bỏ ngày 10/10), 24 bài luật XEM_LAI và 13 bài bằng A2/175cc? Đảo ngược được, không đổi URL, không redirect. | v1_wrong_vehicle_maintenance.csv; legal_findings.jsonl (LEGAL-XEMLAI-24, LEGAL-A2-175CC) |
| OD-2 | P0 | 474 | Bài xe côn tay (Winner X, Exciter) nói cửa hàng cho thuê và niêm yết giá, trong khi cửa hàng không cho thuê côn tay. Chọn: (a) noindex; (b) bỏ câu giá và lời mời thuê, giữ bài thông tin; (c) cập nhật business-facts nếu sắp cho thuê. | facts F04_con_tay; CANN-14 |
| OD-3 | P1 | 684 | Cửa hàng có cho thuê VinFast Klara S / Feliz S / Evo 200 không? business-facts chỉ xác nhận xe máy điện Tailg. Nếu không: bỏ lời mời thuê hoặc noindex 368 bài thuê VinFast theo quận. | F15_fleet_vinfast; CANN-09 |
| OD-4 | P1 | 2731 | Khối trùng lặp: 3.566/3.567 bài V1 có bài V1 khác tương đồng ≥0,60 (trung vị 0,818), 89 cụm ≥0,86 (199 URL). Chọn theo cụm: giữ index, gộp vào URL giữ lại, canonical nội bộ hay noindex theo lô. Không xoá, không redirect khi chưa duyệt. | v1_duplicates.csv (cột max_sim_v1_v1) |
| OD-5 | P1 | 940 | Giao xe tận nơi theo quận: quận nào nằm ngoài bán kính 10 km từ trung tâm Hoàn Kiếm (không giao)? | facts F06b/F06c |
| OD-6 | P1 | 181 | Bài luật có được nhắc bảo hiểm TNDS bắt buộc (mức phạt 200–300 nghìn, NĐ 168 Điều 18) không? business-facts hiện cấm nhắc bảo hiểm trong bài. | F09_insurance_legal; LEGAL-TNDS-CHUA-KC |
| OD-7 | P2 | 3 | B06: vai trò /bang-gia/ và /thue-xe-may/ha-noi/theo-thang/ cho cụm "giá thuê xe máy theo tháng" (534 bài V1 đang trỏ anchor này về /bang-gia/). | CANN-07; gsc_cannibalization |
| OD-8 | P2 | 10 | Hub /xe-dap/ đang hiện trên menu toàn site nhưng cửa hàng không cho thuê xe đạp: giữ hub (viết phần giới thiệu) hay ẩn khỏi menu? | T08, T09 |
| OD-9 | P2 | 3567 | Đổi tác giả JSON-LD của bài V1 từ Person "Nguyễn Hà" sang Organization (chỉ bài đã kiểm chứng mang tên người)? | critic: E-E-A-T |


- Không gửi IndexNow (scripts/indexnow.py chỉ chạy tay; chưa chạy).
- Không gửi yêu cầu index hàng loạt; Google tự crawl qua sitemap.
- Các mục OPEN/OWNER_DECISION ở trên chưa sửa.


## 9. Checkpoint

```json
{
 "batch_id": "OPEN-ALL + B07 hoàn tất (PR #9, #10)",
 "updated": "2026-10-31T15:30:00+07:00",
 "commit_sha": "ea3d59d7fc (main, merge PR #10); b7de944439 (merge PR #9)",
 "state": "Toàn bộ bài index-eligible theo quyết định chủ site 31/10 (4.857 URL sitemap; chỉ /o-to/ và 404 noindex). INDEX_ELIGIBLE ≠ INDEXED: GSC chưa crawl lại (NOT_VERIFIED).",
 "done": [
  "PR #9 mở index toàn bộ; live 4.857/4.857 OK",
  "Audit rủi ro sau mở index (9 agent, kiểm chứng đối kháng)",
  "B07: sửa 2.835 bài V1 theo business-facts (lỗi facts 2.377 → 181 URL); live 91/91 OK"
 ],
 "owner_decisions_pending": [
  "OD-1: Gắn lại noindex,follow cho 572 bài BO (nội dung sai loại xe: bugi, nhớt, curoa cho xe đạp/xe điện; chủ site đã duyệt bỏ ngày 10/10), 24 bài ",
  "OD-2: Bài xe côn tay (Winner X, Exciter) nói cửa hàng cho thuê và niêm yết giá, trong khi cửa hàng không cho thuê côn tay. Chọn: (a) noindex; (b) ",
  "OD-3: Cửa hàng có cho thuê VinFast Klara S / Feliz S / Evo 200 không? business-facts chỉ xác nhận xe máy điện Tailg. Nếu không: bỏ lời mời thuê ho",
  "OD-4: Khối trùng lặp: 3.566/3.567 bài V1 có bài V1 khác tương đồng ≥0,60 (trung vị 0,818), 89 cụm ≥0,86 (199 URL). Chọn theo cụm: giữ index, gộp v",
  "OD-5: Giao xe tận nơi theo quận: quận nào nằm ngoài bán kính 10 km từ trung tâm Hoàn Kiếm (không giao)?",
  "OD-6: Bài luật có được nhắc bảo hiểm TNDS bắt buộc (mức phạt 200–300 nghìn, NĐ 168 Điều 18) không? business-facts hiện cấm nhắc bảo hiểm trong bài",
  "OD-7: B06: vai trò /bang-gia/ và /thue-xe-may/ha-noi/theo-thang/ cho cụm \"giá thuê xe máy theo tháng\" (534 bài V1 đang trỏ anchor này về /bang-gia",
  "OD-8: Hub /xe-dap/ đang hiện trên menu toàn site nhưng cửa hàng không cho thuê xe đạp: giữ hub (viết phần giới thiệu) hay ẩn khỏi menu?",
  "OD-9: Đổi tác giả JSON-LD của bài V1 từ Person \"Nguyễn Hà\" sang Organization (chỉ bài đã kiểm chứng mang tên người)?"
 ],
 "next_auto": [
  "P1 luật chưa kiểm chứng: bỏ vế 'trừ 2 điểm' (173 URL), vế cồn 8–10 triệu/tước 22–24 tháng nếu không có nguồn (88 URL), câu tốc độ/GPLX bài VinFast (284 URL)",
  "P2: anchor 'bảng giá thuê xe máy theo tháng' sau khi chốt OD-7; lỗi 'xe xe' (766 URL) theo từng khung câu",
  "~14/11/2026: kéo GSC (URL Inspection trang chủ + 9 trang tiền; Pages report V1 vs không V1); nếu trang tiền vẫn không index thì đề xuất noindex V1 theo lô"
 ],
 "do_not": [
  "Không chạy scripts/indexnow.py --send khi chưa xử lý OD-1/OD-2",
  "Không yêu cầu index hàng loạt",
  "Không xoá, không redirect, không đổi URL/title khi chưa duyệt"
 ],
 "blocked": [],
 "failed_qa": []
}
```
