# CHECKPOINT – SEO recovery thuha.rentbikehanoi.com

Cập nhật 2026-10-30 23:03. Phiên sau đọc file này trước, rồi `reports/seo-recovery/data/checkpoint.json`.

## Trạng thái

```json
{
 "batch_id": "B01-P0+B02-infra",
 "updated": "2026-10-30T18:25:42+07:00",
 "commit_sha": "9937fccc45 (branch) / 8df6269c1a (main merge PR #2)",
 "completed_urls": [
  "/ (home content)",
  "site-wide title/meta/menu (5.048 trang)"
 ],
 "remaining": "B03: 13 bài V1 đang viết lại (4 agent); 124 bài B còn lại theo lô 40; hub content (7) đang viết; Excel generator đang dựng",
 "next_task": "Thu kết quả B03 -> seo_qa -> cập nhật factory-noindex/reindex -> build -> validate -> commit -> PR -> merge -> verify live -> inspect_urls; sau đó hubs.json tích hợp build.py",
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
