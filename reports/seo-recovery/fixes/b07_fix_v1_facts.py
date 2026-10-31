#!/usr/bin/env python3
"""B07 (31/10/2026): sửa lỗi sự thật trong bài V1 vừa mở index.

Chỉ thay những câu khung khớp NGUYÊN VĂN mà kiểm toán sau mở index đã xác nhận sai,
bằng câu lấy từ config/business-facts.json hoặc nguồn luật đã kiểm chứng (sources của NH-00115).
Không đổi url, slug, title, H2, excerpt; chỉ sửa thân section và câu trả lời FAQ.

    python3 reports/seo-recovery/fixes/b07_fix_v1_facts.py            # dry run, in số đếm
    python3 reports/seo-recovery/fixes/b07_fix_v1_facts.py --write    # ghi shard + log
"""
import json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

R = Path(__file__).resolve().parents[3]
FACTS = json.loads((R / 'config/business-facts.json').read_text(encoding='utf-8'))
REINDEX = set(json.loads((R / 'config/factory-reindex.json').read_text(encoding='utf-8'))['urls'])
LOG = R / 'reports/seo-recovery/data/b07_fix_log.jsonl'

TIER_SO = '150–200 nghìn/ngày, 700–800 nghìn/tuần, 1–1,2 triệu/tháng'
assert FACTS['prices']['xe số'] == TIER_SO
assert FACTS['prices']['xe điện'] == 'giá ngày tùy mẫu, 600–800 nghìn/tuần, 1,5–1,8 triệu/tháng'
assert FACTS['prices']['xe 50cc'] == '200 nghìn/ngày, 1 triệu/tuần, 2 triệu/tháng'
assert FACTS['hours'] == '08:00–17:00 hằng ngày' and FACTS['phone'] == '0334 699 969'
TIER_DIEN = '600–800 nghìn/tuần, 1,5–1,8 triệu/tháng (giá ngày tùy mẫu)'
TIER_50 = '200 nghìn/ngày, 1 triệu/tuần, 2 triệu/tháng'
DISTRICT = r'(Hoàn Kiếm|Hai Bà Trưng|Long Biên|Tây Hồ|Nam Từ Liêm|Thanh Xuân|Ba Đình|Hà Đông|Đống Đa|Bắc Từ Liêm|Cầu Giấy|Hoàng Mai)'
HANOI_DEST = {'hà nội phố cổ và hồ tây', 'vườn quốc gia ba vì', 'làng cổ đường lâm'}


def vehicle(a):
    parts = a.get('intent', '').split('|')
    m = parts[2] if len(parts) > 2 else ''
    if 'winner' in m or 'exciter' in m: return 'con_tay'
    if 'vinfast' in m: return 'xe_dien'
    if '50cc' in m: return '50cc'
    if 'xe đạp' in m: return 'xe_dap'
    return 'khac'


def out_of_hanoi(a):
    parts = a.get('intent', '').split('|')
    return a.get('hub') == 'kinh-nghiem' and len(parts) > 1 and parts[1] not in HANOI_DEST


ALL = lambda a: True
RULES = []  # (id, finding, scope, regex, replacement, basis)
def rule(rid, finding, rx, repl, basis, scope=ALL):
    RULES.append((rid, finding, scope, re.compile(rx), repl, basis))
E = re.escape

# --- Giờ mở cửa (NAP)
rule('F01a', 'F01_hours', E('Cửa hàng mở cửa từ 09:00–21:00 hằng ngày.'),
     'Cửa hàng mở cửa từ 08:00–17:00 hằng ngày.', 'business-facts.hours')

# --- Luật: tốc độ xe 50cc (TT 38/2024/TT-BGTVT Điều 7, trích trong sources NH-00115)
rule('L50-S1', 'LEGAL-50CC-TOC-DO',
     E('Di chuyển bằng xe máy phân khối 50cc cho phép bạn duy trì tốc độ ổn định từ 40 đến 50 km/h, vừa đảm bảo an toàn vừa không bị quá sức.'),
     'Xe gắn máy 50cc chỉ được chạy tối đa 40 km/h (Điều 7 Thông tư 38/2024/TT-BGTVT), vì vậy hãy tính thời gian di chuyển dư dả và giữ tốc độ đều để vừa an toàn vừa không bị quá sức.',
     'TT 38/2024 Điều 7: xe gắn máy tốc độ khai thác tối đa 40 km/h', scope=lambda a: vehicle(a) == '50cc')
rule('L50-S2', 'LEGAL-50CC-TOC-DO',
     E('Khung sườn thép chắc chắn đem lại cảm giác đầm tay lái ở dải tốc độ từ 40 đến 50 km/h, ngăn ngừa triệt để hiện tượng láng xe hay rung lắc tay lái nguy hiểm.'),
     'Khung sườn thép chắc chắn giúp tay lái đầm ở tốc độ đi phố, trong giới hạn tối đa 40 km/h dành cho xe gắn máy (Điều 7 Thông tư 38/2024/TT-BGTVT).',
     'TT 38/2024 Điều 7', scope=lambda a: vehicle(a) == '50cc')
rule('L50-S3', 'LEGAL-50CC-TOC-DO',
     E('Duy trì dải tốc độ ổn định từ 35 đến 45 km/h và tránh thói quen thốc ga đột ngột rồi phanh gấp.'),
     'Giữ tốc độ ổn định, không vượt 40 km/h là mức tối đa của xe gắn máy (Điều 7 Thông tư 38/2024/TT-BGTVT), và tránh thói quen thốc ga đột ngột rồi phanh gấp.',
     'TT 38/2024 Điều 7', scope=lambda a: vehicle(a) == '50cc')

# --- Điều kiện lái/thuê xe 50cc (business-facts.license_50cc, age; bài /luat-giao-thong/xe-50cc-co-can-bang-lai/)
LIC50 = 'xe gắn máy dưới 50cc không yêu cầu bằng A1, người lái phải đủ 16 tuổi và cửa hàng nhận khách thuê xe 50cc từ 18 tuổi.'
rule('G50-1', 'LEGAL-50CC-GPLX',
     E('Người điều khiển xe máy 50cc phải đủ độ tuổi luật định và sở hữu giấy phép lái xe phù hợp với phân khối phương tiện.'),
     'Theo quy định hiện hành, ' + LIC50, 'business-facts.policies.license_50cc + age')
rule('G50-2', 'LEGAL-50CC-GPLX',
     E('Về thủ tục giấy tờ, khách hàng chỉ cần xuất trình căn cước công dân hoặc hộ chiếu còn hiệu lực kèm giấy phép lái xe hợp lệ.'),
     'Về thủ tục giấy tờ, khách hàng xuất trình căn cước công dân hoặc hộ chiếu còn hiệu lực; ' + LIC50,
     'business-facts.policies.license_50cc + age', scope=lambda a: vehicle(a) == '50cc')
rule('G50-3', 'LEGAL-50CC-GPLX',
     E('Đảm bảo luôn mang theo giấy phép lái xe và giấy tờ xe hợp lệ khi tham gia giao thông.'),
     'Đảm bảo luôn mang theo căn cước và giấy tờ xe hợp lệ khi tham gia giao thông; xe gắn máy dưới 50cc không yêu cầu bằng A1.',
     'business-facts.policies.license_50cc', scope=lambda a: vehicle(a) == '50cc')
rule('GXD-3', 'LEGAL-XE-DAP-GPLX',
     E('Đảm bảo luôn mang theo giấy phép lái xe và giấy tờ xe hợp lệ khi tham gia giao thông.'),
     'Đảm bảo luôn mang theo giấy tờ tùy thân khi tham gia giao thông.',
     'xe đạp và xe đạp máy không có hạng giấy phép lái xe (Luật 36/2024 Điều 34, 57)', scope=lambda a: vehicle(a) == 'xe_dap')
rule('F12c', 'F12_rental_conditions',
     E('Về thủ tục giấy tờ, khách hàng chỉ cần xuất trình căn cước công dân hoặc hộ chiếu còn hiệu lực kèm giấy phép lái xe hợp lệ.'),
     'Về thủ tục giấy tờ, khách hàng từ 20 tuổi xuất trình căn cước công dân hoặc hộ chiếu còn hiệu lực kèm giấy phép lái xe phù hợp.',
     'business-facts.policies.age', scope=lambda a: vehicle(a) not in ('50cc', 'xe_dap'))
rule('F12d', 'F12_rental_conditions',
     E('Cửa hàng chụp ảnh lưu hồ sơ đối chiếu và trả lại bản gốc ngay cho khách hàng, không giữ giấy tờ tùy thân của bạn.'),
     'Khi đặt cọc bằng tiền, cửa hàng chụp ảnh lưu hồ sơ đối chiếu và trả lại bản gốc ngay, không giữ giấy tờ gốc; khách nước ngoài có thể chọn đặt cọc bằng hộ chiếu.',
     'business-facts.policies.deposit + deposit_foreigner')

# --- Luật: xe đạp điện không bị phạt như xe cơ giới (Luật 36/2024 Điều 34; NĐ 168/2024 Điều 7, Điều 9)
rule('LXDD', 'LEGAL-XE-DAP-DIEN-PHAT',
     E('Theo luật định, người điều khiển xe đạp điện, xe máy điện đều là đối tượng phải tuân thủ nghiêm ngặt các quy định về an toàn giao thông và chịu mức phạt tương đương xe cơ giới.'),
     'Theo luật định, người điều khiển xe đạp điện và xe máy điện đều phải tuân thủ quy định về an toàn giao thông, nhưng mức phạt khác nhau: xe đạp điện thuộc nhóm xe đạp máy (Điều 34 Luật Trật tự, an toàn giao thông đường bộ 2024) và bị xử phạt theo Điều 9 Nghị định 168/2024/NĐ-CP với khung thấp hơn, còn xe máy điện bị xử phạt như xe mô tô, xe gắn máy theo Điều 7.',
     'sources NH-00115: Luật 36 Điều 34 khoản 2 điểm b; NĐ 168 Điều 9 khoản 2 điểm đ so với Điều 7 khoản 7')

# --- Giá đúng loại xe (business-facts.prices)
rule('F03-dien', 'F03_price_tier', E(TIER_SO), TIER_DIEN, 'business-facts.prices["xe điện"]', scope=lambda a: vehicle(a) == 'xe_dien')
rule('F03-50', 'F03_price_tier', E(TIER_SO), TIER_50, 'business-facts.prices["xe 50cc"]', scope=lambda a: vehicle(a) == '50cc')
# xe điện: fleet chỉ xác nhận xe máy điện Tailg, nên nói giá theo nhóm xe chứ không gắn tên mẫu VinFast
rule('F14a-dien', 'F14_superlative', r'Theo biểu phí đang áp dụng, dòng (.+?) có mức giá cạnh tranh hàng đầu thị trường: ',
     'Theo biểu phí đang áp dụng, giá thuê xe máy điện tại cửa hàng là: ', 'không có trong business-facts; fleet["xe điện"]',
     scope=lambda a: vehicle(a) == 'xe_dien')
rule('F14a', 'F14_superlative', r'Theo biểu phí đang áp dụng, dòng (.+?) có mức giá cạnh tranh hàng đầu thị trường: ',
     r'Theo biểu phí đang áp dụng, giá thuê \1 tại cửa hàng là: ', 'không có trong business-facts',
     scope=lambda a: vehicle(a) not in ('con_tay', 'xe_dien'))

# --- Cam kết dịch vụ không có trong chính sách
DMG = ('Hư hỏng được xử lý theo hợp đồng: lỗi của xe (chết máy giữa đường, hỏng do xe) thì cửa hàng chịu phần lớn chi phí; '
       'đổ xe, va chạm, thủng săm, xịt lốp là lỗi của khách, khách tự chịu.')
rule('F02a', 'F02_damage',
     E('Trong trường hợp phương tiện phát sinh sự cố kỹ thuật bất khả kháng không xuất phát từ lỗi người điều khiển, cửa hàng chịu toàn bộ chi phí sửa chữa hoặc đổi xe mới trong vòng 2 giờ.'),
     DMG, 'business-facts.policies.damage')
rule('F02b', 'F02_damage',
     r'Nếu xe gặp trục trặc không do lỗi người dùng, cửa hàng sẽ hỗ trợ đổi xe tương đương ngay trong ngày để không làm gián đoạn công việc của bạn tại ' + DISTRICT + r'\.',
     DMG, 'business-facts.policies.damage')
rule('F07a', 'F07_deposit_refund',
     E('Khi bàn giao lại xe, nhân viên sẽ đối chiếu nhanh tình trạng vỏ xe và lượng xăng với biên bản ban đầu, tiến hành hoàn cọc ngay lập tức và gửi lời cảm ơn quý khách đã tin tưởng sử dụng dịch vụ.'),
     'Khi bàn giao lại xe, nhân viên đối chiếu tình trạng xe và lượng xăng với biên bản ban đầu (trả xe với khoảng 0,5–1 lít xăng; bình trống phí 20.000đ), rồi hoàn cọc theo điều kiện hợp đồng sau khi trừ các khoản phát sinh nếu có.',
     'business-facts.policies.fuel, damage_cost, loss')
rule('F07b', 'F07_deposit_refund',
     E('Khoản tiền đặt cọc được giữ an toàn và hoàn trả ngay lập tức bằng tiền mặt hoặc chuyển khoản khi khách hàng bàn giao lại xe và hoàn tất thủ tục thanh lý.'),
     'Tiền cọc (2–5 triệu đồng tùy xe và thời hạn thuê) được hoàn lại bằng tiền mặt hoặc chuyển khoản khi trả xe, theo điều kiện hợp đồng và sau khi trừ các khoản phát sinh như phí trả muộn 20.000đ/giờ hoặc chi phí sửa xe nếu hư hỏng do khách.',
     'business-facts.policies.deposit, late_fee, damage_cost')
rule('F08a', 'F08_insurance_store',
     E('Để đảm bảo tính pháp lý cao nhất, Thuê xe máy Nguyễn Hà luôn cung cấp đầy đủ bản sao giấy đăng ký xe và bảo hiểm trách nhiệm dân sự bắt buộc còn hiệu lực.'),
     '', 'business-facts.policies.insurance: không nêu về bảo hiểm')
rule('F08b', 'F08_insurance_store',
     E('Chúng tôi cam kết toàn bộ xe cho thuê đều có giấy tờ hợp pháp, bảo hiểm đầy đủ và được kiểm định kỹ thuật nghiêm ngặt trước khi lăn bánh.'),
     '', 'business-facts.policies.insurance: không nêu về bảo hiểm')
rule('F08c', 'F08_insurance_store',
     E('Đối với phương tiện thuê tại cửa hàng, hãy gọi ngay hotline kỹ thuật của Thuê xe máy Nguyễn Hà để được hỗ trợ hướng dẫn làm việc với cơ quan bảo hiểm và xử lý phương tiện.'),
     'Đối với phương tiện thuê tại cửa hàng, hãy gọi 0334 699 969 trong giờ mở cửa 08:00–17:00 để được hướng dẫn xử lý phương tiện theo hợp đồng.',
     'business-facts.phone, hours, policies.damage')
rule('F10a', 'F10_247',
     E('Hơn thế nữa, bạn hoàn toàn làm chủ phương tiện 24/7 mà không phải chờ đợi tài xế trong những ngày mưa gió hay giờ cao điểm.'),
     'Hơn thế nữa, bạn hoàn toàn làm chủ phương tiện suốt thời gian thuê mà không phải chờ đợi tài xế trong những ngày mưa gió hay giờ cao điểm.',
     'cửa hàng mở 08:00–17:00; "24/7" bị BANNED')
rule('F10b', 'F10_247',
     E('Bạn sẽ không bao giờ phải đứng chờ tài xế dưới trời mưa, không lo bị hủy chuyến vào giờ tan tầm và hoàn toàn chủ động làm chủ lịch trình cá nhân 24/7.'),
     'Bạn sẽ không phải đứng chờ tài xế dưới trời mưa, không lo bị hủy chuyến vào giờ tan tầm và hoàn toàn chủ động lịch trình cá nhân trong suốt thời gian thuê.',
     'cửa hàng mở 08:00–17:00; "24/7" bị BANNED')
rule('F11a', 'F11_airport_false_positive',
     E('Lưu ý rằng dịch vụ cho thuê xe không áp dụng giao nhận tại sân bay Nội Bài.'),
     'Lưu ý: cửa hàng không giao/nhận xe tại sân bay Nội Bài.', 'business-facts.policies.delivery')
F13_RX = r'Khi so sánh với việc sử dụng dịch vụ gọi xe công nghệ mỗi ngày, việc thuê trọn gói (.+?) giúp (.+?) tiết kiệm từ một đến hai triệu đồng mỗi tháng\.'
rule('F13a-dien', 'F13_unsupported_amount', F13_RX,
     r'Khi so sánh với việc gọi xe công nghệ mỗi ngày, \2 nên cộng chi phí gọi xe thực tế trong một tháng rồi so với giá thuê tháng xe máy điện tại cửa hàng.',
     'con số tiết kiệm không có nguồn; fleet["xe điện"]', scope=lambda a: vehicle(a) == 'xe_dien')
rule('F13a', 'F13_unsupported_amount', F13_RX,
     r'Khi so sánh với việc gọi xe công nghệ mỗi ngày, \2 nên cộng chi phí gọi xe thực tế trong một tháng rồi so với giá thuê tháng của \1 tại cửa hàng.',
     'con số tiết kiệm không có nguồn', scope=lambda a: vehicle(a) not in ('xe_dien', 'con_tay'))
# côn tay: cửa hàng không cho thuê (fleet), nên không nhắc "giá thuê tại cửa hàng"
rule('F13a-contay', 'F13_unsupported_amount', F13_RX,
     r'Khi so sánh với việc gọi xe công nghệ mỗi ngày, \2 nên cộng chi phí gọi xe thực tế trong một tháng rồi so với chi phí sở hữu hoặc thuê xe theo tháng.',
     'con số tiết kiệm không có nguồn; fleet["côn tay"]: không cho thuê', scope=lambda a: vehicle(a) == 'con_tay')
rule('F06a', 'F06_delivery',
     E('Quý khách có thể đặt xe trước qua điện thoại hoặc Zalo để được giao xe tận nơi nhanh chóng, tiết kiệm tối đa thời gian và công sức chuẩn bị phương tiện.'),
     'Với hợp đồng thuê nhiều ngày, tuần hoặc tháng, quý khách có thể đặt trước qua điện thoại hoặc Zalo để được giao xe: 50.000đ/lượt trong bán kính 10 km từ trung tâm Hoàn Kiếm, hai chiều 100.000đ; không giao/nhận tại sân bay Nội Bài.',
     'business-facts.policies.delivery')
rule('F05a', 'F05_out_of_hanoi',
     E('Nếu bạn cần thuê phương tiện tại Hà Nội cho cả chuyến đi, đừng quên tham khảo giá thuê theo tuần tại <a href="/bang-gia/">bảng giá thuê xe máy theo tuần</a> để chọn kỳ thuê tiết kiệm nhất.'),
     'Nếu thuê xe tại Hà Nội để đi ra ngoài thành phố, cửa hàng chỉ cho thuê khi thuê từ 48 giờ trở lên và tính theo giá ngày 150–200 nghìn; đi dài ngày vẫn tính giá ngày, không áp giá tuần (xem <a href="/bang-gia/">bảng giá</a>).',
     'business-facts.policies.out_of_hanoi', scope=out_of_hanoi)
rule('LANG-1', 'LANG_chuyen_chuyen', r'chuyến chuyến', 'chuyến', 'lỗi ghép khuôn lặp từ')


def drop_empty_p(s):
    s = re.sub(r'<p>\s*</p>', '', s)
    s = re.sub(r'(<p>)\s+', r'\1', s)
    s = re.sub(r'\s+(</p>)', r'\1', s)
    return re.sub(r'  +', ' ', s)


def fix_text(a, s, hits):
    new = s
    for rid, finding, scope, rx, repl, _ in RULES:
        if not scope(a): continue
        new, n = rx.subn(repl, new)
        if n: hits[rid] += n
    if new != s: new = drop_empty_p(new)
    return new


def main(write):
    files = sorted((R / 'content/articles').glob('NH-*.json'))
    per_rule_urls = defaultdict(set); changed = []
    for f in files:
        a = json.loads(f.read_text(encoding='utf-8'))
        if int(a.get('factoryVersion') or 1) >= 2 or a['url'] in REINDEX: continue
        hits = Counter()
        before = json.dumps(a, ensure_ascii=False)
        frozen = (a['url'], a['title'], a.get('excerpt'), [t for t, _ in a.get('sections') or []], [q for q, _ in a.get('faq') or []])
        a['sections'] = [[t, fix_text(a, b, hits)] for t, b in a.get('sections') or []]
        if a.get('faq'): a['faq'] = [[q, fix_text(a, x, hits)] for q, x in a['faq']]
        assert frozen == (a['url'], a['title'], a.get('excerpt'), [t for t, _ in a['sections']], [q for q, _ in a.get('faq') or []])
        if json.dumps(a, ensure_ascii=False) == before: continue
        for rid in hits: per_rule_urls[rid].add(a['url'])
        changed.append({'id': a['id'], 'url': a['url'], 'file': str(f.relative_to(R)), 'vehicle': vehicle(a), 'rules': dict(hits)})
        if write:
            raw = f.read_text(encoding='utf-8')
            indent = 2 if raw.startswith('{\n') else None
            f.write_text(json.dumps(a, ensure_ascii=False, indent=indent) + ('\n' if raw.endswith('\n') else ''), encoding='utf-8')
    for rid, finding, *_ in RULES:
        print(f'{rid:9s} {finding:28s} {len(per_rule_urls[rid]):5d} URL')
    print('URL thay đổi:', len(changed))
    if write:
        with LOG.open('w', encoding='utf-8') as fh:
            for c in changed: fh.write(json.dumps(c, ensure_ascii=False) + '\n')
        print('log:', LOG.relative_to(R))


if __name__ == '__main__':
    main('--write' in sys.argv)
