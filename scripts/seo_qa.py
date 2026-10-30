#!/usr/bin/env python3
"""QA 100 điểm cho bài viết trước khi mở index (SEO recovery, 10/2026).

Dùng:  python3 scripts/seo_qa.py content/articles/NH-00139.json [more.json ...] [--json] [--report reports/seo-recovery/data/qa_report.jsonl --batch B03]
PASS khi điểm >= 85 và không có lỗi critical.  Điểm nội bộ, không phải bảo đảm Google index.

Thang điểm (100):
  structure 20 | depth 20 | metadata 15 | facts/NAP 15 | sources 10 | internal links 10 | uniqueness 10
Critical (chặn dù đủ điểm): link nội bộ gãy, nhắc rentbikehanoi.com (site chính), cam kết trái business-facts,
  giờ/điện thoại sai, số tiền không có trong business-facts và không có nguồn, trùng >= 0.60 với bài index khác,
  URL/slug thay đổi so với bản đã xuất bản.
"""
import argparse,collections,datetime,glob,html,json,math,re,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
FACTS=json.loads((ROOT/'config/business-facts.json').read_text(encoding='utf-8'))
SITE=json.loads((ROOT/'content/site.json').read_text(encoding='utf-8'))
MONEY=['/thue-xe-may/ha-noi/','/thue-xe-dien/ha-noi/','/thue-xe-50cc/ha-noi/','/bang-gia/','/thue-xe-may/ha-noi/theo-thang/','/thue-xe-may/ha-noi/theo-ngay/','/thue-xe-may/long-bien/','/thue-xe-may/hoan-kiem/','/lien-he/']
NEEDS_SOURCES={'xe-may','xe-dien','luat-giao-thong','bao-duong','du-lich'}
ALLOWED_AMOUNTS={'20.000','50.000','100.000','150.000','200.000','600.000','700.000','800.000','1.000.000','1.200.000','1.500.000','1.800.000','2.000.000','5.000.000','10.000',
 '150 nghìn','200 nghìn','600 nghìn','700 nghìn','800 nghìn','1 triệu','1,2 triệu','1,5 triệu','1,8 triệu','2 triệu','5 triệu','2–5 triệu','2-5 triệu'}
BANNED=[(r'24/7|24h/7|24 giờ/7','hỗ trợ 24/7 không có trong chính sách'),(r'miễn phí (thay nhớt|bảo dưỡng|giao xe)','ưu đãi không có trong chính sách'),
 (r'hoàn (lại )?100% (tiền )?cọc','cam kết hoàn cọc không có trong chính sách'),(r'chiết khấu|giảm giá \d','khuyến mãi không có trong chính sách'),
 (r'bảo hiểm','không nêu bảo hiểm trong bài (chủ cửa hàng 17/10/2026)'),(r'giao (xe |nhận )?(tại|ở) sân bay|sân bay nội bài.*giao','không giao nhận tại sân bay Nội Bài'),
 (r'rentbikehanoi\.com(?!\S*thuha)','không nhắc site chính rentbikehanoi.com')]
HOURS_RE=re.compile(r'(\d{1,2})[:h](\d{2})\s*[–-]\s*(\d{1,2})[:h](\d{2})')
PHONE_RE=re.compile(r'0\d{2,3}[\s.]?\d{3}[\s.]?\d{3,4}|\+84[\s.]?\d{2,3}[\s.]?\d{3}[\s.]?\d{3,4}')
STOP=set('và của cho các một những với trong khi đi ở là có không được tại từ theo bằng xe máy hà nội thuê bài gì nào sao bao nhiêu nên hay thế để này đó đã sẽ cũng như về hơn nếu thì lại ra vào trên dưới cần phải khách cửa hàng nguyễn hà'.split())
def toks(t): return [w for w in re.findall(r'[0-9a-zà-ỹđ]+',t.lower()) if len(w)>1 and w not in STOP and not w.isdigit()]
def plain(h): return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',h))).strip()
def article_text(a):
    secs=a.get('sections') or []
    body=' '.join(f'{t} {b}' for t,b in secs)
    if a.get('faq'): body+=' '+' '.join(f'{q} {x}' for q,x in a['faq'])
    return plain(body)
def load_corpus():
    """All published sources with indexability (same rules as build.py)."""
    posts=json.loads((ROOT/'content/posts.json').read_text(encoding='utf-8'))
    cfg=json.loads((ROOT/'config/content-factory.json').read_text(encoding='utf-8'))
    gl=bool(cfg.get('noindex_factory_articles',False))
    nl=set(json.loads((ROOT/'config/factory-noindex.json').read_text(encoding='utf-8'))['urls'])
    rp=ROOT/'config/factory-reindex.json'
    rl=set(json.loads(rp.read_text(encoding='utf-8'))['urls']) if rp.exists() else set()
    docs={}
    for p in posts: docs[p['url']]=dict(a=p,indexable=True,src='content/posts.json')
    for f in sorted(glob.glob(str(ROOT/'content/articles/*.json'))):
        a=json.loads(open(f,encoding='utf-8').read()); fv=int(a.get('factoryVersion') or 1)
        noind=(a['url'] in nl or (gl and fv<2)) and a['url'] not in rl
        docs[a['url']]=dict(a=a,indexable=not noind,src=f)
    return docs
def existing_urls():
    urls=set()
    for f in ROOT.rglob('index.html'):
        if '.git' in f.parts or 'templates' in f.parts: continue
        rel=f.relative_to(ROOT).parent.as_posix(); urls.add('/' if rel=='.' else '/'+rel+'/')
    return urls
class Uniq:
    def __init__(self,docs):
        self.urls=[u for u,d in docs.items() if d['indexable']]
        self.tok=[toks(article_text(docs[u]['a'])) for u in self.urls]
        df=collections.Counter()
        for t in self.tok:
            for w in set(t): df[w]+=1
        N=len(self.tok)+1; self.vocab={w:i for i,w in enumerate(w for w,c in df.items() if c>=2)}
        self.idf=np.array([math.log(N/(df[w]+1))+1 for w in self.vocab],dtype=np.float32)
        self.M=np.stack([self.vec(t) for t in self.tok]) if self.tok else np.zeros((0,len(self.vocab)),dtype=np.float32)
    def vec(self,t):
        c=collections.Counter(w for w in t if w in self.vocab); v=np.zeros(len(self.vocab),dtype=np.float32)
        for w,n in c.items(): v[self.vocab[w]]=(1+math.log(n))*self.idf[self.vocab[w]]
        n=np.linalg.norm(v); return v/n if n else v
    def max_sim(self,text,exclude_url):
        if not len(self.M): return 0.0,None
        v=self.vec(toks(text)); s=self.M@v
        for i,u in enumerate(self.urls):
            if u==exclude_url: s[i]=-1
        j=int(s.argmax()); return float(s[j]),self.urls[j]
def qa(a,docs,uniq,urls,published_url=None):
    checks={};crit=[];notes=[]
    secs=a.get('sections') or []; faq=a.get('faq') or []
    text=article_text(a); words=len(text.split()); body_html=' '.join(b for _,b in secs)
    # structure 20
    pts=0
    pts+=8 if len(secs)>=5 else (4 if len(secs)>=4 else 0)
    pts+=6 if len(faq)>=3 else (3 if len(faq)>=1 else 0)
    first=plain(secs[0][1]) if secs else ''
    pts+=6 if (secs and len(first.split())<=160 and len(first.split())>=25) else 2
    checks['structure']=pts
    # depth 20
    checks['depth']=20 if words>=1200 else 12 if words>=900 else 6 if words>=700 else 0
    # metadata 15
    title=a.get('title',''); ex=a.get('excerpt','')
    pts=5 if 20<=len(title)<=70 else 2 if len(title)<=80 else 0
    pts+=5 if 90<=len(ex)<=160 else 2 if 60<=len(ex)<=200 else 0
    kw=(a.get('keywords') or '')
    kw1=kw.split(',')[0].strip() if isinstance(kw,str) else (kw[0] if kw else '')
    kt=[w for w in toks(kw1)]; tt=set(toks(title+' '+(secs[0][0] if secs else '')))
    pts+=5 if (kt and sum(w in tt for w in kt)/len(kt)>=0.6) else (2 if kt else 0)
    checks['metadata']=pts
    # facts 15
    pts=15
    for ph in PHONE_RE.findall(text):
        digits=re.sub(r'\D','',ph)
        if digits not in ('0334699969','84334699969'): crit.append(f'số điện thoại lạ: {ph}'); pts-=5
    for h in HOURS_RE.findall(text):
        if (h[0].lstrip('0'),h[2].lstrip('0'))!=('8','17'): crit.append(f'giờ mở cửa sai: {h}'); pts-=5
    for rx,msg in BANNED:
        if re.search(rx,text,re.I): crit.append(msg); pts-=5
    amounts=set(re.findall(r'\d{1,3}(?:\.\d{3})+(?=\s*(?:đ(?![a-zà-ỹđ])|đồng|VNĐ))|\d+(?:,\d+)?\s(?:triệu|nghìn)',text))
    unsupported=sorted(x for x in amounts if x not in ALLOWED_AMOUNTS)
    has_ext=bool(re.search(r'href="https?://(?!thuha\.rentbikehanoi\.com)',body_html))
    srcs=a.get('sources') or []
    if unsupported and not (has_ext or srcs): crit.append('số tiền không có trong business-facts và không có nguồn: '+', '.join(unsupported[:6])); pts-=5
    elif unsupported: notes.append('số tiền ngoài business-facts (có nguồn): '+', '.join(unsupported[:6]))
    checks['facts']=max(0,pts)
    # sources 10
    hub=a.get('hub')
    if hub in NEEDS_SOURCES: checks['sources']=10 if (has_ext and srcs) else 5 if (has_ext or srcs) else 0
    else: checks['sources']=10 if not unsupported or srcs else 5
    # internal links 10
    links=set(re.findall(r'href="(/[^"#?]*)"',body_html))
    broken=[l for l in links if l not in urls and not l.startswith('/assets/')]
    if broken: crit.append('link nội bộ gãy: '+', '.join(broken[:5]))
    to_index=[l for l in links if l in docs and docs[l]['indexable'] or l in MONEY or re.fullmatch(r'/[a-z-]+/',l)]
    pts=10 if (len(to_index)>=3 and any(l in MONEY for l in links)) else 5 if len(to_index)>=1 else 0
    checks['internal_links']=pts
    # uniqueness 10
    ms,mu=uniq.max_sim(text,published_url or a.get('url'))
    checks['uniqueness']=10 if ms<0.5 else 5 if ms<0.6 else 0
    if ms>=0.6: crit.append(f'trùng {ms:.2f} với bài index {mu}')
    if published_url and a.get('url')!=published_url: crit.append('URL thay đổi so với bản đã xuất bản')
    score=sum(checks.values())
    return dict(url=a.get('url'),score=score,pass_=(score>=85 and not crit),checks=checks,critical=crit,notes=notes,words=words,sections=len(secs),faq=len(faq),max_sim=round(ms,3),max_sim_url=mu,title_len=len(title),excerpt_len=len(ex),internal_links=len(links),external_link=has_ext,sources=len(srcs))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('files',nargs='+'); ap.add_argument('--json',action='store_true'); ap.add_argument('--report'); ap.add_argument('--batch',default='')
    args=ap.parse_args()
    docs=load_corpus(); uniq=Uniq(docs); urls=existing_urls()|set(docs)
    out=[]; fails=0
    for f in args.files:
        a=json.loads(Path(f).read_text(encoding='utf-8'))
        r=qa(a,docs,uniq,urls,published_url=a.get('url')); r['file']=f; out.append(r)
        if not r['pass_']: fails+=1
        if not args.json: print(f"{'PASS' if r['pass_'] else 'FAIL'} {r['score']:3d} {a.get('url')}  {r['checks']}  {'CRIT: '+'; '.join(r['critical']) if r['critical'] else ''}")
    if args.json: print(json.dumps(out,ensure_ascii=False,indent=1))
    if args.report:
        with open(args.report,'a',encoding='utf-8') as fh:
            for r in out:
                fh.write(json.dumps(dict(ts=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),batch=args.batch,url=r['url'],score=r['score'],pass_=r['pass_'],checks=r['checks'],critical=r['critical'],after=dict(words=r['words'],sections=r['sections'],faq=r['faq'],max_sim=r['max_sim'],title_len=r['title_len'],excerpt_len=r['excerpt_len'],internal_links=r['internal_links'],external_link=r['external_link'],sources=r['sources'])),ensure_ascii=False)+'\n')
    sys.exit(1 if fails else 0)
if __name__=='__main__': main()
