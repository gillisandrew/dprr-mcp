# Architecture Diagrams

## Overview

```mermaid
flowchart TD
    A["<b>Claude Code Skill</b> (/dprr)<br>analyse → generate → validate → execute → synthesise"]
    B["<b>MCP Server</b> (dprr-server)<br>get_schema · validate_sparql · execute_sparql"]
    C["<b>Local Oxigraph Store</b><br>RDF triples from DPRR dataset"]

    A -- "MCP protocol (streamable-http)" --> B
    B --> C
```

## Server Startup and Data Initialisation

On first startup the server auto-downloads the DPRR RDF dataset and initialises a local Oxigraph store. On subsequent startups the existing store is reopened read-only.

```mermaid
flowchart TD
    start([dprr-server starts]) --> resolve["Resolve data directory<br><code>DPRR_DATA_DIR</code> → <code>$XDG_DATA_HOME/dprr-mcp</code><br>→ <code>~/.local/share/dprr-mcp</code>"]
    resolve --> check{store/ exists<br>and non-empty?}

    check -- Yes --> readonly["Open store read-only<br><code>Store.read_only()</code>"]
    check -- No --> ttl{dprr.ttl exists<br>in data dir?}

    ttl -- Yes --> load
    ttl -- No --> fetch["Download tarball<br><code>DPRR_DATA_URL</code> or<br>latest GitHub release"]
    fetch --> extract["Extract dprr.ttl<br>to data directory"]
    extract --> load["Create mutable store<br><code>Store.bulk_load(dprr.ttl)</code>"]
    load --> close["Close write handle"]
    close --> readonly

    readonly --> context["Load YAML context files<br>prefixes · schemas · examples · tips"]
    context --> schema_dict["Build schema_dict<br>class → predicate → range mappings"]
    schema_dict --> ready([Server ready<br>listening on /mcp])
```

## Tool Execution

### get_schema

Returns the DPRR ontology overview. No query execution or store access.

```mermaid
flowchart LR
    call(["get_schema()"]) --> prefixes["Format PREFIX<br>declarations"]
    prefixes --> classes["Render class<br>summary"]
    classes --> tips["Collect cross-<br>cutting tips"]
    tips --> result["Return prefixes<br>+ classes + tips"]
```

### validate_sparql

Checks a query without executing it. Two-tier validation plus contextual guidance.

```mermaid
flowchart TD
    call(["validate_sparql(sparql)"]) --> tier1

    subgraph tier1 ["Tier 1 — Parse and fix prefixes"]
        parse["Parse query<br><code>rdflib.prepareQuery()</code>"]
        parse -- parse error --> detect{"Missing<br>namespace<br>prefix?"}
        detect -- Yes --> inject["Auto-inject PREFIX<br>declarations from<br>prefixes.yaml"]
        inject --> reparse["Re-parse"]
        detect -- No --> fail1["Return parse error"]
        parse -- ok --> sem
        reparse -- ok --> sem
        reparse -- error --> fail1
    end

    subgraph tier2 ["Tier 2 — Semantic validation"]
        sem["Extract BGP triples<br>from SPARQL algebra"]
        sem --> types["Map ?vars to classes<br>via rdf:type triples"]
        types --> preds["Check each predicate<br>against schema_dict"]
        preds -- unknown predicate --> suggest["Suggest closest match<br>(fuzzy matching)"]
        preds -- all valid --> valid
    end

    subgraph ctx ["Context injection"]
        valid["VALID"] --> extract["Extract referenced<br>classes from query"]
        suggest --> extract
        fail1 --> extract
        extract --> relevant["Attach relevant<br>tips + examples"]
    end

    relevant --> result(["Return VALID / INVALID<br>+ relevant tips and examples"])
```

### execute_sparql

Validates then executes the query against the Oxigraph store.

```mermaid
flowchart TD
    call(["execute_sparql(sparql, timeout)"]) --> v["Tier 1 + 2 validation<br>(same as validate_sparql)"]

    v -- errors --> err(["Return errors<br>+ relevant context"])

    v -- valid --> tier3

    subgraph tier3 ["Tier 3 — Execute query"]
        exec["<code>store.query(sparql)</code><br>against read-only Oxigraph"]
        exec --> rows["Extract variable bindings<br>into row dicts"]
    end

    tier3 --> timeout{"Completed within<br>timeout?"}
    timeout -- Yes --> format["Format results<br>as toons table"]
    timeout -- No --> terr(["Return timeout error"])
    format --> result(["Return results"])
```
