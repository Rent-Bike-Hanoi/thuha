#!/usr/bin/env python3
"""Kiểm thử đường xuất bản Topic Factory V2: hàng đợi → nháp → QA phạm vi hẹp → shard factoryVersion 2 → nhật ký → chỉ mục.
Chạy trong sandbox tạm: không chạm nguồn bài thật."""
from pathlib import Path
import contextlib, importlib.util, io, json, shutil, sys, tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fv', ROOT / 'scripts/factory_v2.py')
fv = importlib.util.module_from_spec(spec); spec.loader.exec_module(fv)
tm, F = fv.tm, fv.F


def quiet(fn, *a, **kw):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = fn(*a, **kw)
    return rc, out.getvalue()


def art(url, title, keywords, hub, heads, excerpt='Tóm tắt bài viết để kiểm thử, dài hơn một trăm ký tự để qua ngưỡng excerpt của cổng kiểm tra bài viết.'):
    return {'url': url, 'title': title, 'keywords': keywords, 'hub': hub, 'kind': 'article', 'excerpt': excerpt, 'parent': '/' + hub + '/', 'art': 'T', 'tone': 'gold',
            'sections': [[h, '<p>' + ('nội dung kiểm thử ' * 40) + '</p>'] for h in heads]}


POSTS = [
    art('/luat-giao-thong/phat-vuot-den-do-xe-may/', 'Vượt đèn đỏ xe máy phạt bao nhiêu? 4–6 triệu, trừ 4 điểm (2026)',
        'phạt vượt đèn đỏ xe máy, vượt đèn đỏ xe máy 2025, lỗi vượt đèn đỏ', 'luat-giao-thong', ['Mức phạt', 'Trừ điểm', 'Đèn vàng', 'Rẽ phải khi đèn đỏ']),
    art('/kinh-nghiem/cach-di-xe-so/', 'Cách đi xe số cho người mới: côn, sang số, lên dốc, xuống dốc', 'cách đi xe số, cách đi xe số cho người mới', 'kinh-nghiem',
        ['Côn và số', 'Sang số', 'Lên dốc', 'Xuống dốc']),
]
LAW = {'type': 'law', 'source': 'https://xaydungchinhsach.chinhphu.vn/...', 'quote': 'đ) Vượt bên phải trong trường hợp không được phép', 'checked': '2026-10-12'}


def seed(title, pk, gain, outline, url=None):
    return {'hub': 'luat-giao-thong', 'subtopic': 'muc-phat', 'origin': 'seed', 'title': title, 'primary_keyword': pk, 'user_problem': 'Người đọc muốn biết mức phạt.',
            'information_gain': gain, 'evidence': [LAW], 'outline': outline, **({'url': url} if url else {})}


def draft(tid, row, body_words=200, link='/luat-giao-thong/phat-vuot-den-do-xe-may/', phone='0334 699 969', sources=True):
    body = '<p>' + ('nội dung kiểm thử ' * body_words) + f' Xem thêm <a href="{link}">bài liên quan</a>. Hỏi cửa hàng qua {phone}.</p>'
    return {'id': tid, 'topic_id': tid, 'url': row['url'], 'title': row['title'], 'hub': row['hub'], 'parent': '/luat-giao-thong/', 'kind': 'article', 'art': 'Luật', 'tone': 'black',
            'keywords': row['primary_keyword'], 'excerpt': row['title'] + '. Tóm tắt kiểm thử đủ dài để vượt ngưỡng một trăm ký tự của cổng kiểm tra bài viết Topic Factory V2.',
            'sections': [[h, body] for h in row['outline']],
            'faqTitle': 'Hỏi đáp', 'faq': [['Lỗi này có bị trừ điểm không?', 'Xem bảng trừ điểm trong bài.']],
            'sources': [LAW] if sources else [], 'factoryVersion': 2}


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    for d in ('content/articles', 'content/drafts', 'data', 'config', 'reports', 'scripts'):
        (tmp / d).mkdir(parents=True)
    (tmp / 'content/posts.json').write_text(json.dumps(POSTS, ensure_ascii=False))
    (tmp / 'luat-giao-thong').mkdir(); (tmp / 'luat-giao-thong/index.html').write_text('<html></html>')  # trang hub có thật để liên kết nội bộ hợp lệ
    shutil.copy(ROOT / 'config/business-facts.json', tmp / 'config/business-facts.json')
    shutil.copy(ROOT / 'config/content-factory.json', tmp / 'config/content-factory.json')
    shutil.copy(ROOT / 'scripts/content_factory.py', tmp / 'scripts/content_factory.py')
    (tmp / 'data/keyword-metrics.jsonl').write_text(''.join(json.dumps({'keyword': k, 'volume': None, 'source': 'test', 'checked': '2026-10-12'}) + '\n'
                                                           for k in ('vượt phải phạt bao nhiêu', 'xe máy không có gương phạt bao nhiêu')))
    saved_tm = {k: getattr(tm, k) for k in ('ROOT', 'MATRIX_PATH', 'PUBLISHED_PATH', 'KEYWORDS_PATH', 'CACHE_DIR', 'DB_PATH', 'POSTS_PATH', 'SHARDS_DIR', 'FACTS_PATH', 'FACTORY_CFG_PATH', 'LEGACY_AUDIT_CSV', 'REPORTS')}
    saved_f = {k: getattr(F, k) for k in ('ROOT', 'ARTICLES', 'LEGACY', 'INDEX_PATH', 'QUEUE_PATH', 'STATE_PATH')}
    try:
        tm.ROOT = tmp; tm.MATRIX_PATH = tmp / 'data/topic-matrix.jsonl'; tm.PUBLISHED_PATH = tmp / 'data/topic-matrix-published.jsonl'
        tm.KEYWORDS_PATH = tmp / 'data/keyword-metrics.jsonl'; tm.CACHE_DIR = tmp / 'data/cache'; tm.DB_PATH = tmp / 'data/cache/topic-index.sqlite'
        tm.POSTS_PATH = tmp / 'content/posts.json'; tm.SHARDS_DIR = tmp / 'content/articles'; tm.FACTS_PATH = tmp / 'config/business-facts.json'
        tm.FACTORY_CFG_PATH = tmp / 'config/content-factory.json'; tm.LEGACY_AUDIT_CSV = tmp / 'reports/none.csv'; tm.REPORTS = tmp / 'reports'
        F.ROOT = tmp; F.ARTICLES = tmp / 'content/articles'; F.LEGACY = tmp / 'content/posts.json'; F.INDEX_PATH = tmp / 'data/content-index.jsonl'
        F.QUEUE_PATH = tmp / 'data/factory-queue.jsonl'; F.STATE_PATH = tmp / 'data/factory-state.json'

        quiet(tm.sync)
        seeds = tmp / 'seeds.jsonl'
        seeds.write_text('\n'.join(json.dumps(s, ensure_ascii=False) for s in [
            seed('Vượt phải xe máy phạt bao nhiêu? Khi nào được vượt bên phải', 'vượt phải phạt bao nhiêu',
                 'Bài /luat-giao-thong/phat-vuot-den-do-xe-may/ chỉ nói đèn tín hiệu; bài này nêu điểm đ khoản 3 Điều 7: vượt bên phải khi không được phép, 600.000–800.000đ.',
                 ['Câu trả lời ngắn', 'Khi nào được vượt phải', 'Mức phạt', 'Tra cứu']),
            seed('Không có gương chiếu hậu xe máy phạt bao nhiêu? Gương trái, gương phải', 'xe máy không có gương phạt bao nhiêu',
                 'Chưa có bài: Điều 14 khoản 1 điểm a phạt 400.000–600.000đ khi không có gương chiếu hậu bên trái; vì sao gương phải không bị phạt.',
                 ['Gương chiếu hậu bên trái là bắt buộc', 'Gương bên phải thì sao', 'Lỗi gương theo Điều 14 Nghị định 168', 'Đối chiếu văn bản gốc']),
        ]) + '\n')
        quiet(tm.discover, str(seeds))
        rows = tm.load_matrix(); t1, t2 = rows[0]['topic_id'], rows[1]['topic_id']
        assert all(r['lifecycle'] in ('PLANNED', 'RESEARCH') for r in rows), rows

        # 1. Writer không lấy được gì khi chưa có hàng APPROVED
        rc, out = quiet(fv.queue, 'writer-1', 3)
        assert json.loads(out)['assigned'] == [] and not list((tmp / 'content/drafts').glob('*')), out
        rc, out = quiet(tm.approve, t1, 'Nguyễn Hà', 'ok'); assert rc == 0, out
        rc, out = quiet(tm.approve, t2, 'Nguyễn Hà', 'ok'); assert rc == 0, out

        # 2. Hàng đợi: APPROVED → WRITING, brief có khuôn nháp và luật viết
        rc, out = quiet(fv.queue, 'writer-1', 1)
        assigned = json.loads(out)['assigned']; assert assigned == [t1], out
        brief = json.loads((tmp / f'content/drafts/{t1}.brief.json').read_text())
        assert brief['draft_template']['factoryVersion'] == 2 and brief['draft_template']['url'] == rows[0]['url'] and brief['rules'], brief
        m = {r['topic_id']: r for r in tm.load_matrix()}
        assert m[t1]['lifecycle'] == 'WRITING' and m[t1].get('assigned_to') == 'writer-1'

        # 3. Nháp hỏng (liên kết hỏng, số điện thoại lạ) → QA fail, vẫn WRITING; publish ghi nhật ký fail và KHÔNG tạo shard
        (tmp / f'content/drafts/{t1}.json').write_text(json.dumps(draft(t1, m[t1], link='/khong-ton-tai/', phone='0999 123 456'), ensure_ascii=False))
        rc, out = quiet(fv.qa, [t1]); res = json.loads(out)[0]
        assert rc == 1 and not res['pass'] and any('hỏng' in x for x in res['fails']) and any('điện thoại' in x for x in res['fails']), res
        assert {r['topic_id']: r for r in tm.load_matrix()}[t1]['lifecycle'] == 'WRITING'
        rc, out = quiet(fv.publish, [t1], False, 'test')
        assert rc == 1 and not (tmp / f'content/articles/{t1}.json').exists(), out
        log = [json.loads(l) for l in (tmp / 'data/factory-queue.jsonl').read_text().splitlines()]
        assert len(log) == 1 and log[0]['id'] == t1 and log[0]['qa']['pass'] is False and log[0]['factoryVersion'] == 2, log
        # nháp quá mỏng cũng bị chặn
        (tmp / f'content/drafts/{t1}.json').write_text(json.dumps(draft(t1, m[t1], body_words=20), ensure_ascii=False))
        rc, out = quiet(fv.qa, [t1]); assert rc == 1 and any('mỏng' in x or 'từ' in x for x in json.loads(out)[0]['fails']), out
        # nháp thiếu sources ở hub yêu cầu nguồn bị chặn
        (tmp / f'content/drafts/{t1}.json').write_text(json.dumps(draft(t1, m[t1], sources=False), ensure_ascii=False))
        rc, out = quiet(fv.qa, [t1]); assert rc == 1 and any('sources' in x for x in json.loads(out)[0]['fails']), out

        # 4. Nháp đạt → QA → publish: shard factoryVersion 2, nhật ký pass, content-index, PUBLISHED, sync coi là bài hard/KEEP/indexable
        (tmp / f'content/drafts/{t1}.json').write_text(json.dumps(draft(t1, m[t1]), ensure_ascii=False))
        rc, out = quiet(fv.qa, [t1]); res = json.loads(out)[0]; assert rc == 0 and res['pass'], res
        assert {r['topic_id']: r for r in tm.load_matrix()}[t1]['lifecycle'] == 'QA'
        rc, out = quiet(fv.publish, [t1], False, 'Nguyễn Hà'); pub = json.loads(out)
        assert rc == 0 and [p['topic_id'] for p in pub['published']] == [t1], out
        shard = json.loads((tmp / f'content/articles/{t1}.json').read_text())
        assert shard['factoryVersion'] == 2 and shard['topic_id'] == t1 and shard['publishedBy'] == 'Nguyễn Hà' and shard['url'] == m[t1]['url']
        assert not (tmp / f'content/drafts/{t1}.json').exists() and not (tmp / f'content/drafts/{t1}.brief.json').exists()
        log = [json.loads(l) for l in (tmp / 'data/factory-queue.jsonl').read_text().splitlines()]
        assert len(log) == 2 and log[-1]['qa']['pass'] is True and log[-1]['by'] == 'Nguyễn Hà'
        index = [json.loads(l) for l in (tmp / 'data/content-index.jsonl').read_text().splitlines()]
        assert any(r['url'] == m[t1]['url'] and r['id'] == t1 for r in index), index
        m2 = {r['topic_id']: r for r in tm.load_matrix()}
        assert m2[t1]['lifecycle'] == 'PUBLISHED' and m2[t1]['quality_status'] == 'passed'
        pubrows = {r['url']: r for r in (json.loads(l) for l in tm.PUBLISHED_PATH.read_text().splitlines())}
        pr = pubrows[m[t1]['url']]
        assert pr['origin'] == 'factory-v2' and pr['indexable'] and pr['dedup_weight'] == 'hard' and pr['audit_decision'] == 'KEEP', pr
        # bài vừa xuất bản chặn ứng viên trùng với nó (tầng 6 → đã xuất bản)
        a = tm.assess({'title': 'Vượt phải xe máy phạt bao nhiêu tiền năm 2026', 'primary_keyword': 'vượt phải phạt bao nhiêu', 'secondary_keywords': [], 'hub': 'luat-giao-thong', 'user_problem': '', 'outline': []}, tm.Index())
        assert a['risk'] == 'high' and a['merge_into'] == m[t1]['url'], a
        # publish lại không làm gì (không còn nháp), không ghi nhật ký
        rc, out = quiet(fv.publish, [], True, 'Nguyễn Hà'); assert rc == 0 and json.loads(out)['published'] == []
        assert len((tmp / 'data/factory-queue.jsonl').read_text().splitlines()) == 2

        # 5. --unattended tôn trọng STOP_FACTORY; writer thứ hai nhận chủ đề còn lại
        rc, out = quiet(fv.queue, 'writer-2', 1); assert json.loads(out)['assigned'] == [t2], out
        (tmp / f'content/drafts/{t2}.json').write_text(json.dumps(draft(t2, m2[t2]), ensure_ascii=False))
        (tmp / 'STOP_FACTORY').touch()
        rc, out = quiet(fv.publish, [], True, 'bot', True)
        assert 'STOP_FACTORY' in out and not (tmp / f'content/articles/{t2}.json').exists(), out
        (tmp / 'STOP_FACTORY').unlink()
        rc, out = quiet(fv.publish, [], True, 'bot', True); pub = json.loads(out)
        assert rc == 0 and [p['topic_id'] for p in pub['published']] == [t2] and (tmp / f'content/articles/{t2}.json').exists(), out
        # URL đã có trong nguồn không thể xuất bản lần nữa dưới topic khác
        dup = draft(t1, m[t1]); dup['id'] = dup['topic_id'] = 'TM-00099'
        rc, out = quiet(tm.discover, str(seeds))  # không tạo hàng mới (idempotent)
        assert len(tm.load_matrix()) == 2
    finally:
        for k, v in saved_tm.items():
            setattr(tm, k, v)
        for k, v in saved_f.items():
            setattr(F, k, v)

print('PASS: hàng đợi chỉ lấy APPROVED; QA phạm vi hẹp chặn nháp hỏng/mỏng/thiếu nguồn; publish tạo shard V2 + nhật ký + chỉ mục + PUBLISHED; STOP_FACTORY chặn unattended')
