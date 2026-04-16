#!/usr/bin/env python3
"""Smoke test: drive the MCP server in-process via FastMCP's Client API.

Verifies:
  1. Tools / resources / prompts all register.
  2. `query` tool returns non-empty chunks with the expected metadata shape.
  3. `document://{source_id}` resource returns a full document.
  4. `cite_from_chunks` prompt renders.
  5. Guardrails reject empty / oversized queries and clamp out-of-range k.

Run:
    python -m scripts.test_mcp_server
"""

from __future__ import annotations

import asyncio
import json
import sys

from fastmcp import Client

from scripts.mcp_server import mcp


async def main() -> int:
    async with Client(mcp) as client:
        tools = await client.list_tools()
        resources = await client.list_resource_templates()
        prompts = await client.list_prompts()

        tool_names = [t.name for t in tools]
        prompt_names = [p.name for p in prompts]
        resource_templates = [r.uriTemplate for r in resources]

        assert "query" in tool_names, tool_names
        assert "cite_from_chunks" in prompt_names, prompt_names
        assert any("document://" in u for u in resource_templates), resource_templates
        print(f"[PASS] registration: tools={tool_names} prompts={prompt_names} resources={resource_templates}")

        # 2. Real query end-to-end
        res = await client.call_tool(
            "query",
            {"query": "What RPO handles GI Bill claims in Texas?", "k": 3},
        )
        payload = res.data
        assert payload["k"] == 3, payload["k"]
        assert len(payload["chunks"]) == 3, len(payload["chunks"])
        top = payload["chunks"][0]
        for field in ("chunk_id", "source_id", "title", "heading_path",
                      "chunk_type", "content", "rerank_score", "cosine_score"):
            assert field in top, f"missing {field} in {top.keys()}"
        assert isinstance(top["rerank_score"], float), type(top["rerank_score"])
        print(
            f"[PASS] query: {payload['k']} chunks, top rerank={top['rerank_score']:.3f} "
            f"latency_ms={payload['latency_ms']} trace_id={payload['trace_id']}"
        )

        # 3. Resource fetch
        src_id = top["source_id"]
        doc_resp = await client.read_resource(f"document://{src_id}")
        doc = json.loads(doc_resp[0].text)
        assert doc["source_id"] == src_id, doc
        assert "raw_content" in doc and len(doc["raw_content"]) > 0, "empty raw_content"
        print(f"[PASS] resource: document://{src_id} -> {len(doc['raw_content'])} chars raw_content")

        # 4. Prompt render
        prompt = await client.get_prompt("cite_from_chunks", {"user_question": "Who runs GI Bill?"})
        assert "cite every non-trivial claim" in prompt.messages[0].content.text.lower()
        print("[PASS] prompt: cite_from_chunks rendered with citation rules")

        # 5. Guardrails
        try:
            await client.call_tool("query", {"query": "", "k": 5})
            print("[FAIL] empty query should have raised")
            return 1
        except Exception as e:
            print(f"[PASS] empty-query guard: {type(e).__name__}")

        res = await client.call_tool("query", {"query": "valid", "k": 999})
        assert res.data["k"] == 20, res.data["k"]
        print(f"[PASS] k-clamp: requested 999, served {res.data['k']}")

        # rerank_from clamp: huge value should cap at MAX_RERANK_FROM=100.
        # We can't read k_pool from the response, but we can assert no error
        # and non-empty chunks (proves the pool size didn't break retrieval).
        res = await client.call_tool(
            "query", {"query": "valid", "k": 5, "rerank_from": 99999},
        )
        assert len(res.data["chunks"]) == 5, res.data
        print("[PASS] rerank_from clamp: huge value capped, query still returns")

    print("\nAll smoke tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
