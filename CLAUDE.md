# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies (including dev tools)
uv sync

# Run all unit tests (excluding live/network tests)
uv run pytest -m "not live"

# Run a single test file
uv run pytest tests/test_extractor.py

# Run a single test by name
uv run pytest tests/test_extractor.py::test_parse_rtp_date

# Run live integration tests (requires internet access to rtp.pt)
uv run pytest -m "live"

# Lint and format checks
uv run ruff check .
uv run ruff format --check .
uv run mypy .

# Run the podcaster
uv run rtp-podcaster
uv run rtp-podcaster --show-url https://www.rtp.pt/play/p254/alta-tensao --max-episodes 5
uv run rtp-podcaster --force-refresh --output p254_feed.xml
```

## Architecture

The tool scrapes RTP Play show pages, extracts episode MP3 URLs, and produces an RSS 2.0 podcast XML feed. The flow is:

1. **`extractor.py`** — `RTPPlayExtractor` fetches the show's episode listing from `rtp.pt/play/bg_l_ep/?listProgram=<id>`, then visits each episode page to find its MP3 URL (via JS regex on `f = "..."` or fallback JSON key search in `<script>` tags) and description (by CSS class: `vod-description`, `sinopse-text`, `podcast-description`). Show metadata (name, image) comes from `og:title` / `og:image` meta tags on the show page.

2. **`generator.py`** — `RSSGenerator` reads the existing feed file with `feedparser` to collect known GUIDs, prepends new episodes, truncates to `max_episodes`, and writes RSS 2.0 XML via `feedgen` (with iTunes podcast extensions). Episodes without an MP3 URL are silently skipped.

3. **`__main__.py`** — Parses CLI args, orchestrates the extractor and generator, and processes new episode metadata in parallel (4-worker `ThreadPoolExecutor`). All output feeds are written to `public/rtp-podcaster/` and the output filename defaults to `p<program_id>_feed.xml`.

### Key design details

- **Incremental updates**: on each run, only episodes whose GUID (= episode URL) is not already in the existing feed are fetched and processed. `--force-refresh` bypasses this and rebuilds from scratch.
- **GUID identity**: episode URLs are used as GUIDs; deduplication is URL-based.
- **Live vs. unit tests**: tests requiring network access are marked `@pytest.mark.live` and excluded from CI's standard unit test run (`-m "not live"`). The live suite runs separately and targets the real RTP Play website.
- **Output location**: always `public/rtp-podcaster/<filename>`. The `--output` flag accepts a filename only (no path); subdirectories are ignored via `os.path.basename`.
- **CI publishes to GitHub Pages**: the `publish.yml` workflow runs daily at 06:45 PT, generates the feed, and deploys `public/` to GitHub Pages.
