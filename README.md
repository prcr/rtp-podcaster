# RTP Podcaster

[![Coverage Status](https://coveralls.io/repos/github/prcr/rtp-podcaster/badge.svg?branch=main)](https://coveralls.io/github/prcr/rtp-podcaster?branch=main)

Generates an RSS 2.0 podcast feed for RTP Play shows.
It scrapes the episodes list, retrieves the mp3 for new episodes,
and updates a `p<program_id>_feed.xml` file.

## Requirements

This repository uses [`uv`](https://github.com/astral-sh/uv) as the package manager and dependency resolver. You can install `uv` by following [their official instructions](https://docs.astral.sh/uv/getting-started/installation/).

## Setup & Development

To setup the virtual environment and install all dependencies (including dev tools like `pytest` and `ruff`):

```bash
uv sync
```

To install the pre-commit git hooks to auto-format your code automatically:

```bash
uv run pre-commit install
```

To run tests and lint checks manually:

```bash
uv run pytest
uv run ruff check .
```

## Usage

To execute the script with default settings:

```bash
uv run rtp-podcaster
```

### Options

You can override the default behavior using command-line arguments:

- `--output`: Define the filename for the generated feed (default: `p<program_id>_feed.xml`). All feeds are saved within the `public/rtp-podcaster/` directory.
- `--show-url`: Full URL of the RTP Play show page (default: `https://www.rtp.pt/play/p254/alta-tensao`). The program ID is extracted from this URL.
- `--max-episodes`: Set the maximum number of episodes to index in the feed (default: `128`).
- `--force-refresh`: Disregard the historical feed metadata and rebuild the entire feed from scratch.

Example:
```bash
uv run rtp-podcaster --output custom_feed.xml --max-episodes 5
```
