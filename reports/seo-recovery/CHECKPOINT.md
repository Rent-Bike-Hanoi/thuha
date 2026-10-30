# CHECKPOINT – SEO recovery thuha.rentbikehanoi.com

Cập nhật 2026-10-30 23:13. Phiên sau đọc file này trước, rồi `reports/seo-recovery/data/checkpoint.json`.

## Trạng thái

```json
{
 "batch_id": "B03",
 "updated": "2026-10-30T23:13:52+07:00",
 "commit_sha": "795fcca86d (merge PR #3, main)",
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
 "remaining": "B04: 31 bài thông số theo mẫu xe (Vision 6, Lead 7, Air Blade 5, Winner X 5, Wave 4, Sirius 4) — dữ liệu sách hướng dẫn đã kiểm chứng ở scratch specs; hub content 7 trang đang viết; NH-00115 BLOCKED (đề xuất nâng cấp /luat-giao-thong/xe-50cc-co-can-bang-lai/)",
 "next_task": "Tích hợp content/hubs.json (sau khi workflow hub xong) -> lô B04 -> nâng cấp trang index có GSC hiển thị cao nhưng vị trí thấp (xe-50cc-co-can-bang-lai 351 hiển thị vị trí 62; xe-may-dien-di-duoc-bao-nhieu-km 148 / 67; xe-50cc-chay-duoc-bao-nhieu-km-h 124 / 57)",
 "open_errors": []
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
