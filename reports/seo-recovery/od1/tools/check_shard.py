#!/usr/bin/env python3
"""Kiểm tra shard OD-1 sau khi viết lại (chạy trong worktree của lô).

    python3 reports/seo-recovery/od1/tools/check_shard.py content/articles/NH-00001.json [...] [--set-wordcount]

Với mỗi file:
  - so với bản HEAD: id/url/hub/parent/kind/art/tone/intent/factoryVersion không được đổi;
  - kiểm tra cấu trúc (sections/faq/sources/rewrite), HTML (không <h1>/<h2> trong thân), lặp chữ;
  - link nội bộ phải tồn tại và đang index; cảnh báo link tới bài V1 chưa kiểm chứng;
  - chạy scripts/seo_qa.py (điểm, critical, độ tương đồng lớn nhất);
  - in độ tương đồng từng cặp giữa các file được truyền vào (để tách biến thể cùng cụm).
--set-wordcount: ghi wordCount = số từ văn bản thuần (như seo_qa).
"""
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / 'scripts'))
import seo_qa  # noqa: E402

FROZEN = ('id', 'url', 'hub', 'parent', 'kind', 'art', 'tone', 'intent', 'factoryVersion')


def head(rel):
    r = subprocess.run(['git', 'show', 'origin/main:' + rel], cwd=ROOT, capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None


def main():
    files = [f for f in sys.argv[1:] if not f.startswith('--')]
    setwc = '--set-wordcount' in sys.argv
    docs = seo_qa.load_corpus(); urls = seo_qa.existing_urls() | set(docs)
    reidx = set(json.loads((ROOT / 'config/factory-reindex.json').read_text(encoding='utf-8'))['urls'])
    uniq = seo_qa.Uniq(docs)
    arts = []
    for f in files:
        p = ROOT / f; rel = str(p.resolve().relative_to(ROOT.resolve()))
        a = json.loads(p.read_text(encoding='utf-8')); b = head(rel) or {}
        errs, warns = [], []
        for k in FROZEN:
            if b and a.get(k) != b.get(k): errs.append(f'đổi trường cấm sửa: {k}')
        secs = a.get('sections') or []; faq = a.get('faq') or []
        if not all(isinstance(s, list) and len(s) == 2 and all(isinstance(x, str) for x in s) for s in secs): errs.append('sections phải là [[h2, html], ...]')
        if not all(isinstance(s, list) and len(s) == 2 for s in faq): errs.append('faq phải là [[q, a], ...]')
        for s in a.get('sources') or []:
            if not (isinstance(s, dict) and s.get('source') and s.get('quote')): errs.append('source thiếu source/quote'); break
        rw = a.get('rewrite') or {}
        if not (rw.get('rewrittenAt') and rw.get('batch')): errs.append('thiếu rewrite.rewrittenAt/batch')
        body = ' '.join(x for _, x in secs)
        if re.search(r'<h[12][ >]', body): errs.append('không dùng <h1>/<h2> trong thân section')
        for t, x in secs:
            if x.count('<p') != x.count('</p>') or x.count('<ul') != x.count('</ul>') or x.count('<table') != x.count('</table>'): errs.append(f'thẻ HTML không cân: {t[:40]}')
        txt = seo_qa.article_text(a)
        for rep in re.findall(r'\b(\w+) \1\b', txt.lower()):
            if rep in ('xe', 'chuyến', 'bánh', 'của', 'và', 'thay', 'kiểm', 'tra'): warns.append(f'lặp chữ: "{rep} {rep}"')
        for l in set(re.findall(r'href="(/[^"#?]*)"', body + ' '.join(y for _, y in faq))):
            if l not in urls: errs.append(f'link nội bộ không tồn tại: {l}')
            elif l in docs and not docs[l]['indexable']: errs.append(f'link tới trang noindex: {l}')
            elif l in docs and str(docs[l]['src']).find('/NH-') >= 0 and int(docs[l]['a'].get('factoryVersion') or 1) < 2 and l not in reidx: warns.append(f'link tới bài V1 chưa kiểm chứng: {l}')
        if setwc:
            a['wordCount'] = len(txt.split()); p.write_text(json.dumps(a, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        r = seo_qa.qa(a, docs, uniq, urls, published_url=a['url'])
        arts.append((a['url'], uniq.vec(seo_qa.toks(txt))))
        print(json.dumps(dict(file=rel, url=a['url'], title=a.get('title'), title_len=len(a.get('title', '')), excerpt_len=len(a.get('excerpt', '')),
                              words=r['words'], score=r['score'], pass_=r['pass_'] and not errs, checks=r['checks'], critical=r['critical'],
                              max_sim=r['max_sim'], max_sim_url=r['max_sim_url'], errors=errs, warnings=warns[:8]), ensure_ascii=False))
    if len(arts) > 1:
        print('pairwise similarity (files given):')
        for i in range(len(arts)):
            for j in range(i + 1, len(arts)):
                s = float(arts[i][1] @ arts[j][1])
                flag = '  <-- quá giống' if s >= 0.5 else ''
                print(f'  {s:.3f}  {arts[i][0]}  ~  {arts[j][0]}{flag}')


if __name__ == '__main__':
    main()
