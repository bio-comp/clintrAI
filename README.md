# clintrAI

Clinical-trial ingestion, normalization, document processing, and retrieval experiments.

## Quality Gates

The default test command runs deterministic unit tests and excludes live API integration tests:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run --no-project \
  --with pytest --with pytest-asyncio \
  --with pydantic --with polars --with httpx --with curl-cffi --with tenacity \
  --with loguru --with duckdb \
  python -m pytest -q -p no:cacheprovider
```

Run the correctness-focused Ruff baseline:

```bash
uv run --no-project --with ruff \
  ruff check clintrai tests scripts airflow --select E9,F63,F7,F82,B
```

Build the package:

```bash
uv build
```

Live ClinicalTrials.gov tests are opt-in:

```bash
uv run --no-project \
  --with pytest --with pytest-asyncio \
  --with pydantic --with httpx --with curl-cffi --with tenacity \
  python -m pytest -m integration tests/integration
```

GitHub Actions runs the same unit, static-analysis, and build gates on pull requests and pushes to `main`.
