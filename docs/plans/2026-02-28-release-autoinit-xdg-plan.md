# Release, Auto-Init, and XDG Data Directory Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace hardcoded `~/.dprr-tool/` paths with XDG-compliant data directories, auto-fetch the DPRR data tarball on first startup, and create a GitHub release workflow.

**Architecture:** A new `get_data_dir()` function computes the data directory using `DPRR_DATA_DIR > XDG_DATA_HOME/dprr-tool > ~/.local/share/dprr-tool` precedence. A new `fetch.py` module downloads and extracts the data tarball on first startup. The release workflow triggers on tag push, building the wheel/sdist and data tarball.

**Tech Stack:** Python 3.13, stdlib urllib.request + tarfile (no new deps), GitHub Actions

---

### Task 1: Add `get_data_dir()` to store.py

**Files:**
- Modify: `dprr_tool/store.py`
- Test: `tests/test_store.py`

**Step 1: Write failing tests for `get_data_dir()`**

Add to `tests/test_store.py`:

```python
from dprr_tool.store import get_data_dir


def test_get_data_dir_default():
    """Falls back to ~/.local/share/dprr-tool when no envvars set."""
    with patch.dict(os.environ, {}, clear=True):
        # Remove both DPRR_DATA_DIR and XDG_DATA_HOME
        os.environ.pop("DPRR_DATA_DIR", None)
        os.environ.pop("XDG_DATA_HOME", None)
        result = get_data_dir()
        assert result == Path.home() / ".local" / "share" / "dprr-tool"


def test_get_data_dir_xdg_data_home():
    """Respects XDG_DATA_HOME when set."""
    with patch.dict(os.environ, {"XDG_DATA_HOME": "/tmp/xdg"}, clear=True):
        result = get_data_dir()
        assert result == Path("/tmp/xdg/dprr-tool")


def test_get_data_dir_dprr_data_dir_overrides_xdg():
    """DPRR_DATA_DIR takes precedence over XDG_DATA_HOME."""
    with patch.dict(os.environ, {"DPRR_DATA_DIR": "/tmp/custom", "XDG_DATA_HOME": "/tmp/xdg"}, clear=True):
        result = get_data_dir()
        assert result == Path("/tmp/custom")
```

Add these imports to the top of `tests/test_store.py`:
```python
import os
from unittest.mock import patch
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_store.py::test_get_data_dir_default tests/test_store.py::test_get_data_dir_xdg_data_home tests/test_store.py::test_get_data_dir_dprr_data_dir_overrides_xdg -v`
Expected: FAIL with `ImportError: cannot import name 'get_data_dir'`

**Step 3: Implement `get_data_dir()` in store.py**

Add to `dprr_tool/store.py` (after the imports, before `get_or_create_store`):

```python
import os


def get_data_dir() -> Path:
    """Compute the DPRR data directory.

    Precedence: DPRR_DATA_DIR > $XDG_DATA_HOME/dprr-tool > ~/.local/share/dprr-tool
    """
    explicit = os.environ.get("DPRR_DATA_DIR")
    if explicit:
        return Path(explicit)
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / "dprr-tool"
```

Note: move the existing `import os` from inside `ensure_initialized` to the module-level imports.

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_store.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add dprr_tool/store.py tests/test_store.py
git commit -m "feat: add get_data_dir() with XDG_DATA_HOME support"
```

---

### Task 2: Update `ensure_initialized()` to use `get_data_dir()`

**Files:**
- Modify: `dprr_tool/store.py`
- Modify: `dprr_tool/mcp_server.py`
- Modify: `tests/test_store.py`
- Modify: `tests/test_mcp_server.py`

**Step 1: Write failing test for new `ensure_initialized()` signature**

The current `ensure_initialized(store_path, rdf_file=None)` takes explicit paths. The new version `ensure_initialized()` takes no arguments — it derives `store_path` and `rdf_path` from `get_data_dir()`.

Add to `tests/test_store.py`:

```python
from dprr_tool.store import ensure_initialized


def test_ensure_initialized_uses_data_dir(tmp_path):
    """ensure_initialized uses get_data_dir() to find store and rdf file."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    rdf_file = data_dir / "dprr.ttl"
    rdf_file.write_text(SAMPLE_TURTLE)

    with patch.dict(os.environ, {"DPRR_DATA_DIR": str(data_dir)}, clear=True):
        store = ensure_initialized()
        results = execute_query(store, "SELECT (COUNT(*) AS ?c) WHERE { ?s ?p ?o }")
        assert int(results[0]["c"]) > 0


def test_ensure_initialized_no_rdf_file_raises(tmp_path):
    """ensure_initialized raises RuntimeError when no dprr.ttl exists."""
    data_dir = tmp_path / "empty"
    data_dir.mkdir()

    with patch.dict(os.environ, {"DPRR_DATA_DIR": str(data_dir)}, clear=True):
        with pytest.raises(RuntimeError, match="dprr.ttl"):
            ensure_initialized()
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_store.py::test_ensure_initialized_uses_data_dir tests/test_store.py::test_ensure_initialized_no_rdf_file_raises -v`
Expected: FAIL (signature mismatch or wrong behavior)

**Step 3: Rewrite `ensure_initialized()` in store.py**

Replace the existing `ensure_initialized` function:

```python
def ensure_initialized() -> Store:
    """Open the store, auto-loading dprr.ttl from data_dir if the store is empty.

    Returns a read-only store. Derives paths from get_data_dir().
    Raises RuntimeError if the store is empty and dprr.ttl is not found.
    """
    data_dir = get_data_dir()
    store_path = data_dir / "store"
    rdf_path = data_dir / "dprr.ttl"

    if is_initialized(store_path):
        return get_read_only_store(store_path)

    if not rdf_path.exists():
        raise RuntimeError(
            f"Store is empty and no data file found at {rdf_path}. "
            "Run the server where data can be fetched, or place dprr.ttl manually."
        )

    store = get_or_create_store(store_path)
    load_rdf(store, rdf_path)
    del store
    return get_read_only_store(store_path)
```

**Step 4: Update mcp_server.py lifespan**

In `dprr_tool/mcp_server.py`:
- Remove `DEFAULT_STORE_PATH` constant (line 34)
- Remove `DPRR_STORE_PATH` environ lookup from `lifespan` (line 50)
- Change `store = ensure_initialized(store_path)` → `store = ensure_initialized()`
- Remove the `store_path` local variable entirely

The lifespan becomes:

```python
@asynccontextmanager
async def lifespan(server: FastMCP):
    """Initialize the Oxigraph store and schema on startup."""
    store = ensure_initialized()
    prefix_map = load_prefixes()
    schemas = load_schemas()
    examples = load_examples()
    tips = load_tips()
    schema_dict = build_schema_dict(schemas, prefix_map)
    yield AppContext(
        store=store,
        prefix_map=prefix_map,
        schema_dict=schema_dict,
        schemas=schemas,
        examples=examples,
        tips=tips,
    )
```

Also remove the unused `Path` import from `mcp_server.py` if it's no longer needed (check if anything else uses it — it's not used anywhere else after removing `DEFAULT_STORE_PATH`).

**Step 5: Run all tests to verify they pass**

Run: `uv run pytest -v`
Expected: All PASS (existing tests in test_mcp_server.py don't test lifespan directly, so they should still pass)

**Step 6: Commit**

```bash
git add dprr_tool/store.py dprr_tool/mcp_server.py tests/test_store.py
git commit -m "refactor: ensure_initialized derives paths from get_data_dir()"
```

---

### Task 3: Create `fetch.py` — tarball download and extraction

**Files:**
- Create: `dprr_tool/fetch.py`
- Create: `tests/test_fetch.py`

**Step 1: Write failing tests for fetch module**

Create `tests/test_fetch.py`:

```python
import os
import tarfile
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from dprr_tool.fetch import DEFAULT_DATA_URL, fetch_data


def _make_tarball(tmp_path: Path, filename: str = "dprr.ttl", content: str = "test data") -> Path:
    """Create a gzipped tarball containing a single file."""
    file_path = tmp_path / filename
    file_path.write_text(content)
    tarball_path = tmp_path / "data.tar.gz"
    with tarfile.open(tarball_path, "w:gz") as tar:
        tar.add(file_path, arcname=filename)
    return tarball_path


def test_fetch_data_extracts_ttl(tmp_path):
    """fetch_data downloads and extracts dprr.ttl to data_dir."""
    tarball_path = _make_tarball(tmp_path, content="<s> <p> <o> .")
    data_dir = tmp_path / "output"
    data_dir.mkdir()

    with patch("dprr_tool.fetch.urllib.request.urlretrieve") as mock_retrieve:
        mock_retrieve.return_value = (str(tarball_path), {})
        fetch_data(data_dir, url="https://example.com/data.tar.gz")

    assert (data_dir / "dprr.ttl").exists()
    assert (data_dir / "dprr.ttl").read_text() == "<s> <p> <o> ."


def test_fetch_data_missing_ttl_in_tarball(tmp_path):
    """fetch_data raises RuntimeError if tarball lacks dprr.ttl."""
    tarball_path = _make_tarball(tmp_path, filename="wrong.txt")
    data_dir = tmp_path / "output"
    data_dir.mkdir()

    with patch("dprr_tool.fetch.urllib.request.urlretrieve") as mock_retrieve:
        mock_retrieve.return_value = (str(tarball_path), {})
        with pytest.raises(RuntimeError, match="dprr.ttl"):
            fetch_data(data_dir, url="https://example.com/data.tar.gz")


def test_fetch_data_url_from_envvar(tmp_path):
    """DPRR_DATA_URL overrides the default URL."""
    tarball_path = _make_tarball(tmp_path, content="env data")
    data_dir = tmp_path / "output"
    data_dir.mkdir()

    with patch.dict(os.environ, {"DPRR_DATA_URL": "https://custom.example.com/data.tar.gz"}):
        with patch("dprr_tool.fetch.urllib.request.urlretrieve") as mock_retrieve:
            mock_retrieve.return_value = (str(tarball_path), {})
            fetch_data(data_dir)
            mock_retrieve.assert_called_once()
            call_url = mock_retrieve.call_args[0][0]
            assert call_url == "https://custom.example.com/data.tar.gz"


def test_fetch_data_default_url():
    """Default URL points to GitHub releases."""
    assert "github.com" in DEFAULT_DATA_URL
    assert "dprr-data.tar.gz" in DEFAULT_DATA_URL


def test_fetch_data_network_error(tmp_path):
    """fetch_data raises RuntimeError on download failure."""
    data_dir = tmp_path / "output"
    data_dir.mkdir()

    with patch("dprr_tool.fetch.urllib.request.urlretrieve", side_effect=OSError("connection refused")):
        with pytest.raises(RuntimeError, match="Failed to download"):
            fetch_data(data_dir, url="https://example.com/data.tar.gz")
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_fetch.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dprr_tool.fetch'`

**Step 3: Implement `fetch.py`**

Create `dprr_tool/fetch.py`:

```python
"""Download and extract the DPRR data tarball."""

import logging
import os
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_DATA_URL = "https://github.com/gillisandrew/dprr-tool/releases/latest/download/dprr-data.tar.gz"


def fetch_data(data_dir: Path, url: str | None = None) -> Path:
    """Download the DPRR data tarball and extract dprr.ttl to data_dir.

    Args:
        data_dir: Directory to extract dprr.ttl into.
        url: Override URL. Falls back to DPRR_DATA_URL envvar, then DEFAULT_DATA_URL.

    Returns:
        Path to the extracted dprr.ttl file.

    Raises:
        RuntimeError: If download fails or tarball doesn't contain dprr.ttl.
    """
    resolved_url = url or os.environ.get("DPRR_DATA_URL", DEFAULT_DATA_URL)
    logger.info("Downloading DPRR data from %s", resolved_url)
    print(f"Downloading DPRR data from {resolved_url} ...", file=sys.stderr)

    try:
        tmp_path, _ = urllib.request.urlretrieve(resolved_url)
    except OSError as e:
        raise RuntimeError(f"Failed to download data from {resolved_url}: {e}") from e

    try:
        with tarfile.open(tmp_path, "r:gz") as tar:
            members = tar.getnames()
            if "dprr.ttl" not in members:
                raise RuntimeError(
                    f"Tarball does not contain dprr.ttl. Found: {members}"
                )
            tar.extract("dprr.ttl", path=str(data_dir))
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    result = data_dir / "dprr.ttl"
    print(f"Extracted dprr.ttl to {result}", file=sys.stderr)
    return result
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_fetch.py -v`
Expected: All PASS

**Step 5: Lint check**

Run: `uv run ruff check dprr_tool/fetch.py tests/test_fetch.py`
Expected: No errors

**Step 6: Commit**

```bash
git add dprr_tool/fetch.py tests/test_fetch.py
git commit -m "feat: add fetch module for auto-downloading DPRR data tarball"
```

---

### Task 4: Wire auto-fetch into `ensure_initialized()`

**Files:**
- Modify: `dprr_tool/store.py`
- Modify: `tests/test_store.py`

**Step 1: Write failing test for auto-fetch behavior**

Add to `tests/test_store.py`:

```python
def test_ensure_initialized_fetches_when_no_ttl(tmp_path):
    """ensure_initialized calls fetch_data when dprr.ttl is missing."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    # No dprr.ttl exists — fetch_data should be called

    def fake_fetch(data_dir, **kwargs):
        (data_dir / "dprr.ttl").write_text(SAMPLE_TURTLE)
        return data_dir / "dprr.ttl"

    with patch.dict(os.environ, {"DPRR_DATA_DIR": str(data_dir)}, clear=True):
        with patch("dprr_tool.store.fetch_data", side_effect=fake_fetch) as mock_fetch:
            store = ensure_initialized()
            mock_fetch.assert_called_once_with(data_dir)
            results = execute_query(store, "SELECT (COUNT(*) AS ?c) WHERE { ?s ?p ?o }")
            assert int(results[0]["c"]) > 0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_store.py::test_ensure_initialized_fetches_when_no_ttl -v`
Expected: FAIL (currently raises RuntimeError instead of calling fetch_data)

**Step 3: Update `ensure_initialized()` to call fetch_data**

In `dprr_tool/store.py`, update `ensure_initialized()`:

```python
def ensure_initialized() -> Store:
    """Open the store, auto-loading dprr.ttl from data_dir if the store is empty.

    If dprr.ttl is not present, attempts to fetch it from the configured URL.
    Returns a read-only store. Derives paths from get_data_dir().
    """
    from dprr_tool.fetch import fetch_data

    data_dir = get_data_dir()
    store_path = data_dir / "store"
    rdf_path = data_dir / "dprr.ttl"

    if is_initialized(store_path):
        return get_read_only_store(store_path)

    if not rdf_path.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        fetch_data(data_dir)

    store = get_or_create_store(store_path)
    load_rdf(store, rdf_path)
    del store
    return get_read_only_store(store_path)
```

Also update the `test_ensure_initialized_no_rdf_file_raises` test from Task 2 — it should now expect fetch_data to be called and fail (rather than the RuntimeError about dprr.ttl). Replace it:

```python
def test_ensure_initialized_fetch_failure_raises(tmp_path):
    """ensure_initialized raises RuntimeError when fetch fails."""
    data_dir = tmp_path / "empty"
    data_dir.mkdir()

    with patch.dict(os.environ, {"DPRR_DATA_DIR": str(data_dir)}, clear=True):
        with patch("dprr_tool.store.fetch_data", side_effect=RuntimeError("download failed")):
            with pytest.raises(RuntimeError, match="download failed"):
                ensure_initialized()
```

**Step 4: Run all tests**

Run: `uv run pytest -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add dprr_tool/store.py tests/test_store.py
git commit -m "feat: auto-fetch DPRR data tarball on first startup"
```

---

### Task 5: Create GitHub release workflow

**Files:**
- Create: `.github/workflows/release.yml`

**Step 1: Create the workflow file**

Create `.github/workflows/release.yml`:

```yaml
name: Release

on:
  push:
    tags: ["v*"]

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: astral-sh/setup-uv@v7

      - name: Run tests
        run: |
          uv sync --group dev
          uv run ruff check .
          uv run pytest -q

      - name: Build package
        run: uv build

      - name: Create data tarball
        run: tar -czf dprr-data.tar.gz -C data dprr.ttl

      - name: Create GitHub release
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          gh release create "${{ github.ref_name }}" \
            dist/*.tar.gz \
            dist/*.whl \
            dprr-data.tar.gz \
            --generate-notes
```

**Step 2: Validate YAML syntax**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))"`
Expected: No errors

**Step 3: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "ci: add tag-triggered release workflow with data tarball"
```

---

### Task 6: Update CLAUDE.md and clean up

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Update environment variable documentation in CLAUDE.md**

Update the Store section to reflect new envvars and behavior:

Replace the Store section with:

```markdown
## Store

- Data directory follows XDG: `DPRR_DATA_DIR` > `$XDG_DATA_HOME/dprr-tool` > `~/.local/share/dprr-tool`.
- On first startup, if no `dprr.ttl` exists in the data directory, the server auto-downloads it from the latest GitHub release. Override the URL with `DPRR_DATA_URL`.
- After first load, the Oxigraph store opens **read-only** (`Store.read_only()`) to avoid file locking. Do not add write operations to the initialized store.
- Tests create ephemeral stores using `SAMPLE_TURTLE` from `tests/test_store.py`. Do not mock the store.
```

**Step 2: Run all tests one final time**

Run: `uv run pytest -v && uv run ruff check .`
Expected: All PASS, no lint errors

**Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md for XDG data dir and auto-fetch"
```
