#!/usr/bin/env python3
"""Mở index có kiểm chứng cho một lô bài V1 đã viết lại (SEO recovery 10/2026).

Dùng: python3 scripts/seo_recover_batch.py --batch B03 content/articles/NH-00693.json [...] [--dry-run]

Với mỗi shard: chạy lại scripts/seo_qa.py; chỉ bài PASS (>= 85, không critical) mới được
  - bỏ khỏi config/factory-noindex.json (nếu có),
  - thêm vào config/factory-reindex.json,
  - ghi rewrite.qa_score vào shard (validator yêu cầu),
  - ghi reports/seo-recovery/data/qa_report.jsonl và changelog.jsonl.
Bài FAIL giữ nguyên trạng thái noindex.  Không đổi URL, slug, canonical.
"""
import argparse,datetime,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import seo_qa
DATA=ROOT/'reports/seo-recovery/data'
def now(): return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).isoformat(timespec='seconds')
def git_show(path):
    r=subprocess.run(['git','show','HEAD:'+path],cwd=ROOT,capture_output=True,text=True)
    return json.loads(r.stdout) if r.returncode==0 and r.stdout.strip() else None
def plainwords(a): return len(seo_qa.article_text(a).split())
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('files',nargs='+'); ap.add_argument('--batch',required=True); ap.add_argument('--dry-run',action='store_true')
    args=ap.parse_args()
    nl_path=ROOT/'config/factory-noindex.json'; rl_path=ROOT/'config/factory-reindex.json'
    nl=json.loads(nl_path.read_text(encoding='utf-8')); rl=json.loads(rl_path.read_text(encoding='utf-8'))
    docs=seo_qa.load_corpus(); uniq=seo_qa.Uniq(docs); urls=seo_qa.existing_urls()|set(docs)
    passed=[];failed=[];qa_rows=[];log=[]
    for f in args.files:
        p=ROOT/f if not Path(f).is_absolute() else Path(f); rel=str(p.relative_to(ROOT))
        a=json.loads(p.read_text(encoding='utf-8')); before=git_show(rel)
        if before and before['url']!=a['url']: print('URL CHANGED, refusing:',rel); failed.append(rel); continue
        r=seo_qa.qa(a,docs,uniq,urls,published_url=(before or a)['url'])
        rw=a.get('rewrite') or {}
        ok=r['pass_'] and bool(rw.get('rewrittenAt'))
        row=dict(ts=now(),batch=args.batch,url=a['url'],score=r['score'],pass_=ok,checks=r['checks'],critical=r['critical']+([] if rw.get('rewrittenAt') else ['missing rewrite.rewrittenAt']),
                 before=dict(title=(before or {}).get('title'),words=plainwords(before) if before else None,noindex=True) ,
                 after=dict(title=a['title'],words=r['words'],sections=r['sections'],faq=r['faq'],max_sim=r['max_sim'],max_sim_url=r['max_sim_url'],sources=r['sources'],external_link=r['external_link'],noindex=not ok),
                 production_verified=False,evidence='scripts/seo_qa.py')
        qa_rows.append(row)
        if not ok: failed.append(rel); print('FAIL',r['score'],a['url'],r['critical']); continue
        passed.append(a['url'])
        rw.update(qa_score=r['score'],qa_checked=now()); a['rewrite']=rw
        if not args.dry_run:
            orig=p.read_text(encoding='utf-8'); ind=2 if orig.startswith('{\n  "') else 1
            p.write_text(json.dumps(a,ensure_ascii=False,indent=ind)+'\n',encoding='utf-8')
        for fld in ('title','excerpt','keywords'):
            if before and before.get(fld)!=a.get(fld):
                log.append(dict(ts=now(),batch=args.batch,url=a['url'],file=rel,change_type='content',field=fld,before=before.get(fld),after=a.get(fld),commit='(pending)',note=''))
        log.append(dict(ts=now(),batch=args.batch,url=a['url'],file=rel,change_type='content',field='sections/faq/sources',before=f"{plainwords(before) if before else '?'} từ, {len((before or {}).get('sections',[]))} mục, 0 nguồn",after=f"{r['words']} từ, {r['sections']} mục, {r['faq']} FAQ, {r['sources']} nguồn; QA {r['score']}",commit='(pending)',note='viết lại toàn bộ, giữ URL'))
        log.append(dict(ts=now(),batch=args.batch,url=a['url'],file='config/factory-noindex.json, config/factory-reindex.json',change_type='indexability',field='robots',before='noindex,follow ('+('factory-noindex.json' if a['url'] in nl['urls'] else 'cờ noindex_factory_articles')+')',after='index-eligible (factory-reindex.json), vào sitemap-posts.xml',commit='(pending)',note=''))
    if not args.dry_run and passed:
        nl['urls']=[u for u in nl['urls'] if u not in set(passed)]
        rl['urls']=sorted(set(rl['urls'])|set(passed))
        nl_path.write_text(json.dumps(nl,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
        rl_path.write_text(json.dumps(rl,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
        with open(DATA/'qa_report.jsonl','a',encoding='utf-8') as fh:
            for x in qa_rows: fh.write(json.dumps(x,ensure_ascii=False)+'\n')
        with open(DATA/'changelog.jsonl','a',encoding='utf-8') as fh:
            for x in log: fh.write(json.dumps(x,ensure_ascii=False)+'\n')
    elif not args.dry_run:
        with open(DATA/'qa_report.jsonl','a',encoding='utf-8') as fh:
            for x in qa_rows: fh.write(json.dumps(x,ensure_ascii=False)+'\n')
    print(json.dumps(dict(batch=args.batch,passed=len(passed),failed=failed),ensure_ascii=False))
    sys.exit(0)
if __name__=='__main__': main()
