#!/usr/bin/env python3
"""Đưa các bài OD-1 đã kiểm chứng lên GitHub từ một worktree sạch.

    python3 ship_batch.py OD1-B01 /home/user/thuha-od1-b01 content/articles/NH-1.json [...] [--to-main] [--dry-run]

1. Worktree ship /home/user/thuha-ship được đặt lại về origin/main (sạch, không dính bài đang viết dở).
2. Chép đúng các shard được chỉ định từ worktree của lô sang.
3. QA greedy (scripts/seo_recover_batch.py --greedy) theo thứ tự kế hoạch; bài FAIL không được ship
   (bản đang chạy giữ nguyên, vẫn index; bản nháp vẫn nằm ở worktree lô để sửa tiếp).
4. Commit nguồn, build, chạy chuỗi kiểm tra như CI, commit build, push nhánh; --to-main: đẩy fast-forward lên main.
In JSON kết quả (passed/failed) để kiểm tra production và cập nhật matrix.
"""
import json, shutil, subprocess, sys
from pathlib import Path

OD = Path('/home/user/thuha/reports/seo-recovery/od1')
SHIP = Path('/home/user/thuha-ship')
REPO = Path('/home/user/thuha')
args = [a for a in sys.argv[1:] if not a.startswith('--')]
batch, src_wt, files = args[0], Path(args[1]), args[2:]
dry = '--dry-run' in sys.argv
SIGN = '\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01YC5sVeVLYfNbEcJXTECzKH'


def sh(*cmd, cwd=SHIP, check=True):
    r = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if check and r.returncode: raise SystemExit(f'FAILED: {" ".join(map(str, cmd))}\n{r.stdout}{r.stderr}')
    return r


sh('git', 'fetch', '-q', 'origin', 'main', cwd=REPO)
if not SHIP.exists(): sh('git', 'worktree', 'add', '-q', '--detach', str(SHIP), 'origin/main', cwd=REPO)
sh('git', 'checkout', '-q', '--detach', 'origin/main'); sh('git', 'reset', '-q', '--hard', 'origin/main'); sh('git', 'clean', '-qfd')
shutil.copy(REPO / 'scripts/seo_recover_batch.py', SHIP / 'scripts/seo_recover_batch.py')

order = []
for p in (OD / 'plan').glob('*.json'):
    order += [e['url'] for e in json.load(open(p, encoding='utf-8'))['entries']]
for f in files:
    a = json.load(open(src_wt / f, encoding='utf-8'))
    head = json.load(open(SHIP / f, encoding='utf-8'))
    if a['url'] != head['url'] or a['id'] != head['id'] or (a.get('rewrite') or {}).get('batch') != batch:
        raise SystemExit(f'không khớp url/id/batch: {f}')
    shutil.copy(src_wt / f, SHIP / f)
files.sort(key=lambda f: order.index(json.load(open(SHIP / f, encoding='utf-8'))['url']) if json.load(open(SHIP / f, encoding='utf-8'))['url'] in order else 9999)

r = sh('python3', 'scripts/seo_recover_batch.py', '--batch', batch, '--greedy', '--dry-run', *files, check=False)
fails = {line.split(' ', 3)[2]: line[:300] for line in r.stdout.splitlines() if line.startswith('FAIL')}
passed = [f for f in files if json.load(open(SHIP / f, encoding='utf-8'))['url'] not in fails]
failed = [f for f in files if f not in passed]
res = dict(batch=batch, passed=[], failed=[dict(file=f, reason=fails.get(json.load(open(SHIP / f, encoding='utf-8'))['url'], '')) for f in failed])
for f in failed: sh('git', 'checkout', '--', f)
if dry or not passed:
    res['passed'] = [dict(file=f, url=json.load(open(SHIP / f, encoding='utf-8'))['url']) for f in passed]
    print(json.dumps(res, ensure_ascii=False, indent=1)); raise SystemExit
sh('python3', 'scripts/seo_recover_batch.py', '--batch', batch, '--greedy', *passed)
for f in passed:
    a = json.load(open(SHIP / f, encoding='utf-8'))
    res['passed'].append(dict(url=a['url'], file=f, title=a['title'], qa_score=(a.get('rewrite') or {}).get('qa_score')))
import time
branch = f'claude/seo-{batch.lower()}-ship-{time.strftime("%m%d%H%M")}'
sh('git', 'checkout', '-q', '-B', branch)
sh('git', 'add', *passed, 'config/factory-reindex.json', 'reports/seo-recovery/data', 'scripts/seo_recover_batch.py')
sh('git', 'commit', '-q', '-m', f'content({batch}): viết lại {len(passed)} bài OD-1 đúng chủ đề URL, nguồn kiểm chứng; giữ URL, vẫn index' + SIGN)
sh('python3', 'scripts/build.py')
for c in (['python3', 'scripts/topic_matrix.py', 'sync'], ['python3', 'scripts/topic_matrix.py', 'validate'], ['python3', 'tests/test_topic_matrix.py'],
          ['python3', 'tests/test_factory_v2.py'], ['python3', 'tests/test_facebook_posts.py'], ['python3', 'tests/test_content_factory.py'],
          ['python3', 'scripts/content_factory.py', 'run', '--dry-run'], ['python3', 'scripts/validate_factory_site.py']):
    sh(*c)
sh('git', 'checkout', '--', 'data/topic-matrix-published.jsonl', 'data/topic-matrix.jsonl', check=False)
sh('git', 'add', '-A')
sh('git', 'commit', '-q', '-m', f'build({batch}): dựng lại trang sau khi viết lại {len(passed)} bài OD-1' + SIGN)
sh('git', 'push', '-q', 'origin', f'HEAD:refs/heads/{branch}')
if '--to-main' in sys.argv:
    sh('git', 'fetch', '-q', 'origin', 'main')
    sh('git', 'merge-base', '--is-ancestor', 'origin/main', 'HEAD')
    sh('git', 'push', '-q', 'origin', 'HEAD:main')
    res['pushed_main'] = True
res['head'] = sh('git', 'rev-parse', 'HEAD').stdout.strip()
print(json.dumps(res, ensure_ascii=False, indent=1))
