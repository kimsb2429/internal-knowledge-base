#!/usr/bin/env python3
"""
RAG generation step: query + retrieved chunks → grounded answer.

Used by the Step 9 eval harness. Separation of concerns: retrieval lives in
retrieve.py; this module only handles context formatting + the Claude call.

Usage:
    from scripts.generate import generate
    from scripts.retrieve import retrieve

    chunks = retrieve("What RPO handles GI Bill claims in Texas?", k=5)
    result = generate("What RPO handles GI Bill claims in Texas?", chunks)
    print(result["answer"])

    # CLI — retrieves + generates in one shot:
    python3 scripts/generate.py "your query" --k 5
"""

import argparse
import os
import sys

from dotenv import load_dotenv

load_dotenv()

import anthropic

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1024
TEMPERATURE = 0.0

SYSTEM_PROMPT = """You are a VA Education Service knowledge assistant answering questions from an internal corpus (M22-3, M22-4, VADIR ICD).

Ground rules:
- Answer ONLY using the provided Context chunks. Do not rely on outside knowledge.
- If the Context does not contain the answer, respond exactly: "I don't know based on the provided context."
- Cite the chunk numbers you used, in brackets, e.g. [1], [2].
- Be concise. Prefer the exact policy language from the chunks when quoting figures, codes, or thresholds.
"""

_CLIENT = None


def _get_client() -> anthropic.Anthropic:
    global _CLIENT
    if _CLIENT is None:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY not set (expected in .env or env)")
        _CLIENT = anthropic.Anthropic()
    return _CLIENT


def _format_chunk(idx: int, chunk: dict) -> str:
    heading = " > ".join(chunk.get("heading_path") or [])
    title = chunk.get("title") or ""
    source = chunk.get("source_id") or ""
    header = f"[Chunk {idx}]\nSource: {source} — {title}\nHeading: {heading}"
    return f"{header}\n\n{chunk['content']}"


def build_context_strings(chunks: list[dict]) -> list[str]:
    return [_format_chunk(i + 1, c) for i, c in enumerate(chunks)]


def generate(query: str, chunks: list[dict]) -> dict:
    context_strings = build_context_strings(chunks)
    context_block = "\n\n---\n\n".join(context_strings)
    user_message = f"Context:\n\n{context_block}\n\nQuestion: {query}"

    response = _get_client().messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    answer = "".join(block.text for block in response.content if block.type == "text")

    return {
        "query": query,
        "answer": answer,
        "retrieved_chunks": chunks,
        "context_strings": context_strings,
        "model": MODEL,
        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--k", type=int, default=5)
    args = ap.parse_args()

    from scripts.retrieve import retrieve

    chunks = retrieve(args.query, k=args.k)
    result = generate(args.query, chunks)

    print("=" * 70)
    print(f"QUERY: {args.query}")
    print("=" * 70)
    print(f"\nRetrieved {len(chunks)} chunks:")
    for i, c in enumerate(chunks, 1):
        print(f"  [{i}] score={c['score']:.3f}  {c['source_id']} — {' > '.join(c['heading_path'] or [])}")
    print(f"\nANSWER ({result['model']}):")
    print(result["answer"])
    print(f"\nUsage: {result['usage']}")


if __name__ == "__main__":
    main()
