#!/usr/bin/env python3
"""
Internal Knowledge Base MCP server.

Wraps the existing retrieve + rerank pipeline (vector search over pgvector,
mxbai-embed-large embeddings, mxbai-rerank-base-v2 cross-encoder) as an
MCP-compliant server. Exposes Tools, Resources, and Prompts.

Transport defaults to stdio (Claude Desktop / Claude Code). Switch to Streamable
HTTP with `--transport http` for gateway-fronted deployments.

The `auth_context` parameter on every tool is the enterprise seam: unused in
v1, populated by an MCP gateway (Kong / Lunar / TrueFoundry / MintMCP) in
production for SSO, tenancy, and audit. See docs/demo-prep-raw.md Act 27.

Usage:
    python -m scripts.mcp_server                         # stdio
    python -m scripts.mcp_server --transport http       # streamable HTTP, :8000
    fastmcp dev scripts/mcp_server.py                    # MCP Inspector
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import os
import sys
import time
from typing import Any

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Observability — wire OTel to Langfuse Cloud if credentials are present.
# Must run BEFORE `from fastmcp import FastMCP` so FastMCP's instrumentation
# picks up our TracerProvider. If LANGFUSE_* env vars are missing, we skip
# OTel setup silently and the server runs un-instrumented (demo-local mode).
# ---------------------------------------------------------------------------
def _init_otel() -> bool:
    pk = os.environ.get("LANGFUSE_PUBLIC_KEY")
    sk = os.environ.get("LANGFUSE_SECRET_KEY")
    host = (
        os.environ.get("LANGFUSE_BASE_URL")
        or os.environ.get("LANGFUSE_HOST")
        or "https://cloud.langfuse.com"
    )
    if not (pk and sk):
        return False

    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    auth = base64.b64encode(f"{pk}:{sk}".encode()).decode()
    exporter = OTLPSpanExporter(
        endpoint=f"{host.rstrip('/')}/api/public/otel/v1/traces",
        headers={"Authorization": f"Basic {auth}"},
    )
    resource = Resource.create({"service.name": "internal-knowledge-base"})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return True


_OTEL_ENABLED = _init_otel()

from fastmcp import FastMCP  # noqa: E402  (must import after OTel setup)
from opentelemetry import trace as _otel_trace  # noqa: E402

from scripts.rerank import rerank  # noqa: E402
from scripts.retrieve import _get_conn, retrieve  # noqa: E402

_tracer = _otel_trace.get_tracer("ikb.mcp")

# ---------------------------------------------------------------------------
# Logging — on stdio transport, stdout is reserved for JSON-RPC. Always stderr.
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger("ikb.mcp")

# ---------------------------------------------------------------------------
# Guardrails — hard limits enforced server-side regardless of client request.
# ---------------------------------------------------------------------------
MAX_K = 20                     # plan step 4 guardrail: result count cap
MIN_K = 1
MAX_RERANK_FROM = 100          # cross-encoder pool ceiling (protects DB + rerank RAM)
MIN_RERANK_FROM = 1
MAX_QUERY_CHARS = 2000         # input validation: reject absurd queries

mcp = FastMCP(
    "internal-knowledge-base",
    instructions=(
        "Retrieval over the VA Education corpus (M22-3, M22-4, VADIR ICD). "
        "Use `query` for question-answering; results come pre-reranked by "
        "cross-encoder. Use the `document://{source_id}` resource to fetch a "
        "full source document when chunk-level context is insufficient. Use "
        "the `cite_from_chunks` prompt to get a citation-heavy answer format."
    ),
)


def _validate_query(q: str) -> str:
    if not isinstance(q, str) or not q.strip():
        raise ValueError("query must be a non-empty string")
    if len(q) > MAX_QUERY_CHARS:
        raise ValueError(f"query exceeds {MAX_QUERY_CHARS} chars")
    return q.strip()


def _clamp_k(k: int) -> int:
    try:
        k = int(k)
    except (TypeError, ValueError):
        k = 5
    return max(MIN_K, min(MAX_K, k))


def _clamp_rerank_from(rerank_from: int, k_out: int) -> int:
    """Clamp to [max(k_out, MIN_RERANK_FROM), MAX_RERANK_FROM]. Can't rerank
    fewer candidates than we want to return, and must respect the ceiling."""
    try:
        r = int(rerank_from)
    except (TypeError, ValueError):
        r = 20
    return max(k_out, MIN_RERANK_FROM, min(MAX_RERANK_FROM, r))


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
@mcp.tool
def query(
    query: str,
    k: int = 5,
    rerank_from: int = 20,
    auth_context: dict[str, Any] | None = None,
) -> dict:
    """Retrieve the top-k most relevant chunks for a natural-language query.

    Pipeline: mxbai-embed-large vector retrieval → mxbai-rerank-base-v2
    cross-encoder rerank → top-k chunks with metadata. Optimized for
    question-answering over the VA Education corpus.

    Args:
        query: Natural-language question (1-2000 chars).
        k: Number of chunks to return after reranking (1-20, default 5).
        rerank_from: Vector retrieval pool size before rerank (default 20).
        auth_context: Reserved for gateway-populated identity/tenancy in
            production. Ignored in v1. Label, don't half-build.

    Returns:
        dict with `chunks` (list of chunk dicts: source_id, title,
        heading_path, chunk_type, content, rerank_score, cosine_score),
        `query` (the validated query), `k` (the effective k used),
        `latency_ms`, and `trace_id` for observability.
    """
    t0 = time.time()
    q = _validate_query(query)
    k_out = _clamp_k(k)
    k_pool = _clamp_rerank_from(rerank_from, k_out)

    # Attach input to the current (tool-call) span so Langfuse renders it.
    _parent_span = _otel_trace.get_current_span()
    _parent_span.set_attribute("input.value", q)
    _parent_span.set_attribute("ikb.k", k_out)
    _parent_span.set_attribute("ikb.rerank_from", k_pool)

    with _tracer.start_as_current_span("retrieve") as span:
        span.set_attribute("k_pool", k_pool)
        candidates = retrieve(q, k=k_pool)
        span.set_attribute("candidates", len(candidates))

    with _tracer.start_as_current_span("rerank") as span:
        span.set_attribute("top_k", k_out)
        top = rerank(q, candidates, top_k=k_out)
        span.set_attribute("returned", len(top))

    chunks = [
        {
            "chunk_id": c["chunk_id"],
            "source_id": c["source_id"],
            "title": c["title"],
            "heading_path": c["heading_path"] or [],
            "chunk_type": c["chunk_type"],
            "token_count": c["token_count"],
            "content": c["content"],
            "cosine_score": c.get("cosine_score"),
            "rerank_score": c.get("rerank_score"),
        }
        for c in top
    ]

    latency_ms = int((time.time() - t0) * 1000)
    trace_id = f"ikb-{int(t0 * 1000)}"

    # Attach output summary to the tool-call span so Langfuse renders it.
    # Keep payload small — full chunk content would bloat traces; summary is
    # enough for debugging. Full content is always available from `retrieve`
    # replay by chunk_id if needed.
    _output_summary = {
        "trace_id": trace_id,
        "latency_ms": latency_ms,
        "top_rerank_score": chunks[0]["rerank_score"] if chunks else None,
        "sources": [
            {"source_id": c["source_id"], "heading_path": c["heading_path"],
             "rerank_score": c["rerank_score"]}
            for c in chunks
        ],
    }
    _parent_span.set_attribute("output.value", json.dumps(_output_summary))
    _parent_span.set_attribute("ikb.trace_id", trace_id)
    _parent_span.set_attribute("ikb.latency_ms", latency_ms)
    _parent_span.set_attribute(
        "ikb.top_rerank_score",
        chunks[0]["rerank_score"] if chunks else -1.0,
    )

    otel_trace_id = format(_parent_span.get_span_context().trace_id, "032x")
    log.info(
        "query trace_id=%s otel_trace_id=%s k=%d pool=%d chunks=%d latency_ms=%d top_score=%.3f auth=%s",
        trace_id, otel_trace_id, k_out, k_pool, len(chunks), latency_ms,
        chunks[0]["rerank_score"] if chunks else -1.0,
        bool(auth_context),
    )

    return {
        "query": q,
        "k": k_out,
        "chunks": chunks,
        "latency_ms": latency_ms,
        "trace_id": trace_id,
    }


# ---------------------------------------------------------------------------
# Resources — expose full source documents by source_id. The consuming LLM
# can fetch these when chunk-level context isn't enough (the "retrieve_full_doc"
# escape valve described in demo-prep-raw.md).
# ---------------------------------------------------------------------------
@mcp.resource("document://{source_id}")
def get_document(source_id: str) -> dict:
    """Return the full raw content + metadata for a source document."""
    sql = """
        SELECT source_id, title, source_type, source_url, authority_tier,
               content_category, last_modified, raw_content
        FROM documents
        WHERE source_id = %s
    """
    with _get_conn().cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (source_id,))
        row = cur.fetchone()
    if not row:
        raise ValueError(f"document not found: {source_id}")
    d = dict(row)
    if d.get("last_modified"):
        d["last_modified"] = d["last_modified"].isoformat()
    return d


# ---------------------------------------------------------------------------
# Prompts — shipped templates so any MCP client gets citation-heavy answers
# for free. Most MCP servers skip this; exposing it is the Tools+Resources+
# Prompts differentiator from the "MCP isn't dead, you're using it wrong" thesis.
# ---------------------------------------------------------------------------
@mcp.prompt
def cite_from_chunks(user_question: str) -> str:
    """Answer the user's question using retrieved chunks with paragraph-level citations."""
    return (
        "You are answering a question over the VA Education corpus. Use the "
        "`query` tool to retrieve relevant chunks, then answer the user's "
        "question with the following rules:\n\n"
        "1. Cite every non-trivial claim using the format "
        "`[source_id > heading_path]` drawn from the retrieved chunks.\n"
        "2. If the retrieved chunks don't contain the answer, say so plainly "
        "— don't invent.\n"
        "3. Prefer direct quotes for regulatory or numeric content.\n"
        "4. If a chunk has `chunk_type: table`, preserve the table's structure "
        "in your answer.\n\n"
        f"User question: {user_question}"
    )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default=os.environ.get("IKB_MCP_TRANSPORT", "stdio"),
        help="stdio (local, Claude Desktop) or http (streamable HTTP for gateways)",
    )
    ap.add_argument("--host", default=os.environ.get("IKB_MCP_HOST", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("IKB_MCP_PORT", "8000")))
    args = ap.parse_args()

    log.info("OTel/Langfuse instrumentation: %s", "ENABLED" if _OTEL_ENABLED else "disabled (no LANGFUSE_* env vars)")
    if args.transport == "stdio":
        log.info("starting ikb MCP server on stdio")
        mcp.run()
    else:
        log.info("starting ikb MCP server on streamable HTTP %s:%d", args.host, args.port)
        mcp.run(transport="http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
