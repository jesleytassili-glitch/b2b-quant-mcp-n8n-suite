#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Automated test suite exercising all declared MCP tools in mcp_server.py."""

import json
import subprocess
import sys
from pathlib import Path

import mcp_server


def test_tools_declaration_complete() -> None:
    """Verify all 30 B2B tools are declared with valid JSON schemas."""
    assert len(mcp_server.TOOLS) >= 30
    for tool in mcp_server.TOOLS:
        assert "name" in tool and tool["name"]
        assert "description" in tool and len(tool["description"]) > 10
        assert "actor_slug" in tool and tool["actor_slug"]
        schema = tool.get("inputSchema", {})
        assert schema.get("type") == "object"


def test_stdio_initialize_and_tools_list() -> None:
    """Exercise JSON-RPC initialize and tools/list over stdio."""
    server_script = Path(mcp_server.__file__).resolve()
    payload = "\n".join([
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
        json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}),
    ]) + "\n"
    proc = subprocess.run(
        [sys.executable, str(server_script)],
        input=payload,
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    lines = [line for line in proc.stdout.strip().splitlines() if line.strip()]
    assert len(lines) == 2
    init_resp = json.loads(lines[0])
    assert init_resp["result"]["serverInfo"]["name"] == "b2b-quant-mcp-n8n-suite"
    tools_resp = json.loads(lines[1])
    assert len(tools_resp["result"]["tools"]) >= 30
