#!/usr/bin/env python3
"""Fanpage Facebook: mỗi ngày 3 bài tóm tắt từ trang web (một bài mỗi nhóm trong config/facebook-posts.json).

- Chỉ lấy trang đang có trong sitemap (đã được index), không bao giờ lấy bài xưởng V1 đã noindex.
- Xoay vòng theo ngày bằng thứ tự băm ổn định: không cần lưu trạng thái, chạy lại cùng ngày ra cùng 3 bài.
- Thông tin liên hệ lấy từ config/business-facts.json (số điện thoại, giờ, địa chỉ, fanpage, Maps).
- Đăng qua Graph API chỉ khi có biến môi trường FB_PAGE_ID và FB_PAGE_TOKEN (GitHub secrets);
  thiếu thì in bài ra để đăng tay. Không dùng AI API, không ảnh hưởng writer hay build.

  python3 scripts/facebook_posts.py show --date 2026-10-13 [--days 7] [--out file.md]
  python3 scripts/facebook_posts.py publish --date 2026-10-13 [--summary FILE] [--dry-run]
"""
import argparse
import datetime as dt
import glob
import hashlib
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_config(root=ROOT):
    return json.loads((root / 'config/facebook-posts.json').read_text())


def load_facts(root=ROOT):
    return json.loads((root / 'config/business-facts.json').read_text())


def sitemap_urls(root=ROOT):
    urls = set()
    for name in ('sitemap-posts.xml', 'sitemap-pages.xml'):
        path = root / name
        if not path.exists():
            raise SystemExit(f'thiếu {name}: chạy python3 scripts/build.py trước')
        urls.update(re.findall(r'<loc>https?://[^/<]+(/[^<]*)</loc>', path.read_text()))
    return urls


def load_candidates(root=ROOT):
    """Bài viết tay (posts.json) và bài V2 (content/articles/TM-*.json) đang có trong sitemap."""
    indexed = sitemap_urls(root)
    items = [p for p in json.loads((root / 'content/posts.json').read_text()) if p.get('kind') in ('article', 'pillar')]
    for path in sorted(glob.glob(str(root / 'content/articles/*.json'))):
        art = json.loads(Path(path).read_text())
        if art.get('factoryVersion', 1) >= 2 and art.get('kind') == 'article':
            items.append(art)
    seen, out = set(), []
    for p in items:
        if p['url'] in indexed and p['url'] not in seen:
            seen.add(p['url'])
            out.append(p)
    return out


def pools(candidates, cfg):
    out = []
    for pool in cfg['pools']:
        items = [p for p in candidates if p.get('hub') in pool['hubs']]
        items.sort(key=lambda p: hashlib.sha1(p['url'].encode()).hexdigest())
        out.append((pool, items))
    return out


def day_index(date, cfg):
    return (date - dt.date.fromisoformat(cfg['start_date'])).days


def headings(item, cfg, limit=3):
    skip = {h.lower() for h in cfg.get('skip_headings', [])}
    out = []
    for sec in item.get('sections') or []:
        head = html.unescape(re.sub(r'<[^>]+>', '', str(sec[0] if isinstance(sec, (list, tuple)) else sec.get('heading', '')))).strip()
        if head and head.lower() not in skip and head not in out:
            out.append(head)
        if len(out) == limit:
            break
    return out


def contact_lines(facts):
    phone_digits = re.sub(r'\D', '', facts['phone'])
    intl_digits = re.sub(r'\D', '', facts['international_phone'])
    lines = [f"📞 Gọi: {facts['phone']}",
             f'💬 Zalo: https://zalo.me/{phone_digits}',
             f'💬 WhatsApp: https://wa.me/{intl_digits}']
    page = urllib.parse.urlparse(facts.get('facebook_url') or '').path.strip('/')
    if page and '/' not in page and not page.endswith('.php'):
        lines.append(f'💬 Messenger: https://m.me/{page}')
    lines.append(f"⏰ Giờ mở cửa: {facts['hours']}")
    address = facts['address'] + (f" ({facts['landmark']})" if facts.get('landmark') else '')
    lines.append(f'📍 Địa chỉ: {address}')
    if facts.get('maps_url'):
        lines.append(f"🗺️ Chỉ đường: {facts['maps_url']}")
    return lines


def post_link(item, site_url, cfg):
    utm = cfg.get('utm')
    return site_url + item['url'] + (f'?{utm}' if utm else '')


def message(item, facts, cfg, site_url):
    parts = [html.unescape(item['title']), '', html.unescape(item.get('excerpt', '')).strip()]
    heads = headings(item, cfg)
    if heads:
        parts += ['', 'Trong bài:'] + [f'• {h}' for h in heads]
    parts += ['', f'👉 Đọc đầy đủ: {post_link(item, site_url, cfg)}', '', facts['brand']] + contact_lines(facts)
    if cfg.get('hashtags'):
        parts += ['', ' '.join(cfg['hashtags'])]
    return '\n'.join(parts)


def plan(date, root=ROOT, cfg=None, facts=None):
    cfg = cfg or load_config(root)
    facts = facts or load_facts(root)
    site_url = json.loads((root / 'content/site.json').read_text())['url'].rstrip('/')
    d = day_index(date, cfg)
    posts = []
    for slot, (pool, items) in zip(cfg['slots'], pools(load_candidates(root), cfg)):
        if not items:
            continue
        item = items[d % len(items)]
        posts.append({'date': date.isoformat(), 'slot': slot, 'pool': pool['name'], 'url': item['url'],
                      'title': item['title'], 'link': post_link(item, site_url, cfg),
                      'message': message(item, facts, cfg, site_url)})
    return posts


def slot_time(date, slot, cfg):
    hh, mm = map(int, slot.split(':'))
    tz = dt.timezone(dt.timedelta(hours=cfg.get('timezone_offset_hours', 7)))
    return dt.datetime(date.year, date.month, date.day, hh, mm, tzinfo=tz)


def as_markdown(posts):
    out = []
    for p in posts:
        out += [f"## {p['date']} {p['slot']} · {p['title']}", '', '```text', p['message'], '```', '']
    return '\n'.join(out)


def graph_post(page_id, token, version, params):
    data = urllib.parse.urlencode({**params, 'access_token': token}).encode()
    req = urllib.request.Request(f'https://graph.facebook.com/{version}/{page_id}/feed', data=data, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return True, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors='replace')
        try:
            err = json.loads(body).get('error', {})
            return False, {'error': err.get('message', body)[:300], 'code': err.get('code')}
        except ValueError:
            return False, {'error': body[:300], 'code': e.code}
    except urllib.error.URLError as e:
        return False, {'error': str(e.reason)[:300]}


def publish(date, root=ROOT, dry_run=False, now=None, poster=graph_post, env=None):
    env = os.environ if env is None else env
    cfg = load_config(root)
    if not cfg.get('enabled', True):
        return [], 'Đăng Facebook đang tắt (config/facebook-posts.json: enabled=false).'
    posts = plan(date, root, cfg)
    page_id, token = env.get('FB_PAGE_ID', '').strip(), env.get('FB_PAGE_TOKEN', '').strip()
    if dry_run or not (page_id and token):
        why = 'chạy thử' if dry_run else 'chưa có secret FB_PAGE_ID / FB_PAGE_TOKEN'
        return posts, f'Không đăng ({why}). Đăng tay {len(posts)} bài dưới đây.'
    now = now or dt.datetime.now(dt.timezone.utc)
    version = env.get('FB_GRAPH_VERSION') or cfg.get('graph_api_version', 'v23.0')
    errors = 0
    for p in posts:
        when = slot_time(date, p['slot'], cfg)
        params = {'message': p['message'], 'link': p['link']}
        # Graph API chỉ nhận lịch đăng từ 10 phút đến 30 ngày tới; giờ đã qua thì đăng ngay.
        if when - now > dt.timedelta(minutes=11):
            params.update(published='false', scheduled_publish_time=str(int(when.timestamp())))
        ok, res = poster(page_id, token, version, params)
        p['result'] = res if ok else {'error': res.get('error'), 'code': res.get('code')}
        p['status'] = ('scheduled' if 'scheduled_publish_time' in params else 'published') if ok else 'failed'
        errors += not ok
    return posts, f"Đã gửi {len(posts) - errors}/{len(posts)} bài lên fanpage." + (f' {errors} bài lỗi.' if errors else '')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    for name in ('show', 'publish'):
        s = sub.add_parser(name)
        s.add_argument('--date', default=dt.datetime.now(dt.timezone(dt.timedelta(hours=7))).date().isoformat())
        if name == 'show':
            s.add_argument('--days', type=int, default=1)
            s.add_argument('--out')
        else:
            s.add_argument('--dry-run', action='store_true')
            s.add_argument('--summary', help='ghi kết quả dạng Markdown (ví dụ $GITHUB_STEP_SUMMARY)')
    a = ap.parse_args(argv)
    date = dt.date.fromisoformat(a.date)
    if a.cmd == 'show':
        posts = [p for i in range(a.days) for p in plan(date + dt.timedelta(days=i))]
        text = as_markdown(posts)
        if a.out:
            Path(a.out).write_text(text)
            print(a.out, len(posts), 'bài')
        else:
            print(text)
        return 0
    posts, note = publish(date, dry_run=a.dry_run)
    report = '\n'.join([f'# Fanpage {a.date}', '', note, ''] +
                       [f"- {p['slot']} {p.get('status', 'chưa đăng')}: {p['title']} ({p['url']})" +
                        (f" — {p['result']['error']}" if p.get('status') == 'failed' else '') for p in posts] +
                       ['', as_markdown(posts)])
    if a.summary:
        with open(a.summary, 'a') as fh:
            fh.write(report + '\n')
    print(report)
    return 1 if any(p.get('status') == 'failed' for p in posts) else 0


if __name__ == '__main__':
    sys.exit(main())
