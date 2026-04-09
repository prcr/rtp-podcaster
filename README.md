# RTP Podcaster

[![Coverage Status](https://coveralls.io/repos/github/prcr/rtp-podcaster/badge.svg?branch=main)](https://coveralls.io/github/prcr/rtp-podcaster?branch=main)

Generates an RSS 2.0 podcast feed for the "Alta Tensão" radio show from RTP Play (program ID 254 by default).
It scrapes the episodes list, retrieves the mp3 for new episodes,
and updates a local `public/p254_feed.xml` file by default (naming tracks program ID).

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
uv run rtp_podcaster
```

### Options

You can override the default behavior using command-line arguments:

- `--output`: Define the path for the generated feed file (default computes to `public/p<program_id>_feed.xml`).
- `--program-id`: Set the target RTP Play program ID to catalog (default: `254`).
- `--max-episodes`: Set the maximum number of episodes to index in the feed (default: `20`).

Example:
```bash
uv run rtp_podcaster --output feed.xml --max-episodes 5
```
