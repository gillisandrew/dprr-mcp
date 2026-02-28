"""Extract all RDF data from the DPRR SPARQL endpoint as Turtle.

Usage:
    uv run python extract_from_endpoint.py [output.ttl]

The endpoint at https://romanrepublic.ac.uk/rdf/endpoint is protected by
Anubis (proof-of-work bot shield).  If direct requests fail, the script
will prompt you to supply a session cookie obtained from a browser.

Steps to get the cookies:
  1. Open https://romanrepublic.ac.uk/rdf/endpoint in your browser.
  2. Complete the Anubis challenge (happens automatically).
  3. Open DevTools → Application → Cookies and copy the values of the
     "techaro.lol-anubis-auth" and "techaro.lol-anubis-cookie-verification"
     cookies.
  4. Re-run this script with:
         ANUBIS_AUTH=<auth> ANUBIS_VERIFY=<verify> uv run python extract_from_endpoint.py
"""

import json
import os
import sys
from pathlib import Path

import httpx
from rdflib import Graph, Namespace

ENDPOINT = "https://romanrepublic.ac.uk/rdf/endpoint"
DEFAULT_OUTPUT = Path("data/dprr_export.ttl")
PAGE_SIZE = 10_000

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def _client() -> httpx.Client:
    cookies = {}
    auth = os.environ.get("ANUBIS_AUTH", "")
    verify = os.environ.get("ANUBIS_VERIFY", "")
    if auth:
        cookies["techaro.lol-anubis-auth"] = auth
    if verify:
        cookies["techaro.lol-anubis-cookie-verification"] = verify
    return httpx.Client(
        headers={"User-Agent": USER_AGENT},
        cookies=cookies,
        timeout=120,
        follow_redirects=True,
    )


def _sparql_query(client: httpx.Client, query: str, accept: str) -> str:
    """Send a SPARQL query and return the response text."""
    resp = client.get(ENDPOINT, params={"query": query}, headers={"Accept": accept})
    if "anubis" in resp.text.lower() and resp.status_code == 200:
        raise RuntimeError(
            "Blocked by Anubis bot protection.\n"
            "Set ANUBIS_AUTH and ANUBIS_VERIFY env vars — see script docstring."
        )
    resp.raise_for_status()
    return resp.text


def count_triples(client: httpx.Client) -> int:
    """Get the total number of triples in the store."""
    query = "SELECT (COUNT(*) AS ?cnt) WHERE { ?s ?p ?o }"
    text = _sparql_query(client, query, "application/sparql-results+json")
    data = json.loads(text)
    return int(data["results"]["bindings"][0]["cnt"]["value"])


def extract_page(client: httpx.Client, offset: int, limit: int) -> str:
    """CONSTRUCT a page of triples and return as Turtle."""
    query = (
        f"CONSTRUCT {{ ?s ?p ?o }} WHERE {{ ?s ?p ?o }} "
        f"LIMIT {limit} OFFSET {offset}"
    )
    return _sparql_query(client, query, "text/turtle")


def extract_all(output: Path) -> None:
    client = _client()

    print(f"Querying {ENDPOINT} …")
    total = count_triples(client)
    print(f"  {total:,} triples reported by endpoint.")

    combined = Graph()
    # Bind the documented prefixes so rdflib doesn't invent ns1/ns2/etc.
    combined.bind("", Namespace("http://romanrepublic.ac.uk/rdf/ontology#"))
    combined.bind("vocab", Namespace("http://romanrepublic.ac.uk/rdf/ontology#"))
    combined.bind("db", Namespace("http://romanrepublic.ac.uk/rdf/entity/"))
    combined.bind("map", Namespace("http://romanrepublic.ac.uk/rdf/entity/#"))
    offset = 0
    while offset < total:
        print(f"  Fetching triples {offset:,}–{min(offset + PAGE_SIZE, total):,} …")
        ttl = extract_page(client, offset, PAGE_SIZE)
        page_g = Graph()
        page_g.parse(data=ttl, format="turtle")
        for triple in page_g:
            combined.add(triple)
        fetched = len(page_g)
        print(f"    got {fetched:,} triples (total so far: {len(combined):,})")
        if fetched == 0:
            break
        offset += PAGE_SIZE

    print(f"\nSerializing {len(combined):,} triples to {output} …")
    output.parent.mkdir(parents=True, exist_ok=True)
    combined.serialize(destination=str(output), format="turtle")
    print("Done.")


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    extract_all(out)
