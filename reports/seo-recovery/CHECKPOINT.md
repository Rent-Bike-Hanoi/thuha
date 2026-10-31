# CHECKPOINT – SEO recovery thuha.rentbikehanoi.com

Cập nhật 2026-10-31 14:37. Phiên sau đọc file này trước, rồi `reports/seo-recovery/data/checkpoint.json`.

## Trạng thái

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

## Quy trình mỗi lô (không bỏ bước)

1. Chọn URL `action=REWRITE_THEN_INDEX, status=OPEN` trong `data/classification.csv` (ưu tiên P1 > P2 > P3).
2. Viết lại shard `content/articles/<ID>.json` giữ id/url/hub/parent/kind/art/tone/intent/factoryVersion; thêm `sources`, `rewrite{rewrittenAt,by,batch}`.
3. `python3 scripts/seo_recover_batch.py --batch <Bxx> <files>` (QA >= 85, chặn trùng >= 0,60, link tới bài noindex).
4. `python3 scripts/build.py && python3 scripts/validate_factory_site.py` + 4 bộ test + `topic_matrix.py validate` + `content_factory.py run --dry-run`.
5. Kiểm kê trước/sau (0 URL mất, 0 canonical đổi) → commit → PR → CI xanh → merge → kiểm tra live → `mcp OpenSEO inspect_urls` (bind tạm property thuha) → cập nhật data + `scripts/seo_matrix_export.py` + `scripts/seo_recovery_report.py`.

## Quy tắc bất biến

Không xoá bài, không đổi slug/URL/canonical/permalink/DNS/CNAME, không redirect hay noindex bài đang index tốt khi chưa có chủ site duyệt, không số liệu không nguồn, không ghi số GSC giả.
