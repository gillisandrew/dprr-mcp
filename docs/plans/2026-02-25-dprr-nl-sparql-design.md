# dprr-tool: Natural Language SPARQL for the Roman Republic

## Problem

Academic researchers studying the Roman Republic need to query the DPRR (Digital Prosopography of the Roman Republic) database, which contains ~4,800 individuals from 509-31 BC with their offices, relationships, statuses, and dates. The data is available as RDF with a SPARQL endpoint, but:

1. The hosted SPARQL endpoint is unreliable (frequent downtime, poor performance)
2. Writing SPARQL requires technical expertise most historians don't have
3. The DPRR ontology has quirks (negative years for BC, assertion-based data model, dual namespaces) that trip up even experienced SPARQL users

## Solution

A Python CLI tool that lets researchers ask natural language questions and get back validated SPARQL queries, results, and academic prose summaries with source citations and uncertainty flags.

```
$ dprr-tool ask "Who held the office of consul between 200 and 150 BC?"
```

## Architecture

### Pipeline

```
User question
  -> Structured extraction (Claude: extract classes, entities, intent)
  -> Context assembly (all schemas + all example queries injected into prompt)
  -> SPARQL generation (Claude: generate query from full context)
  -> Validation loop:
      -> Tier 1: Syntax parse (rdflib) + auto-fix missing prefixes
      -> Tier 2: Semantic validation against schema dictionary
      -> Tier 3: Execute against local Oxigraph
      -> On failure: feed errors back to Claude (max 3 retries)
  -> Response synthesis (Claude: academic prose with citations + caveats)
```

### Components

#### 1. Local Oxigraph Store (`dprr_tool/store.py`)

Wraps `pyoxigraph.Store` for an in-process SPARQL store. No server to manage.

- `dprr-tool init` downloads the DPRR bulk RDF export (Turtle) and loads it into a persistent store at `~/.dprr-tool/store/`
- Also loads the OWL ontology for `rdfs:label`/`rdfs:comment` on classes and properties
- ~100K triples, loads in seconds, queries in milliseconds

Functions:
- `get_or_create_store(path) -> Store`
- `load_rdf(store, file_path, format) -> int` (triple count)
- `execute_query(store, sparql) -> list[dict]`
- `is_initialized() -> bool`

#### 2. Hand-Crafted RAG Context (`dprr_tool/context/`)

Since DPRR has no VoID descriptions or published SPARQL examples (unlike the SIB bioinformatics endpoints), we create and maintain:

**`schemas.yaml`** - One entry per DPRR class with all valid predicates and their ranges:

```yaml
classes:
  Person:
    label: "Roman Republican Person"
    comment: "An individual in the DPRR database (509-31 BC)"
    uri: "vocab:Person"
    properties:
      - pred: "rdfs:label"
        range: "xsd:string"
        comment: "Full Roman name"
      - pred: "vocab:hasDprrID"
        range: "xsd:string"
        comment: "DPRR identifier (e.g., 'CORN0174')"
      - pred: "vocab:hasNomen"
        range: "xsd:string"
        comment: "Family/gens name"
      - pred: "vocab:hasCognomen"
        range: "xsd:string"
        comment: "Third name / cognomen"
      - pred: "vocab:isSex"
        range: "vocab:Sex"
        comment: "Gender (links to Sex/Male or Sex/Female entity)"
      - pred: "vocab:hasEraFrom"
        range: "xsd:integer"
        comment: "Estimated birth year (negative = BC)"
      - pred: "vocab:hasEraTo"
        range: "xsd:integer"
        comment: "Estimated death year (negative = BC)"
      - pred: "vocab:hasHighestOffice"
        range: "xsd:string"
        comment: "Highest office attained"
      - pred: "vocab:isPatrician"
        range: "xsd:boolean"
      - pred: "vocab:isNobilis"
        range: "xsd:boolean"
      - pred: "vocab:isNovus"
        range: "xsd:boolean"
      # ... remaining properties

  PostAssertion:
    label: "Office-Holding Assertion"
    comment: "A claim from a secondary source that a person held a specific office during a date range"
    uri: "vocab:PostAssertion"
    properties:
      - pred: "vocab:isAboutPerson"
        range: "vocab:Person"
      - pred: "vocab:hasOffice"
        range: "vocab:Office"
      - pred: "vocab:hasDateStart"
        range: "xsd:integer"
        comment: "Start year of office tenure (negative = BC)"
      - pred: "vocab:hasDateEnd"
        range: "xsd:integer"
      - pred: "vocab:hasSecondarySource"
        range: "vocab:SecondarySource"
      - pred: "vocab:isUncertain"
        range: "xsd:boolean"
      # ...

  # RelationshipAssertion, StatusAssertion, DateInformation,
  # Office, Province, Sex, Praenomen, Tribe, SecondarySource,
  # PrimarySource, Status, Relationship, DateType
```

**`examples.yaml`** - ~20-30 curated SPARQL queries covering common research patterns:

```yaml
examples:
  - question: "Find all consuls between 200 and 150 BC"
    classes: [Person, PostAssertion, Office]
    pattern: "office-by-date-range"
    sparql: |
      PREFIX vocab: <http://romanrepublic.ac.uk/rdf/entity/vocab/>
      PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
      SELECT DISTINCT ?person ?name ?dateStart
      WHERE {
        ?pa a vocab:PostAssertion ;
            vocab:hasOffice <http://romanrepublic.ac.uk/rdf/entity/Office/3> ;
            vocab:isAboutPerson ?person ;
            vocab:hasDateStart ?dateStart .
        FILTER(?dateStart >= -200 && ?dateStart <= -150)
        ?person rdfs:label ?name .
      }
      ORDER BY ?dateStart
      LIMIT 100

  - question: "Find all women in the DPRR"
    classes: [Person, Sex]
    pattern: "filter-by-property"
    sparql: |
      PREFIX vocab: <http://romanrepublic.ac.uk/rdf/entity/vocab/>
      PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
      SELECT ?person ?name ?id
      WHERE {
        ?person a vocab:Person ;
            vocab:isSex <http://romanrepublic.ac.uk/rdf/entity/Sex/Female> ;
            vocab:hasID ?id ;
            rdfs:label ?name .
      }
      ORDER BY ?name

  # ... ~25 more covering:
  # - family relationships for a person
  # - patricians who held office X
  # - persons with status Y (eques, nobilis)
  # - office holders in a province
  # - date information (birth, death, exile)
  # - uncertain assertions
  # - tribe membership
  # - primary source citations
  # - hierarchical office queries (with parent)
```

**`prefixes.yaml`** - Known prefix map for auto-repair:

```yaml
prefixes:
  vocab: "http://romanrepublic.ac.uk/rdf/entity/vocab/"
  entity: "http://romanrepublic.ac.uk/rdf/entity/"
  rdfs: "http://www.w3.org/2000/01/rdf-schema#"
  rdf: "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
  xsd: "http://www.w3.org/2001/XMLSchema#"
  owl: "http://www.w3.org/2002/07/owl#"
```

**Context strategy: Full injection (no embeddings, no retrieval).**

With ~15 schemas and ~30 examples for a single endpoint, the total context is ~6-8K tokens - trivial for Claude's 200K context window. Every LLM call receives ALL schemas and ALL examples. This eliminates:
- Embedding model dependencies
- Vector database infrastructure
- Retrieval bugs from poor similarity matches
- Missed context from relevant-but-unmatched documents

The LLM itself decides which schemas and examples are relevant to the question. The marginal token cost (~$0.02/query at Sonnet pricing) is negligible compared to the reliability gained by ensuring the model always has complete context.

#### 3. Query Validation (`dprr_tool/validate.py`)

Three-tier validation adapted from the SIB architecture:

**Tier 1 - Syntax + prefix repair:**
- Parse with `rdflib.prepareQuery()`
- On "Unknown namespace prefix": scan for used prefixes, insert missing declarations from `prefixes.yaml`
- On other syntax errors: return error text for LLM retry

**Tier 2 - Semantic validation:**

Build a schema dictionary from `schemas.yaml`:
```
schema_dict[class_uri][predicate_uri] = [range_types]
```

Validate extracted triple patterns:
1. For typed subjects (`?x a vocab:Person`): verify all predicates on `?x` exist in Person's schema
2. For untyped subjects: infer type from predicate domain
3. Error messages include valid alternatives: *"vocab:Person does not have predicate vocab:hasOffice. Valid predicates: vocab:hasNomen, vocab:hasCognomen, ..."*

Handle property paths (sequence `/`, alternative `|`) by decomposition into individual triple patterns.

**Tier 3 - Execution validation:**
- Execute against local Oxigraph
- 0 results: ask Claude to relax constraints
- Runtime error: send error to Claude

Functions:
- `parse_and_fix_prefixes(sparql, prefix_map) -> tuple[str, list[str]]`
- `build_schema_dict(schemas) -> dict`
- `extract_triple_patterns(parsed_query) -> list[Triple]`
- `validate_semantics(triples, schema_dict) -> list[str]`

#### 4. LLM Pipeline (`dprr_tool/pipeline.py`)

Three Claude API calls orchestrated sequentially:

**Call 1 - Structured extraction** (tool use):

```python
@dataclass
class StructuredQuestion:
    intent: Literal["query_data", "general_info"]
    extracted_classes: list[str]    # ["Person", "PostAssertion"]
    extracted_entities: list[str]   # ["Scipio Africanus", "consul"]
    question_steps: list[str]      # sub-questions for complex queries
```

**Call 2 - SPARQL generation** (with retry loop, max 3):

System prompt includes:
- DPRR domain rules: `vocab:` namespace, negative years = BC, assertion-based model
- All class schemas rendered as ShEx-style text
- All example queries (full context injection - no retrieval/embedding needed)
- Extraction result

On validation failure: append error messages as user message, call again.

**Call 3 - Response synthesis:**

Receives: original question, executed SPARQL, result set.
Produces: academic prose with secondary source citations, uncertainty flags, data completeness caveats.

**LLM configuration:** temperature=0, max_tokens=4096 for generation, 8192 for synthesis.

#### 5. CLI Interface (`dprr_tool/cli.py`)

```
dprr-tool init                  # Download DPRR data, load into Oxigraph
dprr-tool ask "question"        # Full pipeline
dprr-tool query "SPARQL"        # Execute raw SPARQL (bypass LLM)
dprr-tool info                  # Store stats
```

Output via `rich`:
- SPARQL in syntax-highlighted code block
- Results as formatted table
- Prose as rendered markdown
- Uncertainty flagged visually

#### 6. System Prompts (`dprr_tool/prompts.py`)

Domain-specific prompt templates:

**Extraction prompt:** Instructs Claude to identify DPRR-relevant classes, Roman names, office titles, and date ranges from the question.

**Generation prompt:** Includes DPRR-specific SPARQL rules:
- Use `vocab:` prefix for all DPRR properties
- Entity URIs follow `http://romanrepublic.ac.uk/rdf/entity/{Type}/{ID}` pattern
- Dates are integers: negative = BC, positive = AD
- The assertion pattern: `PostAssertion -[isAboutPerson]-> Person`, `PostAssertion -[hasOffice]-> Office`
- Use `DISTINCT` and `LIMIT 100` by default
- Include `vocab:isUncertain` when uncertainty matters

**Synthesis prompt:** Instructs Claude to:
- Cite which secondary source(s) the data comes from (Broughton, Rupke, Zmeskal)
- Flag uncertain assertions explicitly
- Note data completeness limitations (DPRR covers 509-31 BC only)
- Use standard prosopographic conventions for Roman names

## Project Structure

```
dprr-tool/
├── pyproject.toml
├── main.py
├── dprr_tool/
│   ├── __init__.py
│   ├── cli.py
│   ├── store.py
│   ├── pipeline.py
│   ├── validate.py
│   ├── prompts.py
│   └── context/
│       ├── schemas.yaml
│       ├── examples.yaml
│       └── prefixes.yaml
├── tests/
│   ├── test_store.py
│   ├── test_validate.py
│   └── test_pipeline.py
└── docs/
    └── plans/
```

## Dependencies

```toml
dependencies = [
    "anthropic",
    "pyoxigraph",
    "rdflib",
    "click",
    "rich",
    "pyyaml",
]
```

## Configuration

- `ANTHROPIC_API_KEY` environment variable (required)
- Store path: `~/.dprr-tool/` (overridable with `--store-path`)
- Python >= 3.13

## Key DPRR Domain Notes

**Namespace quirk:** The formal ontology uses `http://romanrepublic.ac.uk/rdf/ontology#` but the triplestore uses `http://romanrepublic.ac.uk/rdf/entity/vocab/`. All SPARQL queries must use the `entity/vocab/` namespace.

**Assertion-based model:** Data about persons is not stored directly on Person entities. Instead, an assertion pattern is used:
- `PostAssertion` links a Person to an Office via `isAboutPerson` and `hasOffice`
- `RelationshipAssertion` links two Persons via `isAboutPerson`, `hasRelatedPerson`, and `hasRelationship`
- `StatusAssertion` links a Person to a Status
- Each assertion carries its own `SecondarySource`, `isUncertain` flag, and optional date range

**Date convention:** All years are integers. Negative values = BC (e.g., -200 = 200 BC). The `hasDateStart`/`hasDateEnd` properties on assertions and `hasEraFrom`/`hasEraTo` on persons follow this convention.

**Data sources:** Three secondary sources form the backbone:
- Broughton's *Magistrates of the Roman Republic* (1951-86) - offices
- Rupke's *Fasti Sacerdotum* (2005) - priesthoods
- Zmeskal's *Adfinitas* (2009) - family relations

**License:** CC BY-NC 4.0 (non-commercial use only).
