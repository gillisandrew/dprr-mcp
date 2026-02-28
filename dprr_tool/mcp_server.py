"""MCP server exposing DPRR SPARQL tools over stdio or streamable-http."""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from mcp.server.fastmcp import Context, FastMCP

from dprr_tool.context import (
    load_examples,
    load_prefixes,
    load_schemas,
    load_tips,
    render_examples,
    render_schemas_as_shex,
    render_tips,
)
from dprr_tool.store import ensure_initialized, execute_query
from dprr_tool.validate import (
    build_schema_dict,
    parse_and_fix_prefixes,
    validate_and_execute,
)

logger = logging.getLogger(__name__)

QUERY_TIMEOUT = int(os.environ.get("DPRR_QUERY_TIMEOUT", "120"))

DEFAULT_STORE_PATH = Path.home() / ".dprr-tool" / "store"


@dataclass
class AppContext:
    store: object  # pyoxigraph.Store
    prefix_map: dict[str, str]
    schema_dict: dict


@asynccontextmanager
async def lifespan(server: FastMCP):
    """Initialize the Oxigraph store and schema on startup."""
    store_path = Path(os.environ.get("DPRR_STORE_PATH", str(DEFAULT_STORE_PATH)))
    store = ensure_initialized(store_path)
    prefix_map = load_prefixes()
    schemas = load_schemas()
    schema_dict = build_schema_dict(schemas, prefix_map)
    yield AppContext(store=store, prefix_map=prefix_map, schema_dict=schema_dict)


mcp = FastMCP(
    "dprr",
    instructions=(
        "DPRR (Digital Prosopography of the Roman Republic) SPARQL query tools. "
        "Use get_schema to learn the ontology, validate_sparql to check queries, "
        "and execute_sparql to run them against the local RDF store."
    ),
    lifespan=lifespan,
)


@mcp.tool()
def get_schema(ctx: Context) -> str:
    """Get the full DPRR ontology context: namespace prefixes, ShEx schema for all classes/properties, 28 curated example question/SPARQL pairs, and query tips for common pitfalls. Call this first to learn the domain before generating queries."""
    prefix_map = load_prefixes()
    schemas = load_schemas()
    examples = load_examples()
    tips = load_tips()

    prefix_lines = "\n".join(f"PREFIX {k}: <{v}>" for k, v in prefix_map.items())

    return (
        f"## Prefixes\n\n{prefix_lines}\n\n"
        f"## Schema (ShEx)\n\n{render_schemas_as_shex(schemas)}\n\n"
        f"## Examples\n\n{render_examples(examples)}\n\n"
        f"## Query Tips\n\n{render_tips(tips)}"
    )


@mcp.tool()
def validate_sparql(ctx: Context, sparql: str) -> str:
    """Validate a SPARQL query against the DPRR schema without executing it. Checks syntax, auto-repairs missing PREFIX declarations, and validates that all classes and predicates exist in the ontology."""
    app: AppContext = ctx.request_context.lifespan_context

    fixed_sparql, parse_errors = parse_and_fix_prefixes(sparql, app.prefix_map)
    if parse_errors:
        error_list = "\n".join(f"- {e}" for e in parse_errors)
        return f"INVALID\n\nErrors:\n{error_list}"

    from dprr_tool.validate import validate_semantics

    semantic_errors = validate_semantics(fixed_sparql, app.schema_dict)
    if semantic_errors:
        error_list = "\n".join(f"- {e}" for e in semantic_errors)
        return f"INVALID\n\nErrors:\n{error_list}"

    if fixed_sparql != sparql:
        return f"VALID (prefixes auto-repaired)\n\n```sparql\n{fixed_sparql}\n```"
    return "VALID"


def _format_table(rows: list[dict[str, str]]) -> str:
    """Format result rows as a markdown table."""
    if not rows:
        return "(no results)"
    columns = list(rows[0].keys())
    # Build header
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    # Build rows
    lines = [header, separator]
    for row in rows:
        line = "| " + " | ".join(str(row.get(c, "")) for c in columns) + " |"
        lines.append(line)
    return "\n".join(lines)


@mcp.tool()
async def execute_sparql(ctx: Context, sparql: str, timeout: int | None = None) -> str:
    """Validate and execute a SPARQL query against the local DPRR RDF store. Returns results as a markdown table. Automatically repairs missing PREFIX declarations before execution."""
    app: AppContext = ctx.request_context.lifespan_context
    effective_timeout = timeout if timeout is not None else QUERY_TIMEOUT

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(
                validate_and_execute, sparql, app.store, app.schema_dict, app.prefix_map
            ),
            timeout=effective_timeout,
        )
    except asyncio.TimeoutError:
        logger.warning("Query timed out after %ds: %s", effective_timeout, sparql[:200])
        return f"ERROR: Query timed out after {effective_timeout}s. Simplify the query or increase the timeout."
    except OSError as e:
        logger.error("Store error: %s", e)
        return f"ERROR: Store access error: {e}"
    except Exception as e:
        logger.error("Unexpected error executing query: %s", e)
        return f"ERROR: Unexpected error: {e}"

    if not result.success:
        error_list = "\n".join(f"- {e}" for e in result.errors)
        return f"ERROR:\n{error_list}"

    row_count = len(result.rows)
    table = _format_table(result.rows)
    return f"{row_count} result(s)\n\n{table}"


def main():
    """Run the MCP server."""
    import argparse

    parser = argparse.ArgumentParser(description="DPRR MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for HTTP transport (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP transport (default: 8000)")
    args = parser.parse_args()

    if args.transport == "http":
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
