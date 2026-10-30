#!/usr/bin/env python3
"""Sinh báo cáo Markdown của dự án SEO recovery từ reports/seo-recovery/data/.

Dùng: python3 scripts/seo_recovery_report.py   ->  reports/seo-recovery/REPORT.md, CHECKPOINT.md
Chỉ đọc dữ liệu đã ghi (inventory, classification, qa_report, changelog, checkpoint, technical_findings,
repo_audit, gsc_*). Không tạo số liệu: trường nào không có dữ liệu thì ghi NOT_VERIFIED.
"""
import csv,json,collections,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; D=ROOT/'reports/seo-recovery/data'; OUT=ROOT/'reports/seo-recovery'
def rcsv(n,delim=','):
    p=D/n
    return list(csv.DictReader(open(p,encoding='utf-8'),delimiter=delim)) if p.exists() else []
def rjsonl(n):
    p=D/n
    return [json.loads(l) for l in open(p,encoding='utf-8') if l.strip()] if p.exists() else []
def rjson(n,default=None):
    p=D/n
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default
inv=rcsv('inventory.csv'); cls={r['url']:r for r in rcsv('classification.csv')}; qa=rjsonl('qa_report.jsonl'); cl=rjsonl('changelog.jsonl')
tech=rjson('technical_findings.json',[]); repo=rjson('repo_audit.json',[]); cp=rjson('checkpoint.json',{})
insp={r['url']:r for r in rcsv('gsc_inspection_2026-10-30.tsv','\t')}
reidx=json.loads((ROOT/'config/factory-reindex.json').read_text())['urls']
nl=json.loads((ROOT/'config/factory-noindex.json').read_text())['urls']
C=collections.Counter
def t(rows,head):
    s='| '+' | '.join(head)+' |\n|'+'---|'*len(head)+'\n'
    for r in rows: s+='| '+' | '.join(str(x).replace('|','/') for x in r)+' |\n'
    return s
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime('%Y-%m-%d %H:%M')
latest={}
for q in qa:
    if q['url'].startswith('/'): latest[q['url']]=q
recovered=[u for u in reidx]
md=[f'# Báo cáo SEO recovery thuha.rentbikehanoi.com\n\nCập nhật {now} (giờ Hà Nội). Sinh tự động từ `reports/seo-recovery/data/` bằng `scripts/seo_recovery_report.py`.\n',
'> INDEX_ELIGIBLE (trang cho phép index, có trong sitemap) **không** đồng nghĩa INDEXED trên Google. Trạng thái Google chỉ lấy từ Search Console; URL chưa kiểm tra ghi NOT_VERIFIED.\n']
md.append('## 1. Tổng quan trước / sau\n')
pt=C(r['page_type'] for r in inv); ni=C(r['noindex'] for r in inv)
md.append(t([['URL render (kiểm kê đầu dự án)',len(inv)],['  trong đó noindex lúc audit',ni.get('True',0)],['  index-eligible lúc audit',ni.get('False',0)],['URL đã xoá trước dự án (10/10/2026, 404)',sum(1 for _ in open(D/'removed_prior_2026-10-10.csv'))-1],['Bài V1 đã mở index có kiểm chứng',len(recovered)],['URL còn trong config/factory-noindex.json',len(nl)]],['Chỉ số','Giá trị']))
md.append('\n### Phân loại (classification.csv)\n')
md.append(t(sorted(C((r['category'],r['action'],r['status']) for r in cls.values()).items()),['(Nhóm, hành động, trạng thái)','Số URL']))
md.append('\n## 2. Audit hai repository\n'); md.append(t([[r['item'],r['value'],r['risk'],r.get('note','')] for r in repo],['Hạng mục','Kết quả','Rủi ro','Ghi chú']))
md.append('\n## 3. Phục hồi noindex: nguyên nhân và quyết định\n')
md.append(t(sorted(C(r['noindex_reason'] for r in inv if r['noindex']=='True').items()),['Nguyên nhân noindex lúc audit','Số URL']))
md.append('\n### URL đã mở index (lô đã merge/đang merge)\n')
md.append(t([[u,latest.get(u,{}).get('batch',''),latest.get(u,{}).get('score',''),cls.get(u,{}).get('gsc_impressions',''),insp.get(u,{}).get('coverageState','NOT_VERIFIED')] for u in recovered],['URL','Lô','QA','GSC hiển thị (8–10/2026)','GSC index (30/10)']))
blocked=[r for r in cls.values() if r['status']=='BLOCKED' and r['page_type'].startswith('article')]
md.append(f'\n### URL giữ noindex có lý do (BLOCKED): {len(blocked)}\n\nDanh sách đầy đủ trong sheet 03_INDEX_RECOVERY. Theo lý do:\n')
md.append(t(C(r['reason'].split(';')[0].split(' -> ')[0][:120] for r in blocked).most_common(15),['Lý do (rút gọn)','Số URL']))
md.append('\n## 4. Nội dung và trùng lặp\n')
sim=rcsv('similarity.csv'); pairs=[r for r in sim if r['indexable']=='True' and r['max_sim_indexable'] and float(r['max_sim_indexable'])>=0.6]
md.append(f'- Bài index-eligible có cặp tương đồng >= 0,60 với bài index khác: {len(pairs)} (sheet 05).\n- Cụm trùng >= 0,80 giữa bài V1: xem sheet 05 (cluster_id).\n')
md.append('\n## 5. Technical SEO\n'); md.append(t([[x['area'],x['finding'][:260],x['affected_count'],x['status'],x.get('commit','')] for x in tech],['Hạng mục','Phát hiện','Ảnh hưởng','Trạng thái','Commit']))
md.append('\n## 6. Changelog và QA\n'); md.append(f'- Changelog: {len(cl)} dòng (sheet 09).\n- QA: {len(qa)} lượt; PASS {sum(1 for q in qa if q.get("pass_") in (True,"True"))}, FAIL {sum(1 for q in qa if q.get("pass_") in (False,"False"))} (sheet 10).\n')
md.append('\n## 7. GSC\n'); daily=rcsv('gsc_daily_2026-10-05_10-27.tsv','\t')
md.append(f'- Tổng 05–27/10/2026: {sum(int(r["clicks"]) for r in daily)} click, {sum(int(r["impressions"]) for r in daily)} hiển thị (Windsor.ai).\n')
md.append(t(sorted(C(r['coverageState'] for r in insp.values()).items()),['URL Inspection 30/10 (50 URL mẫu)','Số URL']))
md.append('\n## 8. Checkpoint\n'); md.append('```json\n'+json.dumps(cp,ensure_ascii=False,indent=1)+'\n```\n')
(OUT/'REPORT.md').write_text('\n'.join(md),encoding='utf-8')
ck=['# CHECKPOINT – SEO recovery thuha.rentbikehanoi.com\n',f'Cập nhật {now}. Phiên sau đọc file này trước, rồi `reports/seo-recovery/data/checkpoint.json`.\n',
'## Trạng thái\n','```json\n'+json.dumps(cp,ensure_ascii=False,indent=1)+'\n```\n',
'## Quy trình mỗi lô (không bỏ bước)\n','1. Chọn URL `action=REWRITE_THEN_INDEX, status=OPEN` trong `data/classification.csv` (ưu tiên P1 > P2 > P3).',
'2. Viết lại shard `content/articles/<ID>.json` giữ id/url/hub/parent/kind/art/tone/intent/factoryVersion; thêm `sources`, `rewrite{rewrittenAt,by,batch}`.',
'3. `python3 scripts/seo_recover_batch.py --batch <Bxx> <files>` (QA >= 85, chặn trùng >= 0,60, link tới bài noindex).',
'4. `python3 scripts/build.py && python3 scripts/validate_factory_site.py` + 4 bộ test + `topic_matrix.py validate` + `content_factory.py run --dry-run`.',
'5. Kiểm kê trước/sau (0 URL mất, 0 canonical đổi) → commit → PR → CI xanh → merge → kiểm tra live → `mcp OpenSEO inspect_urls` (bind tạm property thuha) → cập nhật data + `scripts/seo_matrix_export.py` + `scripts/seo_recovery_report.py`.\n',
'## Quy tắc bất biến\n','Không xoá bài, không đổi slug/URL/canonical/permalink/DNS/CNAME, không redirect hay noindex bài đang index tốt khi chưa có chủ site duyệt, không số liệu không nguồn, không ghi số GSC giả.\n']
(OUT/'CHECKPOINT.md').write_text('\n'.join(ck),encoding='utf-8')
print('wrote',OUT/'REPORT.md',OUT/'CHECKPOINT.md')
