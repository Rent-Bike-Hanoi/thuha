#!/usr/bin/env python3
"""Đưa một lô OD-1 lên GitHub (chạy trong worktree của lô, cwd = worktree).

    python3 /home/user/thuha/reports/seo-recovery/od1/tools/ship_batch.py OD1-B01 [--dry-run]

1. Cập nhật nhánh lô lên origin/main (fast-forward, giữ thay đổi shard chưa commit).
2. QA greedy (scripts/seo_recover_batch.py --greedy --dry-run) theo thứ tự kế hoạch.
3. Bài FAIL: lưu bản nháp vào reports/seo-recovery/drafts/<lô>/ rồi khôi phục bản đang chạy (không noindex, không đổi URL).
4. Bài PASS: chạy seo_recover_batch thật (factory-reindex + qa_report + changelog), commit nguồn,
   build, chạy chuỗi kiểm tra như CI, commit build, push nhánh.
In JSON kết quả cuối cùng (pass/fail/blocked) để cập nhật matrix và tạo PR.
"""
import csv, json, shutil, subprocess, sys
from pathlib import Path

OD = Path('/home/user/thuha/reports/seo-recovery/od1')
WT = Path.cwd()
batch = sys.argv[1]; dry = '--dry-run' in sys.argv
SIGN = '\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01YC5sVeVLYfNbEcJXTECzKH'


def sh(*cmd, check=True, capture=False):
    r = subprocess.run(cmd, cwd=WT, text=True, capture_output=capture)
    if check and r.returncode: raise SystemExit(f'FAILED: {" ".join(cmd)}\n{r.stdout or ""}{r.stderr or ""}')
    return r


rows = [r for r in csv.DictReader(open(OD / 'od1_matrix.csv', encoding='utf-8')) if r['batch'] == batch]
group = rows[0]['group']
plan = {e['url']: e for e in json.load(open(OD / 'plan' / f'{group}.json', encoding='utf-8'))['entries']}
order = [e['url'] for e in json.load(open(OD / 'plan' / f'{group}.json', encoding='utf-8'))['entries']]
byurl = {r['url']: r for r in rows}

sh('git', 'fetch', '-q', 'origin', 'main')
sh('git', 'merge', '-q', '--ff-only', 'origin/main')
# script batch QA đã sửa log (nằm ở nhánh recovery) — mang theo nếu main chưa có
src = Path('/home/user/thuha/scripts/seo_recover_batch.py')
if src.read_text() != (WT / 'scripts/seo_recover_batch.py').read_text(): shutil.copy(src, WT / 'scripts/seo_recover_batch.py')

changed = [l[3:] for l in sh('git', 'status', '--porcelain', capture=True).stdout.splitlines() if l[3:].startswith('content/articles/')]
mine, stray = [], []
for f in changed:
    a = json.load(open(WT / f, encoding='utf-8'))
    (mine if a['url'] in byurl and (a.get('rewrite') or {}).get('batch') == batch else stray).append(f)
if stray: raise SystemExit(f'shard ngoài lô hoặc chưa ghi rewrite.batch: {stray}')
mine.sort(key=lambda f: order.index(json.load(open(WT / f, encoding='utf-8'))['url']) if json.load(open(WT / f, encoding='utf-8'))['url'] in order else 9999)

r = sh('python3', 'scripts/seo_recover_batch.py', '--batch', batch, '--greedy', '--dry-run', *mine, check=False, capture=True)
fails = {}
for line in r.stdout.splitlines():
    if line.startswith('FAIL'):
        parts = line.split(' ', 3)
        fails[parts[2]] = line
passed = [f for f in mine if json.load(open(WT / f, encoding='utf-8'))['url'] not in fails]
failed = [f for f in mine if f not in passed]
todo = [u for u in byurl if u not in {json.load(open(WT / f, encoding='utf-8'))['url'] for f in mine}]
blocked = [u for u in todo if plan.get(u, {}).get('feasible') is False]
result = dict(batch=batch, passed=[], failed=[], untouched=[u for u in todo if u not in blocked], blocked=blocked)
for f in failed:
    a = json.load(open(WT / f, encoding='utf-8'))
    result['failed'].append(dict(url=a['url'], file=f, reason=fails.get(a['url'], '')[:300]))
if dry:
    result['passed'] = [json.load(open(WT / f, encoding='utf-8'))['url'] for f in passed]
    print(json.dumps(result, ensure_ascii=False, indent=1)); raise SystemExit
for f in failed:
    d = WT / 'reports/seo-recovery/drafts' / batch; d.mkdir(parents=True, exist_ok=True)
    shutil.copy(WT / f, d / Path(f).name)
    sh('git', 'checkout', 'origin/main', '--', f)
if not passed:
    print(json.dumps(result, ensure_ascii=False, indent=1)); raise SystemExit
sh('python3', 'scripts/seo_recover_batch.py', '--batch', batch, '--greedy', *passed, capture=True)
for f in passed:
    a = json.load(open(WT / f, encoding='utf-8'))
    result['passed'].append(dict(url=a['url'], file=f, title=a['title'], qa_score=(a.get('rewrite') or {}).get('qa_score')))
sh('git', 'add', 'content/articles', 'config/factory-reindex.json', 'reports/seo-recovery', 'scripts/seo_recover_batch.py')
sh('git', 'commit', '-q', '-m', f'content({batch}): viết lại {len(passed)} bài OD-1 theo đúng chủ đề URL, nguồn kiểm chứng; giữ URL, vẫn index' + SIGN)
sh('python3', 'scripts/build.py', capture=True)
for c in (['python3', 'scripts/topic_matrix.py', 'sync'], ['python3', 'scripts/topic_matrix.py', 'validate'], ['python3', 'tests/test_topic_matrix.py'],
          ['python3', 'tests/test_factory_v2.py'], ['python3', 'tests/test_facebook_posts.py'], ['python3', 'tests/test_content_factory.py'],
          ['python3', 'scripts/content_factory.py', 'run', '--dry-run'], ['python3', 'scripts/validate_factory_site.py']):
    sh(*c, capture=True)
sh('git', 'checkout', '--', 'data/topic-matrix-published.jsonl', 'data/topic-matrix.jsonl', check=False)
sh('git', 'add', '-A')
sh('git', 'commit', '-q', '-m', f'build({batch}): dựng lại trang sau khi viết lại bài OD-1' + SIGN)
sh('git', 'push', '-q', '-u', 'origin', 'HEAD')
result['head'] = sh('git', 'rev-parse', 'HEAD', capture=True).stdout.strip()
print(json.dumps(result, ensure_ascii=False, indent=1))
