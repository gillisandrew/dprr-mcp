from pathlib import Path

from pyoxigraph import Store, RdfFormat


def get_or_create_store(path: Path) -> Store:
    """Open or create a persistent Oxigraph store at the given directory."""
    path.mkdir(parents=True, exist_ok=True)
    return Store(str(path))


def load_rdf(store: Store, file_path: Path) -> int:
    """Bulk-load a Turtle RDF file into the store. Returns the number of triples after loading."""
    store.bulk_load(
        path=str(file_path),
        format=RdfFormat.TURTLE,
    )
    return len(store)


def execute_query(store: Store, sparql: str) -> list[dict[str, str]]:
    """Execute a SPARQL SELECT query and return results as a list of dicts."""
    results = store.query(sparql)
    variables = [v.value for v in results.variables]
    rows = []
    for solution in results:
        row = {}
        for var_name in variables:
            value = solution[var_name]
            if value is not None:
                row[var_name] = value.value
            else:
                row[var_name] = None
        rows.append(row)
    return rows


def is_initialized(store_path: Path) -> bool:
    """Check whether a store exists and contains data."""
    if not store_path.exists():
        return False
    try:
        store = Store.read_only(str(store_path))
        return len(store) > 0
    except OSError:
        return False


def ensure_initialized(store_path: Path, rdf_file: str | None = None) -> Store:
    """Open the store, auto-loading RDF data from rdf_file if the store is empty.

    If rdf_file is None, reads from the DPRR_RDF_FILE environment variable.
    Raises RuntimeError if the store is empty and no RDF file is available.
    """
    import os

    store = get_or_create_store(store_path)
    if len(store) > 0:
        return store

    rdf_path = rdf_file or os.environ.get("DPRR_RDF_FILE")
    if not rdf_path:
        raise RuntimeError(
            "Store is empty and no RDF file provided. "
            "Set DPRR_RDF_FILE environment variable or run 'dprr-tool init <rdf-file>'."
        )

    path = Path(rdf_path)
    if not path.exists():
        raise RuntimeError(f"RDF file not found: {path}")

    load_rdf(store, path)
    return store
