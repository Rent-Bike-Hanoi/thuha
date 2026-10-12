#!/usr/bin/env python3
"""Topic Factory V2: Master SEO Topic Matrix, kiểm tra trùng lặp nhiều tầng và vòng đời chủ đề.

Chỉ dùng thư viện chuẩn của Python. Không gọi API ngoài.

Dữ liệu
  config/topic-universe.json         vũ trụ chủ đề: hub → subtopic → intent, trục qualifier, ngưỡng
  data/topic-matrix.jsonl            MA TRẬN CHÍNH (nguồn sự thật cho chủ đề PLANNED → PUBLISHED)
  data/topic-matrix-published.jsonl  dẫn xuất từ content/posts.json + content/articles/ bằng `sync`
  data/keyword-metrics.jsonl         số liệu từ khoá đã tra (nguồn, ngày); không tự bịa
  data/cache/topic-index.sqlite      chỉ mục trùng lặp, tái tạo được, cập nhật tăng dần theo sha256

Lệnh
  sync                 cập nhật hàng PUBLISHED và chỉ mục từ nguồn bài (tăng dần)
  discover FILE        nạp ứng viên chủ đề từ file seeds JSONL, chạy cổng kiểm tra, ghi vào ma trận
                       (--update: làm mới bằng chứng/information_gain/outline của hàng PLANNED/RESEARCH cùng từ khoá)
  validate             chạy lại cổng kiểm tra cho mọi hàng chưa xuất bản; lỗi → exit 1 (fail-closed)
  approve ID --by TÊN  duyệt biên tập (chỉ khi qua cổng; không bao giờ tự động)
  next --writer TÊN    cấp topic APPROVED cho writer (chuyển sang WRITING); writer không tự tạo topic
  set ID --lifecycle   chuyển trạng thái có kiểm soát (WRITING→QA→PUBLISHED, hoặc REJECTED)
  check-article FILE   QA phạm vi hẹp cho một bài đã viết (trùng lặp, facts, link, từ cấm)
  audit                báo cáo reports/topic-factory-v2-audit.md (trùng lặp bài cũ, slot cũ, ma trận)
  status | export      thống kê | xuất CSV
"""
from pathlib import Path
import argparse, collections, csv, datetime, hashlib, json, math, re, sqlite3, sys, unicodedata

ROOT = Path(__file__).resolve().parents[1]
UNIVERSE_PATH = ROOT / 'config/topic-universe.json'
MATRIX_PATH = ROOT / 'data/topic-matrix.jsonl'
PUBLISHED_PATH = ROOT / 'data/topic-matrix-published.jsonl'
KEYWORDS_PATH = ROOT / 'data/keyword-metrics.jsonl'
CACHE_DIR = ROOT / 'data/cache'
DB_PATH = CACHE_DIR / 'topic-index.sqlite'
POSTS_PATH = ROOT / 'content/posts.json'
SHARDS_DIR = ROOT / 'content/articles'
FACTS_PATH = ROOT / 'config/business-facts.json'
FACTORY_CFG_PATH = ROOT / 'config/content-factory.json'
LEGACY_AUDIT_CSV = ROOT / 'reports/factory-audit.csv'
REPORTS = ROOT / 'reports'
# Chỉ mục tự tái tạo khi mã hoặc vũ trụ chủ đề (stopword, qualifier, ngưỡng) thay đổi.
SCHEMA_VERSION = '4:' + hashlib.sha256(UNIVERSE_PATH.read_bytes()).hexdigest()[:12]

LIFECYCLE = ['PLANNED', 'RESEARCH', 'APPROVED', 'WRITING', 'QA', 'PUBLISHED', 'REJECTED']
TRANSITIONS = {
    'PLANNED': {'RESEARCH', 'APPROVED', 'REJECTED'},
    'RESEARCH': {'PLANNED', 'APPROVED', 'REJECTED'},
    'APPROVED': {'WRITING', 'RESEARCH', 'REJECTED'},
    'WRITING': {'QA', 'APPROVED', 'REJECTED'},
    'QA': {'PUBLISHED', 'WRITING', 'REJECTED'},
    'PUBLISHED': set(),
    'REJECTED': {'PLANNED'},
}
DECISIONS = ['KEEP', 'REWRITE', 'MERGE-CANDIDATE', 'REJECT', 'NEEDS-RESEARCH']
LEGACY_MAP = {'GIU': 'KEEP', 'GIU_SUA': 'REWRITE', 'XEM_LAI': 'REWRITE', 'GOP': 'MERGE-CANDIDATE', 'BO': 'REJECT'}
UNIVERSE = json.loads(UNIVERSE_PATH.read_text())
TH = UNIVERSE['dedup_thresholds']
RULES = UNIVERSE['approval_rules']


def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
def today(): return datetime.date.today().isoformat()


# ── Chuẩn hoá tiếng Việt ─────────────────────────────────────────────────────
def fold(s):
    """Bỏ dấu, chữ thường, đ→d; chỉ dùng cho slug và so khớp qualifier. KHÔNG dùng để so sánh nội dung."""
    s = unicodedata.normalize('NFD', str(s or '').lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn').replace('đ', 'd')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9]+', ' ', s)).strip()


def slugify(s):
    return re.sub(r'-+', '-', fold(s).replace(' ', '-')).strip('-')


STOP = set(UNIVERSE['stopwords'])
MARKERS = set(UNIVERSE['intent_markers'])
_QUAL_BY_AXIS = {axis: {tuple(q.split()) for q in lst} for axis, lst in UNIVERSE['qualifier_axes'].items()}
_QUAL_CACHE = {}
# Khoá từ khoá giữ trục "context": bối cảnh (trời mưa, ban đêm, giờ cao điểm) có thể chính là chủ đề tìm kiếm,
# không được gộp "đi xe máy mùa đông" với "đi xe máy trời mưa". Khoá hoán vị tiêu đề vẫn bỏ mọi trục (bắt title V1).
KEYWORD_AXES = frozenset(a for a in UNIVERSE['qualifier_axes'] if a != 'context')
_WORD_RE = re.compile(r'[^\W_]+', re.UNICODE)


def _qual_phrases(axes=None):
    key = frozenset(axes) if axes is not None else None
    if key not in _QUAL_CACHE:
        sel = [a for a in _QUAL_BY_AXIS if key is None or a in key]
        _QUAL_CACHE[key] = sorted({p for a in sel for p in _QUAL_BY_AXIS[a]}, key=len, reverse=True)
    return _QUAL_CACHE[key]


def toks(text):
    """Token chữ thường, giữ dấu (NFC)."""
    return [unicodedata.normalize('NFC', t) for t in _WORD_RE.findall(str(text or '').lower())]


def strip_qualifiers(tokens_list, axes=None):
    """Bỏ cụm chỉ quận, đối tượng, bối cảnh, thời lượng, nhóm, năm, từ đệm (so khớp trên dạng bỏ dấu của token).
    axes=None: mọi trục; truyền tập trục để giữ lại một số trục (xem KEYWORD_AXES)."""
    folded = [fold(t) or t for t in tokens_list]
    keep = [True] * len(folded)
    for phrase in _qual_phrases(axes):
        n = len(phrase)
        for i in range(len(folded) - n + 1):
            if all(keep[i:i + n]) and tuple(folded[i:i + n]) == phrase:
                for j in range(i, i + n):
                    keep[j] = False
    return [t for t, k in zip(tokens_list, keep) if k and not re.fullmatch(r'(19|20)\d{2}', t)]


def head(text):
    """Phần chính của tiêu đề (trước ':', '?', '|', ' – '). Nếu quá ngắn thì dùng cả tiêu đề."""
    text = str(text or '')
    part = re.split(r'[:?|]|\s[–—-]\s', text, maxsplit=1)[0]
    return part if len(toks(part)) >= 3 else text


def tokens(text):
    """Token nội dung cho túi từ TF-IDF: giữ qualifier, bỏ stopword."""
    return [t for t in toks(text) if (len(t) >= 2 or t.isdigit()) and t not in STOP]


def core_tokens(text):
    """Token lõi của câu hỏi: phần đầu tiêu đề, bỏ qualifier, stopword, từ đánh dấu intent và số."""
    return sorted({t for t in strip_qualifiers(toks(head(text))) if len(t) >= 2 and t not in STOP and t not in MARKERS and not t.isdigit()})


def permutation_key(text):
    """Khoá hoán vị: token phần đầu tiêu đề (kể cả từ đánh dấu) sau khi bỏ qualifier và stopword.
    Hai tiêu đề chỉ khác nhau ở quận/đối tượng/bối cảnh/năm có cùng khoá → bài hoán vị template.
    Phần đầu quá ngắn (dưới 4 token, ví dụ chỉ là tên xe) thì dùng cả tiêu đề để tránh bắt nhầm."""
    key = {t for t in strip_qualifiers(toks(head(text))) if len(t) >= 2 and t not in STOP}
    if len(key) < 4:
        key = {t for t in strip_qualifiers(toks(text)) if len(t) >= 2 and t not in STOP}
    return ' '.join(sorted(key))


def keyword_key(kw):
    """Khoá từ khoá chuẩn hoá: bỏ qualifier (trừ bối cảnh) + stopword, sắp xếp. 'cách đi xe số cho sinh viên' == 'cách đi xe số'."""
    return ' '.join(sorted({t for t in strip_qualifiers(toks(kw), KEYWORD_AXES) if len(t) >= 2 and t not in STOP}))


def title_tokens(text):
    """Token phần hỏi chính của tiêu đề (bỏ qualifier, stopword, từ đánh dấu intent, số) cho Jaccard trọng số IDF."""
    return sorted({t for t in strip_qualifiers(toks(head(text))) if len(t) >= 2 and t not in STOP and t not in MARKERS and not t.isdigit()})


def intent_class(text, hub=None):
    f = ' ' + fold(text) + ' '
    ic = UNIVERSE['intent_classes']
    for cls in ('troubleshooting', 'transactional', 'commercial'):
        if any(p in f for p in ic[cls]):
            return cls
    plain = ' '.join(fold(t) for t in toks(head(text)) if t not in STOP)
    for ent in ic['navigational_entities']:
        if plain == ent or (ent in plain and len(plain.split()) <= len(ent.split()) + 2 and not any(p in f for p in ic['informational'])):
            return 'navigational'
    return 'informational'


def cluster_key(text, hub=None):
    return intent_class(text, hub) + '::' + ' '.join(core_tokens(text))


def jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a or b else 0.0


def weighted_jaccard(a, b, weight):
    a, b = set(a), set(b)
    union = sum(weight(t) for t in a | b)
    return sum(weight(t) for t in a & b) / union if union else 0.0


def profile_terms(title, keywords=(), extra_texts=()):
    """Túi từ cho TF-IDF: unigram + bigram của tiêu đề, từ khoá, câu hỏi/outline."""
    bag = collections.Counter()
    for part in [title] + list(keywords) + list(extra_texts):
        tk = tokens(part)
        bag.update(tk)
        bag.update(a + '_' + b for a, b in zip(tk, tk[1:]))
    return bag


# ── Chỉ mục SQLite tăng dần ──────────────────────────────────────────────────
DOC_COLS = ['doc_id', 'kind', 'lifecycle', 'weight', 'url', 'hub', 'title', 'sha', 'cluster', 'perm_key', 'intent',
            'core_json', 'title_json', 'keywords_json', 'kwkeys_json', 'outline_json', 'bag_json']


class Index:
    def __init__(self, path=None):
        path = Path(path) if path else DB_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path))
        ver = dict(self.db.execute("SELECT key, value FROM meta").fetchall()) if self.db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='meta'").fetchone() else {}
        if ver.get('schema') != SCHEMA_VERSION:
            self.db.executescript('DROP TABLE IF EXISTS docs; DROP TABLE IF EXISTS postings; DROP TABLE IF EXISTS meta;')
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS docs(doc_id TEXT PRIMARY KEY, kind TEXT, lifecycle TEXT, weight TEXT, url TEXT, hub TEXT,
            title TEXT, sha TEXT, cluster TEXT, perm_key TEXT, intent TEXT, core_json TEXT, title_json TEXT,
            keywords_json TEXT, kwkeys_json TEXT, outline_json TEXT, bag_json TEXT);
          CREATE TABLE IF NOT EXISTS postings(term TEXT, doc_id TEXT, tf INTEGER, hard INTEGER);
          CREATE INDEX IF NOT EXISTS ix_post_hard_term ON postings(hard, term);
          CREATE INDEX IF NOT EXISTS ix_post_doc ON postings(doc_id);
          CREATE INDEX IF NOT EXISTS ix_docs_cluster ON docs(cluster);
          CREATE INDEX IF NOT EXISTS ix_docs_perm ON docs(perm_key);
          CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);''')
        self.db.execute('INSERT OR REPLACE INTO meta VALUES(?,?)', ('schema', SCHEMA_VERSION))
        self.db.commit()  # không giữ khoá ghi khi chỉ đọc
        self._df = None

    def close(self): self.db.close()

    def shas(self): return dict(self.db.execute('SELECT doc_id, sha FROM docs'))

    def remove(self, doc_id):
        if self._df is not None:  # cập nhật df tăng dần thay vì tính lại toàn bộ sau mỗi lần ghi
            terms = [t for (t,) in self.db.execute('SELECT term FROM postings WHERE doc_id=? AND hard=1', (doc_id,))]
            for t in terms:
                self._df[t] -= 1
            if terms:
                self._nhard -= 1
        self.db.execute('DELETE FROM postings WHERE doc_id=?', (doc_id,))
        self.db.execute('DELETE FROM docs WHERE doc_id=?', (doc_id,))

    def upsert(self, d):
        """d: doc_id, kind, lifecycle, weight('hard'|'soft'), url, hub, title, sha, keywords(list), outline(list), extra(list)."""
        self.remove(d['doc_id'])
        kws = [k for k in d.get('keywords', []) if k]
        bag = profile_terms(d['title'], kws, list(d.get('outline', [])) + list(d.get('extra', [])))
        hard = 1 if d.get('weight', 'hard') == 'hard' else 0
        if self._df is not None and hard and bag:
            for t in bag:
                self._df[t] = self._df.get(t, 0) + 1
            self._nhard += 1
        self.db.execute('INSERT INTO docs VALUES(%s)' % ','.join('?' * len(DOC_COLS)), (
            d['doc_id'], d['kind'], d.get('lifecycle', 'PUBLISHED'), d.get('weight', 'hard'), d['url'], d.get('hub') or '', d['title'], d['sha'],
            cluster_key(d['title'], d.get('hub')), permutation_key(d['title']), intent_class(d['title']),
            json.dumps(core_tokens(d['title']), ensure_ascii=False), json.dumps(title_tokens(d['title']), ensure_ascii=False),
            json.dumps([fold(k) for k in kws]), json.dumps(sorted({keyword_key(k) for k in kws if keyword_key(k)}), ensure_ascii=False),
            json.dumps([' '.join(title_tokens(h)) for h in d.get('outline', [])], ensure_ascii=False), json.dumps(bag, ensure_ascii=False)))
        self.db.executemany('INSERT INTO postings VALUES(?,?,?,?)', [(t, d['doc_id'], c, hard) for t, c in bag.items()])

    def commit(self): self.db.commit()
    def ndocs(self): return self.db.execute('SELECT COUNT(*) FROM docs').fetchone()[0]

    def df(self):
        """Tần suất tài liệu tính trên bài 'hard' (được index / viết tay / ma trận): bài V1 đã ẩn không làm loãng IDF."""
        if self._df is None:
            self._df = dict(self.db.execute("SELECT term, COUNT(*) FROM postings WHERE hard=1 GROUP BY term"))
            self._nhard = self.db.execute("SELECT COUNT(*) FROM docs WHERE weight='hard'").fetchone()[0]
        return self._df

    def nhard(self):
        self.df(); return max(1, self._nhard)

    def _row(self, row):
        d = dict(zip(DOC_COLS, row))
        for k, src in (('core', 'core_json'), ('title_tokens', 'title_json'), ('keywords', 'keywords_json'),
                       ('kwkeys', 'kwkeys_json'), ('outline', 'outline_json'), ('bag', 'bag_json')):
            d[k] = json.loads(d.pop(src))
        return d

    def doc(self, doc_id):
        row = self.db.execute('SELECT * FROM docs WHERE doc_id=?', (doc_id,)).fetchone()
        return self._row(row) if row else None

    def all_docs(self): return [self._row(r) for r in self.db.execute('SELECT * FROM docs')]
    def by_cluster(self, cluster): return [self._row(r) for r in self.db.execute('SELECT * FROM docs WHERE cluster=?', (cluster,))]
    def by_perm(self, key): return [self._row(r) for r in self.db.execute('SELECT * FROM docs WHERE perm_key=?', (key,))]

    def by_keyword(self, folded_kw, kwkey):
        rows = self.db.execute("SELECT * FROM docs WHERE keywords_json LIKE ? OR kwkeys_json LIKE ?",
                               ('%"' + folded_kw.replace('"', '') + '"%', '%"' + kwkey.replace('"', '') + '"%')).fetchall()
        return [self._row(r) for r in rows]

    def idf(self, term):
        n = self.nhard(); d = self.df().get(term, 0)
        return math.log((n + 1) / (d + 1)) + 1.0

    def vector(self, bag):
        v = {t: (1 + math.log(c)) * self.idf(t) for t, c in bag.items()}
        return v, (math.sqrt(sum(x * x for x in v.values())) or 1.0)

    def semantic_candidates(self, bag, limit=80):
        """Ứng viên 'hard' qua inverted index (chỉ term có df thấp), rồi tính cosine TF-IDF đúng trên ứng viên."""
        n = self.nhard(); dfm = self.df()
        informative = [t for t in bag if 0 < dfm.get(t, 0) <= max(2, n * TH['max_doc_freq_ratio_for_candidates'])]
        if not informative:
            return []
        q = ("SELECT doc_id, COUNT(*) FROM postings WHERE hard=1 AND term IN (%s) GROUP BY doc_id"
             % ','.join('?' * len(informative)))
        counts = dict(self.db.execute(q, informative).fetchall())
        need = 1 if len(informative) <= 3 else 2
        cands = sorted((d for d, c in counts.items() if c >= need), key=lambda d: -counts[d])
        qv, qn = self.vector(bag)
        out = []
        for doc_id in cands[:500]:
            doc = self.doc(doc_id)
            dv, dn = self.vector(doc['bag'])
            dot = sum(w * dv.get(t, 0.0) for t, w in qv.items())
            out.append((dot / (qn * dn), doc))
        out.sort(key=lambda x: -x[0])
        return out[:limit]


# ── Đánh giá trùng lặp 6 tầng ────────────────────────────────────────────────
def has_own_demand(cand, doc):
    """Từ khoá chính của ứng viên có khối lượng tìm kiếm đo được (≥ ngưỡng P1) và chứa từ không có trong tiêu đề/từ khoá bài trùng
    → ý định tìm kiếm riêng, không phải hoán vị template. Không có số liệu = không có ngoại lệ (không bịa nhu cầu)."""
    vol = cand.get('keyword_volume')
    if not isinstance(vol, (int, float)) or vol < UNIVERSE['priority_rules']['P1']['min_volume']:
        return False
    own = {fold(t) for t in toks(cand.get('primary_keyword') or '') if t not in STOP}
    known = {fold(t) for t in toks(doc.get('title') or '') if t not in STOP}
    for k in doc.get('keywords') or []:
        known.update(k.split())
    return bool(own) and not own <= known


def assess(cand, index, exclude_ids=()):
    """cand: title, primary_keyword, secondary_keywords, hub, user_problem, outline(list).
    Trả về risk (none/low/medium/high), hits theo URL, merge_into, permutation_of, decision_hint, legacy_overlap.
    Bài 'soft' (xưởng V1 đã noindex) không ảnh hưởng risk, chỉ được liệt kê để cân nhắc redirect sau này."""
    excl = set(exclude_ids)
    hits = []
    kws = [k for k in [cand.get('primary_keyword', '')] + list(cand.get('secondary_keywords', [])) if k]
    # Tầng 1: trùng từ khoá (chính xác sau bỏ dấu) hoặc trùng khoá từ khoá chuẩn hoá (bỏ qualifier)
    for kw in kws:
        kk = keyword_key(kw)
        for d in index.by_keyword(fold(kw), kk or '§'):
            if d['doc_id'] in excl:
                continue
            exact = fold(kw) in d['keywords']
            hits.append({'url': d['url'], 'layer': 'exact_keyword' if exact else 'keyword_normalized', 'score': 1.0, 'detail': kw, 'w': d['weight']})
    # Tầng 5: hoán vị template (chỉ khác qualifier) hoặc trùng tiêu đề
    perm_of = None
    for d in index.by_perm(permutation_key(cand['title'])):
        if d['doc_id'] in excl:
            continue
        same = fold(d['title']) == fold(cand['title'])
        if not same and has_own_demand(cand, d):
            # Qualifier bị bỏ lại chính là chủ đề ("giờ cao điểm Hà Nội" 320 lượt/tháng ≠ "đi xe máy ở Hà Nội"):
            # không phải biến thể template bịa nhu cầu → tín hiệu cao, biên tập quyết (override + information gain), không tự REJECT.
            hits.append({'url': d['url'], 'layer': 'permutation_with_demand', 'score': 1.0, 'detail': 'khác qualifier nhưng từ khoá có nhu cầu đo được riêng', 'w': d['weight']})
            continue
        hits.append({'url': d['url'], 'layer': 'same_title' if same else 'permutation', 'score': 1.0, 'detail': 'khác nhau chỉ ở qualifier' if not same else 'trùng tiêu đề', 'w': d['weight']})
        # Hoán vị của một URL đã có (kể cả bài V1 đã ẩn) không tạo thêm thông tin → REJECT, trừ khi biên tập override.
        perm_of = perm_of or d['url']
    # Tầng 2: cụm intent (intent class + token lõi)
    ck = cluster_key(cand['title'], cand.get('hub'))
    for d in index.by_cluster(ck):
        if d['doc_id'] not in excl:
            hits.append({'url': d['url'], 'layer': 'intent_cluster', 'score': 1.0, 'detail': ck, 'w': d['weight']})
    cand_core = core_tokens(cand['title'])
    cand_tt = title_tokens(cand['title'])
    cand_outline = [x for x in (' '.join(title_tokens(h)) for h in cand.get('outline', [])) if x]  # mục chỉ gồm từ đánh dấu ("Mức phạt") không so được
    # Tầng 3 + 4: ngữ nghĩa TF-IDF, tiêu đề (Jaccard trọng số IDF), outline, cụm gần
    bag = profile_terms(cand['title'], kws, [cand.get('user_problem', '')] + list(cand.get('outline', [])))
    cand_intent = intent_class(cand['title'])
    for sim, d in index.semantic_candidates(bag):
        if d['doc_id'] in excl:
            continue
        if sim >= TH['semantic_medium']:
            hits.append({'url': d['url'], 'layer': 'semantic', 'score': round(sim, 3), 'w': d['weight']})
        if d['intent'] == cand_intent and cand_core and d['cluster'] != ck and jaccard(cand_core, d['core']) >= TH['core_jaccard_cluster']:
            hits.append({'url': d['url'], 'layer': 'intent_cluster_near', 'score': round(jaccard(cand_core, d['core']), 3), 'w': d['weight']})
        tj = weighted_jaccard(cand_tt, d['title_tokens'], index.idf)
        if tj >= TH['title_jaccard_medium']:
            hits.append({'url': d['url'], 'layer': 'title', 'score': round(tj, 3), 'w': d['weight']})
        if cand_outline and d['outline']:
            oj = jaccard(cand_outline, [x for x in d['outline'] if x])
            if oj >= TH['outline_jaccard_review']:
                hits.append({'url': d['url'], 'layer': 'outline', 'score': round(oj, 3), 'w': d['weight']})
    by_url, soft = collections.OrderedDict(), collections.OrderedDict()
    for h in hits:
        (by_url if h.get('w') == 'hard' else soft).setdefault(h['url'], {}).setdefault(h['layer'], h)
    risk, merge_into = 'none', None
    HIGH_LAYERS = ('exact_keyword', 'keyword_normalized', 'permutation', 'permutation_with_demand', 'same_title', 'intent_cluster')
    for url, layers in by_url.items():
        high = any(l in layers for l in HIGH_LAYERS) or layers.get('semantic', {}).get('score', 0) >= TH['semantic_high'] \
            or layers.get('title', {}).get('score', 0) >= TH['title_jaccard_high']
        medium = any(l in layers for l in ('semantic', 'title', 'intent_cluster_near', 'outline'))
        if high and risk != 'high':
            risk, merge_into = 'high', url
        elif medium and risk not in ('high',):
            if risk != 'medium':
                merge_into = url
            risk = 'medium'
        elif risk == 'none':
            risk = 'low'
    if perm_of:
        hint = 'REJECT'
    elif risk == 'high':
        hint = 'MERGE-CANDIDATE'
    elif risk == 'medium':
        hint = 'NEEDS-RESEARCH'
    else:
        hint = 'KEEP' if cand.get('evidence') else 'NEEDS-RESEARCH'
    pack = lambda m: [{'url': u, 'layers': sorted(ls), 'scores': {k: ls[k]['score'] for k in ls}} for u, ls in m.items()]
    return {'risk': risk, 'hits': pack(by_url)[:12], 'legacy_overlap': pack(soft)[:6], 'merge_into': merge_into if risk in ('high', 'medium') else None,
            'permutation_of': perm_of, 'decision_hint': hint, 'cluster': ck}


# ── Nguồn bài đã xuất bản ────────────────────────────────────────────────────
def load_sources():
    out = []
    posts = json.loads(POSTS_PATH.read_text()) if POSTS_PATH.exists() else []
    for p in posts:
        p = dict(p); p['_source'] = 'content/posts.json'; out.append(p)
    if SHARDS_DIR.exists():
        for f in sorted(SHARDS_DIR.glob('*.json')):
            try:
                a = json.loads(f.read_text()); a['_source'] = 'content/articles/' + f.name; out.append(a)
            except Exception:
                pass
    return out


def article_text(a):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', ' '.join(h + ' ' + b for h, b in a.get('sections', []))))


def source_sha(a):
    return hashlib.sha256(json.dumps({k: a.get(k) for k in ('url', 'title', 'keywords', 'excerpt', 'sections')},
                                     ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def legacy_decisions():
    if not LEGACY_AUDIT_CSV.exists():
        return {}
    return {r['url']: (LEGACY_MAP.get(r['decision'], 'NEEDS-RESEARCH'), r.get('merge_into') or None, r.get('fit') or '')
            for r in csv.DictReader(LEGACY_AUDIT_CSV.open(encoding='utf-8'))}


def v1_core(intent):
    """Ý định lõi của bài xưởng V1: các trục mang thông tin thật. Quận/đối tượng/bối cảnh chỉ nhân bản trang."""
    p = intent.split('|')
    return (p[0], p[1], p[2]) if p[0] in ('thue-xe', 'xe-info') else (p[0], p[1])


TOPIC_FIT = {  # chủ đề bảo dưỡng → lớp xe áp dụng (từ scripts/audit_factory.py)
    'thay-dau-nhot': {'xe_so', 'xe_ga'}, 'thay-loc-gio-dong-co': {'xe_so', 'xe_ga'}, 'thay-the-bugi': {'xe_so', 'xe_ga'},
    'ky-nang-tiet-kiem-nhien-lieu': {'xe_so', 'xe_ga'}, 'khoi-dong-buoi-sang-lanh': {'xe_so', 'xe_ga'},
    've-sinh-kim-phun-fi': {'xe_so', 'xe_ga'}, 'kiem-tra-nuoc-lam-mat': 'liquid', 'thay-day-curoa': {'xe_ga'},
    'thay-nhot-hop-so-lap': {'xe_ga'}, 'cham-soc-pin-xe-dien': {'xe_dien'}, 've-sinh-xich-lip': {'xe_so', 'xe_dap'},
    'kiem-tra-ac-quy': {'xe_so', 'xe_ga', 'xe_dien'},
}


def v1_fit_problem(intent):
    p = intent.split('|')
    if p[0] != 'xe-info':
        return ''
    topic, subject = p[1], p[2].lower()
    vc = 'xe_dap' if 'xe đạp' in subject else 'xe_dien' if ('vinfast' in subject or 'điện' in subject) else \
        'xe_ga' if any(k in subject for k in ('vision', 'lead', 'air blade', 'grande', 'tay ga', 'xe ga')) else 'xe_so'
    rule = TOPIC_FIT.get(topic)
    if rule == 'liquid' and not any(k in subject for k in ('air blade', 'lead', 'winner x', 'exciter')):
        return f'"{topic}" không áp dụng cho xe làm mát bằng gió ({subject})'
    if isinstance(rule, set) and vc not in rule:
        return f'"{topic}" không áp dụng cho {subject}'
    return ''


def matrix_row_sha(r):
    return hashlib.sha256(json.dumps({k: r.get(k) for k in ('title', 'primary_keyword', 'secondary_keywords', 'user_problem', 'outline', 'url', 'lifecycle')},
                                     ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def index_matrix_row(idx, r):
    idx.upsert({'doc_id': r['topic_id'], 'kind': 'matrix', 'lifecycle': r['lifecycle'], 'weight': 'hard', 'url': r.get('url') or '', 'hub': r.get('hub'),
                'title': r['title'], 'sha': matrix_row_sha(r), 'keywords': [r.get('primary_keyword') or ''] + list(r.get('secondary_keywords') or []),
                'outline': list(r.get('outline') or []), 'extra': [r.get('user_problem') or '']})


def sync(verbose=True, index=None):
    """Dẫn xuất topic-matrix-published.jsonl từ nguồn bài và cập nhật chỉ mục tăng dần (theo sha256)."""
    idx = index or Index()
    known = idx.shas()
    sources = load_sources()
    legacy = legacy_decisions()
    noindex_all = bool(json.loads(FACTORY_CFG_PATH.read_text()).get('noindex_factory_articles', False)) if FACTORY_CFG_PATH.exists() else False
    def v1(a):  # shard xưởng cũ: content/articles/ với factoryVersion < 2; shard V2 (factory_v2.py) là bài được index như bài viết tay
        try:
            return a['_source'].startswith('content/articles/') and int(a.get('factoryVersion') or 1) < 2
        except (TypeError, ValueError):
            return True
    groups = collections.defaultdict(list)
    for a in sources:
        if a.get('intent') and v1(a):
            groups[v1_core(a['intent'])].append(a)
    rep = {key: sorted(arts, key=lambda x: (-x.get('wordCount', 0), len(x['url'])))[0]['url'] for key, arts in groups.items()}
    rows, seen = [], set()
    added = updated = 0
    for a in sources:
        if a.get('kind') in ('hub', 'page'):
            continue
        doc_id = 'PUB-' + hashlib.sha1(a['url'].encode()).hexdigest()[:10]
        seen.add(doc_id)
        sha = source_sha(a)
        is_factory = v1(a)
        fit = ''
        if a['_source'].startswith('content/articles/') and not is_factory:
            decision, merge_into, origin = 'KEEP', None, 'factory-v2'
        elif is_factory:
            fit = v1_fit_problem(a['intent'])
            if a['url'] in legacy:
                decision, merge_into, _ = legacy[a['url']]
            elif fit:
                decision, merge_into = 'REJECT', None
            elif rep.get(v1_core(a['intent'])) == a['url']:
                decision, merge_into = ('REWRITE' if a['intent'].startswith('luat|') else 'KEEP'), None
            else:
                decision, merge_into = 'MERGE-CANDIDATE', rep.get(v1_core(a['intent']))
            origin = 'factory-v1'
        else:
            decision, merge_into, origin = 'KEEP', None, 'hand-written'
        indexable = not (is_factory and (noindex_all or decision != 'KEEP'))
        kws = [k.strip() for k in str(a.get('keywords', '')).split(',') if k.strip()]
        rows.append({
            'topic_id': doc_id, 'lifecycle': 'PUBLISHED', 'origin': origin, 'url': a['url'], 'slug': a['url'].strip('/').split('/')[-1],
            'title': a['title'], 'hub': a.get('hub'), 'subtopic': None, 'cluster': cluster_key(a['title'], a.get('hub')),
            'primary_keyword': kws[0] if kws else None, 'secondary_keywords': kws[1:8], 'intent': intent_class(a['title']),
            'word_count': a.get('wordCount') or len(article_text(a).split()), 'indexable': indexable,
            'dedup_weight': 'hard' if indexable or not is_factory else 'soft',
            'audit_decision': decision, 'merge_into': merge_into, 'audit_note': fit,
            'v1_intent': a.get('intent'), 'source_file': a['_source'], 'sha256': sha, 'synced': today(),
        })
        if known.get(doc_id) != sha:
            idx.upsert({'doc_id': doc_id, 'kind': 'published', 'lifecycle': 'PUBLISHED', 'weight': rows[-1]['dedup_weight'], 'url': a['url'],
                        'hub': a.get('hub'), 'title': a['title'], 'sha': sha, 'keywords': kws,
                        'outline': [h for h, _ in a.get('sections', [])], 'extra': [a.get('excerpt', '')]})
            added += doc_id not in known; updated += doc_id in known
    for r in load_matrix():  # tầng 6: hàng PLANNED/RESEARCH/APPROVED/WRITING/QA cũng là "đã có" đối với ứng viên mới
        if r['lifecycle'] in ('REJECTED', 'PUBLISHED'):  # đã loại: bỏ khỏi chỉ mục; đã xuất bản: bài nguồn (PUB-…) đại diện
            if r['topic_id'] in known:
                idx.remove(r['topic_id'])
            continue
        seen.add(r['topic_id'])
        if known.get(r['topic_id']) != matrix_row_sha(r):
            index_matrix_row(idx, r)
    for doc_id in set(known) - seen:
        idx.remove(doc_id)
    idx.db.execute('INSERT OR REPLACE INTO meta VALUES(?,?)', ('synced', now()))
    idx.commit()
    PUBLISHED_PATH.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
    if verbose:
        print(json.dumps({'published_rows': len(rows), 'index_docs': idx.ndocs(), 'index_added': added, 'index_updated': updated,
                          'removed': len(set(known) - seen), 'decisions': collections.Counter(r['audit_decision'] for r in rows),
                          'hard_docs': sum(r['dedup_weight'] == 'hard' for r in rows)}, ensure_ascii=False))
    return rows


# ── Ma trận chính ────────────────────────────────────────────────────────────
REQUIRED = ['topic_id', 'lifecycle', 'hub', 'title', 'primary_keyword', 'intent', 'user_problem', 'origin']


def load_matrix():
    if not MATRIX_PATH.exists():
        return []
    return [json.loads(l) for l in MATRIX_PATH.read_text().splitlines() if l.strip()]


def save_matrix(rows):
    MATRIX_PATH.parent.mkdir(parents=True, exist_ok=True)
    MATRIX_PATH.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))


def next_id(rows):
    n = max([int(r['topic_id'].split('-')[1]) for r in rows if r['topic_id'].startswith('TM-')] + [0]) + 1
    return f'TM-{n:05d}'


def keyword_metrics():
    out = {}
    if KEYWORDS_PATH.exists():
        for l in KEYWORDS_PATH.read_text().splitlines():
            if l.strip():
                r = json.loads(l); out[fold(r['keyword'])] = r
    return out


def priority_for(row):
    vol = row.get('keyword_volume')
    p0 = UNIVERSE['priority_rules']['P0']
    if (vol or 0) >= p0['min_volume'] or (row.get('hub') == p0['or_service_hub'] and row.get('intent') in ('transactional', 'commercial')):
        return 'P0'
    if (vol or 0) >= UNIVERSE['priority_rules']['P1']['min_volume']:
        return 'P1'
    return 'P2'


def hub_cfg(hub): return UNIVERSE['hubs'].get(hub or '', {})


def gate_errors(row, assessment, all_rows):
    """Lỗi cứng: hàng không được APPROVED/WRITING nếu còn lỗi."""
    errs = [f'thiếu trường {k}' for k in REQUIRED if not row.get(k)]
    if row.get('lifecycle') not in LIFECYCLE:
        errs.append('lifecycle không hợp lệ')
    hc = hub_cfg(row.get('hub'))
    if not hc:
        errs.append('hub không có trong topic-universe')
    elif not hc.get('active'):
        errs.append(f'hub {row["hub"]} đang tắt: {hc.get("reason", "")}')
    elif row.get('subtopic') and row['subtopic'] not in hc.get('subtopics', {}):
        errs.append('subtopic không có trong hub')
    url = row.get('url') or ''
    if url:
        if not re.fullmatch(r'/[a-z0-9\-/]+/', url):
            errs.append('url phải là đường dẫn ascii thường, bắt đầu và kết thúc bằng /')
        hub_path = hc.get('path') or '/'
        if hc and not (url.startswith(hub_path) or (row.get('hub') == 'thue-xe' and url.startswith('/thue-xe'))):
            errs.append(f'url không nằm dưới hub {hub_path}')
        if any(r.get('url') == url and r['topic_id'] != row['topic_id'] and r['lifecycle'] != 'REJECTED' for r in all_rows):
            errs.append('trùng url với hàng khác trong ma trận')
    if len(row.get('title', '')) > RULES['title_max_chars']:
        errs.append(f'tiêu đề dài hơn {RULES["title_max_chars"]} ký tự')
    pk_core = core_tokens(row.get('primary_keyword', ''))
    tt = set(toks(row.get('title', '')))
    if pk_core and sum(t in tt for t in pk_core) < max(1, math.ceil(len(pk_core) * 0.6)):
        errs.append('tiêu đề không chứa các từ lõi của từ khoá chính')
    if assessment['permutation_of']:
        errs.append('hoán vị của bài đã có: ' + assessment['permutation_of'])
    if assessment['risk'] in RULES['block_risks'] and not (row.get('editorial_approval') or {}).get('override_reason'):
        errs.append('trùng lặp mức cao với ' + (assessment['merge_into'] or '?') + ' (merge vào bài đó, hoặc override có lý do)')
    return errs


def approval_blockers(row, assessment, all_rows=()):
    """Điều kiện để được DUYỆT (ngoài gate_errors). Điểm trùng lặp thấp KHÔNG tự động đồng nghĩa với 'khác bài'."""
    bl = []
    ig = (row.get('information_gain') or '').strip()
    if len(ig) < RULES['information_gain_min_chars']:
        bl.append(f'information_gain phải ≥ {RULES["information_gain_min_chars"]} ký tự: người đọc nhận được gì mà bài hiện có chưa cung cấp')
    mi = assessment['merge_into']
    if assessment['risk'] in RULES['review_risks'] and mi and mi not in ig:
        # Cặp chủ đề lân cận chỉ cần một bên nêu rõ "khác gì bên kia": hàng được thêm sau đã dẫn URL hàng này thì đủ.
        cited_back = any(r.get('url') == mi and row.get('url') and row['url'] in (r.get('information_gain') or '') and r['lifecycle'] != 'REJECTED' for r in all_rows)
        if not cited_back:
            bl.append('trùng lặp mức trung bình: information_gain phải nêu URL ' + mi + ' và khác gì bài đó')
    hc = hub_cfg(row.get('hub'))
    ev = [e for e in (row.get('evidence') or []) if e.get('type') in RULES['allowed_evidence_types']]
    if hc.get('requires_sources') and RULES['evidence_required_when_hub_requires_sources']:
        ok = [e for e in ev if e.get('checked') and e.get('type') in hc.get('evidence_types', []) and (e.get('source') or e.get('type') in ('business-facts', 'owner'))]
        if not ok:
            bl.append(f'hub {row["hub"]} cần ≥1 bằng chứng đã kiểm tra thuộc loại {hc.get("evidence_types")} (có source)')
    if row.get('keyword_volume') is None and not row.get('keyword_source'):
        bl.append('chưa có số liệu khối lượng tìm kiếm: ghi keyword_source="unknown" (không được bịa số)')
    return bl


def normalize_candidate(c, rows, kw):
    """Tạo hàng ma trận từ một ứng viên seed."""
    title = c['title'].strip()
    hub = c.get('hub')
    pk = (c.get('primary_keyword') or title).strip()
    url = c.get('url') or (hub_cfg(hub).get('path', '/') + slugify(c.get('slug') or head(title)) + '/')
    m = kw.get(fold(pk))
    evidence = list(c.get('evidence') or [])
    if m:
        evidence.append({'type': 'keyword-volume', 'source': m['source'], 'value': m.get('volume'), 'checked': m['checked'], 'keyword': m['keyword']})
    row = {
        'topic_id': c.get('topic_id') or next_id(rows), 'lifecycle': 'PLANNED', 'origin': c.get('origin', 'seed'),
        'hub': hub, 'subtopic': c.get('subtopic'), 'cluster': None, 'url': url, 'slug': url.strip('/').split('/')[-1], 'title': title,
        'primary_keyword': pk, 'secondary_keywords': list(c.get('secondary_keywords') or []),
        'intent': c.get('intent') or intent_class(title, hub), 'user_problem': c.get('user_problem', ''),
        'information_gain': c.get('information_gain', ''), 'evidence': evidence,
        'research_status': 'verified' if any(e.get('checked') and e.get('type') != 'keyword-volume' for e in evidence) else 'none',
        'keyword_volume': m.get('volume') if m else c.get('keyword_volume'),
        'keyword_source': ((m['source'] + ':' + m['checked'] + ('' if m.get('volume') is not None else ' (no volume data)')) if m else c.get('keyword_source')) or None,
        'keyword_difficulty': m.get('kd') if m else c.get('keyword_difficulty'),
        'outline': list(c.get('outline') or []), 'suggested_internal_links': list(c.get('suggested_internal_links') or []),
        'content_type': c.get('content_type') or hub_cfg(hub).get('subtopics', {}).get(c.get('subtopic'), {}).get('content_type', 'guide'),
        'schema': c.get('schema') or ['Article', 'BreadcrumbList', 'FAQPage'],
        'priority': None, 'quality_status': 'n/a', 'editorial_approval': ({'override_reason': c['override_reason']} if c.get('override_reason') else None),
        'notes': c.get('notes', ''), 'created': now(), 'updated': now(),
    }
    row['priority'] = c.get('priority') or priority_for(row)
    return row


def apply_assessment(row, a, errs=None, blockers=None):
    row['cluster'] = a['cluster']
    row['overlap'] = a['hits']
    row['legacy_overlap'] = a['legacy_overlap']
    row['cannibalization_risk'] = a['risk']
    row['merge_into'] = a['merge_into'] if a['risk'] in ('high', 'medium') else None
    row['permutation_of'] = a['permutation_of']
    row['decision_hint'] = a['decision_hint']
    row['gate_errors'] = errs if errs is not None else []
    if blockers is not None:
        row['approval_blockers'] = blockers
    row['updated'] = now()


RESEARCH_FIELDS = ('secondary_keywords', 'user_problem', 'information_gain', 'evidence', 'outline', 'notes', 'suggested_internal_links', 'content_type')


def classify_new(row, a, errs, bl):
    """Vòng đời ban đầu cho hàng mới/được làm mới: chỉ hoán vị template (không có nhu cầu riêng) bị loại tự động.
    Điểm tương đồng cao chỉ là tín hiệu: hàng ở RESEARCH với decision MERGE-CANDIDATE và lỗi cổng cho tới khi biên tập gộp hoặc override có lý do."""
    row['audit_decision'] = a['decision_hint']
    if a['permutation_of']:
        row['lifecycle'] = 'REJECTED'
        row['rejected_reason'] = 'hoán vị của ' + a['permutation_of']
    elif a['risk'] in ('high', 'medium') or row['research_status'] != 'verified' or bl or errs:
        row['lifecycle'] = 'RESEARCH'
    else:
        row['lifecycle'] = 'PLANNED'


def refresh_row(row, c, kw, idx, all_rows):
    """Làm mới trường nghiên cứu của hàng PLANNED/RESEARCH từ seed (bằng chứng, information_gain, outline...).
    Không đổi tiêu đề/URL/từ khoá chính, không chạm hàng đã duyệt hoặc đã loại: seed không thể nới lỏng phê duyệt."""
    changed = False
    for k in RESEARCH_FIELDS:
        if k not in c:
            continue
        cur = [e for e in (row.get(k) or [])] if k == 'evidence' else row.get(k)
        if k == 'evidence':
            cur = [e for e in cur if e.get('type') != 'keyword-volume']  # bằng chứng khối lượng do hệ thống gắn, không so với seed
        if (c[k] or None) != (cur or None):
            row[k] = c[k]; changed = True
    if not changed:
        return False
    m = kw.get(fold(row['primary_keyword']))
    row['evidence'] = [e for e in (row.get('evidence') or []) if e.get('type') != 'keyword-volume'] + (
        [{'type': 'keyword-volume', 'source': m['source'], 'value': m.get('volume'), 'checked': m['checked'], 'keyword': m['keyword']}] if m else [])
    row['research_status'] = 'verified' if any(e.get('checked') and e.get('type') != 'keyword-volume' for e in row['evidence']) else 'none'
    a = assess(row, idx, exclude_ids=[row['topic_id']])
    errs = gate_errors(row, a, all_rows); bl = approval_blockers(row, a, all_rows)
    apply_assessment(row, a, errs, bl)
    classify_new(row, a, errs, bl)
    if row['lifecycle'] == 'REJECTED':
        idx.remove(row['topic_id'])
    else:
        index_matrix_row(idx, row)
    return True


def discover(path, dry_run=False, index=None, update=False):
    rows = load_matrix()
    idx = index or Index()
    kw = keyword_metrics()
    seeds = [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip() and not l.startswith('#')]
    by_id = {r['topic_id']: r for r in rows}
    existing_pk = {keyword_key(r.get('primary_keyword') or ''): r['topic_id'] for r in rows}
    out, created, skipped, refreshed = collections.Counter(), [], [], []
    for c in seeds:
        kk = keyword_key(c.get('primary_keyword') or c['title'])
        if kk in existing_pk:  # cùng khoá từ khoá với hàng đã có (chạy lại file, hoặc chỉ khác quận/đối tượng) → không tạo hàng mới
            row = by_id.get(existing_pk[kk])
            same_seed = row is not None and fold(row['title']) == fold(c['title'])  # seed khác tiêu đề nhưng cùng khoá từ khoá không được ghi đè hàng cũ
            if update and same_seed and row['lifecycle'] in ('PLANNED', 'RESEARCH') and refresh_row(row, c, kw, idx, rows + created):
                out['refreshed'] += 1; refreshed.append({'topic_id': row['topic_id'], 'lifecycle': row['lifecycle'], 'decision': row['audit_decision']})
            else:
                out['skipped_existing_keyword'] += 1
                skipped.append({'title': c['title'], 'same_keyword_as': existing_pk[kk]})
            continue
        row = normalize_candidate(c, rows + created, kw)
        a = assess(row, idx)
        errs = gate_errors(row, a, rows + created)
        bl = approval_blockers(row, a, rows + created)
        apply_assessment(row, a, errs, bl)
        classify_new(row, a, errs, bl)
        created.append(row); existing_pk[keyword_key(row['primary_keyword'])] = row['topic_id']
        out[row['lifecycle'] + '/' + row['audit_decision']] += 1
        if row['lifecycle'] != 'REJECTED':  # ứng viên sau trong cùng file được so với ứng viên trước (tầng 6: planned)
            index_matrix_row(idx, row)
    if not dry_run:
        save_matrix(rows + created); idx.commit()
    print(json.dumps({'seeds': len(seeds), 'created': len(created), 'summary': out, 'skipped': skipped, 'refreshed': refreshed, 'dry_run': dry_run}, ensure_ascii=False, indent=2))
    return created


def validate(strict=True, index=None):
    rows = load_matrix()
    idx = index or Index()
    problems = []
    for r in rows:
        if r['lifecycle'] in ('PUBLISHED', 'REJECTED'):
            continue
        a = assess(r, idx, exclude_ids=[r['topic_id']])
        errs = gate_errors(r, a, rows); bl = approval_blockers(r, a, rows)
        apply_assessment(r, a, errs, bl)
        if r['lifecycle'] in ('PLANNED', 'RESEARCH'):
            r['audit_decision'] = a['decision_hint']  # chưa duyệt: phân loại đi theo đánh giá mới nhất (hàng chặn đã bị loại → hết MERGE-CANDIDATE)
        if r['lifecycle'] in ('APPROVED', 'WRITING', 'QA') and (errs or bl):
            problems.append({'topic_id': r['topic_id'], 'lifecycle': r['lifecycle'], 'errors': errs + bl})
    save_matrix(rows)
    summary = collections.Counter((r['lifecycle'], r.get('cannibalization_risk', '-')) for r in rows)
    print(json.dumps({'rows': len(rows), 'by_lifecycle_risk': {f'{k[0]}/{k[1]}': v for k, v in sorted(summary.items())},
                      'hard_errors_on_approved': problems}, ensure_ascii=False, indent=2))
    if problems and strict:
        print('FAIL: có hàng APPROVED/WRITING/QA vi phạm cổng kiểm tra', file=sys.stderr)
        return 1
    return 0


def transition(row, to, **fields):
    frm = row['lifecycle']
    if to not in TRANSITIONS.get(frm, set()):
        raise ValueError(f'không được chuyển {frm} → {to} cho {row["topic_id"]}')
    row['lifecycle'] = to; row['updated'] = now(); row.update(fields)
    row.setdefault('history', []).append({'from': frm, 'to': to, 'at': now(), **{k: v for k, v in fields.items() if k in ('by', 'reason', 'assigned_to')}})


def approve(topic_id, by, note='', override=None, index=None):
    rows = load_matrix(); idx = index or Index()
    row = next((r for r in rows if r['topic_id'] == topic_id), None)
    if not row:
        raise SystemExit('không tìm thấy ' + topic_id)
    if override:
        row['editorial_approval'] = {'override_reason': override}
    a = assess(row, idx, exclude_ids=[row['topic_id']])
    errs = gate_errors(row, a, rows); bl = approval_blockers(row, a, rows)
    apply_assessment(row, a, errs, bl)
    if errs or bl or row['lifecycle'] not in ('PLANNED', 'RESEARCH'):
        if row['lifecycle'] not in ('PLANNED', 'RESEARCH'):
            errs = errs + [f'chỉ duyệt được từ PLANNED/RESEARCH (hiện {row["lifecycle"]})']
        save_matrix(rows)
        print(json.dumps({'approved': False, 'topic_id': topic_id, 'gate_errors': errs, 'approval_blockers': bl}, ensure_ascii=False, indent=2))
        return 1
    transition(row, 'APPROVED', by=by)
    row['editorial_approval'] = {'by': by, 'at': now(), 'note': note, **({'override_reason': override} if override else {})}
    row['audit_decision'] = 'KEEP'
    save_matrix(rows); index_matrix_row(idx, row); idx.commit()
    print(json.dumps({'approved': True, 'topic_id': topic_id, 'url': row['url'], 'priority': row['priority']}, ensure_ascii=False))
    return 0


def next_topics(writer, n=1, hub=None, ids=()):
    """Giao hàng APPROVED cho writer (→ WRITING). ids: điều phối viên chỉ định chủ đề cụ thể; vẫn chỉ lấy hàng đã duyệt."""
    rows = load_matrix()
    order = {'P0': 0, 'P1': 1, 'P2': 2}
    ids = set(ids or ())
    pool = [r for r in rows if r['lifecycle'] == 'APPROVED' and (not hub or r['hub'] == hub) and (not ids or r['topic_id'] in ids) and not r.get('gate_errors')]
    pool.sort(key=lambda r: (order.get(r.get('priority'), 9), -(r.get('keyword_volume') or 0), r['topic_id']))
    picked = pool[:n]
    for r in picked:
        transition(r, 'WRITING', assigned_to=writer)
    save_matrix(rows)
    keys = ('topic_id', 'url', 'title', 'hub', 'subtopic', 'primary_keyword', 'secondary_keywords', 'intent', 'user_problem', 'information_gain',
            'evidence', 'outline', 'suggested_internal_links', 'content_type', 'overlap', 'legacy_overlap', 'merge_into', 'priority')
    print(json.dumps({'writer': writer, 'assigned': [{k: r.get(k) for k in keys} for r in picked], 'remaining_approved': len(pool) - len(picked)}, ensure_ascii=False, indent=2))
    return 0


def set_lifecycle(topic_id, to, reason='', url=None, by=''):
    rows = load_matrix()
    row = next((r for r in rows if r['topic_id'] == topic_id), None)
    if not row:
        raise SystemExit('không tìm thấy ' + topic_id)
    if to == 'PUBLISHED':
        target = url or row.get('url')
        if target not in {a['url'] for a in load_sources()}:
            raise SystemExit(f'không thể PUBLISHED: {target} chưa có trong content/posts.json hoặc content/articles/')
        row['url'] = target
    try:
        transition(row, to, reason=reason, by=by)
    except ValueError as exc:
        raise SystemExit(str(exc))
    if to == 'REJECTED':
        row['rejected_reason'] = reason; row['audit_decision'] = 'REJECT'
    save_matrix(rows)
    idx = Index()  # hàng bị loại không còn chặn ứng viên khác (tầng 6); hàng quay lại PLANNED được index lại; đã xuất bản → bài nguồn đại diện
    if to in ('REJECTED', 'PUBLISHED'):
        idx.remove(topic_id)
    else:
        index_matrix_row(idx, row)
    idx.commit(); idx.close()
    print(json.dumps({'topic_id': topic_id, 'lifecycle': to}, ensure_ascii=False))
    return 0


# ── QA phạm vi hẹp cho một bài đã viết ───────────────────────────────────────
def check_article_dict(art, idx, rows, facts, sources, topic_id=None):
    fails, warns = [], []
    body = ' '.join(b for _, b in art.get('sections', []))
    text = article_text(art); wc = len(text.split())
    # Loại chính bài này và hàng ma trận có cùng URL (hoặc topic được chỉ định) khỏi so sánh.
    own = ['PUB-' + hashlib.sha1(art['url'].encode()).hexdigest()[:10]] + ([topic_id] if topic_id else []) \
        + [r['topic_id'] for r in rows if r.get('url') == art['url']]
    kws = [k.strip() for k in str(art.get('keywords', '')).split(',') if k.strip()]
    cand = {'title': art['title'], 'primary_keyword': kws[0] if kws else art['title'], 'secondary_keywords': kws[1:], 'hub': art.get('hub'),
            'user_problem': art.get('excerpt', ''), 'outline': [h for h, _ in art.get('sections', [])]}
    ass = assess(cand, idx, exclude_ids=own)
    if ass['permutation_of']:
        fails.append('hoán vị của ' + ass['permutation_of'])
    elif ass['risk'] == 'high':
        fails.append('trùng lặp mức cao với ' + str(ass['merge_into']))
    elif ass['risk'] == 'medium':
        warns.append('trùng lặp mức trung bình với ' + str(ass['merge_into']) + ' – biên tập xác nhận khác biệt')
    if wc < 700:
        fails.append(f'bài quá mỏng: {wc} từ')
    if len(art.get('sections') or []) < 4:
        fails.append('ít hơn 4 mục')
    if not (35 <= len(art.get('title', '')) <= 90):
        warns.append(f'độ dài tiêu đề {len(art.get("title", ""))}')
    if not (100 <= len(art.get('excerpt', '')) <= 220):
        warns.append(f'độ dài excerpt {len(art.get("excerpt", ""))}')
    for bad in RULES['forbidden_in_content']:
        if bad in body.replace('thuha.rentbikehanoi.com', ''):
            fails.append('chứa liên kết/nhắc tới site chính: ' + bad)
    hype = [w for w in RULES['hype_words'] if w in text.lower()]
    if hype:
        warns.append('từ quảng cáo: ' + ', '.join(hype))
    matrix_urls = {r.get('url') for r in rows if r['lifecycle'] != 'REJECTED'}
    for l in re.findall(r'href="(/[^"#?]*)"', body):
        if l not in sources and l not in matrix_urls and not (ROOT / l.strip('/') / 'index.html').exists():
            fails.append('liên kết nội bộ hỏng ' + l)
    for ph in set(re.findall(r'0\d{2,3}[\s.]?\d{3}[\s.]?\d{3,4}', text)):
        if ph.replace('.', ' ') != facts['phone'] and ph.replace(' ', '') != facts['phone'].replace(' ', ''):
            fails.append('số điện thoại không có trong business-facts: ' + ph)
    hc = hub_cfg(art.get('hub'))
    if hc.get('requires_sources') and re.search(r'\d', text) and not (art.get('sources') or re.search(r'href="https?://', body)):
        warns.append('bài có số liệu nhưng không có trường sources hoặc liên kết nguồn ngoài')
    return {'url': art['url'], 'pass': not fails, 'fails': fails, 'warnings': warns, 'words': wc, 'overlap_risk': ass['risk'],
            'overlap': ass['hits'][:5], 'legacy_overlap': ass['legacy_overlap'][:3]}


def check_article(path, topic_id=None):
    a = json.loads(Path(path).read_text())
    idx = Index(); rows = load_matrix(); facts = json.loads(FACTS_PATH.read_text()); sources = {s['url'] for s in load_sources()}
    results = [check_article_dict(art, idx, rows, facts, sources, topic_id) for art in (a if isinstance(a, list) else [a])]
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if all(r['pass'] for r in results) else 1


# ── Báo cáo audit ────────────────────────────────────────────────────────────
def audit(next_slots=300):
    import importlib.util
    pub = [json.loads(l) for l in PUBLISHED_PATH.read_text().splitlines()] if PUBLISHED_PATH.exists() else sync(verbose=False)
    rows = load_matrix()
    fac = [r for r in pub if r['origin'] == 'factory-v1']; hand = [r for r in pub if r['origin'] == 'hand-written']
    fam = collections.defaultdict(list)
    for r in fac:
        fam[r['v1_intent'].split('|')[0]].append(r)
    lines = ['# Audit Topic Factory V2', '', f'Ngày: {today()}. Nguồn: content/posts.json ({len(hand)} bài viết tay), content/articles/ ({len(fac)} bài xưởng V1).', '',
             '## 1. Bài xưởng V1: ý định tìm kiếm thực so với số bài', '',
             '| Họ bài | Số bài | Ý định lõi | Trùng (hoán vị) | Tỷ lệ trùng | KEEP | REWRITE | MERGE-CANDIDATE | REJECT |', '|---|---|---|---|---|---|---|---|---|']
    tot = collections.Counter()
    for f, rs in sorted(fam.items()):
        cores = {v1_core(r['v1_intent']) for r in rs}
        dec = collections.Counter(r['audit_decision'] for r in rs); tot.update(dec)
        lines.append(f'| {f} | {len(rs)} | {len(cores)} | {len(rs) - len(cores)} | {100 * (len(rs) - len(cores)) / len(rs):.1f}% | {dec["KEEP"]} | {dec["REWRITE"]} | {dec["MERGE-CANDIDATE"]} | {dec["REJECT"]} |')
    allcores = {v1_core(r['v1_intent']) for r in fac}
    if fac:
        lines.append(f'| **Tổng** | {len(fac)} | {len(allcores)} | {len(fac) - len(allcores)} | {100 * (len(fac) - len(allcores)) / len(fac):.1f}% | {tot["KEEP"]} | {tot["REWRITE"]} | {tot["MERGE-CANDIDATE"]} | {tot["REJECT"]} |')
    lines += ['', 'Cách đọc: "ý định lõi" là các trục mang thông tin thật (chủ đề × loại xe, hoặc điểm đến, hoặc lỗi luật). Quận, đối tượng, bối cảnh, thời lượng, nhóm chỉ nhân bản trang. Toàn bộ bài V1 hiện là noindex và được coi là "trùng mềm": không chặn chủ đề mới, chỉ được ghi lại để cân nhắc chuyển hướng sau khi bài mới xuất bản.', '']
    try:
        spec = importlib.util.spec_from_file_location('factory', ROOT / 'scripts/content_factory.py'); F = importlib.util.module_from_spec(spec); spec.loader.exec_module(F)
        start = json.loads((ROOT / 'data/factory-state.json').read_text())['next_sequence']
        idx = Index(); cls = collections.Counter(); seen = set(); new_cores = set(); slot_rows = []
        existing_cores = {v1_core(r['v1_intent']) for r in fac}
        for seq in range(start, start + next_slots):
            s = F.spec_for(seq); c = v1_core(s['intent']); fit = v1_fit_problem(s['intent'])
            a = assess({'title': s['title'], 'primary_keyword': s['title'], 'secondary_keywords': [], 'hub': s['hub'], 'user_problem': '', 'outline': []}, idx)
            if fit: d, why = 'REJECT', fit
            elif c in existing_cores: d, why = 'MERGE-CANDIDATE', 'ý định lõi đã có bài'
            elif c in seen: d, why = 'REJECT', 'hoán vị của slot khác trong cùng lô'
            else: d, why = 'NEEDS-RESEARCH', 'ý định mới, chưa có nguồn'; new_cores.add(c)
            seen.add(c); cls[d] += 1
            v2_match = a['merge_into'] or a['permutation_of'] or (a['legacy_overlap'][0]['url'] if a['legacy_overlap'] else '')
            slot_rows.append({'sequence': seq, 'writer': s['writer'], 'title': s['title'], 'url': s['url'], 'decision': d, 'reason': why,
                              'v2_risk_vs_hard': a['risk'], 'v2_legacy_overlap': len(a['legacy_overlap']), 'v2_match': v2_match})
        REPORTS.mkdir(exist_ok=True)
        with (REPORTS / f'slot-audit-{next_slots}.csv').open('w', newline='', encoding='utf-8') as fh:
            w = csv.DictWriter(fh, fieldnames=list(slot_rows[0].keys())); w.writeheader(); w.writerows(slot_rows)
        soft_hits = sum(1 for r in slot_rows if r['v2_legacy_overlap'])
        lines += [f'## 2. {next_slots} slot kế tiếp của bộ lập kế hoạch cũ (sequence {start}–{start + next_slots - 1})', '',
                  f'Phân loại theo ý định lõi: {dict(cls)}. Ý định mới xuất hiện: **{len(new_cores)}**.',
                  f'Cổng V2 chạy trên 300 tiêu đề: {soft_hits}/{next_slots} slot trùng với bài V1 đã có (trùng mềm); {sum(1 for r in slot_rows if r["v2_risk_vs_hard"] in ("high", "medium"))} slot còn trùng cả với bài viết tay/bài được index.',
                  f'Chi tiết: reports/slot-audit-{next_slots}.csv.', '']
    except Exception as exc:  # pragma: no cover
        lines += [f'(không chạy được audit slot cũ: {exc})', '']
    lc = collections.Counter(r['lifecycle'] for r in rows); dec = collections.Counter(r.get('audit_decision') for r in rows)
    risk = collections.Counter(r.get('cannibalization_risk') for r in rows if r['lifecycle'] != 'PUBLISHED')
    lines += ['## 3. Ma trận chủ đề (data/topic-matrix.jsonl)', '', f'Số hàng: {len(rows)}. Vòng đời: {dict(lc)}. Phân loại: {dict(dec)}. Rủi ro trùng lặp: {dict(risk)}.', '']
    by_hub = collections.Counter((r['hub'], r['lifecycle']) for r in rows)
    if by_hub:
        lines += ['| Hub | ' + ' | '.join(LIFECYCLE) + ' |', '|---|' + '---|' * len(LIFECYCLE)]
        for h in sorted({k[0] for k in by_hub}):
            lines.append(f'| {h} | ' + ' | '.join(str(by_hub[(h, s)]) for s in LIFECYCLE) + ' |')
    lines += ['', '## 4. Bài viết tay', '', f'{len(hand)} bài, tất cả KEEP; đây là lớp phủ hiện tại mà mọi chủ đề mới phải so sánh.', '']
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / 'topic-factory-v2-audit.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    return 0


def status():
    rows = load_matrix(); pub = [json.loads(l) for l in PUBLISHED_PATH.read_text().splitlines()] if PUBLISHED_PATH.exists() else []
    idx = Index()
    print(json.dumps({'matrix_rows': len(rows), 'by_lifecycle': collections.Counter(r['lifecycle'] for r in rows),
                      'by_hub': collections.Counter(r['hub'] for r in rows), 'published_rows': len(pub), 'index_docs': idx.ndocs(),
                      'index_synced': dict(idx.db.execute('SELECT key, value FROM meta')).get('synced')}, ensure_ascii=False, indent=2))
    return 0


def export(path):
    rows = load_matrix()
    cols = ['topic_id', 'lifecycle', 'priority', 'hub', 'subtopic', 'intent', 'url', 'title', 'primary_keyword', 'keyword_volume', 'keyword_source',
            'cannibalization_risk', 'merge_into', 'audit_decision', 'research_status', 'information_gain', 'origin']
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    print(f'wrote {path} ({len(rows)} rows)')
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    sp.add_parser('sync')
    d = sp.add_parser('discover'); d.add_argument('file'); d.add_argument('--dry-run', action='store_true')
    d.add_argument('--update', action='store_true', help='làm mới trường nghiên cứu của hàng PLANNED/RESEARCH có cùng từ khoá (không chạm hàng đã duyệt/đã loại)')
    v = sp.add_parser('validate'); v.add_argument('--no-strict', action='store_true')
    a = sp.add_parser('approve'); a.add_argument('topic_id'); a.add_argument('--by', required=True); a.add_argument('--note', default=''); a.add_argument('--override', default=None)
    n = sp.add_parser('next'); n.add_argument('--writer', required=True); n.add_argument('--n', type=int, default=1); n.add_argument('--hub')
    n.add_argument('--topic', action='append', default=[], help='chỉ giao chủ đề APPROVED có mã này (lặp lại được)')
    s = sp.add_parser('set'); s.add_argument('topic_id'); s.add_argument('--lifecycle', required=True, choices=LIFECYCLE); s.add_argument('--reason', default=''); s.add_argument('--url'); s.add_argument('--by', default='')
    c = sp.add_parser('check-article'); c.add_argument('file'); c.add_argument('--topic')
    au = sp.add_parser('audit'); au.add_argument('--slots', type=int, default=300)
    sp.add_parser('status')
    e = sp.add_parser('export'); e.add_argument('--csv', default=str(REPORTS / 'topic-matrix.csv'))
    args = ap.parse_args()
    if args.cmd == 'sync': sync(); return 0
    if args.cmd == 'discover': discover(args.file, args.dry_run, update=args.update); return 0
    if args.cmd == 'validate': return validate(strict=not args.no_strict)
    if args.cmd == 'approve': return approve(args.topic_id, args.by, args.note, args.override)
    if args.cmd == 'next': return next_topics(args.writer, args.n, args.hub, args.topic)
    if args.cmd == 'set': return set_lifecycle(args.topic_id, args.lifecycle, args.reason, args.url, args.by)
    if args.cmd == 'check-article': return check_article(args.file, args.topic)
    if args.cmd == 'audit': return audit(args.slots)
    if args.cmd == 'status': return status()
    if args.cmd == 'export': return export(args.csv)


if __name__ == '__main__':
    raise SystemExit(main())
