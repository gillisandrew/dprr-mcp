# Release, Auto-Init, and XDG Data Directory Design

## Overview

Three related features that form a distribution pipeline: release the data via GitHub, auto-fetch it on first startup, and store it in the XDG-compliant location.

## 1. XDG Data Directory & Configuration

Replace the hardcoded `~/.dprr-tool/` path and `DPRR_STORE_PATH` / `DPRR_RDF_FILE` envvars with XDG-compliant defaults.

**Data layout:**

```
$XDG_DATA_HOME/dprr-tool/       # defaults to ~/.local/share/dprr-tool/
├── store/                      # Oxigraph persistent store (read-only after init)
└── dprr.ttl                    # Extracted RDF data file
```

**Environment variables:**

| Variable | Default | Purpose |
|----------|---------|---------|
| `XDG_DATA_HOME` | `~/.local/share` | Standard XDG base |
| `DPRR_DATA_DIR` | `$XDG_DATA_HOME/dprr-tool` | Override the entire data directory |
| `DPRR_DATA_URL` | GitHub latest release URL | Override where to fetch the data tarball |
| `DPRR_QUERY_TIMEOUT` | `600` | Unchanged |

**Precedence for data directory:** `DPRR_DATA_DIR` > `$XDG_DATA_HOME/dprr-tool` > `~/.local/share/dprr-tool`

**Removed:** `DPRR_STORE_PATH` and `DPRR_RDF_FILE` -- both derived from the data directory (`$data_dir/store` and `$data_dir/dprr.ttl`).

A new `get_data_dir()` function in `store.py` computes the path using the precedence above. `ensure_initialized()` uses this internally instead of taking explicit paths.

## 2. Auto-Init & Data Fetching

On first startup, if the store is empty, the server downloads the data tarball, extracts `dprr.ttl`, and initializes the Oxigraph store. Subsequent starts skip this.

**Startup flow:**

```
1. Compute data_dir via get_data_dir()
2. Check if store is initialized (store_dir has data)
   +-- YES -> open read-only store, continue
   +-- NO  ->
       a. Check if dprr.ttl already exists in data_dir
          +-- YES -> skip download
          +-- NO  -> fetch tarball from DPRR_DATA_URL, extract dprr.ttl to data_dir
       b. Bulk-load dprr.ttl into store
       c. Close writable store, reopen read-only
3. Load YAML context, yield AppContext
```

**Fetching logic (new module `dprr_tool/fetch.py`):**

- Default URL: `https://github.com/gillisandrew/dprr-tool/releases/latest/download/dprr-data.tar.gz`
- Uses `urllib.request` (stdlib -- no new dependency)
- Downloads to a temp file, extracts `dprr.ttl` into `data_dir`
- Logs progress to stderr
- Raises `RuntimeError` with a clear message on failure

Users who have a local `.ttl` file can place it at `$data_dir/dprr.ttl` manually and the server will use it without downloading.

## 3. GitHub Release Workflow

A new GitHub Actions workflow triggers on version tag pushes, builds the Python package, and creates a GitHub release.

**Workflow: `.github/workflows/release.yml`**

**Trigger:** Push of tags matching `v*` (e.g., `v0.2.0`)

**Steps:**

1. Checkout repo (with `data/dprr.ttl`)
2. Install `uv`
3. Run tests (`uv run pytest -q`) -- gate the release on passing tests
4. Build sdist + wheel via `uv build`
5. Create data tarball: `tar -czf dprr-data.tar.gz -C data dprr.ttl`
6. Create GitHub release via `gh release create $TAG` with:
   - `dist/*.tar.gz` (sdist)
   - `dist/*.whl` (wheel)
   - `dprr-data.tar.gz`
   - Auto-generated release notes

**Tarball structure:** Single file `dprr.ttl` at the root (no nested directory).

**Version management:** Version in `pyproject.toml` is the source of truth. Tag name must match (e.g., tag `v0.2.0` corresponds to version `0.2.0`).

## 4. File Changes

**New files:**

- `dprr_tool/fetch.py` -- tarball download and extraction logic
- `.github/workflows/release.yml` -- tag-triggered release workflow

**Modified files:**

- `dprr_tool/store.py` -- replace hardcoded `~/.dprr-tool/` with `get_data_dir()` using XDG precedence; remove `rdf_file` parameter from `ensure_initialized()`; derive store path and rdf path from data dir
- `dprr_tool/mcp_server.py` -- update lifespan to call fetch when store is uninitialized; remove `DPRR_RDF_FILE` / `DPRR_STORE_PATH` references
- `pyproject.toml` -- no new runtime dependencies (urllib.request + tarfile are stdlib)
- `tests/test_store.py` -- update for new `get_data_dir()` signature and removed params
- `tests/test_mcp_server.py` -- update for removed envvar references

**New tests:**

- `tests/test_fetch.py` -- test tarball extraction, error handling, URL override via `DPRR_DATA_URL`
- `tests/test_store.py` additions -- test `get_data_dir()` precedence

**Removed:**

- `DPRR_STORE_PATH` envvar
- `DPRR_RDF_FILE` envvar

**Unchanged:**

- `dprr_tool/context/` (YAML files)
- `dprr_tool/validate.py`
- `.github/workflows/ci.yml`
- `scripts/`
