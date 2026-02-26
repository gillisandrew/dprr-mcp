import asyncio
import json
import sys
from unittest.mock import patch, MagicMock

import pytest

from dprr_tool.mcp_server import main, execute_sparql, QUERY_TIMEOUT


# --- argparse tests ---


def test_main_defaults_to_stdio():
    """main() with no args runs stdio transport."""
    with patch("dprr_tool.mcp_server.mcp") as mock_mcp:
        with patch("sys.argv", ["dprr-server"]):
            main()
        mock_mcp.run.assert_called_once_with(transport="stdio")


def test_main_http_transport():
    """main() with --transport http runs streamable-http."""
    with patch("dprr_tool.mcp_server.mcp") as mock_mcp:
        with patch("sys.argv", ["dprr-server", "--transport", "http"]):
            main()
        assert mock_mcp.settings.host == "127.0.0.1"
        assert mock_mcp.settings.port == 8000
        mock_mcp.run.assert_called_once_with(transport="streamable-http")


def test_main_http_custom_host_port():
    """main() with --transport http --host/--port sets settings."""
    with patch("dprr_tool.mcp_server.mcp") as mock_mcp:
        with patch("sys.argv", ["dprr-server", "--transport", "http", "--host", "0.0.0.0", "--port", "9000"]):
            main()
        assert mock_mcp.settings.host == "0.0.0.0"
        assert mock_mcp.settings.port == 9000
        mock_mcp.run.assert_called_once_with(transport="streamable-http")


def test_main_invalid_transport():
    """main() with invalid transport exits with error."""
    with patch("sys.argv", ["dprr-server", "--transport", "grpc"]):
        with pytest.raises(SystemExit):
            main()


# --- execute_sparql timeout and error handling tests ---


def _make_mock_ctx(store=None, prefix_map=None, schema_dict=None):
    """Create a mock Context with AppContext."""
    from dprr_tool.mcp_server import AppContext

    app = AppContext(
        store=store or MagicMock(),
        prefix_map=prefix_map or {},
        schema_dict=schema_dict or {},
    )
    ctx = MagicMock()
    ctx.request_context.lifespan_context = app
    return ctx


@pytest.mark.asyncio
async def test_execute_sparql_timeout():
    """execute_sparql returns structured error on timeout."""
    ctx = _make_mock_ctx()

    async def slow_thread(*args, **kwargs):
        await asyncio.sleep(10)

    with patch("dprr_tool.mcp_server.QUERY_TIMEOUT", 0.1), \
         patch("dprr_tool.mcp_server.asyncio.to_thread", side_effect=slow_thread):
        result_str = await execute_sparql(ctx, "SELECT ?x WHERE { ?x ?y ?z }")

    result = json.loads(result_str)
    assert result["success"] is False
    assert "timed out" in result["errors"][0]


@pytest.mark.asyncio
async def test_execute_sparql_os_error():
    """execute_sparql returns structured error on OSError."""
    ctx = _make_mock_ctx()

    async def raise_os_error(*args, **kwargs):
        raise OSError("store locked")

    with patch("dprr_tool.mcp_server.asyncio.to_thread", side_effect=raise_os_error):
        result_str = await execute_sparql(ctx, "SELECT ?x WHERE { ?x ?y ?z }")

    result = json.loads(result_str)
    assert result["success"] is False
    assert "Store access error" in result["errors"][0]


@pytest.mark.asyncio
async def test_execute_sparql_unexpected_error():
    """execute_sparql returns structured error on unexpected exceptions."""
    ctx = _make_mock_ctx()

    async def raise_unexpected(*args, **kwargs):
        raise RuntimeError("something broke")

    with patch("dprr_tool.mcp_server.asyncio.to_thread", side_effect=raise_unexpected):
        result_str = await execute_sparql(ctx, "SELECT ?x WHERE { ?x ?y ?z }")

    result = json.loads(result_str)
    assert result["success"] is False
    assert "Unexpected error" in result["errors"][0]


@pytest.mark.asyncio
async def test_execute_sparql_success():
    """execute_sparql returns results on success."""
    from dprr_tool.validate import ValidationResult

    ctx = _make_mock_ctx()
    mock_result = ValidationResult(
        success=True,
        sparql="SELECT ?x WHERE { ?x ?y ?z }",
        rows=[{"x": "http://example.com/1"}],
        errors=[],
    )

    async def mock_thread(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    with patch("dprr_tool.mcp_server.asyncio.to_thread", return_value=mock_result) as mock_to_thread:
        # Bypass the actual to_thread by making wait_for resolve our mock
        with patch("dprr_tool.mcp_server.asyncio.wait_for", return_value=mock_result):
            result_str = await execute_sparql(ctx, "SELECT ?x WHERE { ?x ?y ?z }")

    result = json.loads(result_str)
    assert result["success"] is True
    assert result["row_count"] == 1
    assert result["errors"] == []
