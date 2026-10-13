#!/usr/bin/env python3
"""Kiểm tra scripts/facebook_posts.py: chọn bài, nội dung bài đăng, đăng/không đăng."""
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import facebook_posts as F  # noqa: E402

FACTS = json.loads((ROOT / 'config/business-facts.json').read_text())
DAY = dt.date(2026, 10, 13)


def test_three_posts_one_per_pool():
    posts = F.plan(DAY)
    assert len(posts) == 3, posts
    assert [p['pool'] for p in posts] == ['dich-vu', 'huong-dan', 'luat']
    assert len({p['url'] for p in posts}) == 3


def test_only_indexed_pages():
    indexed = F.sitemap_urls()
    v1 = {json.loads(p.read_text())['url'] for p in (ROOT / 'content/articles').glob('NH-*.json')}
    for i in range(60):
        for p in F.plan(DAY + dt.timedelta(days=i)):
            assert p['url'] in indexed, p['url']
            assert p['url'] not in v1, p['url']


def test_message_has_contact_block():
    for p in F.plan(DAY):
        m = p['message']
        for needle in (FACTS['phone'], 'https://zalo.me/0334699969', 'https://wa.me/84334699969', FACTS['hours'],
                       FACTS['address'], p['link'], 'Thuê xe máy Nguyễn Hà'):
            assert needle in m, (needle, p['url'])
        assert p['link'].startswith('https://thuha.rentbikehanoi.com' + p['url'] + '?utm_source=facebook')
        assert 'rentbikehanoi.com/' not in m.replace('thuha.rentbikehanoi.com/', '')
        assert len(m) < 2000


def test_deterministic_and_rotates():
    assert F.plan(DAY) == F.plan(DAY)
    week = [p['url'] for i in range(7) for p in F.plan(DAY + dt.timedelta(days=i)) if p['pool'] == 'huong-dan']
    assert len(set(week)) == 7, week


def test_no_token_does_not_post():
    called = []
    posts, note = F.publish(DAY, poster=lambda *a: called.append(a), env={})
    assert not called and len(posts) == 3 and 'FB_PAGE_TOKEN' in note


def test_publish_schedules_future_slots_and_posts_past_ones():
    sent = []

    def fake(page, token, version, params):
        sent.append(params)
        return True, {'id': 'x'}
    now = F.slot_time(DAY, '12:00', F.load_config())
    posts, note = F.publish(DAY, poster=fake, env={'FB_PAGE_ID': '1', 'FB_PAGE_TOKEN': 't'}, now=now)
    assert [p['status'] for p in posts] == ['published', 'scheduled', 'scheduled'], posts
    assert 'scheduled_publish_time' not in sent[0] and sent[1]['published'] == 'false'
    assert all('access_token' not in s for s in sent)


def test_failed_post_reported():
    posts, note = F.publish(DAY, poster=lambda *a: (False, {'error': 'Invalid token', 'code': 190}),
                            env={'FB_PAGE_ID': '1', 'FB_PAGE_TOKEN': 't'})
    assert all(p['status'] == 'failed' for p in posts) and '3 bài lỗi' in note


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
    print(f'OK {len(tests)} tests')
