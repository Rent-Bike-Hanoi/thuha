#!/usr/bin/env python3
"""Topic Factory V2 — điều phối viên duy nhất của đường xuất bản:

  hàng đợi (APPROVED → WRITING) → nháp của writer → QA phạm vi hẹp → xuất bản shard → nhật ký → chỉ mục

  queue   --writer W [--n N] [--hub H]          lấy hàng APPROVED từ ma trận (→ WRITING), ghi brief content/drafts/<TM>.brief.json
  qa      [TM ...] [--all]                      QA nháp content/drafts/<TM>.json; đạt → QA, không đạt → vẫn WRITING (không ghi nhật ký)
  publish [TM ...] [--all] --by NAME [--unattended]
                                                nháp đạt QA → content/articles/<TM>.json (factoryVersion 2), nhật ký hàng đợi append-only,
                                                reindex, hàng → PUBLISHED, sync chỉ mục trùng lặp. --unattended tôn trọng STOP_FACTORY và v2.enabled.
  status                                        brief/nháp/hàng theo vòng đời

Writer chỉ nhận brief và viết nháp; writer không duyệt chủ đề, không đổi vòng đời, không ghi vào content/articles/.
content/drafts/ không phải nguồn bài: build.py, sitemap, chỉ mục tìm kiếm không đọc thư mục này.
Không gọi API AI hay mạng: nội dung nháp do người/agent viết từ brief và bằng chứng đã đối chiếu.
"""
import argparse, collections, contextlib, datetime, importlib.util, io, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


tm = _load('topic_matrix', HERE / 'topic_matrix.py')
F = _load('content_factory', HERE / 'content_factory.py')  # chỉ dùng reindex() và nhật ký hàng đợi cùng định dạng với xưởng V1

TONES = ('gold', 'black', 'white')
DRAFT_RULES = [
    'Chỉ viết đúng ý định trong brief; không mở rộng sang câu hỏi của bài đã có (xem overlap/merge_into).',
    'Mọi con số, mức phạt, giá, điều khoản phải có trong evidence/sources hoặc config/business-facts.json; không được bịa.',
    'Trích dẫn nguồn ngay trong bài (href tới văn bản gốc) và liệt kê trong trường sources.',
    'Tối thiểu 700 từ và 4 mục; độ dài theo nhu cầu người đọc, không nhồi chữ.',
    'Ít nhất 2 liên kết nội bộ tới bài cùng cụm/hub (suggested_internal_links, merge_into); không liên kết hỏng.',
    'Số điện thoại duy nhất: theo business-facts; không nhắc rentbikehanoi.com.',
    'Tiêu đề giữ từ khoá chính; keywords = từ khoá chính, từ khoá phụ (phân cách bằng dấu phẩy).',
    'FAQ (faq) 3–5 câu nếu bài có câu hỏi phụ thật; không lặp lại nội dung mục chính.',
]


def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def drafts_dir(): return tm.ROOT / 'content/drafts'
def queue_path(): return tm.ROOT / 'data/factory-queue.jsonl'
def brief_path(tid): return drafts_dir() / f'{tid}.brief.json'
def draft_path(tid): return drafts_dir() / f'{tid}.json'


def cfg_v2():
    cfg = json.loads(tm.FACTORY_CFG_PATH.read_text()) if tm.FACTORY_CFG_PATH.exists() else {}
    return {'enabled': True, 'min_words': 700, 'max_publish_per_run': 10, **(cfg.get('v2') or {})}


def _capture(fn, *a, **kw):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = fn(*a, **kw)
    return rc, out.getvalue()


def _row(rows, tid):
    row = next((r for r in rows if r['topic_id'] == tid), None)
    if not row:
        raise SystemExit('không tìm thấy ' + tid)
    return row


def _log(entry):
    queue_path().parent.mkdir(parents=True, exist_ok=True)
    with queue_path().open('a', encoding='utf-8') as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + '\n')


# ── Hàng đợi ─────────────────────────────────────────────────────────────────
def queue(writer, n=1, hub=None, ids=()):
    rc, out = _capture(tm.next_topics, writer, n, hub, ids)
    assigned = json.loads(out)['assigned']
    drafts_dir().mkdir(parents=True, exist_ok=True)
    hub_paths = {h: c.get('path') for h, c in tm.UNIVERSE['hubs'].items()}
    paths = []
    for t in assigned:
        template = {
            'id': t['topic_id'], 'url': t['url'], 'title': t['title'], 'hub': t['hub'], 'parent': hub_paths.get(t['hub'], '/'),
            'kind': 'article', 'art': '', 'tone': 'gold', 'keywords': ', '.join([t['primary_keyword']] + list(t.get('secondary_keywords') or [])),
            'excerpt': '', 'sections': [[h, '<p></p>'] for h in (t.get('outline') or [])] or [['', '<p></p>']],
            'faqTitle': '', 'faq': [],
            'sources': [{k: e.get(k) for k in ('type', 'source', 'quote', 'checked') if e.get(k) is not None} for e in (t.get('evidence') or []) if e.get('type') != 'keyword-volume'],
            'factoryVersion': 2, 'topic_id': t['topic_id'],
        }
        brief = {'writer': writer, 'queued': now(), 'topic': t, 'rules': DRAFT_RULES, 'draft_file': str(draft_path(t['topic_id']).relative_to(tm.ROOT)), 'draft_template': template}
        brief_path(t['topic_id']).write_text(json.dumps(brief, ensure_ascii=False, indent=2) + '\n')
        paths.append(str(brief_path(t['topic_id']).relative_to(tm.ROOT)))
    print(json.dumps({'writer': writer, 'assigned': [t['topic_id'] for t in assigned], 'briefs': paths}, ensure_ascii=False, indent=2))
    return 0


# ── QA phạm vi hẹp ───────────────────────────────────────────────────────────
def qa_draft(tid, rows, idx, facts, source_urls, cfg=None):
    cfg = cfg or cfg_v2()
    row = _row(rows, tid)
    res = {'topic_id': tid, 'url': row.get('url'), 'pass': False, 'fails': [], 'warnings': [], 'words': 0}
    if row['lifecycle'] not in ('WRITING', 'QA'):
        res['fails'].append(f'hàng đang ở {row["lifecycle"]}, chỉ QA được hàng WRITING/QA'); return res
    p = draft_path(tid)
    if not p.exists():
        res['fails'].append('chưa có nháp ' + str(p.relative_to(tm.ROOT))); return res
    try:
        art = json.loads(p.read_text())
    except Exception as exc:
        res['fails'].append(f'nháp không phải JSON hợp lệ: {exc}'); return res
    fails = res['fails']
    if art.get('id') != tid or art.get('topic_id') != tid:
        fails.append('id/topic_id của nháp phải là ' + tid)
    if art.get('url') != row.get('url'):
        fails.append(f'url nháp {art.get("url")} khác url trong ma trận {row.get("url")}')
    if art.get('hub') != row.get('hub'):
        fails.append('hub nháp khác hub trong ma trận')
    if int(art.get('factoryVersion') or 0) != 2:
        fails.append('factoryVersion phải là 2')
    if art.get('kind') != 'article':
        fails.append('kind phải là article')
    hub_path = tm.hub_cfg(row.get('hub')).get('path') or '/'
    if not str(art.get('parent') or '').startswith(hub_path) and not (row.get('hub') == 'thue-xe' and str(art.get('parent') or '').startswith('/thue-xe')):
        fails.append('parent phải nằm dưới ' + hub_path)
    if art.get('tone') not in TONES or not art.get('art'):
        fails.append('thiếu art (nhãn ngắn) hoặc tone không thuộc ' + '/'.join(TONES))
    secs = art.get('sections')
    block = re.compile(r'<(p|ul|ol|table|div)\b')  # mục chỉ gồm danh sách hoặc bảng vẫn là HTML khối hợp lệ
    if not (isinstance(secs, list) and secs and all(isinstance(s, list) and len(s) == 2 and str(s[0]).strip() and block.search(str(s[1])) for s in secs)):
        fails.append('sections phải là danh sách [tiêu đề mục, html có khối <p>/<ul>/<ol>/<table>]')
    if art.get('faq') and not all(isinstance(q, list) and len(q) == 2 and q[0] and q[1] for q in art['faq']):
        fails.append('faq phải là danh sách [câu hỏi, trả lời]')
    pk = row.get('primary_keyword') or ''
    core = tm.core_tokens(pk); tt = set(tm.toks(art.get('title', '')))
    if core and sum(t in tt for t in core) < max(1, -(-len(core) * 6 // 10)):
        fails.append('tiêu đề không giữ từ lõi của từ khoá chính: ' + pk)
    if tm.fold(pk) not in tm.fold(str(art.get('keywords', ''))):
        fails.append('keywords phải chứa từ khoá chính: ' + pk)
    hc = tm.hub_cfg(row.get('hub'))
    srcs = art.get('sources') or []
    if hc.get('requires_sources') and not any((s.get('source') or s.get('type') in ('business-facts', 'owner')) for s in srcs):
        fails.append(f'hub {row.get("hub")} yêu cầu sources (nguồn đã đối chiếu) trong nháp')
    if fails:
        return res
    chk = tm.check_article_dict(art, idx, rows, facts, source_urls, tid)
    res.update({'words': chk['words'], 'overlap_risk': chk['overlap_risk'], 'overlap': chk['overlap'], 'warnings': chk['warnings']})
    fails.extend(chk['fails'])
    if chk['words'] < int(cfg.get('min_words', 700)):
        fails.append(f'dưới {cfg.get("min_words", 700)} từ ({chk["words"]})')
    res['pass'] = not fails
    return res


def _qa_context():
    rows = tm.load_matrix(); idx = tm.Index()
    facts = json.loads(tm.FACTS_PATH.read_text()); sources = tm.load_sources()
    return rows, idx, facts, {s['url']: s for s in sources}


def qa(ids=(), all_=False):
    rows, idx, facts, sources = _qa_context()
    ids = list(ids) or ([r['topic_id'] for r in rows if r['lifecycle'] in ('WRITING', 'QA') and draft_path(r['topic_id']).exists()] if all_ else [])
    results = []
    for tid in ids:
        res = qa_draft(tid, rows, idx, facts, set(sources))
        row = _row(rows, tid)
        if res['pass'] and row['lifecycle'] == 'WRITING':
            tm.transition(row, 'QA', reason='QA phạm vi hẹp đạt')
        row['quality_status'] = 'passed' if res['pass'] else 'failed'
        row['qa_result'] = {'at': now(), 'pass': res['pass'], 'fails': res['fails'], 'warnings': res['warnings'], 'words': res['words']}
        results.append(res)
    tm.save_matrix(rows); idx.close()
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if results and all(r['pass'] for r in results) else 1


# ── Xuất bản ─────────────────────────────────────────────────────────────────
def publish(ids=(), all_=False, by='', unattended=False):
    cfg = cfg_v2()
    if unattended:
        if (tm.ROOT / 'STOP_FACTORY').exists():
            print('Factory paused by STOP_FACTORY. Skipping publish.'); return 0
        if not cfg.get('enabled', True):
            print('Topic Factory V2 disabled: "v2.enabled" is false in config/content-factory.json. Skipping publish.'); return 0
    elif (tm.ROOT / 'STOP_FACTORY').exists():
        print('Lưu ý: STOP_FACTORY đang tồn tại; xuất bản thủ công vẫn chạy vì thay đổi đi qua pull request do chủ cửa hàng duyệt.', file=sys.stderr)
    if not by:
        raise SystemExit('cần --by NAME (người/agent chịu trách nhiệm xuất bản)')
    rows, idx, facts, sources = _qa_context()
    ids = list(ids) or ([r['topic_id'] for r in rows if r['lifecycle'] in ('WRITING', 'QA') and draft_path(r['topic_id']).exists()] if all_ else [])
    if unattended:
        ids = ids[:int(cfg.get('max_publish_per_run', 10))]
    published, rejected = [], []
    for tid in ids:
        row = _row(rows, tid)
        res = qa_draft(tid, rows, idx, facts, set(sources), cfg)
        target = tm.SHARDS_DIR / f'{tid}.json'
        if res['pass'] and (target.exists() or row.get('url') in sources):
            res['pass'] = False; res['fails'].append('URL/shard đã tồn tại trong nguồn bài: ' + str(row.get('url')))
        entry = {'timestamp': now(), 'sequence': None, 'id': tid, 'url': row.get('url'), 'intent': row.get('cluster'), 'writer': row.get('assigned_to'),
                 'factoryVersion': 2, 'by': by, 'qa': {'pass': res['pass'], 'fails': res['fails'], 'warnings': res['warnings'], 'words': res['words'], 'overlap_risk': res.get('overlap_risk')}}
        if not res['pass']:
            row['quality_status'] = 'failed'; row['qa_result'] = {'at': now(), **entry['qa']}
            _log(entry); rejected.append(res); continue
        art = json.loads(draft_path(tid).read_text())
        art.update({'factoryVersion': 2, 'topic_id': tid, 'publishedAt': entry['timestamp'], 'publishedBy': by})
        tm.SHARDS_DIR.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(art, ensure_ascii=False, indent=2) + '\n')
        draft_path(tid).unlink()
        if brief_path(tid).exists():
            brief_path(tid).unlink()
        _log(entry)
        sources[row['url']] = art
        if row['lifecycle'] == 'WRITING':
            tm.transition(row, 'QA', reason='QA phạm vi hẹp đạt khi xuất bản')
        row['quality_status'] = 'passed'; row['qa_result'] = {'at': now(), **entry['qa']}
        published.append({'topic_id': tid, 'url': row['url'], 'shard': str(target.relative_to(tm.ROOT)), 'words': res['words']})
    tm.save_matrix(rows); idx.close()
    if published:
        F.reindex()
        for p in published:  # URL đã có trong nguồn bài → được phép chuyển PUBLISHED; chỉ mục trùng lặp cập nhật tăng dần
            _capture(tm.set_lifecycle, p['topic_id'], 'PUBLISHED', 'factory_v2 publish', None, by)
        tm.sync(verbose=False)
    print(json.dumps({'published': published, 'rejected': [{'topic_id': r['topic_id'], 'fails': r['fails']} for r in rejected],
                      'unattended': unattended, 'by': by}, ensure_ascii=False, indent=2))
    return 0 if not rejected else 1


def status():
    rows = tm.load_matrix()
    briefs = sorted(p.name for p in drafts_dir().glob('*.brief.json')) if drafts_dir().exists() else []
    drafts = sorted(p.name for p in drafts_dir().glob('*.json') if not p.name.endswith('.brief.json')) if drafts_dir().exists() else []
    print(json.dumps({'by_lifecycle': collections.Counter(r['lifecycle'] for r in rows), 'briefs': briefs, 'drafts': drafts,
                      'writing': [(r['topic_id'], r.get('assigned_to')) for r in rows if r['lifecycle'] == 'WRITING'],
                      'qa_passed_waiting_publish': [r['topic_id'] for r in rows if r['lifecycle'] == 'QA'],
                      'stop_factory': (tm.ROOT / 'STOP_FACTORY').exists(), 'v2': cfg_v2()}, ensure_ascii=False, indent=2))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    q = sp.add_parser('queue'); q.add_argument('--writer', required=True); q.add_argument('--n', type=int, default=1); q.add_argument('--hub')
    q.add_argument('--topic', action='append', default=[], help='chỉ giao chủ đề APPROVED có mã này (lặp lại được)')
    a = sp.add_parser('qa'); a.add_argument('ids', nargs='*'); a.add_argument('--all', action='store_true')
    p = sp.add_parser('publish'); p.add_argument('ids', nargs='*'); p.add_argument('--all', action='store_true'); p.add_argument('--by', default=''); p.add_argument('--unattended', action='store_true')
    sp.add_parser('status')
    args = ap.parse_args()
    if args.cmd == 'queue': return queue(args.writer, args.n, args.hub, args.topic)
    if args.cmd == 'qa': return qa(args.ids, args.all)
    if args.cmd == 'publish': return publish(args.ids, args.all, args.by, args.unattended)
    return status()


if __name__ == '__main__':
    sys.exit(main())
