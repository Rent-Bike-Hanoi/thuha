# Audit SEO thuha.rentbikehanoi.com (15/10/2026)

Nguồn: HarborRank crawl 500 trang (audit e766c839, Free plan, không Lighthouse), Google Search Console 11/7–11/10/2026, URL Inspection 8 URL, kiểm tra cục bộ toàn bộ 4.809 trang HTML đã build.

## Kết luận

**Không có lỗi critical hay warning về kỹ thuật** (0 link gãy, 0 lỗi server, 0 trùng title/description, 1 H1/trang). Vấn đề chính là **index**: Google mới index trang tiền; các bài V2 lấy mẫu đều "Đã phát hiện, chưa lập chỉ mục". Nguyên nhân khả dĩ nhất: site mới, ít uy tín, và **78% số trang (3.744/4.809) là bài V1 noindex vẫn được link từ menu và trang chuyên mục**, kéo crawl budget khỏi 1.028 trang cần index.

## 3 việc nên làm trước

1. **Ngừng dẫn Googlebot vào bài V1 noindex** (không xoá, không đổi URL): bỏ hub Xe đạp, Ô tô khỏi menu (2 hub này chỉ chứa bài noindex, menu có ở mọi trang); trang chuyên mục và phân trang chỉ liệt kê bài đang index (170/208 trang phân trang đang noindex). Cần chủ site duyệt vì đổi cấu trúc điều hướng.
2. **Đẩy /thue-xe-may/ha-noi/ cho "thuê xe máy hà nội"** (8.100 lượt/tháng, KD 7): trang đang ở vị trí 46 cho từ này, trong khi /thue-xe-may/ha-noi/theo-thang/ cũng xuất hiện (vị trí 21): Google đang lẫn 2 trang. Thêm link nội bộ anchor "thuê xe máy Hà Nội" từ trang chủ và trang theo tháng về trang chính; giữ trang theo tháng tập trung "theo tháng".
3. **Tăng tín hiệu uy tín bên ngoài**: hồ sơ Google Business đã có (trỏ rentbikehanoi.com); backlink thật từ blog du lịch, homestay, đối tác (mục 9 kế hoạch SEO). Không có tín hiệu này, Google sẽ index chậm 1.000 bài.

## Bảng vấn đề

| Ưu tiên | Vấn đề | Trang bị ảnh hưởng | Bằng chứng | Cách sửa | Công sức |
|---|---|---|---|---|---|
| 1 | Bài V2 chưa được index | ~1.000 bài | URL Inspection: 5/5 bài V2 lấy mẫu "Discovered – currently not indexed"; trang tiền "Submitted and indexed" (crawl 10/10) | Mục 1, 3 ở trên; theo dõi tỷ lệ index ở mốc tuần 4 (~07/11) | project |
| 1 | Crawl budget vào trang noindex | 3.744 trang noindex; 2.676 link từ trang index | Crawl 500 trang: 253 noindex (51%); menu mọi trang link /xe-dap/, /o-to/ (noindex); hub xe-may/trang-2…5 link 63–84 bài noindex mỗi trang | Bỏ 2 hub khỏi menu; hub chỉ liệt kê bài index | moderate |
| 2 | Trang tiền chưa lên top cho từ khoá chính | /thue-xe-may/ha-noi/ | GSC: "thuê xe máy hà nội" vị trí 46 (2 lần hiển thị); 29 lần hiển thị cả trang, vị trí TB 10,1, 0 click | Link nội bộ anchor chính xác; không đổi title (đã chứa từ khoá) | quick |
| 2 | Hai trang cùng nhắm "thuê xe máy hà nội" | /thue-xe-may/ha-noi/, /thue-xe-may/ha-noi/theo-thang/ | GSC: cả hai hiển thị cho "thuê xe máy hà nội", "thuê xe máy hà nội giá", "thuê xe máy theo ngày" | Trang theo tháng link về trang chính bằng anchor "thuê xe máy Hà Nội" | quick |
| 3 | Title dài | 1.011/1.028 trang > 65 ký tự | Đuôi " \| Thuê xe máy Nguyễn Hà" (24 ký tự) bị cắt trên Google | Bỏ đuôi thương hiệu khi title đã > 45 ký tự (đổi template, cần chủ site duyệt vì quy tắc không đổi title hàng loạt) | quick |
| 3 | Meta description dài | 745/1.028 > 160 ký tự | Kiểm tra cục bộ; crawl: 385 | Rút excerpt khi build (cắt ở câu gần 155 ký tự) | quick |
| 4 | Trang nằm sâu | 11 bài du lịch ở độ sâu 5 | Crawl: deep-page | Đã cải thiện bằng bài liên quan; thêm danh sách "mới cập nhật" ở hub | quick |
| 4 | Thứ tự heading nhảy cấp | /xe-dap/ và 9 trang phân trang | Crawl: heading-order-skip | Tự hết nếu bỏ hub Xe đạp khỏi điều hướng | quick |

## Không kiểm tra

Lighthouse/tốc độ (Free plan bỏ qua); 4.309 trang ngoài 500 trang crawl (đã bù bằng kiểm tra cục bộ toàn bộ HTML); tỷ lệ index toàn site (Search Console không trả báo cáo coverage qua API, chỉ kiểm từng URL).

## Workflow tiếp theo

`keyword-clustering` cho nhóm truy vấn "thuê xe máy hà nội / giá / theo ngày / theo tháng" để chốt mỗi truy vấn thuộc trang nào, bắt đầu từ bảng query × page của Search Console ở trên.
