#!/usr/bin/env bash
# Đồng bộ worktree lô với origin/main: bỏ bản cục bộ của shard đã DEPLOYED (main giữ bản đã ship, có qa_score), rồi fast-forward.
set -e
cd "$1"
git fetch -q origin main
DEPLOYED=$(python3 -c "
import csv
for r in csv.DictReader(open('/home/user/thuha/reports/seo-recovery/od1/od1_matrix.csv',encoding='utf-8')):
    if r['status']=='DEPLOYED': print(r['file'])")
for f in $(git status --porcelain | awk '{print $2}' | grep '^content/articles/' || true); do
  if echo "$DEPLOYED" | grep -qx "$f"; then git checkout -q -- "$f"; fi
done
git merge -q --ff-only origin/main
echo "synced $(git rev-parse --short HEAD); còn $(git status --porcelain | wc -l) file chưa ship"
