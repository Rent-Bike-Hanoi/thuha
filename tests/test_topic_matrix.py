#!/usr/bin/env python3
"""Kiểm thử Topic Factory V2 (scripts/topic_matrix.py).

Chạy trên kho dữ liệu tổng hợp nhỏ trong thư mục tạm (không đụng data/ thật), rồi một kiểm thử khói
trên nguồn bài thật. Mọi đường dẫn của module được trỏ sang thư mục tạm trong lúc chạy.
"""
from pathlib import Path
import contextlib, importlib.util, io, json, shutil, sys, tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tm', ROOT / 'scripts/topic_matrix.py')
tm = importlib.util.module_from_spec(spec); spec.loader.exec_module(tm)


def art(url, title, keywords, hub, heads, excerpt='Tóm tắt bài viết để kiểm thử, dài hơn một trăm ký tự để qua ngưỡng excerpt của cổng kiểm tra bài.'):
    return {'url': url, 'title': title, 'keywords': keywords, 'hub': hub, 'kind': 'article', 'excerpt': excerpt,
            'sections': [[h, '<p>' + ('nội dung kiểm thử ' * 40) + '</p>'] for h in heads]}


POSTS = [
    art('/luat-giao-thong/phat-vuot-den-do-xe-may/', 'Vượt đèn đỏ xe máy phạt bao nhiêu? 4–6 triệu, trừ 4 điểm (2026)',
        'phạt vượt đèn đỏ xe máy, vượt đèn đỏ xe máy 2025, lỗi vượt đèn đỏ', 'luat-giao-thong', ['Mức phạt', 'Trừ điểm', 'Đèn vàng', 'Rẽ phải khi đèn đỏ']),
    art('/kinh-nghiem/cach-di-xe-so/', 'Cách đi xe số cho người mới: côn, sang số, lên dốc, xuống dốc', 'cách đi xe số, cách đi xe số cho người mới', 'kinh-nghiem',
        ['Côn và số', 'Sang số', 'Lên dốc', 'Xuống dốc']),
    art('/du-lich/mien-bac/ha-noi-di-moc-chau-bang-xe-may/', 'Hà Nội đi Mộc Châu bằng xe máy bao nhiêu km? Đi quốc lộ 6 thế nào',
        'hà nội đi mộc châu bằng xe máy bao nhiêu km, đường đi mộc châu bằng xe máy', 'du-lich', ['Bao nhiêu km', 'Quốc lộ 6', 'Mùa đẹp', 'Chuẩn bị xe']),
    art('/xe-may/chon-xe-so-hay-xe-ga/', 'Xe số hay xe ga: chọn theo thói quen của bạn', 'xe số hay xe ga, chọn xe số hay xe ga', 'xe-may', ['Xe số', 'Xe ga', 'Chi phí', 'Kết luận']),
    art('/luat-giao-thong/tra-cuu-phat-nguoi-xe-may/', 'Tra cứu phạt nguội xe máy 2026: cách kiểm tra và xử lý khi có vi phạm', 'tra cứu phạt nguội xe máy, phạt nguội xe máy',
        'luat-giao-thong', ['Tra cứu trên csgt.vn', 'VNeTraffic', 'Thông báo', 'Nộp phạt']),
]
SHARD = {'id': 'NH-00001', 'url': '/xe-may/hoan-kiem/honda-wave-alpha/chon-xe-nguoi-di-lam-van-phong/', 'title': 'Honda Wave Alpha tại Hoàn Kiếm: chọn xe khi đi làm giờ cao điểm sáng tối',
         'hub': 'xe-may', 'excerpt': 'Cẩm nang chọn xe Honda Wave Alpha tại Hoàn Kiếm cho người đi làm văn phòng, biểu phí và thủ tục cọc tại Nguyễn Hà.',
         'sections': [['Nhu cầu thuê', '<p>' + 'x ' * 50 + '</p>'], ['Checklist', '<p>' + 'y ' * 50 + '</p>']], 'keywords': 'chọn xe Honda Wave Alpha Hoàn Kiếm',
         'kind': 'article', 'wordCount': 100, 'intent': 'thue-xe|chọn xe|honda wave alpha|hoàn kiếm|người đi làm văn phòng|đi làm giờ cao điểm sáng tối|quãng đường dưới 5 km mỗi ngày', 'factoryVersion': 1}


@contextlib.contextmanager
def sandbox():
    saved = {k: getattr(tm, k) for k in ('ROOT', 'MATRIX_PATH', 'PUBLISHED_PATH', 'KEYWORDS_PATH', 'CACHE_DIR', 'DB_PATH', 'POSTS_PATH', 'SHARDS_DIR',
                                        'FACTS_PATH', 'FACTORY_CFG_PATH', 'LEGACY_AUDIT_CSV', 'REPORTS')}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / 'content/articles').mkdir(parents=True); (tmp / 'data').mkdir(); (tmp / 'config').mkdir(); (tmp / 'reports').mkdir(); (tmp / 'scripts').mkdir()
        shutil.copy(ROOT / 'scripts/content_factory.py', tmp / 'scripts/content_factory.py')  # audit() đọc bộ lập kế hoạch cũ từ ROOT
        (tmp / 'content/posts.json').write_text(json.dumps(POSTS, ensure_ascii=False))
        (tmp / 'content/articles/NH-00001.json').write_text(json.dumps(SHARD, ensure_ascii=False))
        shutil.copy(ROOT / 'config/business-facts.json', tmp / 'config/business-facts.json')
        shutil.copy(ROOT / 'config/content-factory.json', tmp / 'config/content-factory.json')
        (tmp / 'data/keyword-metrics.jsonl').write_text(json.dumps({'keyword': 'vượt phải phạt bao nhiêu', 'volume': None, 'source': 'test', 'checked': '2026-10-12'}) + '\n'
                                                       + json.dumps({'keyword': 'xe máy đi vào đường cao tốc phạt bao nhiêu', 'volume': 1300, 'source': 'test', 'checked': '2026-10-12'}) + '\n')
        tm.ROOT = tmp; tm.MATRIX_PATH = tmp / 'data/topic-matrix.jsonl'; tm.PUBLISHED_PATH = tmp / 'data/topic-matrix-published.jsonl'
        tm.KEYWORDS_PATH = tmp / 'data/keyword-metrics.jsonl'; tm.CACHE_DIR = tmp / 'data/cache'; tm.DB_PATH = tmp / 'data/cache/topic-index.sqlite'
        tm.POSTS_PATH = tmp / 'content/posts.json'; tm.SHARDS_DIR = tmp / 'content/articles'; tm.FACTS_PATH = tmp / 'config/business-facts.json'
        tm.FACTORY_CFG_PATH = tmp / 'config/content-factory.json'; tm.LEGACY_AUDIT_CSV = tmp / 'reports/none.csv'; tm.REPORTS = tmp / 'reports'
        try:
            yield tmp
        finally:
            for k, v in saved.items():
                setattr(tm, k, v)


def quiet(fn, *a, **kw):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = fn(*a, **kw)
    return rc, out.getvalue()


def seed(**kw):
    base = {'hub': 'luat-giao-thong', 'subtopic': 'muc-phat', 'origin': 'seed', 'user_problem': 'Người đọc muốn biết mức phạt và cách phòng tránh.'}
    base.update(kw); return base


# ── 1. Chuẩn hoá tiếng Việt: dấu phải được giữ khi so sánh nội dung ──────────
assert 'đèn' in tm.core_tokens('Vượt đèn đỏ xe máy phạt bao nhiêu') and 'đỏ' in tm.core_tokens('Vượt đèn đỏ xe máy phạt bao nhiêu'), 'mất dấu: đèn đỏ bị coi là đến đó'
assert tm.core_tokens('Mức phạt vượt đèn đỏ xe máy mới nhất dành cho sinh viên') == tm.core_tokens('Vượt đèn đỏ xe máy phạt bao nhiêu?'), 'qualifier/marker chưa được bỏ'
assert tm.permutation_key('Honda Wave Alpha tại Cầu Giấy: chọn xe khi đi làm giờ cao điểm') == tm.permutation_key('Honda Wave Alpha tại Hoàn Kiếm: chọn xe khi đi làm giờ cao điểm sáng tối')
assert tm.keyword_key('cách đi xe số cho sinh viên') == tm.keyword_key('cách đi xe số'), 'từ khoá chỉ khác đối tượng phải cùng khoá'
assert tm.intent_class('Thuê xe máy Hà Nội theo tháng') == 'transactional'
assert tm.intent_class('Xe máy không đề được phải làm sao') == 'troubleshooting'
assert tm.intent_class('Xe số hay xe ga nên chọn loại nào') == 'commercial'
assert tm.intent_class('Bến xe Gia Lâm') == 'navigational'
assert tm.intent_class('Vượt phải phạt bao nhiêu') == 'informational'
assert tm.slugify('Vượt phải xe máy phạt bao nhiêu?') == 'vuot-phai-xe-may-phat-bao-nhieu'

with sandbox() as tmp:
    rc, out = quiet(tm.sync)
    idx = tm.Index()
    assert idx.ndocs() == 6, idx.ndocs()
    hard = idx.db.execute("SELECT COUNT(*) FROM docs WHERE weight='hard'").fetchone()[0]
    assert hard == 5, 'bài xưởng V1 đã noindex phải là soft'
    pub = [json.loads(l) for l in tm.PUBLISHED_PATH.read_text().splitlines()]
    assert {r['audit_decision'] for r in pub if r['origin'] == 'factory-v1'} == {'KEEP'}  # đại diện duy nhất của nhóm → KEEP (đã noindex)
    # sync tăng dần: chạy lại không thêm gì
    rc, out = quiet(tm.sync); s = json.loads(out.strip().splitlines()[-1])
    assert s['index_added'] == 0 and s['index_updated'] == 0 and s['removed'] == 0, s

    # ── 2. Sáu tầng trùng lặp ────────────────────────────────────────────────
    def A(title, pk, hub='luat-giao-thong', **kw):
        c = {'title': title, 'primary_keyword': pk, 'secondary_keywords': [], 'hub': hub, 'user_problem': '', 'outline': []}; c.update(kw)
        return tm.assess(c, idx)
    a = A('Honda Wave Alpha tại Cầu Giấy: chọn xe khi đi làm giờ cao điểm sáng tối', 'honda wave alpha cầu giấy', 'xe-may')
    assert a['decision_hint'] == 'REJECT' and a['permutation_of'] == SHARD['url'], a           # tầng 5: hoán vị (kể cả bài V1 soft)
    a = A('Mức phạt vượt đèn đỏ xe máy mới nhất dành cho sinh viên', 'mức phạt vượt đèn đỏ xe máy')
    assert a['risk'] == 'high' and a['merge_into'] == POSTS[0]['url'], a                        # tầng 2: cùng cụm intent
    a = A('Cách đi xe số cho sinh viên mới học lái', 'cách đi xe số cho sinh viên', 'kinh-nghiem')
    assert a['decision_hint'] == 'REJECT' and any('keyword_normalized' in h['layers'] for h in a['hits']), a  # tầng 1b + 5
    # Qualifier bị bỏ chính là chủ đề: không có số liệu nhu cầu → vẫn là hoán vị (REJECT); có nhu cầu đo được ≥ P1 → tín hiệu cao, biên tập quyết
    a = A('Cách đi xe số ban đêm cho người mới: côn, đèn, quan sát', 'đi xe số ban đêm', 'kinh-nghiem')
    assert a['decision_hint'] == 'REJECT' and a['permutation_of'] == POSTS[1]['url'], a
    a = A('Cách đi xe số ban đêm cho người mới: côn, đèn, quan sát', 'đi xe số ban đêm', 'kinh-nghiem', keyword_volume=150)
    assert a['permutation_of'] is None and a['risk'] == 'high' and a['decision_hint'] == 'MERGE-CANDIDATE' \
        and any('permutation_with_demand' in h['layers'] for h in a['hits']), a
    a = A('Phạt nguội xe máy là gì? Khác gì phạt trực tiếp', 'phạt nguội xe máy')
    assert a['risk'] == 'high' and any('exact_keyword' in h['layers'] for h in a['hits']), a      # tầng 1: trùng từ khoá
    a = A('Hà Nội đi Mộc Châu bao nhiêu km? Đi xe máy theo quốc lộ 6', 'hà nội đi mộc châu bao nhiêu km', 'du-lich')
    assert a['risk'] == 'high' and a['merge_into'] == POSTS[2]['url'], a                        # tầng 4: tiêu đề + từ khoá chuẩn hoá
    a = A('Xe số hay xe ga: nên chọn loại nào để đi làm trong phố', 'xe số hay xe ga', 'xe-may')
    assert a['risk'] == 'high' and a['merge_into'] == POSTS[3]['url'] and a['decision_hint'] in ('REJECT', 'MERGE-CANDIDATE'), a  # cùng câu hỏi với bài viết tay
    a = A('Vượt phải xe máy phạt bao nhiêu? Khi nào được vượt bên phải', 'vượt phải phạt bao nhiêu')
    assert a['risk'] != 'high' and a['permutation_of'] is None and a['decision_hint'] == 'NEEDS-RESEARCH', a  # chủ đề mới: không bị chặn, cần bằng chứng
    a = A('Vượt đèn đỏ bị trừ mấy điểm bằng lái?', 'vượt đèn đỏ trừ mấy điểm')
    assert a['risk'] in ('medium', 'high') and a['merge_into'] == POSTS[0]['url'], a             # câu hỏi con: tín hiệu để biên tập quyết, không tự coi là khác bài
    # tầng 3: outline giống nhau cũng bị đánh dấu
    a = A('Lỗi đèn tín hiệu với xe máy: phạt, điểm, rẽ phải', 'lỗi đèn tín hiệu xe máy', outline=['Mức phạt', 'Trừ điểm', 'Đèn vàng', 'Rẽ phải khi đèn đỏ'])
    assert any('outline' in h['layers'] for h in a['hits']), a

    # ── 3. discover → cổng kiểm tra → vòng đời ───────────────────────────────
    seeds = tmp / 'seeds.jsonl'
    rows = [
        seed(title='Vượt phải xe máy phạt bao nhiêu? Khi nào được vượt bên phải', primary_keyword='vượt phải phạt bao nhiêu',
             information_gain='Bài /luat-giao-thong/phat-vuot-den-do-xe-may/ chỉ nói đèn tín hiệu; bài này nêu điểm đ khoản 3 Điều 7: vượt bên phải khi không được phép, 600.000–800.000đ, và các trường hợp được vượt phải.',
             evidence=[{'type': 'law', 'source': 'https://xaydungchinhsach.chinhphu.vn/...', 'quote': 'đ) Vượt bên phải trong trường hợp không được phép', 'checked': '2026-10-12'}]),
        seed(title='Mức phạt vượt đèn đỏ xe máy mới nhất dành cho sinh viên', primary_keyword='mức phạt vượt đèn đỏ xe máy'),          # trùng cao → RESEARCH/MERGE-CANDIDATE, không duyệt được nếu không override
        seed(title='Honda Wave Alpha tại Cầu Giấy: chọn xe khi đi làm giờ cao điểm sáng tối', primary_keyword='honda wave alpha cầu giấy', hub='xe-may', subtopic='chon-xe'),  # hoán vị → REJECTED
        seed(title='Xe máy đi vào đường cao tốc phạt bao nhiêu? Mức phạt và trừ điểm', primary_keyword='xe máy đi vào đường cao tốc phạt bao nhiêu'),  # thiếu bằng chứng → RESEARCH
        seed(title='Xe đạp địa hình: bảo dưỡng phanh đĩa', primary_keyword='bảo dưỡng phanh đĩa xe đạp', hub='xe-dap', subtopic=None),   # hub tắt → lỗi cổng
        seed(title='Vượt phải xe máy bị phạt thế nào cho người mới lấy bằng', primary_keyword='vượt phải phạt bao nhiêu cho người mới'),  # hoán vị của ứng viên trước trong cùng file (tầng 6)
    ]
    seeds.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
    rc, out = quiet(tm.discover, str(seeds)); summary = json.loads(out)['summary']
    m = {r['title']: r for r in tm.load_matrix()}
    dup = m[rows[1]['title']]
    assert dup['lifecycle'] == 'RESEARCH' and dup['audit_decision'] == 'MERGE-CANDIDATE' and dup['merge_into'] == POSTS[0]['url'] \
        and any('trùng lặp mức cao' in e for e in dup['gate_errors']), dup  # tương đồng cao = tín hiệu cho biên tập, không tự REJECT
    assert m[rows[2]['title']]['lifecycle'] == 'REJECTED' and 'hoán vị' in m[rows[2]['title']]['rejected_reason']
    assert rows[5]['title'] not in m and summary.get('skipped_existing_keyword') == 1, 'ứng viên cùng khoá từ khoá với ứng viên trước trong lô phải bị bỏ qua (idempotent)'
    n_before = len(tm.load_matrix()); quiet(tm.discover, str(seeds))
    assert len(tm.load_matrix()) == n_before, 'discover chạy lại cùng file không được tạo thêm hàng'
    assert m[rows[3]['title']]['lifecycle'] == 'RESEARCH' and m[rows[3]['title']]['keyword_volume'] == 1300 and m[rows[3]['title']]['priority'] == 'P0'
    # approve: fail-closed khi thiếu bằng chứng / thiếu information gain
    rc, out = quiet(tm.approve, m[rows[3]['title']]['topic_id'], 'test')
    assert rc == 1 and 'bằng chứng' in out, out
    # --update: seed bổ sung bằng chứng + information_gain → hàng RESEARCH được làm mới (không tạo hàng mới, không trùng bằng chứng khối lượng)
    rows[3] = dict(rows[3], information_gain='Chưa có bài nào về cao tốc: điểm b khoản 7 Điều 7 (4–6 triệu, trừ 6 điểm) và danh sách cao tốc quanh Hà Nội cấm xe máy.',
                   evidence=[{'type': 'law', 'source': 'https://xaydungchinhsach.chinhphu.vn/...', 'quote': 'b) Điều khiển xe đi vào đường cao tốc', 'checked': '2026-10-12'}])
    rows[1] = dict(rows[1], information_gain='x' * 80)  # hàng MERGE-CANDIDATE: làm mới không được nới lỏng lỗi cổng
    seeds.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
    rc, out = quiet(tm.discover, str(seeds), update=True); summary = json.loads(out)['summary']
    m = {r['title']: r for r in tm.load_matrix()}
    assert len(tm.load_matrix()) == n_before and summary.get('refreshed') == 2, summary
    hw = m[rows[3]['title']]
    assert hw['lifecycle'] == 'PLANNED' and hw['research_status'] == 'verified' and sum(e['type'] == 'keyword-volume' for e in hw['evidence']) == 1 and hw['keyword_volume'] == 1300, hw
    assert m[rows[1]['title']]['lifecycle'] == 'RESEARCH' and m[rows[1]['title']]['gate_errors'], 'làm mới seed không được xoá lỗi trùng lặp mức cao'
    assert any('đang tắt' in e for e in m[rows[4]['title']]['gate_errors']), m[rows[4]['title']]['gate_errors']
    good = m[rows[0]['title']]
    assert good['lifecycle'] in ('PLANNED', 'RESEARCH') and good['cannibalization_risk'] != 'high' and good['keyword_source'].endswith('(no volume data)'), good
    assert good['url'] == '/luat-giao-thong/vuot-phai-xe-may-phat-bao-nhieu/', good['url']

    # approve hợp lệ; writer chỉ nhận APPROVED
    rc, out = quiet(tm.approve, good['topic_id'], 'Nguyễn Hà', 'ok')
    assert rc == 0, out
    rc, out = quiet(tm.next_topics, 'writer-1', 5)
    assigned = json.loads(out)['assigned']
    assert [x['topic_id'] for x in assigned] == [good['topic_id']], assigned
    assert tm.load_matrix()[0]['lifecycle'] == 'WRITING'
    # chuyển trạng thái sai bị chặn; PUBLISHED cần URL có thật trong nguồn
    try:
        tm.transition({'topic_id': 'x', 'lifecycle': 'PLANNED'}, 'PUBLISHED'); raise AssertionError('PLANNED→PUBLISHED phải bị chặn')
    except ValueError:
        pass
    try:
        quiet(tm.set_lifecycle, good['topic_id'], 'QA'); quiet(tm.set_lifecycle, good['topic_id'], 'PUBLISHED'); raise AssertionError('PUBLISHED khi chưa có bài phải bị chặn')
    except SystemExit:
        pass
    # validate: hàng APPROVED/WRITING hợp lệ → exit 0; cố tình làm hỏng → exit 1 (fail-closed)
    rc, out = quiet(tm.validate); assert rc == 0, out
    rows_now = tm.load_matrix(); rows_now[0]['information_gain'] = ''; tm.save_matrix(rows_now)
    rc, out = quiet(tm.validate); assert rc == 1, 'validate phải fail khi hàng đang WRITING mất information_gain'

    # ── 4. check-article: QA phạm vi hẹp ─────────────────────────────────────
    new_art = art('/luat-giao-thong/vuot-phai-xe-may-phat-bao-nhieu/', 'Vượt phải xe máy phạt bao nhiêu? Khi nào được vượt bên phải', 'vượt phải phạt bao nhiêu', 'luat-giao-thong',
                  ['Câu trả lời ngắn', 'Khi nào được vượt phải', 'Mức phạt', 'Tra cứu'])
    new_art['sections'][0][1] += '<p>Xem thêm <a href="/luat-giao-thong/phat-vuot-den-do-xe-may/">vượt đèn đỏ</a> và <a href="/khong-ton-tai/">hỏng</a>. Gọi 0999 123 456.</p>'
    f = tmp / 'new.json'; f.write_text(json.dumps(new_art, ensure_ascii=False))
    rc, out = quiet(tm.check_article, str(f)); res = json.loads(out)[0]
    assert rc == 1 and any('hỏng' in x for x in res['fails']) and any('điện thoại' in x for x in res['fails']), res
    dup_art = art('/luat-giao-thong/vuot-den-do-xe-may-sinh-vien/', 'Vượt đèn đỏ xe máy phạt bao nhiêu với sinh viên', 'vượt đèn đỏ xe máy phạt bao nhiêu', 'luat-giao-thong', ['a', 'b', 'c', 'd'])
    f.write_text(json.dumps(dup_art, ensure_ascii=False))
    rc, out = quiet(tm.check_article, str(f)); res = json.loads(out)[0]
    assert rc == 1 and any('hoán vị' in x or 'trùng lặp' in x for x in res['fails']), res

    # ── 5. audit chạy được, không đụng dữ liệu nguồn ─────────────────────────
    (tmp / 'data/factory-state.json').write_text(json.dumps({'next_sequence': 3678}))
    rc, out = quiet(tm.audit, 5)
    assert (tmp / 'reports/topic-factory-v2-audit.md').exists() and (tmp / 'reports/slot-audit-5.csv').exists()

# ── 6. Kiểm thử khói trên nguồn thật: chỉ mục dựng được, mỗi bài viết tay là một cụm riêng ───
with tempfile.TemporaryDirectory() as tmp:
    saved = (tm.DB_PATH, tm.PUBLISHED_PATH)
    tm.DB_PATH = Path(tmp) / 'idx.sqlite'; tm.PUBLISHED_PATH = Path(tmp) / 'pub.jsonl'
    try:
        rc, out = quiet(tm.sync)
        idx = tm.Index(tm.DB_PATH)
        pub = [json.loads(l) for l in tm.PUBLISHED_PATH.read_text().splitlines()]
        hand = [r for r in pub if r['origin'] == 'hand-written']
        live_matrix = [r for r in tm.load_matrix() if r['lifecycle'] not in ('REJECTED', 'PUBLISHED')]  # tầng 6: hàng chưa loại/chưa xuất bản nằm trong chỉ mục; bài đã xuất bản do PUB-… đại diện
        assert len(hand) >= 73 and idx.ndocs() == len(pub) + len(live_matrix), (len(hand), idx.ndocs(), len(pub), len(live_matrix))
        clusters = [r['cluster'] for r in hand]
        dup_clusters = {c for c in clusters if clusters.count(c) > 1}
        assert not dup_clusters, 'bài viết tay trùng cụm intent: ' + str(dup_clusters)
        assert all(r['audit_decision'] in tm.DECISIONS for r in pub)
    finally:
        tm.DB_PATH, tm.PUBLISHED_PATH = saved

print('PASS: chuẩn hoá giữ dấu; 6 tầng trùng lặp; discover/approve/next fail-closed; check-article; audit; chỉ mục thật không trùng cụm bài viết tay')
