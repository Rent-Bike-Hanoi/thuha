#!/usr/bin/env python3
"""Cập nhật od1_matrix.csv sau khi ship + kiểm tra production.

    python3 matrix_update.py ship.json live.json      # live.json = output của verify_live.py
Bài trong ship.passed và ok trên production -> DEPLOYED (qa_score, title mới, commit, live_verified=ngày).
Bài trong ship.failed -> RETRY (ghi lý do ở note).
"""
import csv, datetime, json, sys
from pathlib import Path

M = Path('/home/user/thuha/reports/seo-recovery/od1/od1_matrix.csv')
ship = json.load(open(sys.argv[1], encoding='utf-8'))
live = json.load(open(sys.argv[2], encoding='utf-8')) if len(sys.argv) > 2 else {'fails': []}
bad = {x['url'] for x in live.get('fails', [])}
today = datetime.date.today().isoformat()
rows = list(csv.DictReader(open(M, encoding='utf-8'))); cols = list(rows[0].keys())
by = {r['url']: r for r in rows}
for p in ship.get('passed', []):
    r = by.get(p['url'])
    if not r: continue
    r.update(status='DEPLOYED' if p['url'] not in bad else 'DEPLOYED_LIVE_FAIL', new_title=p.get('title', ''), qa_score=str(p.get('qa_score', '')),
             commit=ship.get('head', '')[:10], pr='push main (GitHub MCP ngắt)', live_verified=today if p['url'] not in bad else '')
for f in ship.get('failed', []):
    a = json.load(open('/home/user/thuha-ship/' + f['file'], encoding='utf-8')) if Path('/home/user/thuha-ship/' + f['file']).exists() else {}
    r = by.get(a.get('url', ''))
    if r: r.update(status='RETRY', note=f.get('reason', '')[:200])
with open(M, 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows)
c = {}
for r in rows: c[r['status']] = c.get(r['status'], 0) + 1
print(c)
