#!/usr/bin/env python3
"""Kiểm tra production sau khi deploy một lô OD-1.

    python3 verify_live.py ship_result.json        # file JSON do ship_batch.py in ra

Mỗi URL đã PASS: HTTP 200, <title> mới, canonical tự trỏ, không noindex, có trong sitemap-posts.xml.
"""
import html, json, re, sys, time, urllib.request

SITE = 'https://thuha.rentbikehanoi.com'
res = json.load(open(sys.argv[1], encoding='utf-8'))


def get(u):
    req = urllib.request.Request(u + ('&' if '?' in u else '?') + f'v={int(time.time())}', headers={'User-Agent': 'Mozilla/5.0 od1-verify'})
    with urllib.request.urlopen(req, timeout=40) as r: return r.status, r.read().decode('utf-8', 'replace')


_, sm = get(SITE + '/sitemap-posts.xml')
out = []
for p in res['passed']:
    u = SITE + p['url']
    try:
        st, h = get(u)
        t = html.unescape((re.search(r'<title>(.*?)</title>', h, re.S) or [None, ''])[1])
        canon = (re.search(r'<link rel="canonical" href="([^"]+)"', h) or [None, ''])[1]
        robots = (re.search(r'<meta name="robots" content="([^"]+)"', h) or [None, ''])[1]
        ok = st == 200 and p['title'] in t and canon == u and 'noindex' not in robots and f'<loc>{u}</loc>' in sm
        out.append(dict(url=p['url'], ok=ok, status=st, title_ok=p['title'] in t, canonical_ok=canon == u, noindex='noindex' in robots, in_sitemap=f'<loc>{u}</loc>' in sm))
    except Exception as e:
        out.append(dict(url=p['url'], ok=False, error=str(e)))
print(json.dumps(dict(batch=res['batch'], checked=len(out), ok=sum(x['ok'] for x in out), fails=[x for x in out if not x['ok']]), ensure_ascii=False, indent=1))
