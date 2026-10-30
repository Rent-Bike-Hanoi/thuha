from pathlib import Path
import json,html,re,xml.etree.ElementTree as ET
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parent.parent
S=json.loads((ROOT/'content/site.json').read_text())
FACTORY_CFG=json.loads((ROOT/'config/content-factory.json').read_text()) if (ROOT/'config/content-factory.json').exists() else {}
E=html.escape
# When true, factory articles (content/articles/ shards, not posts.json) are
# rendered noindex,follow and left out of the sitemap.  Default false = no change.
NOINDEX_FACTORY=bool(FACTORY_CFG.get('noindex_factory_articles',False))
# Per-article list (config/factory-noindex.json, from scripts/audit_factory.py):
# those factory articles are rendered noindex,follow and left out of the sitemap.
NOINDEX_LIST=set(json.loads((ROOT/'config/factory-noindex.json').read_text()).get('urls',[])) if (ROOT/'config/factory-noindex.json').exists() else set()
# Allowlist (config/factory-reindex.json, SEO recovery 10/2026): factory articles that were rewritten,
# passed scripts/seo_qa.py (>= 85, no critical) and may be indexed again even while the global
# noindex_factory_articles flag stays on for the rest of the V1 corpus.  URL unchanged.
REINDEX_LIST=set(json.loads((ROOT/'config/factory-reindex.json').read_text()).get('urls',[])) if (ROOT/'config/factory-reindex.json').exists() else set()
def is_factory(p): return str(p.get('_source','')).startswith('content/articles/')
def factory_version(p):
 try:return int(p.get('factoryVersion') or 1)
 except (TypeError,ValueError):return 1
# The global switch only covers the old template factory (factoryVersion < 2).  Topic Factory V2
# shards (scripts/factory_v2.py) are indexable unless listed in factory-noindex.json explicitly.
def factory_noindex(p): return is_factory(p) and p['url'] not in REINDEX_LIST and (p['url'] in NOINDEX_LIST or (NOINDEX_FACTORY and factory_version(p)<2))
HUBS=[
('thue-xe','Thuê xe','Bảng giá, thủ tục và lựa chọn xe cho từng hành trình.',['Thuê xe máy Hà Nội','Thuê xe 50cc','Thuê xe điện','Theo ngày, tuần, tháng']),
('xe-may','Xe máy','Tìm hiểu xe số, xe ga và các mẫu xe quen thuộc.',['Honda','Yamaha','Xe số & xe ga','Đánh giá & so sánh']),
('xe-dien','Xe điện','Pin, sạc và những điều cần biết khi sử dụng xe điện.',['Xe máy điện','Xe đạp điện','Pin & sạc','Đánh giá & so sánh']),
('xe-dap','Xe đạp','Chọn xe và chuẩn bị cho những chuyến đi bằng sức mình.',['Xe phổ thông','Xe thể thao','Xe địa hình','Bảo dưỡng']),
('o-to','Ô tô','Kiến thức lựa chọn và sử dụng ô tô.',['Hãng xe','Đánh giá','So sánh','Kinh nghiệm sử dụng']),
('bao-duong','Sửa chữa & bảo dưỡng','Kiểm tra xe, nhận biết bất thường và chăm sóc định kỳ.',['Xe máy','Xe điện','Xe đạp','Ô tô']),
('du-lich','Du lịch Việt Nam','Những điểm đến, lịch trình và cách di chuyển.',['Hà Nội','Miền Bắc','Miền Trung','Miền Nam']),
('luat-giao-thong','Luật & bằng lái','Tra cứu nguồn chính thức và chuẩn bị giấy tờ trước chuyến đi.',['Bằng lái','Xe máy','Xe điện','Biển báo']),
('kinh-nghiem','Kinh nghiệm di chuyển','Chọn phương tiện, chuẩn bị hành trình và đi lại an toàn.',['Đi xe máy','Đi phượt','An toàn','Tuyến đường'])]
P=[]
def add(url,title,hub,excerpt,sections,keywords='',parent=None,kind='article',art='01',tone='gold'):
 P.append(dict(url=url,title=title,hub=hub,excerpt=excerpt,sections=sections,keywords=keywords,parent=parent or '/'+hub+'/',kind=kind,art=art,tone=tone))
PRICE='''<div class="table-scroll"><table><thead><tr><th>Loại xe</th><th>Ngày</th><th>Tuần</th><th>Tháng</th></tr></thead><tbody><tr><td>Xe số</td><td>150–200 nghìn</td><td>700–800 nghìn</td><td>1–1,2 triệu</td></tr><tr><td>Xe ga</td><td>150–200 nghìn</td><td>600 nghìn–1 triệu</td><td>1,2–2 triệu</td></tr><tr><td>Xe điện</td><td>Tùy mẫu</td><td>600–800 nghìn</td><td>1,5–1,8 triệu</td></tr><tr><td>Xe 50cc</td><td>200 nghìn</td><td>1 triệu</td><td>2 triệu</td></tr></tbody></table></div><p>Đơn vị: đồng Việt Nam. Giá cụ thể tùy mẫu xe, thời gian thuê và xe còn sẵn; liên hệ cửa hàng trước khi đến.</p>'''
_BIZ=json.loads((ROOT/'config/site-config.json').read_text()).get('business',{})
CONTACT=f'<p><strong>{E(S["name"])}</strong><br>{E(S["address"])}<br>Giờ mở cửa: {E(S["hours"])}.<br>Điện thoại / Zalo / WhatsApp: <a href="tel:+84334699969">0334 699 969</a>.<br>Email: <a href="mailto:{S["email"]}">{S["email"]}</a>.'+''.join(f'<br><a href="{E(u,quote=True)}" target="_blank" rel="noopener noreferrer">{t}</a>' for t,u in (('Xem trên Google Maps',_BIZ.get('maps')),('Fanpage Facebook',_BIZ.get('facebook'))) if u)+'</p>'
add('/thue-xe-may/ha-noi/','Thuê xe máy Hà Nội: chọn xe, giá thuê và thủ tục','thue-xe','Thông tin thuê xe tại Nguyễn Hà, từ lựa chọn xe đến nhận xe và ký hợp đồng.',[
('Chọn xe theo nhu cầu','<p>Xe số phù hợp nếu bạn quen sang số và muốn một chiếc xe gọn. Xe ga thuận tiện cho việc di chuyển trong thành phố. Nếu quan tâm 50cc hoặc xe điện, hãy trao đổi với cửa hàng về mẫu xe còn sẵn và nhu cầu đi lại trước khi quyết định.</p>'),('Giá thuê theo ngày, tuần và tháng',PRICE),('Giấy tờ, thanh toán và tiền cọc','<p>Tiền cọc từ 2–5 triệu đồng tùy xe và thời hạn thuê, đồng thời thanh toán tiền thuê. Khi cọc tiền, cửa hàng kiểm tra và chụp một giấy tờ nhận dạng để làm hợp đồng; không giữ bản gốc. Khách nước ngoài có thể trao đổi trực tiếp về lựa chọn cọc hộ chiếu hoặc cọc tiền.</p><p>Thanh toán bằng tiền mặt hoặc chuyển khoản ngân hàng Việt Nam. Kiểm tra điều khoản, thời điểm nhận/trả xe và mức tiền cọc trước khi ký.</p>'),('Nhận xe và giao xe','<p>Thuê ngắn hạn nhận xe tại cửa hàng. Giao xe áp dụng cho hợp đồng nhiều ngày, tuần hoặc tháng sau khi thống nhất và ký hợp đồng. Cửa hàng không giao hoặc nhận xe tại sân bay Nội Bài. Trong bán kính 10 km tính từ trung tâm Hoàn Kiếm, phí giao hoặc nhận là 50.000đ/lượt; hai chiều 100.000đ. Ngoài phạm vi này cần thỏa thuận trước.</p>'),('Liên hệ cửa hàng',CONTACT)],'thuê xe máy Hà Nội cho thuê xe máy Hanoi motorbike rental',kind='pillar',art='HN')
add('/bang-gia/','Bảng giá thuê xe máy Nguyễn Hà','thue-xe','Giá xe số, xe ga, xe điện và 50cc theo ngày, tuần, tháng.',[('Bảng giá thuê xe',PRICE),('Thời gian thuê và trả xe','<p>Một ngày thuê được tính là 24 giờ. Thuê theo giờ hoặc nửa ngày vẫn tính giá một ngày. Phụ phí quá giờ là 20.000đ/giờ; quá 6 giờ tính tròn một ngày thuê (config/business-facts.json).</p><p>Trả xe trước ngày kết thúc hợp đồng không được hoàn lại tiền thuê đã thanh toán. Đọc kỹ điều khoản trước khi ký.</p>'),('Khoản cọc và chi phí khác','<p>Cọc tiền 2–5 triệu đồng tùy xe và thời gian thuê. Mũ bảo hiểm cơ bản được cung cấp miễn phí. Xe cần được trả với khoảng 0,5–1 lít xăng; nếu bình trống, phí là 20.000đ. Các khoản liên quan đến hư hỏng được hai bên xử lý theo hợp đồng.</p>')],'giá thuê xe bảng giá tiền thuê cọc',parent='/thue-xe-may/ha-noi/',art='150k')
add('/thue-xe-50cc/ha-noi/','Thuê xe máy 50cc Hà Nội','thue-xe','Thông tin giá thuê và cách kiểm tra xe 50cc trước khi nhận.',[('Xe 50cc tại Nguyễn Hà','<p>Theo thông tin chủ cửa hàng (10/2026), cửa hàng có 3 xe 50cc: SYM Elite 50 màu xanh đen, một xe ga 50cc màu trắng và một xe Cub 50. Bạn nên liên hệ trước để xác nhận xe còn sẵn và đến trực tiếp lái thử, kiểm tra tình trạng xe. Không xác nhận đặt xe qua bài viết.</p>'),('Giá thuê xe 50cc','<p>200.000đ/ngày, 1.000.000đ/tuần và 2.000.000đ/tháng. Tiền cọc và tiền thuê là hai khoản riêng; hỏi cửa hàng về mức cọc cho thời hạn thuê của bạn.</p>'),('Chọn xe phù hợp hành trình','<p>Xe 50cc có công suất hạn chế. Khi chở thêm người, đi dốc hoặc mang hành lý, bạn cần đánh giá khả năng vận hành của chiếc xe thực tế. Lái thử ở nơi phù hợp trước khi ký hợp đồng và tránh chọn xe chỉ vì giá.</p>'),('Độ tuổi và giấy tờ','<p>Chính sách cửa hàng ưu tiên khách từ 20 tuổi với giấy phép phù hợp. Khách từ 18 đến dưới 20 tuổi cần trao đổi trực tiếp về thuê 50cc. Điều kiện pháp luật phụ thuộc phân loại phương tiện; kiểm tra nguồn chính thức trong mục Luật & bằng lái trước khi lái.</p>')],'50cc thuê không bằng lái',parent='/thue-xe-may/ha-noi/',kind='pillar',art='50cc',tone='black')
add('/thue-xe-may/ha-noi/theo-thang/','Thuê xe máy Hà Nội theo tháng','thue-xe','Chọn xe đi làm hoặc lưu trú dài ngày, kiểm tra hợp đồng và chi phí.',[('Giá thuê một tháng','<p>Xe số: 1–1,2 triệu đồng. Xe ga: 1,2–2 triệu đồng. Xe điện: 1,5–1,8 triệu đồng. Xe 50cc: 2 triệu đồng. Giá cụ thể cần xác nhận theo xe còn sẵn.</p>'),('Chuẩn bị hợp đồng','<p>Hợp đồng tháng cần được ký trước khi nhận xe. Ghi rõ thông tin xe, thời gian thuê, tiền cọc, ngày trả, tình trạng xe và cách xử lý hư hỏng. Trả trước thời hạn không được hoàn tiền thuê đã thanh toán.</p>'),('Kiểm tra cho việc dùng mỗi ngày','<p>Thử độ cao yên, khả năng chống chân và thao tác phanh. Kiểm tra cốp, đèn, còi, lốp và khóa xe. Nếu sử dụng xe điện, hãy làm rõ nơi sạc, bộ sạc đi kèm và quãng đường phù hợp với lịch đi lại.</p>')],'thuê xe tháng dài hạn người đi làm',parent='/thue-xe-may/ha-noi/',art='30',tone='white')
add('/thue-xe-may/ha-noi/theo-ngay/','Thuê xe máy Hà Nội theo ngày và tuần','thue-xe','Cách tính 24 giờ và những điều nên xác nhận trước khi nhận xe.',[('Một ngày là 24 giờ','<p>Thuê xe theo ngày được tính 24 giờ từ thời điểm nhận. Thuê chỉ một giờ hoặc 12 giờ vẫn tính giá một ngày. Xác nhận thời điểm trả trong hợp đồng để tránh nhầm với cách tính theo ngày lịch.</p>'),('Chọn ngày hay tuần','<p>Xe số có giá 150–200 nghìn đồng/ngày hoặc 700–800 nghìn đồng/tuần. Xe ga có giá 150–200 nghìn đồng/ngày hoặc 600 nghìn–1 triệu đồng/tuần. So sánh tổng chi phí của kỳ thuê thực tế với cửa hàng.</p>'),('Nhận xe','<p>Thuê ngắn hạn nhận xe tại cửa hàng. Nếu cần giao xe cho kỳ thuê nhiều ngày hoặc tuần, trao đổi trước về hợp đồng, địa điểm và phí giao nhận. Không có dịch vụ giao hoặc nhận ở sân bay Nội Bài.</p>')],'thuê xe ngày tuần 1 ngày 2 ngày 3 ngày theo giờ',parent='/thue-xe-may/ha-noi/',art='24h')
add('/thue-xe-may/long-bien/','Thuê xe máy Long Biên: nhận xe ở Nguyễn Văn Cừ','thue-xe','Hướng dẫn liên hệ cửa hàng tại Bồ Đề, gần Bến xe Gia Lâm.',[('Địa điểm nhận xe',CONTACT),('Chuẩn bị trước khi đến','<p>Gọi hoặc nhắn số 0334 699 969, cho biết loại xe và số ngày muốn thuê. Xác nhận xe còn sẵn và giờ hẹn. Chuẩn bị giấy tờ nhận dạng, tiền thuê và tiền cọc theo thỏa thuận.</p>'),('Đi từ Long Biên vào trung tâm','<p>Chọn tuyến đường phù hợp với chiếc xe, kiểm tra biển báo và điều kiện giao thông trước khi đi. Khi đến Phố Cổ, tìm chỗ gửi xe được phép rồi đi bộ tham quan; không mặc định mọi phố đều cho xe máy vào mọi thời điểm.</p>')],'Long Biên Bồ Đề Nguyễn Văn Cừ Ngọc Lâm bến xe Gia Lâm',parent='/thue-xe-may/ha-noi/',art='LB',tone='black')
add('/thue-xe-may/hoan-kiem/','Thuê xe máy Hoàn Kiếm và Phố Cổ: cách nhận xe','thue-xe','Cửa hàng ở Long Biên; hướng dẫn liên hệ giao nhận khi lưu trú tại trung tâm.',[('Cửa hàng và khu vực giao nhận','<p>Nguyễn Hà có địa chỉ tại Ngõ 5 Nguyễn Văn Cừ, Bồ Đề, Long Biên; không có thông tin về chi nhánh Hoàn Kiếm. Khách ở Hoàn Kiếm hoặc Phố Cổ có thể đến cửa hàng hoặc trao đổi giao xe cho hợp đồng nhiều ngày, tuần, tháng.</p>'),('Phí và điều kiện','<p>Trong bán kính 10 km từ trung tâm Hoàn Kiếm, giao hoặc nhận xe là 50.000đ/lượt, hai chiều 100.000đ. Địa chỉ cụ thể và giờ giao cần được xác nhận trước. Thuê ngắn hạn không giao xe; không giao nhận sân bay Nội Bài.</p>'),('Lưu ý khi tham quan','<p>Khu vực trung tâm có phố đi bộ và các hạn chế giao thông tùy thời điểm. Kiểm tra biển báo, gửi xe tại nơi được phép và không để giấy tờ hay đồ giá trị trong cốp.</p>')],'Hoàn Kiếm Phố Cổ giao tận nơi Hồ Gươm',parent='/thue-xe-may/ha-noi/',art='PC',tone='white')
add('/thue-xe-dien/ha-noi/','Thuê xe điện Hà Nội: giá thuê và điều cần hỏi','thue-xe','Xác nhận loại phương tiện, pin, sạc và điều kiện thuê trước khi chọn xe.',[('Giá tham khảo tại Nguyễn Hà','<p>Xe điện có giá ngày tùy mẫu, giá tuần 600–800 nghìn đồng và giá tháng 1,5–1,8 triệu đồng. Chưa có danh sách mẫu xe điện được xác nhận trong blog; liên hệ cửa hàng để hỏi xe đang có.</p>'),('Làm rõ loại xe','<p>Xe máy điện và xe đạp điện là các loại phương tiện khác nhau. Xe điện không có dung tích xi-lanh nên không nên gọi chung là “xe điện 50cc”. Khi thuê, hỏi rõ tên mẫu, phân loại phương tiện và giấy tờ cần thiết.</p>'),('Pin và sạc','<p>Hỏi mức pin lúc nhận, quãng đường dùng thực tế, vị trí sạc, bộ sạc đi kèm và cách xử lý nếu hết pin. Không mặc định quãng đường công bố của một mẫu xe áp dụng cho mọi chiếc xe.</p>')],'thuê xe điện máy điện đạp điện pin sạc',parent='/thue-xe-may/ha-noi/',kind='pillar',art='EV')
add('/xe-may/chon-xe-so-hay-xe-ga/','Xe số hay xe ga: chọn theo thói quen của bạn','xe-may','So sánh thao tác, chỗ để đồ và nhu cầu đi lại khi thuê xe.',[('Thao tác điều khiển','<p>Xe ga không cần thao tác sang số bằng chân; xe số cần bạn quen với cách sang số và phối hợp ga. Chiếc xe phù hợp là chiếc bạn điều khiển tự tin, không chỉ loại xe bạn thấy quen tên.</p>'),('Kiểm tra chiếc xe thực tế','<p>Ngồi lên xe để thử khả năng chống chân, dắt xe và quay đầu. Xem cốp, vị trí móc đồ, phanh và độ rõ của gương. Tình trạng bảo dưỡng và sự phù hợp với người lái quan trọng hơn kết luận chung theo loại xe.</p>'),('Những mẫu có thể hỏi','<p>Danh sách xe đã cung cấp gồm Honda Wave, Blade và Yamaha Sirius ở nhóm xe số; Honda Vision, Air Blade, Click, Lead và Yamaha Mio ở nhóm xe ga. Mẫu xe còn sẵn cần xác nhận trực tiếp với cửa hàng.</p>')],'Honda Yamaha Wave Sirius Vision Lead Air Blade Click xe số xe ga review so sánh',art='02',tone='black')
add('/xe-dien/pin-sac/','Pin và sạc xe điện: checklist khi nhận xe','xe-dien','Kiểm tra bộ sạc, mức pin và thỏa thuận hỗ trợ trước khi thuê.',[('Bộ sạc đi kèm','<p>Dùng bộ sạc phù hợp theo hướng dẫn nhà sản xuất và xác nhận bộ sạc thuộc chiếc xe thuê. Kiểm tra dây, đầu nối, tình trạng bên ngoài và hướng dẫn vận hành. Nếu thấy bất thường, hỏi cửa hàng trước khi sử dụng.</p>'),('Lịch di chuyển và chỗ sạc','<p>Cho cửa hàng biết quãng đường bạn dự định đi mỗi ngày và nơi lưu trú có chỗ sạc hay không. Hỏi thời gian sạc theo đúng mẫu xe. Không đặt một con số chung cho mọi loại pin.</p>'),('Khi có sự cố','<p>Dừng sử dụng nếu pin hoặc sạc có dấu hiệu bất thường. Không tự tháo pin hoặc can thiệp hệ thống điện trên xe thuê. Liên hệ cửa hàng để nhận hướng dẫn xử lý theo tình trạng thực tế.</p>')],'xe điện pin sạc hết pin',art='EV',tone='white')
add('/bao-duong/xe-may/kiem-tra-truoc-khi-nhan/','Checklist kiểm tra xe máy trước khi nhận','bao-duong','Ghi nhận tình trạng xe, thử thao tác và thống nhất các vấn đề trước khi ký.',[('Ghi nhận hiện trạng','<p>Chụp lại các vết xước, biển số, đồng hồ và phụ kiện đi kèm khi có mặt hai bên. Đưa những bất thường vào biên bản nhận xe để tránh tranh luận khi trả.</p>'),('Kiểm tra cùng cửa hàng','<p>Nhờ cửa hàng kiểm tra phanh, đèn, còi, gương, lốp và khóa. Thử phanh ở tốc độ thấp trong khu vực được phép và có sự hỗ trợ nếu cần. Nếu xe có dấu hiệu mất an toàn, không nhận xe cho tới khi được xử lý.</p>'),('Xác nhận hỗ trợ','<p>Lưu số liên hệ 0334 699 969. Hỏi cách xử lý khi xe hỏng trên đường, phạm vi hỗ trợ và điều khoản chi phí. Không tự sửa lớn hoặc thay phụ tùng khi chưa thống nhất với cửa hàng.</p>')],'kiểm tra phanh lốp đèn còi bảo dưỡng nhận xe',art='05')
add('/du-lich/ha-noi/','Du lịch Hà Nội: bắt đầu từ một hành trình vừa sức','du-lich','Gợi ý chọn khu vực tham quan, cách di chuyển và lịch trình linh hoạt.',[('Chọn một khu vực cho mỗi buổi','<p>Thay vì cố đi nhiều nơi, bạn có thể chọn Phố Cổ và khu vực Hồ Gươm cho một buổi, Hồ Tây cho một buổi khác. Giữ khoảng trống cho ăn uống, nghỉ và thay đổi lịch khi thời tiết không thuận lợi.</p>'),('Chọn phương tiện theo hành trình','<p>Đi bộ hợp với đoạn ngắn và phố nhỏ. Xe máy giúp chủ động khi nối các khu vực, nhưng cần kinh nghiệm lái, giấy tờ phù hợp và chỗ gửi xe. Nếu chưa quen giao thông Hà Nội, cân nhắc phương tiện khác.</p>'),('Chuẩn bị trước khi đi','<p>Xem thời tiết, giờ mở cửa và quy định của từng điểm đến từ nguồn chính thức. Giữ hành lý gọn, sạc điện thoại và chọn một điểm hẹn dễ tìm. Không dùng lịch trình tham khảo thay cho thông tin giao thông hiện tại.</p>')],'du lịch Hà Nội tham quan lịch trình Phố Cổ Hồ Gươm Hồ Tây',kind='pillar',art='HN',tone='white')
add('/du-lich/ha-noi/pho-co/','Phố Cổ Hà Nội: đi bộ sau khi gửi xe','du-lich','Một cách khám phá những phố nhỏ mà không phải liên tục tìm chỗ dừng xe.',[('Bắt đầu với một tuyến ngắn','<p>Chọn vài con phố gần nhau, một điểm ăn uống và một điểm nghỉ. Giữ lịch linh hoạt để có thời gian quan sát cuộc sống trên phố, thay vì chạy theo danh sách quá dài.</p>'),('Nếu đến bằng xe máy','<p>Kiểm tra biển báo và quy định đi lại tại thời điểm tham quan. Gửi xe ở nơi được phép, hỏi giá và giờ lấy xe trước khi gửi. Chụp hoặc lưu thông tin vị trí để tìm lại khi kết thúc buổi đi.</p>'),('Kết nối với lịch trình Hà Nội','<p>Phố Cổ có thể là một phần của lịch trình trung tâm. Nếu chuyển tới Hồ Tây hoặc Long Biên, tính thêm thời gian di chuyển và nghỉ. Tránh lái xe khi quá mệt hoặc chưa quen đường.</p>')],'Phố Cổ Hoàn Kiếm gửi xe tham quan',parent='/du-lich/ha-noi/',art='PC',tone='black')
add('/kinh-nghiem/lai-xe-o-ha-noi/','Đi xe máy ở Hà Nội: chuẩn bị trước chuyến đi','kinh-nghiem','Lựa chọn xe phù hợp, kiểm tra hành trình và giữ thời gian di chuyển linh hoạt.',[('Đánh giá sự tự tin của người lái','<p>Nếu chưa quen lái xe hoặc giao thông đông, nên chọn phương tiện khác hoặc luyện tập ở khu vực phù hợp với sự hướng dẫn. Không lấy việc thuê được xe làm bằng chứng rằng bạn đủ điều kiện hoặc sẵn sàng lái.</p>'),('Chuẩn bị xe và giấy tờ','<p>Kiểm tra tình trạng xe cùng cửa hàng, đội mũ bảo hiểm phù hợp và mang giấy tờ cần thiết. Hỏi rõ loại giấy phép được yêu cầu đối với chiếc xe bạn chọn. Với giấy phép nước ngoài, cần kiểm tra nguồn chính thức trước khi lái tại Việt Nam.</p>'),('Chuẩn bị lộ trình','<p>Xem tuyến đường trước khi xuất phát. Nếu cần xem bản đồ hoặc liên lạc, dừng ở vị trí an toàn. Kiểm tra quy định giao thông, biển báo và thời tiết theo thời điểm thực tế.</p>')],'lái xe Hà Nội an toàn du khách nước ngoài đường đi',art='HN')
add('/luat-giao-thong/nguon-tra-cuu/','Bằng lái và luật giao thông: tra cứu nguồn chính thức','luat-giao-thong','Các bước xác định phương tiện và kiểm tra quy định trước khi lái.',[('Xác định đúng chiếc xe','<p>Hỏi cửa hàng tên mẫu, loại phương tiện và thông tin đăng ký. Không kết luận yêu cầu bằng lái chỉ từ tên gọi quảng cáo, đặc biệt với xe điện. Chính sách độ tuổi của cửa hàng cũng có thể khác điều kiện tối thiểu theo pháp luật.</p>'),('Tra cứu từ nguồn chính thức','<p>Kiểm tra văn bản đang có hiệu lực tại <a href="https://vbpl.vn/" target="_blank" rel="noopener noreferrer">Cơ sở dữ liệu quốc gia về văn bản pháp luật</a> và hướng dẫn trên <a href="https://www.csgt.vn/" target="_blank" rel="noopener noreferrer">website Cục Cảnh sát giao thông</a>. Chú ý ngày hiệu lực, loại xe và loại giấy phép được nêu trong văn bản.</p>'),('Giấy phép nước ngoài','<p>Đừng mặc định mọi bằng lái hoặc giấy phép quốc tế đều sử dụng được tại Việt Nam. Xác nhận quốc gia cấp, loại giấy phép, hiệu lực và điều kiện công nhận qua nguồn chính thức trước khi nhận xe.</p>')],'luật bằng lái độ tuổi 50cc quốc tế giấy phép',art='GPLX',tone='white')
add('/lien-he/','Liên hệ Thuê xe máy Nguyễn Hà','thue-xe','Địa chỉ, số điện thoại, Zalo, WhatsApp và giờ mở cửa.',[('Thông tin cửa hàng',CONTACT),('Trước khi đến','<p>Gọi hoặc nhắn trước để hỏi loại xe, số ngày thuê, mức cọc và xe còn sẵn. Cửa hàng xác nhận việc thuê và thanh toán trực tiếp theo hợp đồng. Không có xác nhận đặt xe tự động qua chatbot.</p>')],'liên hệ địa chỉ giờ email điện thoại Zalo WhatsApp',art='NH')
# Published article source, editable by agents without changing templates.
posts_file=ROOT/'content/posts.json'
if not posts_file.exists(): posts_file.write_text(json.dumps(P,ensure_ascii=False,indent=2))
P=json.loads(posts_file.read_text())
for p in P: p['_source']='content/posts.json'
# Factory articles are sharded so tens of thousands of records do not contend
# on one JSON file.  The legacy posts.json remains supported.
article_dir=ROOT/'content/articles'
if article_dir.exists():
 for article_file in sorted(article_dir.glob('*.json')):
  article=json.loads(article_file.read_text())
  article['_source']='content/articles/'+article_file.name
  if not any(p['url']==article['url'] for p in P): P.append(article)
CUSTOM=json.loads((ROOT/'content/pages.json').read_text())
FAQ=json.loads((ROOT/'content/faq.json').read_text())
for item in CUSTOM:
 item.update(hub='thue-xe',keywords=item['title'],parent='/',kind='page',art='NH',tone='white',_source='content/pages.json')
P.extend(CUSTOM)
# A hub is indexable only while it lists at least one indexable article.  Computed here so that
# menus, the homepage grid and the hub pages all agree on which hubs are empty (noindex).
INDEXABLE_HUBS={q['hub'] for q in P if q['kind'] not in ['hub','page'] and not factory_noindex(q)}
def hub_indexable(slug): return slug in INDEXABLE_HUBS

# Real source dates.  datePublished of a factory article is the first time the
# QA gate passed it (append-only queue log) or, failing that, the commit that
# added its shard; lastmod/dateModified is the last commit touching the source
# file.  All git dates come from ONE `git log` pass.  Shallow clones or missing
# git fall back to the previous fixed date instead of crashing.
import zoneinfo,subprocess
from datetime import datetime
VN_TZ=zoneinfo.ZoneInfo('Asia/Ho_Chi_Minh')
FALLBACK_ISO='2026-10-06T08:00:00+07:00'
# Byline used on every article; the author page only states facts already in the repo.
AUTHOR_NAME='Nguyễn Hà'
AUTHOR_URL='/tac-gia/nguyen-ha/'
GIT_SOURCES=['content/articles','content/posts.json','content/pages.json','content/faq.json','content/site.json','config/business-facts.json']
def git_source_dates():
 """Return ({path: last commit ISO}, {path: first-add commit ISO}) or empty dicts."""
 try:
  shallow=subprocess.run(['git','rev-parse','--is-shallow-repository'],cwd=ROOT,capture_output=True,text=True,timeout=30)
  if shallow.returncode!=0 or shallow.stdout.strip()!='false':
   print('NOTE: git history unavailable or shallow; using fallback dates for lastmod/dateModified')
   return {},{}
  out=subprocess.run(['git','-c','core.quotepath=off','log','--format=%x00%cI','--name-status','--no-renames','--']+GIT_SOURCES,cwd=ROOT,capture_output=True,text=True,check=True,timeout=300).stdout
 except Exception as exc:
  print(f'NOTE: git dates unavailable ({exc}); using fallback dates')
  return {},{}
 modified={};added={};cur=None
 for line in out.splitlines():
  if line.startswith('\x00'):cur=line[1:].strip();continue
  if not line.strip() or cur is None or '\t' not in line:continue
  status,path=line.split('\t',1)
  modified.setdefault(path,cur)  # newest first
  if status.startswith('A'):added[path]=cur  # keeps overwriting -> oldest add wins
 return modified,added
GIT_MODIFIED,GIT_ADDED=git_source_dates()
def to_vn(ts):
 try:return datetime.fromisoformat(ts).astimezone(VN_TZ)
 except Exception:return None
def src_modified(*paths):
 dts=[d for d in (to_vn(GIT_MODIFIED[x]) for x in paths if x in GIT_MODIFIED) if d]
 return max(dts) if dts else None
QUEUE_PASS={};QUEUE_ANY={}
queue_file=ROOT/'data/factory-queue.jsonl'
if queue_file.exists():
 for line in queue_file.read_text(encoding='utf-8').splitlines():
  if not line.strip(): continue
  try:
   entry=json.loads(line)
   if entry.get('id') and entry.get('timestamp'):
    QUEUE_ANY[entry['id']]=entry['timestamp']
    if (entry.get('qa') or {}).get('pass') and entry['id'] not in QUEUE_PASS: QUEUE_PASS[entry['id']]=entry['timestamp']
  except Exception: pass
def fmt_display(dt): return dt.strftime('%H:%M %d.%m.%Y')
for p in P:
 src=p.get('_source')
 mod=src_modified(src) if src else None
 if p['kind'] in ['hub','page']:
  if mod: p['modified_dt']=mod
  continue
 pub=None
 if src and src.startswith('content/articles/'):
  # Only factory shards have a per-article publish date.
  pub=to_vn(QUEUE_PASS.get(p.get('id'),'')) or to_vn(GIT_ADDED.get(src,'')) or to_vn(QUEUE_ANY.get(p.get('id'),''))
 if pub is None and mod is None: pub=mod=datetime.fromisoformat(FALLBACK_ISO)
 # Without a real publish date, the one real date is used for both fields.
 p['has_publish_date']=pub is not None
 if pub is None: pub=mod
 if mod is None or mod<pub: mod=pub
 p['publish_dt']=pub;p['modified_dt']=mod
 p['publish_iso']=pub.isoformat(timespec='seconds');p['modified_iso']=mod.isoformat(timespec='seconds')
 p['publish_display']=fmt_display(pub);p['modified_display']=fmt_display(mod)
 p['publish_time']=pub.strftime('%H:%M');p['publish_date']=pub.strftime('%d.%m.%Y')

TOP_LINKS=[('Trang chủ','/'),('Cẩm nang','/cam-nang/'),('Giới thiệu','/gioi-thieu/')]
BOTTOM_LINKS=[('FAQ','/faq/'),('Liên hệ','/lien-he/'),('Điều khoản dịch vụ','/dieu-khoan-dich-vu/'),('Chính sách bảo mật','/chinh-sach-bao-mat/')]
def utility_links(items): return ''.join('<a href="'+u+'">'+E(t)+'</a>' for t,u in items)
# One source of truth for all navigation; submenu links always point to real hub sections or existing pages.
NAV=[]
for slug,label,desc,children in HUBS:
 NAV.append(dict(slug=slug,label=label,url='/'+slug+'/',description=desc,children=[dict(label=x,url='/'+slug+'/#muc-'+str(i+1)) for i,x in enumerate(children)]))
NAV[0]['children']=[dict(label='Thuê xe máy Hà Nội',url='/thue-xe-may/ha-noi/'),dict(label='Thuê xe 50cc',url='/thue-xe-50cc/ha-noi/'),dict(label='Thuê xe điện',url='/thue-xe-dien/ha-noi/'),dict(label='Theo ngày, tuần, tháng',url='/thue-xe-may/ha-noi/theo-thang/'),dict(label='Bảng giá',url='/bang-gia/')]
NAV[6]['children'][0]['url']='/du-lich/ha-noi/'
for h in NAV:
 sections=[]
 for i,c in enumerate(h['children']):
  matches=[p for p in P if p['hub']==h['slug']]
  content=f'<p>{E(h["description"])}</p>'
  if c['url'].split('#')[0] not in ['/'+h['slug']+'/']:
   content+=f'<p><a href="{c["url"]}">Đọc: {E(c["label"])}</a></p>'
  elif matches:content+='<p>Chọn bài trong danh sách bên dưới để đọc thông tin hiện có.</p>'
  else:content+='<p>Chuyên mục chưa có bài viết. Bạn có thể xem cẩm nang thuê xe và di chuyển tại Hà Nội trong thời gian chờ nội dung mới.</p>'
  sections.append((c['label'],content))
 add(h['url'],h['label'],h['slug'],h['description'],sections,h['label'],parent='/',kind='hub',art=str(NAV.index(h)+1).zfill(2))
ICON_PATH={
'menu':'<path d="M4 7h16M4 12h16M4 17h16"/>','sun':'<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.4 1.4m11.2 11.2L19 19M5 19l1.4-1.4M17.6 6.4 19 5"/>','moon':'<path d="M20 15.5A9 9 0 0 1 8.5 4 9 9 0 1 0 20 15.5Z"/>','close':'<path d="m6 6 12 12M6 18 18 6"/>','chat':'<path d="M21 11.5a8.5 8.5 0 0 1-9 8.5 10 10 0 0 1-3.5-.6L4 21v-5a8.5 8.5 0 1 1 17-4.5Z"/><path d="m7 14 4-4 3 3 3-3"/>','phone':'<path d="M7 3H4a1 1 0 0 0-1 1c0 9.4 7.6 17 17 17a1 1 0 0 0 1-1v-3l-5-2-2 2a13 13 0 0 1-7-7l2-2-2-5Z"/>','send':'<path d="m12 19 0-14M6 11l6-6 6 6"/>','refresh':'<path d="M20 7v5h-5M4 17v-5h5"/><path d="M6 7a7 7 0 0 1 12-1l2 3M4 15l2 3a7 7 0 0 0 12-1"/>'}
def icon(n):return f'<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">{ICON_PATH[n]}</svg>'
import sys
sys.path.insert(0, str(ROOT))
import scripts.templates as T
# Header/footer menus and the homepage grid only list hubs that have at least one indexable
# article.  An empty (noindex) hub keeps its URL and stays reachable from /cam-nang/ and breadcrumbs,
# so no page is lost; it just stops being linked from every page of the site.
NAV_MENU=[h for h in NAV if hub_indexable(h['slug'])]
def header(): return T.render_header(TOP_LINKS, NAV_MENU)
def footer(): return T.render_footer(TOP_LINKS, NAV_MENU, CONTACT)
# Real shop photos (content/photos.json).  Articles embed them with
# <!--photos:id1,id2--> so alt text, captions and sizes live in one file.
# A photo marked "illustration" is not of the shop's own bike: it must name its
# source in "credit", is captioned as such and never enters the LocalBusiness schema.
PHOTOS={x['id']:x for x in json.loads((ROOT/'content/photos.json').read_text())['photos']} if (ROOT/'content/photos.json').exists() else {}
for x in PHOTOS.values():
 if x.get('illustration') and not (x.get('credit') or {}).get('author'):raise SystemExit('Illustration photo without source credit: '+x['id'])
FACTS=json.loads((ROOT/'config/business-facts.json').read_text())
def ext_link(text,url): return f'<a href="{E(url,quote=True)}" target="_blank" rel="noopener noreferrer">{E(text)}</a>' if url else E(text)
def photo_credit(c):
 parts=[ext_link(c['author'],c.get('url'))]+([ext_link(c['license'],c.get('license_url'))] if c.get('license') else [])+([E(c['changes'])] if c.get('changes') else [])
 return ' Nguồn: '+', '.join(parts)+'.'
def photo_gallery(ids):
 out=[]
 for i in ids:
  if i not in PHOTOS:raise SystemExit('Unknown photo id in <!--photos:...-->: '+i)
  x=PHOTOS[i];sm,lg=x['sm'],x['lg']
  cls,sizes=(' class="wide"','(max-width:760px) 100vw, 480px') if x.get('wide') else ('','(max-width:760px) 50vw, 240px')
  out.append(f'<figure{cls}><a href="{lg["src"]}"><img src="{sm["src"]}" srcset="{sm["src"]} {sm["width"]}w, {lg["src"]} {lg["width"]}w" sizes="{sizes}" width="{sm["width"]}" height="{sm["height"]}" alt="{E(x["alt"],quote=True)}" loading="lazy" decoding="async"></a><figcaption>{E(x["caption"])}{photo_credit(x["credit"]) if x.get("illustration") else ""}</figcaption></figure>')
 return '<div class="photo-grid">'+''.join(out)+'</div>'
def expand_photos(html_text): return re.sub(r'<!--photos:([a-z0-9,-]+)-->',lambda m:photo_gallery(m.group(1).split(',')),html_text)
def local_map():
 from urllib.parse import quote
 query=quote(S['address'])
 return f'<section class="local-map" aria-label="Bản đồ địa điểm cửa hàng"><div class="map-heading"><div><h2>Tìm đường đến Nguyễn Hà</h2><p>{E(S["address"])}</p></div><a class="text-link" href="{E(FACTS.get("maps_url") or "https://www.google.com/maps/search/?api=1&query="+query,quote=True)}" target="_blank" rel="noopener noreferrer">Mở Google Maps</a></div><iframe title="Bản đồ địa chỉ Thuê xe máy Nguyễn Hà" src="https://maps.google.com/maps?q={(str(FACTS["geo"]["latitude"])+","+str(FACTS["geo"]["longitude"])) if FACTS.get("geo") else query}&amp;z=17&amp;output=embed" loading="lazy" referrerpolicy="no-referrer" allowfullscreen></iframe></section>'
def widgets(): return T.render_widgets()
def card(p): return T.render_card(p, NAV)
GA4_ID=T.SITE_CFG.get('analytics',{}).get('ga4_measurement_id','')
if GA4_ID and not re.fullmatch(r'G-[A-Z0-9]+',GA4_ID):raise SystemExit('Invalid GA4 measurement id: '+GA4_ID)
GA4_TAG=(f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag(\'js\',new Date());gtag(\'config\',\'{GA4_ID}\');</script>') if GA4_ID else ''
# <title>: keep the brand suffix only while the whole tag stays readable (<= 65 characters).  A long
# editorial title already names the topic; search engines cut title tags at about 60 characters, so
# the suffix was the part being truncated on 1.200+ indexable pages.  H1 and the source title are untouched.
def seo_title(title,url):
 if S['name'].lower() in title.lower():return title
 full=title+' | '+S['name']
 return full if (url=='/' or len(full)<=65 or len(title)<40) else title
# Meta description: when the excerpt is longer than 160 characters, cut at the last sentence end before
# 158 characters, else at a word boundary.  The visible excerpt in the page header is not changed.
def seo_desc(desc):
 if len(desc)<=160:return desc
 cut=max(desc.rfind(m,0,158) for m in ('. ','; ','! ','? '))
 if cut>=90:return desc[:cut+1]
 cut=desc.rfind(' ',0,156)
 return (desc[:cut].rstrip(' ,;:')+'…') if cut>60 else desc
def shell(title,desc,url,body,extra=None,noindex=False):
 brand=T.SITE_CFG.get('site',{})
 logo={'@type':'ImageObject','@id':S['url']+'/#logo','url':S['url']+brand['logo'],'contentUrl':S['url']+brand['logo'],'width':512,'height':512,'caption':'Logo '+S['name']}
 publisher={'@type':'Organization','@id':S['url']+'/#organization','name':S['name'],'url':S['url']+'/','logo':logo,**({'sameAs':[u for u in [FACTS.get('facebook_url'),FACTS.get('maps_url')] if u]} if FACTS.get('facebook_url') or FACTS.get('maps_url') else {})}
 image={'path':brand['og_image'],'alt':brand['og_image_alt'],'width':brand['og_image_width'],'height':brand['og_image_height']}
 if url=='/': image={'path':'/assets/hanoi.webp','alt':'Người đi xe máy qua góc phố Bà Triệu ở Hà Nội','width':1400,'height':788}
 page_source=next((p for p in P if p['url']==url),{})
 # A supplied article image must depict that article and include accurate metadata.
 if page_source.get('image'): image=page_source['image']
 image_url=S['url']+image['path']
 image_type='image/'+('jpeg' if image['path'].endswith(('.jpg','.jpeg')) else image['path'].rsplit('.',1)[-1])
 image_meta=f'<meta property="og:image" content="{E(image_url,quote=True)}"><meta property="og:image:secure_url" content="{E(image_url,quote=True)}"><meta property="og:image:type" content="{image_type}"><meta property="og:image:width" content="{image["width"]}"><meta property="og:image:height" content="{image["height"]}"><meta property="og:image:alt" content="{E(image["alt"],quote=True)}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{E(title,quote=True)}"><meta name="twitter:description" content="{E(seo_desc(desc),quote=True)}"><meta name="twitter:image" content="{E(image_url,quote=True)}"><meta name="twitter:image:alt" content="{E(image["alt"],quote=True)}">'
 extra=list(extra or [])
 for entity in extra:
  if entity.get('@type')=='LocalBusiness': entity.update({'@id':publisher['@id'],'logo':logo})
  if entity.get('@type')=='BlogPosting':
   entity['publisher']={'@id':publisher['@id']}
   if page_source.get('image'): entity['image']={'@type':'ImageObject','url':image_url,'width':image['width'],'height':image['height'],'caption':image['alt']}

 schema={'@context':'https://schema.org','@type':'Blog','name':S['name'],'url':S['url'],'inLanguage':'vi-VN'}
 schema['publisher']={'@id':publisher['@id']}
 schemas=[publisher,schema]
 if extra:schemas+=extra
 schemas_json=json.dumps(schemas,ensure_ascii=False).replace('</','<\\/')
 return f'''<!doctype html><html lang="vi"><head>{GA4_TAG}<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="google-site-verification" content="{S['verification']}"><title>{E(seo_title(title,url))}</title><meta name="description" content="{E(seo_desc(desc),quote=True)}"><meta name="theme-color" content="#ffa266"><meta name="color-scheme" content="light dark">{'<meta name="robots" content="noindex,follow">' if noindex else ''}<link rel="canonical" href="{S['url']+url}"><meta property="og:type" content="{'article' if any(e.get('@type')=='BlogPosting' for e in extra) else 'website'}"><meta property="og:title" content="{E(title,quote=True)}"><meta property="og:description" content="{E(seo_desc(desc),quote=True)}"><meta property="og:url" content="{S['url']+url}"><meta property="og:locale" content="vi_VN"><meta property="og:site_name" content="{E(S['name'],quote=True)}">{image_meta}<link rel="icon" href="/assets/favicon-48.png" type="image/png" sizes="48x48"><link rel="apple-touch-icon" href="/assets/apple-touch-icon.png" sizes="180x180"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><script>try{{const t=localStorage.getItem('nguyenha-theme');document.documentElement.dataset.theme=t==='light'||t==='dark'?t:(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light')}}catch{{document.documentElement.dataset.theme=matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light'}}</script><link rel="stylesheet" href="/assets/site.css"><script type="application/ld+json">{schemas_json}</script><script src="/assets/site.js" defer></script></head><body>{header()}<main id="main" class="wrap">{body}</main>{footer()}{widgets()}</body></html>'''
def write(url,text):
 path=ROOT/('index.html' if url=='/' else url.strip('/')+'/index.html');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
FEATURE=[P[0],P[2],P[3]]
LATEST=[p for p in reversed(P) if p["kind"] in ["article","pillar"] and p["url"]!="/lien-he/" and not factory_noindex(p)][:3]
# Homepage copy lives in content/home.json (business facts only); the layout stays in the builder.
HOME=json.loads((ROOT/'content/home.json').read_text())
home_sections=''.join(f'<section id="muc-{i+1}"><h2>{E(t)}</h2>{b}{PRICE if i==0 else ""}</section>' for i,(t,b) in enumerate(HOME['sections']))
body=f'''<section class="hero"><div><p class="eyebrow">{E(HOME['eyebrow'])}</p><h1>{HOME['h1_html']}</h1><p>{E(HOME['hero_text'])}</p><div class="hero-actions"><a class="pill gold" href="{HOME['primary_cta']['url']}">{E(HOME['primary_cta']['label'])}</a><a class="text-link" href="{HOME['secondary_cta']['url']}">{E(HOME['secondary_cta']['label'])}</a></div></div><div><div class="hero-visual"><img src="/assets/hanoi.webp" alt="Người đi xe máy qua góc phố Bà Triệu ở Hà Nội" width="1400" height="788" decoding="async" fetchpriority="high"><div class="image-label"><div><small>ĐIỂM BẮT ĐẦU</small><strong>Hà Nội, qua từng con phố.</strong></div><span class="number">01</span></div></div><p class="credit">Ảnh: <a href="https://unsplash.com/@elliot_ra8" target="_blank" rel="noopener noreferrer">Elliot Andrews / Unsplash</a></p></div></section><nav class="topic-strip" aria-label="Chủ đề nhanh"><a class="chip active" href="/thue-xe-may/ha-noi/">Thuê xe máy Hà Nội</a><a class="chip" href="/thue-xe-50cc/ha-noi/">Xe 50cc</a><a class="chip" href="/thue-xe-dien/ha-noi/">Xe điện</a><a class="chip" href="/thue-xe-may/ha-noi/theo-thang/">Thuê theo tháng</a><a class="chip" href="/du-lich/ha-noi/">Du lịch Hà Nội</a><a class="chip" href="/bang-gia/">Bảng giá</a></nav><section class="section"><div class="section-head"><div><p class="eyebrow">BẮT ĐẦU TỪ ĐÂY</p><h2>Chọn xe. Chọn hành trình.</h2></div><a class="text-link" href="/thue-xe/">Xem cẩm nang</a></div><div class="grid">{''.join(card(p) for p in FEATURE)}</div></section><section class="section"><article class="article-body information-page">{home_sections}</article></section><section class="section"><div class="feature-band"><div><h2>Một chiếc xe.<br>Nhiều cách khám phá.</h2><p>Giá thuê theo ngày, tuần và tháng. Xem chi phí và điều kiện trước khi lên đường.</p></div><a class="pill gold" href="/bang-gia/">Xem bảng giá</a></div></section><section class="section"><div class="section-head"><div><p class="eyebrow">ĐỌC THEO CHỦ ĐỀ</p><h2>Từ xe đến những điểm đến.</h2></div></div><div class="hub-grid">{''.join('<a class="hub-tile" href="'+h['url']+'"><span class="hub-no">'+str(i+1).zfill(2)+'</span><h3>'+E(h['label'])+'</h3><p>'+E(h['description'])+'</p></a>' for i,h in enumerate(NAV_MENU))}</div></section><section class="section"><div class="section-head"><div><p class="eyebrow">BÀI VIẾT MỚI</p><h2>Mới trên cẩm nang.</h2></div></div><div class="grid">{''.join(card(p) for p in LATEST)}</div></section>'''
local={'@context':'https://schema.org','@type':'LocalBusiness','name':S['name'],**({'alternateName':FACTS['google_business_name']} if FACTS.get('google_business_name') else {}),'url':S['url'],'telephone':S['internationalPhone'],'email':S['email'],'address':{'@type':'PostalAddress','streetAddress':'Ngõ 5 Nguyễn Văn Cừ, Bồ Đề','addressLocality':'Long Biên, Hà Nội','addressCountry':'VN'},'openingHoursSpecification':[{'@type':'OpeningHoursSpecification','dayOfWeek':['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'],'opens':'08:00','closes':'17:00'}],'image':[S['url']+'/assets/nguyen-ha-journal-social.png']+[S['url']+x['lg']['src'] for x in [x for x in PHOTOS.values() if not x.get('illustration')][:4]],**({'sameAs':[u for u in [FACTS.get('facebook_url'),FACTS.get('maps_url')] if u]} if FACTS.get('facebook_url') or FACTS.get('maps_url') else {}),**({'geo':{'@type':'GeoCoordinates','latitude':FACTS['geo']['latitude'],'longitude':FACTS['geo']['longitude']}} if FACTS.get('geo') else {}),'priceRange':'150.000–200.000đ/ngày','areaServed':{'@type':'City','name':'Hà Nội'},'hasMap':FACTS.get('maps_url') or 'https://www.google.com/maps/search/?api=1&query='+__import__('urllib.parse').parse.quote(S['address'])}
write('/',shell(HOME['title'],HOME['description'],'/',body,[local]))
lookup={p['url']:p for p in P}
# Previous / next article: only published, indexable articles in the same hub,
# in source order (posts.json, then factory shards by id).  Rebuilt every build,
# so adding or removing an article keeps the chain in sync.
POST_NAV_ON=T.SITE_CFG.get('features',{}).get('enable_post_nav',True)
NAV_CHAIN={}
for q in P:
 if q['kind'] not in ['hub','page'] and q['url']!='/lien-he/' and not factory_noindex(q):NAV_CHAIN.setdefault(q['hub'],[]).append(q)
NAV_POS={q['url']:(h,i) for h,chain in NAV_CHAIN.items() for i,q in enumerate(chain)}
# INDEXABLE_HUBS / hub_indexable are defined right after the sources are loaded (see above).
def post_nav(p):
 if not POST_NAV_ON or p['url'] not in NAV_POS:return ''
 h,i=NAV_POS[p['url']];chain=NAV_CHAIN[h];prev=chain[i-1] if i>0 else None;nxt=chain[i+1] if i+1<len(chain) else None
 if not prev and not nxt:return ''
 link=lambda q,cls,label:f'<a class="post-nav-link {cls}" href="{q["url"]}" rel="{"prev" if cls=="prev" else "next"}"><small>{label}</small><span>{E(q["title"])}</span></a>' if q else '<span></span>'
 return f'<nav class="post-nav" aria-label="Bài viết trước và sau">{link(prev,"prev","← Bài trước")}{link(nxt,"next","Bài tiếp theo →")}</nav>'
# Service pages matched to an article's place, vehicle or rental length, so that
# relevant articles link to the matching rental page with a descriptive anchor.
# Order is priority (place, then vehicle, then duration); at most two links,
# never the article itself or a page its body already links to.
SERVICE_LINKS=[
 ('/thue-xe-may/long-bien/','Thuê xe máy Long Biên gần Bến xe Gia Lâm',('long biên','long-bien','gia lâm','gia-lam','bồ đề','bo-de')),
 ('/thue-xe-may/hoan-kiem/','Thuê xe máy Hoàn Kiếm và Phố Cổ',('hoàn kiếm','hoan-kiem','phố cổ hà nội','/ha-noi/pho-co/')),
 ('/thue-xe-dien/ha-noi/','Thuê xe máy điện Hà Nội',('xe điện','xe-dien','vinfast')),
 ('/thue-xe-50cc/ha-noi/','Thuê xe máy 50cc Hà Nội',('50cc',)),
 ('/thue-xe-may/ha-noi/theo-thang/','Thuê xe máy theo tháng Hà Nội',('theo tháng','theo-thang','dài hạn','dai-han','sinh viên','sinh-vien','đi làm','di-lam','thuê hay mua','thue-hay-mua','mua xe máy cũ','mua-xe-may-cu','ở lâu','người nước ngoài','nuoc-ngoai','expat')),
 ('/thue-xe-may/ha-noi/theo-ngay/','Thuê xe máy Hà Nội theo ngày và tuần',('theo ngày','theo-ngay','theo tuần','theo-tuan','trong ngày','cuối tuần','day-trip','ngày 1 đêm','ngày 2 đêm','ngày 3 đêm')),
]
# Bảng rộng phải cuộn ngang trên điện thoại: bọc mọi <table> chưa nằm trong .table-scroll (nguồn bài viết tay lẫn V2).
def wrap_tables(h): return re.sub(r'(<div class="table-scroll">\s*)?(<table\b.*?</table>)',lambda m:m.group(0) if m.group(1) else f'<div class="table-scroll">{m.group(2)}</div>',h,flags=re.S)
def service_nav(p,sections_html):
 text=' '.join([p['url'],p['title'],p.get('intent',''),p.get('keywords','')]).lower()
 # Bài nói đến thuê theo tháng trong thân bài (không chỉ ở tiêu đề/từ khoá) cũng được gợi ý trang thuê theo tháng.
 if p['hub'] in ('thue-xe','xe-dien','xe-may','kinh-nghiem') and re.search(r'thuê[^.<]{0,40}(?:tháng|dài ngày|lâu dài)',re.sub(r'<[^>]+>',' ',sections_html),re.I):text+=' theo tháng'
 picks=[(u,a) for u,a,keys in SERVICE_LINKS if u!=p['url'] and f'href="{u}"' not in sections_html and any(k in text for k in keys)][:2]
 if not picks:return ''
 return '<nav class="post-nav" aria-label="Dịch vụ thuê xe liên quan">'+''.join(f'<a class="post-nav-link" href="{u}"><small>Dịch vụ liên quan</small><span>{E(a)}</span></a>' for u,a in picks)+'</nav>'
# Bài liên quan theo chủ đề: cùng hub, đang index, chấm điểm theo từ chung trong tiêu đề, từ khoá và slug (ổn định, không ngẫu nhiên).
_STOP=set('và của cho các một những với trong khi đi ở là có không được tại từ theo bằng xe máy hà nội thuê bài gì nào sao bao nhiêu nên hay thế'.split())
def _toks(q):
 t=' '.join([q['title'],q.get('keywords','') if isinstance(q.get('keywords',''),str) else ' '.join(q.get('keywords',[])),q['url'].replace('-',' ').replace('/',' ')]).lower()
 return {w for w in re.findall(r'\w+',t) if len(w)>1 and w not in _STOP and not w.isdigit()}
_RELPOOL={}
for q in P:
 if q['kind'] not in ['hub','page'] and not factory_noindex(q):_RELPOOL.setdefault(q['hub'],[]).append((q,_toks(q)))
def related_for(p):
 mine=_toks(p);pool=_RELPOOL.get(p['hub'],[])
 scored=sorted(((-len(mine&t),q['parent']!=p['url'],q['url'],q) for q,t in pool if q['url']!=p['url']),key=lambda x:x[:3])
 return [x[3] for x in scored[:25]]
# Lượt 2: giữ 3 bài sát chủ đề nhất, thêm bài thứ 4 là bài ít được trỏ tới nhất trong 10 ứng viên đầu, để bài mới không bị bỏ rơi.
_REL={q['url']:related_for(q) for q in P if q['kind'] not in ['hub','page'] and not factory_noindex(q)}
_RELIN={}
for _u,_c in _REL.items():
 for _q in _c[:3]:_RELIN[_q['url']]=_RELIN.get(_q['url'],0)+1
def related_final(p):
 c=_REL.get(p['url']) or related_for(p)
 top=c[:3];rest=[q for q in c[3:] if q not in top]
 if rest:
  pick=min(rest,key=lambda q:(min(_RELIN.get(q['url'],0),3),rest.index(q)));_RELIN[pick['url']]=_RELIN.get(pick['url'],0)+1;top=top+[pick]
 return top
for p in P:
 par=lookup.get(p['parent']);hub=next(h for h in NAV if h['slug']==p['hub'])
 crumbs='<a href="/">Trang chủ</a><span>/</span><a href="'+hub['url']+'">'+E(hub['label'])+'</a>'
 if par and par['url']!=hub['url']:crumbs+='<span>/</span><a href="'+par['url']+'">'+E(par['title'])+'</a>'
 if p['kind']!='hub':crumbs+='<span>/</span><span>'+E(p['title'])+'</span>'
 sections=''.join(f'<section id="muc-{i+1}"><h2>{E(t)}</h2>{wrap_tables(expand_photos(b))}</section>' for i,(t,b) in enumerate(p['sections']))
 if p.get('faq'):
  n=len(p['sections'])+1
  sections+=f'<section id="muc-{n}" class="article-faq"><h2>{E(p.get("faqTitle","Câu hỏi thường gặp khi thuê xe máy Hà Nội"))}</h2>'+''.join(f'<details class="faq-item"><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q,a in p['faq'])+'</section>'
 related=related_final(p)
 if p['kind']=='page':
  if p['url']=='/faq/':
   sections=''.join(f'<details class="faq-item" id="muc-{i+1}"><summary>{E(q)}</summary><p>{E(a)}</p></details>' for i,(q,a) in enumerate(FAQ))
   page=f'<nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Trang chủ</a><span>/</span><span>{E(p["title"])}</span></nav><header class="page-heading"><h1>{E(p["title"])}</h1><p>{E(p["excerpt"])}</p></header><article class="article-body information-page">{sections}</article>'
  elif p['url']=='/cam-nang/':
    all_articles=[q for q in reversed(P) if q['kind'] not in ['hub','page']]
    # Same order as hub pages: hand-written and indexable articles first (sort is stable).
    all_articles.sort(key=lambda q:(factory_noindex(q),q.get('_source')!='content/posts.json'))
    total_articles_count=len(all_articles)
    total_hubs_count=len(NAV)
    recent_10=all_articles[:10]
    slider_cards_html=''.join(card(q) for q in recent_10)
    slider_block=f'<section class="cam-nang-slider-section"><div class="section-head" style="margin-bottom:18px"><div><p class="eyebrow" style="margin-bottom:6px">MỚI CẬP NHẬT</p><h2 style="font-size:26px">10 bài viết mới nhất</h2><p>Các nội dung kiến thức, hướng dẫn và kinh nghiệm vừa được cập nhật trên blog.</p></div></div><div class="cam-nang-slider-wrap"><div class="cam-nang-slider">{slider_cards_html}</div></div></section>'
    
    quick_nav_chips=''.join(f'<a class="chip" href="#{h["slug"]}">{E(h["label"])}</a>' for h in NAV if any(q['hub']==h['slug'] and q['kind'] not in ['hub','page'] for q in P))
    quick_nav_block=f'<nav class="cam-nang-quick-nav" aria-label="Chuyển nhanh đến chuyên mục"><span style="font-weight:650;font-size:13px;color:var(--muted);display:flex;align-items:center;margin-right:6px">CHUYÊN MỤC:</span>{quick_nav_chips}</nav>'
    
    stats_bar=f'<div class="cam-nang-stats"><div class="cam-nang-stat-pill"><span>Tổng số bài viết</span><span class="num">{total_articles_count:,}</span></div><div class="cam-nang-stat-pill"><span>Chuyên mục</span><span class="num">{total_hubs_count}</span></div><div class="cam-nang-stat-pill"><span>Cập nhật</span><span class="num">Tự động</span></div></div>'
    
    hub_blocks=[]
    for h in NAV:
     h_articles=[q for q in all_articles if q['hub']==h['slug']]
     if h_articles:
      hub_blocks.append(f'<div id="{h["slug"]}" class="cam-nang-hub" style="margin-bottom:48px;scroll-margin-top:100px"><div class="section-head" style="margin-bottom:18px"><div><p class="eyebrow" style="margin-bottom:6px">{E(h["label"])}</p><h2 style="font-size:26px"><a href="{h["url"]}">{E(h["label"])}</a><span class="badge-count">{len(h_articles)} bài</span></h2><p>{E(h["description"])}</p></div><a class="text-link" href="{h["url"]}">Xem tất cả ({len(h_articles)})</a></div><div class="grid">' + ''.join(card(q) for q in h_articles[:3]) + '</div></div>')
    
    # Hubs without indexable articles are not in the menu; keep one inbound link here so no URL is orphaned.
    other_hubs=[h for h in NAV if h not in NAV_MENU]
    other_block=('<p class="cam-nang-other">Chuyên mục đang chuẩn bị nội dung: '+', '.join(f'<a href="{h["url"]}">{E(h["label"])}</a>' for h in other_hubs)+'.</p>') if other_hubs else ''
    sections_cam_nang=f'{stats_bar}{slider_block}{quick_nav_block}' + ''.join(hub_blocks) + other_block
    page=f'<nav class="breadcrumb" aria-label="Breadcrumb">{crumbs}</nav><header class="page-heading"><h1>{E(p["title"])}</h1><p>{E(p["excerpt"])}</p></header><section class="section" style="padding-top:10px">{sections_cam_nang}</section>'
  else:
   page=f'<nav class="breadcrumb" aria-label="Breadcrumb">{crumbs}</nav><header class="page-heading"><h1>{E(p["title"])}</h1><p>{E(p["excerpt"])}</p></header><article class="article-body information-page">{sections}</article>'
 elif p['kind']=='hub':
   items=[q for q in reversed(P) if q['hub']==p['hub'] and q['kind'] not in ['hub','page']]
   # Hand-written and indexable articles first, noindexed factory articles last;
   # newest first within each group (sort is stable).
   items.sort(key=lambda q:(factory_noindex(q),q.get('_source')!='content/posts.json'))
   page_size=25
   total_pages=max(1,(len(items)+page_size-1)//page_size) if items else 1
   hub_sections_body='<div class="article-body" style="margin-top:30px">'+''.join(f'<section id="muc-{i+1}"><h2>{E(t)}</h2>{b}</section>' for i,(t,b) in enumerate(p['sections']))+'</div>' if p['sections'] else ''
   def make_hub_page(page_num):
    start=(page_num-1)*page_size
    page_items=items[start:start+page_size]
    if page_items:
     sec='<div class="grid">'+''.join(card(q) for q in page_items)+'</div>'
     if total_pages>1:
      sec+=T.render_pagination(p['url'],page_num,total_pages)
    else:
     sec='<div class="empty"><h2>Nội dung đang được chuẩn bị</h2><p>Chuyên mục chưa có bài viết. Bạn có thể bắt đầu với cẩm nang thuê xe và du lịch Hà Nội.</p><a class="pill gold" href="/thue-xe-may/ha-noi/">Đọc cẩm nang thuê xe</a></div>'
    if page_num==1 and hub_sections_body:
     sec+=hub_sections_body
    return f'<nav class="breadcrumb" aria-label="Breadcrumb">{crumbs}</nav><header class="page-heading"><p class="eyebrow">CHUYÊN MỤC</p><h1>{E(p["title"])}</h1><p>{E(p["excerpt"])}</p></header><section class="section">{sec}</section>'
   page=make_hub_page(1)
   for p_num in range(2,total_pages+1):
    sub_page=make_hub_page(p_num)
    sub_title=f"{p['title']} - Trang {p_num}"
    sub_url=f"{p['url']}trang-{p_num}/"
    sub_bc=[{'@type':'ListItem','position':1,'name':'Trang chủ','item':S['url']+'/'},{'@type':'ListItem','position':2,'name':sub_title,'item':S['url']+sub_url}]
    sub_extra=[{'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':sub_bc}]
    # A listing page that only links to noindexed factory articles is thin; keep it crawlable but out of the index.
    sub_noindex=all(factory_noindex(q) for q in items[(p_num-1)*page_size:p_num*page_size])
    write(sub_url,shell(sub_title,p['excerpt'],sub_url,sub_page,sub_extra,noindex=sub_noindex))
 else:
  aside='<h3>Trong bài viết</h3>'+''.join(f'<a href="#muc-{i+1}">{E(t)}</a>' for i,(t,b) in enumerate(p['sections']))+(f'<a href="#muc-{len(p["sections"])+1}">Câu hỏi thường gặp</a>' if p.get('faq') else '')+f'<p>Thông tin xe còn sẵn và điều kiện thuê cần được cửa hàng xác nhận.</p><a class="pill gold" href="/lien-he/">Liên hệ Nguyễn Hà</a>'
  cta_block=T.render_conditional_cta(p['hub'])
  author_block=T.render_author_box(AUTHOR_NAME,AUTHOR_URL)
  nav_block=post_nav(p)
  service_block=service_nav(p,sections)
  related_block=T.PARTIAL_RELATED_POSTS.format(related_cards_html=''.join(card(q) for q in related)) if related else ''
  pub_display=p['publish_display'];pub_iso=p['publish_iso']
  mod_display=p['modified_display'];mod_iso=p['modified_iso']
  if p.get('has_publish_date'):
   dates_html=f'Đăng <time datetime="{pub_iso}">{pub_display}</time>'
   if mod_display!=pub_display:dates_html+=f' · Cập nhật <time datetime="{mod_iso}">{mod_display}</time>'
  else:
   dates_html=f'Cập nhật <time datetime="{mod_iso}">{mod_display}</time>'
  byline=f'<span class="meta"><a href="{AUTHOR_URL}" rel="author">{E(AUTHOR_NAME)}</a> · {dates_html}</span>'
  page=f'<nav class="breadcrumb" aria-label="Breadcrumb">{crumbs}</nav><header class="page-heading"><p class="eyebrow">{E(hub["label"])}</p><h1>{E(p["title"])}</h1><p>{E(p["excerpt"])}</p>{byline}</header><div class="article-layout"><article class="article-body">{sections}{service_block}{cta_block}{author_block}{nav_block}<p><a href="{p["parent"]}">Về {E(par["title"] if par else hub["label"])}</a></p></article><aside class="article-aside">{aside}</aside></div>{related_block}'
 bc=[{'@type':'ListItem','position':1,'name':'Trang chủ','item':S['url']+'/'}]
 if p['kind'] not in ['hub','page']:bc.append({'@type':'ListItem','position':2,'name':hub['label'],'item':S['url']+hub['url']})
 bc.append({'@type':'ListItem','position':len(bc)+1,'name':p['title'],'item':S['url']+p['url']})
 extra=[{'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':bc}]
 if p['kind'] not in ['hub','page']:extra.append({'@context':'https://schema.org','@type':'BlogPosting','headline':p['title'],'description':p['excerpt'],'mainEntityOfPage':S['url']+p['url'],'datePublished':p['publish_iso'],'dateModified':p['modified_iso'],'inLanguage':'vi-VN',**({'wordCount':p['wordCount']} if 'wordCount' in p else {}),'author':{'@type':'Person','@id':S['url']+AUTHOR_URL+'#person','name':AUTHOR_NAME,'url':S['url']+AUTHOR_URL}})
 if p['url']=='/lien-he/':
  extra.append(local)
  page+=local_map()
 if p['kind']=='page':extra.append({'@context':'https://schema.org','@type':'WebPage','name':p['title'],'url':S['url']+p['url']})
 if p.get('faq'):extra.append({'@context':'https://schema.org','@type':'FAQPage','mainEntity':[{'@type':'Question','name':q,'acceptedAnswer':{'@type':'Answer','text':a}} for q,a in p['faq']]})
 if p.get('localBusiness') and p['url']!='/lien-he/':
  extra.append(local)
  page+=local_map()
 if p['url']=='/faq/':extra.append({'@context':'https://schema.org','@type':'FAQPage','mainEntity':[{'@type':'Question','name':q,'acceptedAnswer':{'@type':'Answer','text':a}} for q,a in FAQ]})
 write(p['url'],shell(p['title'],p['excerpt'],p['url'],page,extra,noindex=(p['kind']=='hub' and not hub_indexable(p['hub'])) or (factory_noindex(p))))
(ROOT/'404.html').write_text(shell('Không tìm thấy trang','Trang bạn đang tìm không tồn tại.','/404.html','<section class="notice404"><p class="eyebrow">404</p><h1>Ta đổi hướng nhé.</h1><p>Trang này không còn ở địa chỉ bạn vừa mở.</p><a class="pill gold" href="/">Về trang chủ</a></section>',noindex=True))

# Author page: only repo facts (byline name, brand, address, hours, phone).
FACTS=json.loads((ROOT/'config/business-facts.json').read_text())
author_articles=[q for q in reversed(P) if q['kind'] not in ['hub','page']]
author_person={'@type':'Person','@id':S['url']+AUTHOR_URL+'#person','name':AUTHOR_NAME,'url':S['url']+AUTHOR_URL,'worksFor':{'@id':S['url']+'/#organization'}}
author_extra=[{'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'Trang chủ','item':S['url']+'/'},{'@type':'ListItem','position':2,'name':AUTHOR_NAME,'item':S['url']+AUTHOR_URL}]},
 {'@context':'https://schema.org','@type':'ProfilePage','url':S['url']+AUTHOR_URL,'name':'Tác giả '+AUTHOR_NAME,'inLanguage':'vi-VN','mainEntity':author_person}]
author_desc=f'{AUTHOR_NAME} là tên ký trên các bài viết trong cẩm nang của {FACTS["brand"]}.'
author_body=(f'<nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Trang chủ</a><span>/</span><span>{E(AUTHOR_NAME)}</span></nav>'
 f'<header class="page-heading"><p class="eyebrow">TÁC GIẢ</p><h1>{E(AUTHOR_NAME)}</h1><p>{E(author_desc)}</p></header>'
 f'<article class="article-body information-page">'
 f'<section id="muc-1"><h2>Về tên ký bài</h2><p>{E(author_desc)} Các bài viết chia sẻ kiến thức xe máy, xe điện, du lịch và kinh nghiệm di chuyển tại Hà Nội. Hiện có {format(len(author_articles),",").replace(",",".")} bài viết mang tên ký này.</p></section>'
 f'<section id="muc-2"><h2>Thông tin cửa hàng</h2><p><strong>{E(FACTS["brand"])}</strong><br>Địa chỉ: {E(FACTS["address"])} ({E(FACTS["landmark"])})<br>Giờ mở cửa: {E(FACTS["hours"])}<br>Điện thoại / Zalo: <a href="tel:{FACTS["phone"].replace(" ","")}">{E(FACTS["phone"])}</a></p><p>Thông tin xe còn sẵn và điều kiện thuê cần được cửa hàng xác nhận trực tiếp.</p></section>'
 f'<section id="muc-3"><h2>Bài viết mới</h2><p>Xem toàn bộ bài viết theo chuyên mục tại <a href="/cam-nang/">Cẩm nang</a>.</p></section>'
 '</article><div class="grid">'+''.join(card(q) for q in author_articles[:6])+'</div>')
write(AUTHOR_URL,shell('Tác giả '+AUTHOR_NAME,author_desc,AUTHOR_URL,author_body,author_extra))

# Older published routes can survive changes to the article source. Keep their
# body intact while refreshing the shared shell and brand metadata as well.
for legacy in ROOT.rglob('index.html'):
 if 'templates' in legacy.parts or '.git' in legacy.parts: continue
 old=legacy.read_text()
 if '/assets/nguyen-ha-logo.svg' in old: continue
 main_match=re.search(r'<main id="main" class="wrap">(.*?)</main>',old,re.S)
 canonical_match=re.search(r'<link rel="canonical" href="([^"]+)"',old)
 title_match=re.search(r'<title>(.*?)</title>',old,re.S)
 desc_match=re.search(r'<meta name="description" content="([^"]*)"',old)
 schema_match=re.search(r'<script type="application/ld\+json">(.*?)</script>',old,re.S)
 if not all([main_match,canonical_match,title_match,desc_match]): continue
 legacy_url=html.unescape(canonical_match[1]).removeprefix(S['url'])
 if not legacy_url.startswith('/'): continue
 old_extra=json.loads(schema_match[1]) if schema_match else []
 if isinstance(old_extra,dict): old_extra=[old_extra]
 old_extra=[e for e in old_extra if e.get('@type') not in ['Blog','Organization']]
 legacy.write_text(shell(html.unescape(title_match[1]).removesuffix(' | Nguyễn Hà Journal').removesuffix(' | '+S['name']),html.unescape(desc_match[1]),legacy_url,main_match[1],old_extra,noindex='noindex,follow' in old))

# Crawl rendered article HTML locally, rather than relying on titles alone.
class TextParser(HTMLParser):
 def __init__(self):super().__init__();self.out=[];self.depth=0;self.article=False
 def handle_starttag(self,t,a):
  if t=='article' and dict(a).get('class')=='article-body':self.article=True
 def handle_endtag(self,t):
  if t=='article':self.article=False
 def handle_data(self,d):
  if self.article:self.out.append(d)
index=[]
# Search/chatbot index: every published, indexable non-hub page (money pages,
# static pages, kept factory articles).  Noindexed factory articles are left out,
# so the file stays small and the shop's own pages are never cut off.
searchable=[p for p in P if p['kind']!='hub' and not factory_noindex(p)]
limit=int(FACTORY_CFG.get('search_index_limit',2500))
if len(searchable)>limit:searchable=[p for p in searchable if not is_factory(p)]+[p for p in searchable if is_factory(p)][-(limit-sum(1 for p in searchable if not is_factory(p))):]
for p in searchable:
 parser=TextParser();parser.feed((ROOT/p['url'].strip('/')/'index.html').read_text())
 full_text=' '.join(parser.out)
 text_summary=full_text[:600] if len(full_text)>600 else full_text
 index.append({'url':p['url'],'title':p['title'],'hub':p['hub'],'core':0 if is_factory(p) else (2 if p['kind']=='pillar' else 1),'excerpt':p['excerpt'],'keywords':p['keywords'],'text':(p['excerpt']+' '+text_summary).strip(),'headings':' '.join([t for t,b in p['sections']]+[re.sub('<[^>]+>','',x) for t,b in p['sections'] for x in re.findall(r'<h3[^>]*>(.*?)</h3>',b)]),'sections':[{'heading':t,'text':re.sub('<[^>]+>',' ',b)[:200],'url':p['url']+'#muc-'+str(i+1)} for i,(t,b) in enumerate(p['sections'])]})
(ROOT/'assets/search-index.json').write_text(json.dumps({'version':'2026-10-06','site':S,'documents':index},ensure_ascii=False,separators=(',',':')))
(ROOT/'assets/navigation.json').write_text(json.dumps({'primary':[dict(label=t,url=u) for t,u in TOP_LINKS],'hubs':NAV_MENU,'support':[dict(label=t,url=u) for t,u in BOTTOM_LINKS]},ensure_ascii=False,indent=2))
(ROOT/'content/editorial-matrix.json').write_text(json.dumps([{'title':p['title'],'keyword':p['keywords'],'hub':p['hub'],'pillar':p['parent'],'url':p['url'],'priority':'P0' if p['hub']=='thue-xe' else 'P1','status':'published',**({'word_count':p['wordCount']} if 'wordCount' in p else {})} for p in P if p['kind'] not in ['hub','page']],ensure_ascii=False,indent=2))
# Sitemap index: sitemap-pages.xml (home, hubs, static pages, posts.json) and
# sitemap-posts.xml (factory shards).  lastmod is the source's own date.
FALLBACK_DT=datetime.fromisoformat(FALLBACK_ISO)
ARTICLES_ALL=[p for p in P if p['kind'] not in ['hub','page']]
def newest(items,default=None):
 dts=[q['modified_dt'] for q in items if q.get('modified_dt')]
 return max(dts) if dts else default
SITE_NEWEST=newest(ARTICLES_ALL,FALLBACK_DT)
def lastmod_for(p):
 if p['kind']=='hub':return newest([q for q in ARTICLES_ALL if q['hub']==p['hub']],SITE_NEWEST)
 if p['url']=='/cam-nang/':return SITE_NEWEST
 if p['url']=='/faq/':return src_modified('content/pages.json','content/faq.json') or FALLBACK_DT
 return p.get('modified_dt') or FALLBACK_DT
indexed=[p for p in P if p['kind']!='hub' or hub_indexable(p['hub'])]
page_entries=[('/',SITE_NEWEST)]+[(p['url'],lastmod_for(p)) for p in indexed if not is_factory(p)]
page_entries.append((AUTHOR_URL,src_modified('content/site.json','config/business-facts.json') or FALLBACK_DT))
post_entries=[(p['url'],lastmod_for(p)) for p in indexed if is_factory(p) and not factory_noindex(p)]
urls=[u for u,_ in page_entries+post_entries]
SITEMAP_CHUNK=40000  # well under the 50,000-URL protocol limit
def urlset(entries): return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join('<url><loc>'+E(S['url']+u)+'</loc><lastmod>'+d.isoformat(timespec='seconds')+'</lastmod></url>\n' for u,d in entries)+'</urlset>\n'
for old in ROOT.glob('sitemap-*.xml'): old.unlink()
children=[]
for base,entries in [('sitemap-pages',page_entries),('sitemap-posts',post_entries)]:
 for pos in range(0,len(entries),SITEMAP_CHUNK):
  name=base+('' if pos==0 else '-'+str(pos//SITEMAP_CHUNK+1))+'.xml'
  chunk=entries[pos:pos+SITEMAP_CHUNK]
  (ROOT/name).write_text(urlset(chunk))
  children.append((name,max(d for _,d in chunk)))
(ROOT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join('<sitemap><loc>'+S['url']+'/'+name+'</loc><lastmod>'+d.isoformat(timespec='seconds')+'</lastmod></sitemap>\n' for name,d in children)+'</sitemapindex>\n')
(ROOT/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+S['url']+'/sitemap.xml\n')
(ROOT/'CNAME').write_text('thuha.rentbikehanoi.com\n');(ROOT/'.nojekyll').touch()
print(f'Built {len(P)+1} pages, {len(index)} searchable articles, {len(urls)} sitemap URLs')
