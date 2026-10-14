#!/usr/bin/env python3
"""Gửi URL trong sitemap tới IndexNow (Bing, Yandex, Seznam...). Chạy tay sau khi deploy:
    python3 scripts/indexnow.py            # in số URL sẽ gửi (dry run)
    python3 scripts/indexnow.py --send     # gửi thật
File khoá nằm ở gốc site: /282a473d9e0925b49f8c68e70a4a862c.txt (phải truy cập được trên domain thật trước khi gửi)."""
import json,re,sys,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
KEY='282a473d9e0925b49f8c68e70a4a862c'
site=json.loads((ROOT/'content/site.json').read_text())['url']
urls=[]
for f in ('sitemap-posts.xml','sitemap-pages.xml'):
 urls+=re.findall(r'<loc>([^<]+)</loc>',(ROOT/f).read_text())
host=site.split('://',1)[1].strip('/')
body={'host':host,'key':KEY,'keyLocation':f'{site}/{KEY}.txt','urlList':urls[:10000]}
if '--send' not in sys.argv:
 print(f'{len(urls)} URL, host {host}. Thêm --send để gửi.');sys.exit(0)
req=urllib.request.Request('https://api.indexnow.org/indexnow',data=json.dumps(body).encode(),headers={'Content-Type':'application/json; charset=utf-8'})
print(urllib.request.urlopen(req,timeout=60).status)
