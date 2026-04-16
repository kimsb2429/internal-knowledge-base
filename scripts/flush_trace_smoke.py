#!/usr/bin/env python3
"""Fire one real query through the MCP server and flush OTel spans to Langfuse."""
import asyncio

from fastmcp import Client
from opentelemetry import trace

from scripts.mcp_server import mcp


async def main():
    async with Client(mcp) as client:
        res = await client.call_tool(
            "query",
            {"query": "What RPO handles GI Bill claims in Texas?", "k": 3},
        )
        print(f"trace_id={res.data['trace_id']} latency_ms={res.data['latency_ms']} chunks={len(res.data['chunks'])}")

    # Force the BatchSpanProcessor to flush before process exit.
    provider = trace.get_tracer_provider()
    if hasattr(provider, "force_flush"):
        provider.force_flush(timeout_millis=10_000)
        print("OTel flush: done")


if __name__ == "__main__":
    asyncio.run(main())
