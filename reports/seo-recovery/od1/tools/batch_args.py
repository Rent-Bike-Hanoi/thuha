#!/usr/bin/env python3
"""In args JSON cho workflow od1-batch: python3 batch_args.py OD1-B01 [max_per_cluster]"""
import csv, json, sys
from collections import OrderedDict
OD = '/home/user/thuha/reports/seo-recovery/od1'
batch = sys.argv[1]; cap = int(sys.argv[2]) if len(sys.argv) > 2 else 4
rows = [r for r in csv.DictReader(open(f'{OD}/od1_matrix.csv', encoding='utf-8')) if r['batch'] == batch and r['status'] in ('TODO', 'RETRY')]
group = rows[0]['group']
libs = {'LUAT': ['legal_a', 'legal_b'], 'XDTP': ['bicycle_a', 'bicycle_b'], 'XDTR': ['bicycle_a', 'bicycle_b'], 'MTB': ['bicycle_a', 'bicycle_b'],
        'EVO': ['vinfast'], 'FELIZ': ['vinfast'], 'KLARA': ['vinfast'], 'XEMAY': ['xemay']}[group]
by = OrderedDict()
for r in rows: by.setdefault(r['cluster'], []).append(r)
clusters = []
for k, rs in by.items():
    for i in range(0, len(rs), cap):
        clusters.append({'key': f'{k}#{i // cap + 1}' if len(rs) > cap else k, 'items': [{'url': r['url'], 'id': r['id'], 'file': r['file']} for r in rs[i:i + cap]]})
# gộp cụm 1 bài (chủ đề luật khác nhau) thành nhóm tối đa `cap` bài cho đỡ số agent
merged, buf = [], []
for c in clusters:
    if len(c['items']) == 1:
        buf.append(c)
        if len(buf) == cap: merged.append({'key': '+'.join(x['key'] for x in buf), 'items': [i for x in buf for i in x['items']]}); buf = []
    else: merged.append(c)
if buf: merged.append({'key': '+'.join(x['key'] for x in buf), 'items': [i for x in buf for i in x['items']]})
num = batch.split('B')[-1].lower()
print(json.dumps({'batch': batch, 'group': group, 'worktree': f'/home/user/thuha-od1-b{num}', 'libs': libs, 'clusters': merged}, ensure_ascii=False))
