#!/usr/bin/env python3
"""Đồng bộ trạng thái hiện tại vào reports/seo-recovery/data/ sau mỗi lô đã build.

- current_state.csv: url, noindex_now, in_sitemap_now, fix_method (đọc HTML đã build + sitemap).
- classification.csv: URL trong config/factory-reindex.json -> status DONE (category giữ nguyên);
  shard có rewrite.batch nhưng không được mở index -> giữ status do lô ghi (BLOCKED nếu đã ghi).
Dùng: python3 scripts/seo_state_sync.py
"""
import csv,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; D=ROOT/'reports/seo-recovery/data'; SITE='https://thuha.rentbikehanoi.com'
reidx=set(json.loads((ROOT/'config/factory-reindex.json').read_text())['urls'])
sm=set()
for f in ROOT.glob('sitemap-*.xml'): sm|={u.replace(SITE,'') for u in re.findall(r'<loc>([^<]+)</loc>',f.read_text())}
rw={}
for f in (ROOT/'content/articles').glob('NH-*.json'):
    a=json.loads(f.read_text(encoding='utf-8'))
    if a.get('rewrite'): rw[a['url']]=a['rewrite']
rows=list(csv.DictReader(open(D/'inventory.csv',encoding='utf-8')))
with open(D/'current_state.csv','w',newline='',encoding='utf-8') as fh:
    w=csv.writer(fh); w.writerow(['url','noindex_now','in_sitemap_now','fix_method'])
    for r in rows:
        u=r['url']; h=ROOT/(u.strip('/'))/'index.html' if u!='/' else ROOT/'index.html'
        txt=h.read_text(encoding='utf-8') if h.exists() else ''
        noi='name="robots" content="noindex' in txt
        fm=''
        if u in reidx: fm=f"rewrite {rw.get(u,{}).get('batch','')} + QA {rw.get(u,{}).get('qa_score','')} + factory-reindex.json"
        elif u in rw: fm=f"rewrite {rw[u].get('batch','')}; kept noindex (see reason)"
        w.writerow([u,noi,u in sm,fm])
cls=list(csv.DictReader(open(D/'classification.csv',encoding='utf-8'))); fields=list(cls[0].keys())
n=0
for r in cls:
    if r['url'] in reidx and r['status']!='DONE': r['status']='DONE'; n+=1
with open(D/'classification.csv','w',newline='',encoding='utf-8') as fh:
    w=csv.DictWriter(fh,fieldnames=fields); w.writeheader(); w.writerows(cls)
print('current_state rows',len(rows),'| classification set DONE:',n)
