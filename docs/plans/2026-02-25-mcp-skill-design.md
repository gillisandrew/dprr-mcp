# DPRR Tool: MCP Server + Claude Skill Design

## Problem

The current CLI makes 3-4 Anthropic API calls per question (extraction, SPARQL generation, retry, synthesis). This is redundant when used from Claude Code or Claude Desktop, where Claude itself can orchestrate the pipeline directly. The tool should expose its RDF/SPARQL capabilities via MCP and let Claude handle the intelligence.

## Architecture

```
┌─────────────────────────────────────┐
│  Claude Code Skill (/dprr)          │  System prompt with DPRR domain knowledge
│  Orchestrates: extract → generate   │  (ontology rules, assertion model, dates,
│  → validate → synthesize            │   citation style)
└──────────────┬──────────────────────┘
               │ MCP protocol (stdio)
┌──────────────▼──────────────────────┐
│  MCP Server (dprr-tool serve)       │  3 tools: get_schema, validate_sparql,
│  Python, stdio transport            │  execute_sparql
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Local Oxigraph Store               │  Auto-initialized from .ttl on first use
└─────────────────────────────────────┘
```

Claude is the orchestrator. The MCP server provides domain tools. No Anthropic API calls needed on the MCP path. The existing CLI (`init`, `info`, `query`, `ask`) remains alongside the new `serve` command.

## MCP Server Tools

### `get_schema`

Returns the full DPRR ontology context for SPARQL generation.

- **Input**: None
- **Output**: `{ prefixes: {str: str}, schema_shex: str, examples: [{question, sparql}] }`
- **Source**: Combines `context/prefixes.yaml`, `context/schemas.yaml`, `context/examples.yaml`

### `validate_sparql`

Syntax + prefix repair (Tier 1) and semantic validation (Tier 2) without execution.

- **Input**: `{ sparql: str }`
- **Output**: `{ valid: bool, fixed_sparql: str, errors: [str] }`

### `execute_sparql`

Full validation (Tier 1-3) then execution against the local Oxigraph store.

- **Input**: `{ sparql: str }`
- **Output**: `{ success: bool, sparql: str, rows: [{col: val}], row_count: int, errors: [str] }`

## Claude Skill

File: `.claude/skills/dprr/SKILL.md`

Trigger: `/dprr <question>`

The skill prompt contains:

1. **Domain knowledge**: DPRR namespace, assertion-based model (PostAssertion for offices, not Person), entity URI patterns, negative integers for BC dates, DISTINCT + LIMIT 100.

2. **Workflow**:
   - Call `get_schema` to load ontology context
   - Analyze user's question (identify intent, classes, entities)
   - Generate SPARQL using schema and examples
   - Call `validate_sparql` to check the query
   - If errors, fix and re-validate (up to 2 retries)
   - Call `execute_sparql` to run the query
   - Synthesize results into academic prose

3. **Synthesis rules**: Cite sources (Broughton MRR, Rupke Fasti, Zmeskal Adfinitas), flag uncertain data, use Roman naming conventions, format dates as "200 BC" not "-200".

## Implementation Plan

### New files

- `dprr_tool/mcp_server.py` — MCP server using `mcp` Python SDK, stdio transport, 3 tool handlers
- `.claude/skills/dprr/SKILL.md` — Claude Code skill prompt

### Modified files

- `cli.py` — Add `dprr-tool serve` command that starts the MCP server
- `store.py` — Add lazy-init: if store is empty and `DPRR_RDF_FILE` env var is set, auto-load on first tool call
- `pyproject.toml` — Add `mcp` dependency

### Unchanged files

- `validate.py` — Reused by MCP tool handlers
- `context/` — Reused by `get_schema` tool
- `pipeline.py` — Kept for existing `ask` CLI command
- `prompts.py` — Kept for existing `ask` CLI command

### MCP client configuration

```json
{
  "mcpServers": {
    "dprr": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/dprr-tool", "dprr-tool", "serve"],
      "env": {
        "DPRR_RDF_FILE": "/path/to/dprr-data.ttl"
      }
    }
  }
}
```

## Data Flow Example

User: `/dprr Who were the consuls in 100 BC?`

1. Skill activates, Claude calls `get_schema` → receives prefixes, ShEx schema, 22 examples
2. Claude analyzes question: intent=query_data, classes=[PostAssertion, Person, Office], entities=["consul", "100 BC"]
3. Claude writes SPARQL:
   ```sparql
   PREFIX vocab: <http://romanrepublic.ac.uk/rdf/entity/vocab/>
   SELECT DISTINCT ?name ?praenomen ?nomen ?cognomen ?uncertain
   WHERE {
     ?assertion a vocab:PostAssertion ;
       vocab:isAboutPerson ?person ;
       vocab:hasOffice ?office ;
       vocab:hasDateStart ?date .
     ?office rdfs:label "Consul" .
     FILTER(?date = -100)
     ?person vocab:hasPraenomen/rdfs:label ?praenomen ;
       vocab:hasNomen ?nomen .
     OPTIONAL { ?person vocab:hasCognomen ?cognomen }
     OPTIONAL { ?assertion vocab:isUncertain ?uncertain }
     BIND(CONCAT(?praenomen, " ", ?nomen, COALESCE(CONCAT(" ", ?cognomen), "")) AS ?name)
   } LIMIT 100
   ```
4. Claude calls `validate_sparql` → `{ valid: true, ... }`
5. Claude calls `execute_sparql` → rows with consul data
6. Claude synthesizes: "In 100 BC, the consuls were Gaius Marius (his sixth consulship) and Lucius Valerius Flaccus, according to Broughton's MRR..."
