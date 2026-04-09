# RTP Podcaster

Generates an RSS 2.0 podcast feed for the "Alta Tensão" radio show from RTP Play.
It scrapes the episodes list, retrieves the mp3 for new episodes,
and updates a local `feed.xml` file.

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

To execute the scripts inside the virtual environment:

```bash
uv run rtp_podcaster
```
