#!/usr/bin/env python3
"""Verify whether FastMCP hoists top-level dict `_meta` to CallToolResult._meta.

Uses a **standalone minimal FastMCP** instance — no DB, no reranker, no real
retrieval — to isolate the `_meta` hoisting question. The same FastMCP version
mcp_server.py uses.

Run:
    python -m scripts.test_meta_hoist
"""

from __future__ import annotations

import asyncio
import json
import sys

import fastmcp
from fastmcp import Client, FastMCP
from fastmcp.tools.tool import ToolResult


mcp = FastMCP("meta-hoist-test")


@mcp.tool
def echo_with_meta() -> ToolResult:
    """Returns ToolResult with explicit meta= — the pattern used by mcp_server.py's query tool."""
    return ToolResult(
        structured_content={
            "payload": "the actual data",
            "chunks": [{"source_id": "sample", "content": "hi"}],
        },
        meta={"anthropic/maxResultSizeChars": 500000},
    )


@mcp.resource("document://{source_id}")
def echo_resource(source_id: str) -> dict:
    return {
        "source_id": source_id,
        "raw_content": "hello world",
        "_meta": {"anthropic/maxResultSizeChars": 500000},
    }


async def main() -> int:
    print(f"FastMCP version: {fastmcp.__version__}")

    async with Client(mcp) as client:
        # --- TOOL ---
        print("\n=== Tool call `echo_with_meta` ===")
        res = await client.call_tool("echo_with_meta", {})

        print(f"type(res) = {type(res).__name__}")

        # Check envelope-level _meta attributes
        for attr in ("meta", "_meta"):
            if hasattr(res, attr):
                print(f"res.{attr} = {getattr(res, attr)!r}")

        # Check res.data (FastMCP auto-parses JSON here)
        data = getattr(res, "data", None)
        if isinstance(data, dict):
            print(f"res.data keys = {list(data.keys())}")
            print(f"res.data.get('_meta') = {data.get('_meta')!r}")

        # Check res.content[0] (raw MCP TextContent)
        content = getattr(res, "content", None) or []
        if content:
            c0 = content[0]
            print(f"res.content[0] type = {type(c0).__name__}")
            for attr in ("meta", "_meta"):
                if hasattr(c0, attr):
                    val = getattr(c0, attr)
                    if val is not None:
                        print(f"res.content[0].{attr} = {val!r}")
            text = getattr(c0, "text", None)
            if text:
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict):
                        print(f"parsed(res.content[0].text).get('_meta') = {parsed.get('_meta')!r}")
                        print(f"parsed(res.content[0].text) keys = {list(parsed.keys())}")
                except json.JSONDecodeError:
                    pass

        # Full model dump if available
        if hasattr(res, "model_dump"):
            dumped = res.model_dump()
            print(f"\nres.model_dump() top-level keys = {list(dumped.keys())}")
            if "meta" in dumped or "_meta" in dumped:
                print(f"  envelope meta in dump: {dumped.get('meta') or dumped.get('_meta')!r}")

        # --- RESOURCE ---
        print("\n=== Resource read `document://abc` ===")
        doc_resp = await client.read_resource("document://abc")
        print(f"type(doc_resp) = {type(doc_resp).__name__}")
        if doc_resp:
            first = doc_resp[0]
            print(f"doc_resp[0] type = {type(first).__name__}")
            for attr in ("meta", "_meta"):
                if hasattr(first, attr):
                    val = getattr(first, attr)
                    if val is not None:
                        print(f"doc_resp[0].{attr} = {val!r}")
            text = getattr(first, "text", None)
            if text:
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict):
                        print(f"parsed(doc_resp[0].text).get('_meta') = {parsed.get('_meta')!r}")
                        print(f"parsed(doc_resp[0].text) keys = {list(parsed.keys())}")
                except json.JSONDecodeError:
                    pass

    print("\n=== VERDICT ===")
    print("If envelope `_meta` is populated with {anthropic/maxResultSizeChars: 500000},")
    print("FastMCP hoists correctly and the edit in mcp_server.py works as-is.")
    print("If envelope is None/missing but the value only appears nested in parsed text,")
    print("FastMCP does NOT hoist — need to use explicit FastMCP meta API.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
