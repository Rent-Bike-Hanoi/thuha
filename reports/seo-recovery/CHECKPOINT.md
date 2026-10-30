# CHECKPOINT – SEO recovery thuha.rentbikehanoi.com

Cập nhật 2026-10-31 00:04. Phiên sau đọc file này trước, rồi `reports/seo-recovery/data/checkpoint.json`.

## Trạng thái

```json
{
 "batch_id": "B04 (đang viết) — đã xong HUB-01 (PR #4), B05 (PR #5)",
 "updated": "2026-10-31T00:04:04+07:00",
 "commit_sha": "40e52b2e60 (merge PR #5, main); nhánh làm việc claude/seo-recovery-2026-10-30",
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
  "/xe-may/xe-tay-ga-honda-air-blade/kiem-tra-nuoc-lam-mat-tai-xe-cong-nghe-chay-xe-lien-tuc-moc-bao-duong-dinh-ky-5000-km-dau-hieu-can-kiem-tra/",
  "/xe-may/xe-tay-ga-honda-air-blade/thay-nhot-hop-so-lap-nguoi-moi-mua-xe-lan-dau-nhung-ngay-nang-nong-dinh-diem-sai-lam-pho-bien/",
  "/xe-may/xe-tay-ga-honda-vision/can-chinh-co-phot-nguoi-moi-mua-xe-lan-dau-nhung-ngay-nang-nong-dinh-diem-chi-phi-thuc-te/"
 ],
 "remaining": "B04: 31 bài thông số mẫu xe — Lead 7 + Vision 6 đã viết (greedy QA thử: 10 PASS, 3 Lead trùng Vision cần viết lại vòng 2); Air Blade 5, Winner X 5, Wave 4, Sirius 4 đang viết. B06 (/bang-gia/ vs /theo-thang/ trùng 0,74–0,77) BLOCKED chờ chủ site quyết định phân vai. NH-00115 BLOCKED. 3.588 bài V1 còn noindex theo phân loại.",
 "next_task": "Khi workflow B04 xong: chạy seo_recover_batch.py --greedy theo thứ tự Vision, Air Blade, Wave Alpha, Sirius, Lead, Winner X; viết lại vòng 2 các bài trùng; bài vẫn trùng -> khôi phục bản gốc từ scratch originals + BLOCKED; commit nguồn -> build -> validate/test -> PR -> merge -> xác minh live -> GSC baseline -> matrix/report.",
 "open_errors": [
  "Trang tiền + trang chủ 'Crawled - currently not indexed' (GSC 29/10) — chờ Google crawl lại sau nội dung mới; không ép index",
  "6 hub 'URL is unknown to Google' — đã có trong sitemap + menu"
 ],
 "history": [
  {
   "ts": "2026-10-31T00:04:04+07:00",
   "done": [
    "HUB-01 PR #4 merge b69b1b5162, live 7/7",
    "B05 PR #5 merge 40e52b2e60, live: theo-ngay QA 95; ngày thật cho 73 bài viết tay; bot refresh 0 diff",
    "B06 BLOCKED (ghi changelog)"
   ]
  }
 ]
}
```

## Quy trình mỗi lô (không bỏ bước)

1. Chọn URL `action=REWRITE_THEN_INDEX, status=OPEN` trong `data/classification.csv` (ưu tiên P1 > P2 > P3).
2. Viết lại shard `content/articles/<ID>.json` giữ id/url/hub/parent/kind/art/tone/intent/factoryVersion; thêm `sources`, `rewrite{rewrittenAt,by,batch}`.
3. `python3 scripts/seo_recover_batch.py --batch <Bxx> <files>` (QA >= 85, chặn trùng >= 0,60, link tới bài noindex).
4. `python3 scripts/build.py && python3 scripts/validate_factory_site.py` + 4 bộ test + `topic_matrix.py validate` + `content_factory.py run --dry-run`.
5. Kiểm kê trước/sau (0 URL mất, 0 canonical đổi) → commit → PR → CI xanh → merge → kiểm tra live → `mcp OpenSEO inspect_urls` (bind tạm property thuha) → cập nhật data + `scripts/seo_matrix_export.py` + `scripts/seo_recovery_report.py`.

## Quy tắc bất biến

Không xoá bài, không đổi slug/URL/canonical/permalink/DNS/CNAME, không redirect hay noindex bài đang index tốt khi chưa có chủ site duyệt, không số liệu không nguồn, không ghi số GSC giả.
