"""Rebind prefixes in dprr_export.ttl to match the documented DPRR namespaces.

Usage:
    uv run python rebind_prefixes.py [input.ttl] [output.ttl]

Defaults: data/dprr_export.ttl → data/dprr_export.ttl (in-place)
"""

import sys
from pathlib import Path

from rdflib import Graph, Namespace

PREFIXES = {
    "": Namespace("http://romanrepublic.ac.uk/rdf/ontology#"),
    "vocab": Namespace("http://romanrepublic.ac.uk/rdf/ontology#"),
    "db": Namespace("http://romanrepublic.ac.uk/rdf/entity/"),
    "map": Namespace("http://romanrepublic.ac.uk/rdf/entity/#"),
}

DEFAULT = Path("data/dprr_export.ttl")


def rebind(src: Path, dst: Path) -> None:
    g = Graph()
    print(f"Parsing {src} …")
    g.parse(src, format="turtle")
    print(f"  {len(g):,} triples loaded.")

    for prefix, ns in PREFIXES.items():
        g.bind(prefix, ns, override=True)

    print(f"Writing {dst} …")
    g.serialize(destination=str(dst), format="turtle")
    print("Done.")


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src
    rebind(src, dst)
