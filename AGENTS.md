# AGENTS.md — Nguyễn Hà content factory

Repository files are the source of truth. Read `docs/CONTENT-FACTORY.md` before changing the writer.

## Non-negotiable rules

- Never bypass the score threshold, critical-error gate, duplicate URL, duplicate intent or similarity check.
- Never edit `data/content-index.jsonl` manually; regenerate it with `python3 scripts/content_factory.py reindex`.
- Article source belongs in one JSON shard under `content/articles/`. Existing `content/posts.json` remains legacy source.
- A production run publishes up to 50 pairs: 100 articles.
- Never add an external AI API, token or network content dependency to the writer.
- Business facts come from `config/business-facts.json`. Do not invent price, availability, legal advice or real-time information.
- Failed QA remains rejected in the append-only queue log and must not enter article source, sitemap or search index.
- Do not force-push, reset factory state or reuse a published URL/intent.

## Topic Factory V2 (read `docs/TOPIC-FACTORY-V2.md` before touching topics)

- `data/topic-matrix.jsonl` is the only source of topics. Writers take only rows in lifecycle `APPROVED`, through `python3 scripts/factory_v2.py queue --writer <name>`; they never create rows, change lifecycle, or loosen `editorial_approval`.
- Writers draft into `content/drafts/<TM-id>.json` from the brief; only `python3 scripts/factory_v2.py publish --by <name>` moves a draft into `content/articles/<TM-id>.json` (`factoryVersion: 2`), after scoped QA, and records it in the append-only `data/factory-queue.jsonl`. Never copy a draft into `content/articles/` by hand. `content/drafts/` is not an article source.
- `data/topic-matrix-published.jsonl` and `data/cache/` are derived; regenerate with `python3 scripts/topic_matrix.py sync`, never edit by hand.
- Never bypass `discover` → `validate` → `approve`. A similarity score is a signal for the editor, never an automatic approval; every approved row must state in `information_gain` what the reader gets that existing articles do not.
- Template permutations (same question, different district/audience/context/year) are rejected automatically and must not be re-seeded under a new wording. Search demand is only `data/keyword-metrics.jsonl` (checked date + source); do not invent volumes.
- Legacy V1 articles stay noindexed "soft" duplicates: no deletion, URL change or redirect without the owner's approval.

## Required checks

```sh
python3 scripts/content_factory.py run --dry-run
python3 tests/test_content_factory.py
python3 tests/test_topic_matrix.py
python3 tests/test_factory_v2.py
python3 tests/test_facebook_posts.py
python3 scripts/topic_matrix.py validate
python3 scripts/build.py
python3 scripts/validate_factory_site.py
```

Facebook fanpage: `scripts/facebook_posts.py` posts 3 summaries a day (one per pool in `config/facebook-posts.json`) only from URLs in the sitemap, with contact details from `config/business-facts.json`. It posts through the Graph API only when the repo secrets `FB_PAGE_ID` and `FB_PAGE_TOKEN` exist; never commit or print the token. Pause with `enabled: false` in `config/facebook-posts.json`.

Stop production safely by adding a root file named `STOP_FACTORY`, or set `enabled` to `false` in `config/content-factory.json`. Resume by reversing that change. Scheduled runs are serialized through workflow concurrency.
