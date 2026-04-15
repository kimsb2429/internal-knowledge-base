#!/usr/bin/env python3
"""
Generate per-chunk context prefixes via Anthropic's Message Batches API.

Implements Anthropic's Contextual Retrieval pattern: for each chunk, prepend
a 50-100 token LLM-generated context that situates the chunk in its parent
document. The contextualized text is what we embed (improving retrieval).
The original `content` field is preserved unchanged for generation.

Why batch instead of live API:
  - 50% discount on input + output tokens
  - No per-request rate limits (live mode caps at ~0.9 chunks/s for Haiku)
  - Prompt caching still works — each document's full text cached, reused
    across all chunks in that doc

Lifecycle:
  1. Build per-chunk requests (chunks from the same doc grouped contiguously
     so prompt caching has hot cache reads)
  2. Submit one batch (up to 100K requests / 256MB)
  3. Poll until processing_status == "ended"
  4. Stream results, write all_chunks_contextualized.json

Resume-safe: --resume reads existing output, only enqueues missing chunks.

Usage:
    .venv/bin/python scripts/contextualize_chunks.py                # submit + wait
    .venv/bin/python scripts/contextualize_chunks.py --limit-docs 5 # subset
    .venv/bin/python scripts/contextualize_chunks.py --submit-only  # submit, exit
    .venv/bin/python scripts/contextualize_chunks.py --batch-id ID  # poll an existing batch
"""

import argparse
import json
import os
import sys
import time

from dotenv import load_dotenv

load_dotenv(".env")

import anthropic

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "knowva_manuals", "chunks")
IN_PATH = os.path.join(DATA_DIR, "all_chunks.json")
OUT_PATH = os.path.join(DATA_DIR, "all_chunks_contextualized.json")
BATCH_STATE_PATH = os.path.join(DATA_DIR, "contextualize_batch_state.json")

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 150  # context is supposed to be 50-100 tokens
MAX_DOC_CHARS = 30000  # cap document text passed to Haiku as context base

POLL_INTERVAL_SECONDS = 30

SYSTEM_INSTRUCTIONS = (
    "You produce succinct retrieval-friendly context strings for document chunks. "
    "Given the full document and a specific chunk, return a 1-2 sentence context "
    "(50-100 tokens) that situates this chunk within the document — mentioning the "
    "specific topic, parent section, entity types, and any policy/chapter/section "
    "identifiers that would help a search query match this chunk. Answer with the "
    "context only — no preamble, no quotes."
)


def build_doc_text(chunks_for_source: list[dict]) -> str:
    title = (chunks_for_source[0].get("source_metadata") or {}).get("title", "")
    body = "\n\n".join(c["content"] for c in chunks_for_source)
    if title:
        body = f"{title}\n\n{body}"
    return body[:MAX_DOC_CHARS]


import re

# Anthropic custom_id constraint: ^[a-zA-Z0-9_-]{1,64}$
# Strip anything else; also collapse repeats. Keep a reversible map.
_SID_TO_TOKEN: dict[str, str] = {}
_TOKEN_TO_SID: dict[str, str] = {}


def _sid_token(source_id: str) -> str:
    if source_id in _SID_TO_TOKEN:
        return _SID_TO_TOKEN[source_id]
    safe = re.sub(r"[^a-zA-Z0-9]+", "_", source_id).strip("_")
    # Reserve room for "__<chunk_index up to ~6 digits>" so the full id ≤ 64
    safe = safe[:50]
    # Ensure uniqueness if truncation collides
    base = safe
    n = 1
    while safe in _TOKEN_TO_SID and _TOKEN_TO_SID[safe] != source_id:
        safe = f"{base}_{n}"[:50]
        n += 1
    _SID_TO_TOKEN[source_id] = safe
    _TOKEN_TO_SID[safe] = source_id
    return safe


def custom_id(source_id: str, chunk_index: int) -> str:
    cid = f"{_sid_token(source_id)}__{chunk_index}"
    assert len(cid) <= 64 and re.fullmatch(r"[a-zA-Z0-9_-]+", cid), cid
    return cid


def parse_custom_id(cid: str) -> tuple[str, int]:
    token, ci = cid.rsplit("__", 1)
    return _TOKEN_TO_SID.get(token, token), int(ci)


def build_request(source_id: str, chunk: dict, doc_text: str) -> dict:
    heading = " > ".join(chunk.get("heading_path") or [])
    return {
        "custom_id": custom_id(source_id, chunk["chunk_index"]),
        "params": {
            "model": MODEL,
            "max_tokens": MAX_TOKENS,
            "temperature": 0.0,
            "system": SYSTEM_INSTRUCTIONS,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"<document>\n{doc_text}\n</document>",
                            "cache_control": {"type": "ephemeral"},
                        },
                        {
                            "type": "text",
                            "text": (
                                f"Here is a chunk from the document above. "
                                f"Heading path: {heading}\n\n<chunk>\n{chunk['content']}\n</chunk>\n\n"
                                "Give a 1-2 sentence context (50-100 tokens) that situates this chunk "
                                "within the overall document, explicitly naming the subject matter, "
                                "policy/section identifiers, and entity types. Answer with the context only."
                            ),
                        },
                    ],
                }
            ],
        },
    }


def load_existing_contexts() -> dict[tuple[str, int], str]:
    if not os.path.exists(OUT_PATH):
        return {}
    with open(OUT_PATH) as f:
        prior = json.load(f)
    out = {}
    for c in prior:
        if c.get("context"):
            out[(c["source_id"], c["chunk_index"])] = c["context"]
    return out


def submit_batch(args, client: anthropic.Anthropic) -> str:
    with open(IN_PATH) as f:
        chunks = json.load(f)
    print(f"Loaded {len(chunks)} chunks")

    prior = load_existing_contexts() if args.resume else {}
    if prior:
        print(f"Resume: skipping {len(prior)} chunks already contextualized")

    by_source: dict[str, list[dict]] = {}
    for c in chunks:
        by_source.setdefault(c["source_id"], []).append(c)
    source_ids = list(by_source.keys())
    if args.limit_docs:
        source_ids = source_ids[: args.limit_docs]

    requests: list[dict] = []
    for sid in source_ids:
        src_chunks = by_source[sid]
        doc_text = build_doc_text(src_chunks)
        for chunk in src_chunks:
            key = (sid, chunk["chunk_index"])
            if key in prior:
                continue
            requests.append(build_request(sid, chunk, doc_text))

    print(f"Submitting batch with {len(requests)} requests across {len(source_ids)} docs...")
    if not requests:
        print("Nothing to submit. Exiting.")
        sys.exit(0)

    batch = client.messages.batches.create(requests=requests)
    state = {
        "batch_id": batch.id,
        "submitted_at": time.time(),
        "n_requests": len(requests),
        "source_ids": source_ids,
        "limit_docs": args.limit_docs,
        "sid_token_map": dict(_SID_TO_TOKEN),  # persist for --batch-id resume
    }
    with open(BATCH_STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)
    print(f"Submitted batch_id={batch.id}  status={batch.processing_status}")
    print(f"State saved to {BATCH_STATE_PATH}")
    return batch.id


def poll_batch(client: anthropic.Anthropic, batch_id: str) -> "anthropic.types.messages.MessageBatch":
    print(f"Polling batch {batch_id} every {POLL_INTERVAL_SECONDS}s...")
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        counts = batch.request_counts
        total = counts.processing + counts.succeeded + counts.errored + counts.canceled + counts.expired
        pct = 100 * (counts.succeeded + counts.errored + counts.canceled + counts.expired) / max(total, 1)
        print(
            f"  status={batch.processing_status}  "
            f"processing={counts.processing}  ok={counts.succeeded}  "
            f"err={counts.errored}  cancel={counts.canceled}  exp={counts.expired}  "
            f"({pct:.0f}%)"
        )
        if batch.processing_status == "ended":
            return batch
        time.sleep(POLL_INTERVAL_SECONDS)


def collect_results(client: anthropic.Anthropic, batch_id: str):
    """Return mapping custom_id -> (context_text, error_or_None, usage)."""
    out = {}
    for entry in client.messages.batches.results(batch_id):
        cid = entry.custom_id
        if entry.result.type == "succeeded":
            msg = entry.result.message
            text = "".join(b.text for b in msg.content if b.type == "text").strip()
            usage = {
                "input_tokens": msg.usage.input_tokens,
                "output_tokens": msg.usage.output_tokens,
                "cache_creation_input_tokens": getattr(msg.usage, "cache_creation_input_tokens", 0) or 0,
                "cache_read_input_tokens": getattr(msg.usage, "cache_read_input_tokens", 0) or 0,
            }
            out[cid] = (text, None, usage)
        else:
            err_type = entry.result.type
            err_detail = getattr(entry.result, "error", None)
            out[cid] = (None, f"{err_type}: {err_detail}", None)
    return out


def write_output(by_source: dict[str, list[dict]], contexts: dict[tuple[str, int], str]):
    """Write all_chunks_contextualized.json preserving original chunk order."""
    out_chunks = []
    for sid, src_chunks in by_source.items():
        for c in src_chunks:
            ctx = contexts.get((sid, c["chunk_index"]), "")
            out_chunks.append({**c, "context": ctx})
    with open(OUT_PATH, "w") as f:
        json.dump(out_chunks, f)
    print(f"Wrote {len(out_chunks)} chunks to {OUT_PATH}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-docs", type=int, help="Only process first N docs")
    ap.add_argument("--resume", action="store_true", default=True,
                    help="Skip chunks already in OUT_PATH (default)")
    ap.add_argument("--no-resume", action="store_false", dest="resume")
    ap.add_argument("--submit-only", action="store_true",
                    help="Submit batch and exit (don't poll)")
    ap.add_argument("--batch-id", help="Skip submit; poll & collect this existing batch")
    args = ap.parse_args()

    client = anthropic.Anthropic()

    if args.batch_id:
        batch_id = args.batch_id
        # Restore sid token map if we have it from prior submit
        if os.path.exists(BATCH_STATE_PATH):
            with open(BATCH_STATE_PATH) as f:
                st = json.load(f)
            for sid, tok in (st.get("sid_token_map") or {}).items():
                _SID_TO_TOKEN[sid] = tok
                _TOKEN_TO_SID[tok] = sid
    else:
        batch_id = submit_batch(args, client)
        if args.submit_only:
            print(f"\nTo poll later: .venv/bin/python scripts/contextualize_chunks.py --batch-id {batch_id}")
            return

    batch = poll_batch(client, batch_id)
    print(f"\nBatch ended. Final status: {batch.processing_status}")
    print(f"Results URL: {batch.results_url}")

    print("\nDownloading results...")
    new_contexts = collect_results(client, batch_id)
    n_ok = sum(1 for v in new_contexts.values() if v[1] is None)
    n_err = len(new_contexts) - n_ok
    print(f"  {n_ok} succeeded, {n_err} errored")

    # Aggregate usage from successful results
    totals = {"input_tokens": 0, "output_tokens": 0,
              "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
    for cid, (_, err, usage) in new_contexts.items():
        if usage:
            for k in totals:
                totals[k] += usage[k]

    # Merge with prior + write output
    with open(IN_PATH) as f:
        chunks = json.load(f)
    by_source: dict[str, list[dict]] = {}
    for c in chunks:
        by_source.setdefault(c["source_id"], []).append(c)

    contexts = load_existing_contexts()  # preserve prior runs
    for cid, (text, err, _) in new_contexts.items():
        if text is not None:
            sid, ci = parse_custom_id(cid)
            contexts[(sid, ci)] = text
    write_output(by_source, contexts)

    # Cost calc — Haiku 4.5 BATCH pricing: 50% off across the board
    # Standard: $1/M in, $5/M out, $1.25/M cache write, $0.10/M cache read
    cost = (
        totals["input_tokens"]                * 0.5  / 1_000_000
        + totals["output_tokens"]             * 2.5  / 1_000_000
        + totals["cache_creation_input_tokens"] * 0.625 / 1_000_000
        + totals["cache_read_input_tokens"]   * 0.05 / 1_000_000
    )
    print("\n" + "=" * 60)
    print(f"Successful contexts:     {n_ok}")
    print(f"Errored requests:        {n_err}")
    print(f"Input tokens:            {totals['input_tokens']:,}")
    print(f"Output tokens:           {totals['output_tokens']:,}")
    print(f"Cache creation:          {totals['cache_creation_input_tokens']:,}")
    print(f"Cache reads:             {totals['cache_read_input_tokens']:,}")
    print(f"Estimated cost (batch):  ${cost:.3f}")


if __name__ == "__main__":
    main()
