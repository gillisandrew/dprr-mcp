"""Convert DPRR N3 export to TTL with the namespace the tool expects.

The N3 export uses:
    @prefix : <http://romanrepublic.ac.uk/rdf/ontology#> .

The dprr-tool expects:
    @prefix vocab: <http://romanrepublic.ac.uk/rdf/entity/vocab/> .

This script parses the N3 graph and re-serializes it as Turtle after
rebinding the ontology namespace.
"""

import sys
from pathlib import Path

from rdflib import Graph, Namespace

SRC_NS = Namespace("http://romanrepublic.ac.uk/rdf/ontology#")
DST_NS = Namespace("http://romanrepublic.ac.uk/rdf/entity/vocab/")


def convert(src: Path, dst: Path) -> None:
    g = Graph()
    print(f"Parsing {src} …")
    g.parse(src, format="n3")
    print(f"  {len(g)} triples loaded.")

    # Rewrite triples whose predicates / objects use the old namespace
    new_g = Graph()
    for pfx, ns in g.namespaces():
        if str(ns) == str(SRC_NS):
            new_g.bind("vocab", DST_NS)
        else:
            new_g.bind(pfx, ns)

    for s, p, o in g:
        s2 = _rewrite(s)
        p2 = _rewrite(p)
        o2 = _rewrite(o)
        new_g.add((s2, p2, o2))

    print(f"Writing {dst} …")
    new_g.serialize(destination=str(dst), format="turtle")
    print("Done.")


def _rewrite(term):
    """If the term is a URI in the old ontology namespace, rewrite it."""
    from rdflib import URIRef

    if isinstance(term, URIRef) and str(term).startswith(str(SRC_NS)):
        local = str(term)[len(str(SRC_NS)):]
        return URIRef(str(DST_NS) + local)
    return term


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.n3> <output.ttl>")
        sys.exit(1)
    convert(Path(sys.argv[1]), Path(sys.argv[2]))
