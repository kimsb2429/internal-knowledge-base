#!/usr/bin/env python3
"""Mark a Langfuse trace as public so it can be viewed without login.

Usage:
    python -m scripts.make_trace_public <trace_id>

The trace ID is the 32-char hex OTel trace ID (logged by the MCP server as
`otel_trace_id=...`). The public URL shape is:

    {LANGFUSE_BASE_URL}/project/{LANGFUSE_PROJECT_ID}/traces/{trace_id}

We go through the ingestion API rather than setting the `langfuse.trace.public`
OTel attribute because FastMCP's wrapper span is the true OTel root; our
tool function's span is a child, and Langfuse only promotes trace-level
attributes from the root span.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.request
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()


def make_public(trace_id: str) -> None:
    pk = os.environ["LANGFUSE_PUBLIC_KEY"]
    sk = os.environ["LANGFUSE_SECRET_KEY"]
    host = (
        os.environ.get("LANGFUSE_BASE_URL")
        or os.environ.get("LANGFUSE_HOST")
        or "https://cloud.langfuse.com"
    ).rstrip("/")

    auth = base64.b64encode(f"{pk}:{sk}".encode()).decode()
    payload = {
        "batch": [{
            "id": str(uuid.uuid4()),
            "type": "trace-create",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "body": {"id": trace_id, "public": True},
        }]
    }
    req = urllib.request.Request(
        f"{host}/api/public/ingestion",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        print(f"HTTP {resp.status} — {resp.read().decode()[:300]}")

    project_id = os.environ.get("LANGFUSE_PROJECT_ID", "<project-id>")
    print(f"public URL: {host}/project/{project_id}/traces/{trace_id}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("trace_id", help="32-char hex OTel trace ID")
    args = ap.parse_args()
    make_public(args.trace_id)
