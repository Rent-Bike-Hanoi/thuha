#!/usr/bin/env python3
"""Kiểm tra nguồn tự động cho shard OD-1 (chạy trong worktree; không cần mạng).

    python3 check_sources.py content/articles/NH-xxxxx.json [...]

- Mỗi quote trong sources[] có nằm nguyên văn (bỏ khác biệt khoảng trắng) trong thư viện od1/lib/*.json không;
  quote không có trong thư viện = nguồn người viết tự mở -> cần kiểm chứng tay.
- Mỗi con số có đơn vị trong thân bài (km, V, Ah, L, ml, Nm, kPa, %, °C, tháng, năm, điểm, triệu, nghìn, đồng/đ)
  phải xuất hiện trong ít nhất một quote của chính bài; số không có trong quote nào = cần kiểm chứng.
"""
import glob, json, re, sys, unicodedata

OD = '/home/user/thuha/reports/seo-recovery/od1'


def norm(s):
    s = unicodedata.normalize('NFC', s or '').lower()
    return re.sub(r'\s+', '', s)


LIB = []
for f in glob.glob(f'{OD}/lib/*.json'):
    d = json.load(open(f, encoding='utf-8'))
    items = d if isinstance(d, list) else d.get('facts', [])
    for x in items:
        if isinstance(x, dict) and x.get('quote'): LIB.append(norm(x['quote']))
LIBTXT = '\n'.join(LIB)
NUM = re.compile(r'(\d+(?:[.,]\d+)*)\s?(?:–|-|đến)?\s?(\d+(?:[.,]\d+)*)?\s?(km/h|km|kPa|kW|Ah|Nm|ml|mm|cm³|cm3|cc|°C|V|L|lít|%|tháng|năm|giờ|ngày|điểm|triệu|nghìn|đồng|đ\b)')


def plain(h): return re.sub(r'<[^>]+>', ' ', h or '')


for f in sys.argv[1:]:
    a = json.load(open(f, encoding='utf-8'))
    quotes = [s.get('quote', '') for s in a.get('sources') or []]
    qn = ' '.join(norm(q) for q in quotes)
    unknown = [q[:90] for q in quotes if norm(q) not in LIBTXT and norm(q)[:60] not in LIBTXT]
    body = ' '.join(plain(b) for _, b in a.get('sections') or []) + ' ' + ' '.join(plain(x) for _, x in a.get('faq') or [])
    nums = set()
    for m in NUM.finditer(body):
        for g in (m.group(1), m.group(2)):
            if g and len(g.replace('.', '').replace(',', '')) >= 2: nums.add(g)
    unsup = sorted(n for n in nums if norm(n) not in qn and norm(n.replace(',', '.')) not in qn and norm(n.replace('.', ',')) not in qn)
    print(json.dumps(dict(file=f, sources=len(quotes), quotes_not_in_library=unknown, numbers_without_quote=unsup[:25]), ensure_ascii=False))
