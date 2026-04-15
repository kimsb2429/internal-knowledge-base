#!/usr/bin/env python3
"""
Structural audit of the golden query set.

Checks per query (independent of retrieval/generation performance):
  A) Every expected source_article_id exists in the corpus
  B) Distinctive terms from the expected answer appear in the expected
     source article's content (answerability check)
  C) Same distinctive terms appear in OTHER articles too (candidate
     expansion for expected_source_ids)

Output: data/golden_set_audit.json and a console summary.

Usage:
    python3 scripts/audit_golden_set.py
"""

import json
import os
import re
from collections import Counter

import psycopg2

DB_URL = os.environ.get("IKB_DB_URL", "postgresql://ikb:ikb_local@localhost:5433/ikb")
GOLDEN_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "golden_query_set.json")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "golden_set_audit.json")

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "for", "with", "from", "to", "of", "in",
    "on", "at", "by", "as", "is", "are", "was", "were", "be", "been", "being",
    "has", "have", "had", "do", "does", "did", "will", "would", "should", "could",
    "can", "may", "might", "must", "this", "that", "these", "those", "it", "its",
    "i", "we", "you", "he", "she", "they", "them", "their", "his", "her", "not",
    "no", "yes", "if", "then", "else", "so", "than", "also", "only", "just", "very",
    "any", "some", "all", "each", "every", "few", "more", "most", "such", "other",
    "which", "who", "whom", "whose", "what", "when", "where", "why", "how",
    "per", "into", "out", "up", "down", "off", "over", "under", "above", "below",
    "between", "through", "during", "before", "after", "about", "against", "within",
    "without", "upon", "based", "provided", "effective", "applicable", "general",
}


QUESTION_WORDS = {"what", "when", "where", "why", "how", "who", "which", "does", "do", "is",
                  "are", "can", "could", "should", "would", "will", "did", "has", "have"}


def extract_distinctive_query_terms(query: str) -> list[str]:
    """Pull distinctive subject nouns from the query itself.

    These are the strongest answerability signal: if the source article
    doesn't even mention the query's subject, the query can't be answered
    from that source. Drops question words, stopwords, and generic verbs.
    """
    if not query:
        return []
    # Same patterns as answer extraction, but seeded from the question
    tokens = re.findall(
        r"\$[\d,]+(?:\.\d+)?|"
        r"\d+\s*%|"
        r"[A-Z]{2,}(?:-\d+)?|"
        r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|"
        r"\b[a-z]{5,}\b|"
        r"\b\d+\b",
        query,
    )
    terms = []
    seen = set()
    for t in tokens:
        tl = t.lower().strip()
        if not tl or tl in STOPWORDS or tl in QUESTION_WORDS:
            continue
        # Filter common verbs / function words specific to questions
        if tl in {"chapter", "chapters", "course", "courses", "service", "services",
                  "veteran", "veterans", "benefit", "benefits", "claim", "claims",
                  "system", "data", "field", "operation", "operations", "code", "codes"}:
            # keep these only if no more-distinctive term exists; tag for now
            continue
        if tl in seen:
            continue
        seen.add(tl)
        terms.append(t)
    return terms


def extract_key_terms(text: str) -> list[str]:
    """Pull distinctive tokens from answer text.

    Keeps: capitalized words/acronyms, numbers/dates/dollar amounts, and
    long-ish lowercase domain words. Drops stopwords and tiny fragments.
    """
    if not text:
        return []
    # Token patterns: proper nouns / acronyms, dollar amounts, dates, numbers, regular words
    tokens = re.findall(
        r"\$[\d,]+(?:\.\d+)?|"                            # $45,000
        r"\d+\s*%|"                                       # 80%
        r"\d{4}[-/]\d{1,2}[-/]\d{1,2}|"                   # 2020-08-01
        r"\b\d{1,2}/\d{1,2}/\d{2,4}\b|"                   # 8/1/2020
        r"[A-Z]{2,}(?:-\d+)?|"                            # M22-4, RPO, BAH
        r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|"                # Muskogee, August, Post-9/11
        r"\b[a-z]{5,}\b|"                                 # 5+ char lowercase words
        r"\b\d+\b",                                       # bare numbers
        text,
    )
    terms = []
    seen = set()
    for t in tokens:
        tl = t.lower().strip()
        if not tl or tl in STOPWORDS:
            continue
        if tl in seen:
            continue
        seen.add(tl)
        terms.append(t)
    return terms


def term_present(term: str, text: str) -> bool:
    return term.lower() in text.lower()


def main():
    with open(GOLDEN_PATH) as f:
        queries = json.load(f)["queries"]

    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    # Build a map: source_id -> full raw_content
    cur.execute("SELECT source_id, title, raw_content FROM documents")
    docs = {row[0]: {"title": row[1], "content": row[2]} for row in cur.fetchall()}

    print(f"Auditing {len(queries)} queries against {len(docs)} documents...")
    print()

    issues = []
    stats = Counter()

    for q in queries:
        qid = q["id"]
        expected_ids = []
        if "source_article_id" in q:
            expected_ids.append(str(q["source_article_id"]))
        for alt in q.get("source_article_id_alt", []) or []:
            expected_ids.append(str(alt))
        has_source_id = bool(expected_ids)

        expected_answer = q.get("answer", "")
        key_terms = extract_key_terms(expected_answer)[:10]
        query_subject_terms = extract_distinctive_query_terms(q["query"])[:8]

        record = {
            "id": qid,
            "query": q["query"],
            "query_type": q.get("query_type"),
            "expected_source_ids": expected_ids,
            "key_terms": key_terms,
            "query_subject_terms": query_subject_terms,
            "checks": {},
        }

        # Check A: expected source exists
        if has_source_id:
            missing = [sid for sid in expected_ids if sid not in docs]
            record["checks"]["expected_source_missing"] = missing
            if missing:
                stats["missing_source"] += 1
        else:
            record["checks"]["no_source_id_specified"] = True
            stats["no_source_id"] += 1

        # Check B: answerability — distinctive query subject terms must appear in source
        if has_source_id and expected_ids and expected_ids[0] in docs:
            src_content = docs[expected_ids[0]]["content"]
            # Subject-term check (the strict one)
            subj_found = [t for t in query_subject_terms if term_present(t, src_content)]
            subj_missing = [t for t in query_subject_terms if not term_present(t, src_content)]
            subj_hit = len(subj_found) / len(query_subject_terms) if query_subject_terms else None
            # Answer-term check (corroborating)
            ans_found = [t for t in key_terms if term_present(t, src_content)]
            ans_missing = [t for t in key_terms if not term_present(t, src_content)]
            ans_hit = len(ans_found) / len(key_terms) if key_terms else None

            record["checks"]["query_subject_in_source"] = {
                "total": len(query_subject_terms),
                "found": len(subj_found),
                "missing": subj_missing,
                "hit_rate": round(subj_hit, 2) if subj_hit is not None else None,
            }
            record["checks"]["answer_terms_in_source"] = {
                "total": len(key_terms),
                "found": len(ans_found),
                "missing": ans_missing,
                "hit_rate": round(ans_hit, 2) if ans_hit is not None else None,
            }
            # Flag if any distinctive query subject term is missing from the source
            if query_subject_terms and subj_missing:
                stats["query_subject_missing_in_source"] += 1
                record["checks"]["FLAG_subject_missing"] = True

        # Check C: are other articles equally on-topic? (suggests expansion)
        if key_terms:
            term_doc_hits = {}
            # Use a subset of distinctive terms (dollars, percents, proper nouns)
            distinctive = [t for t in key_terms if re.match(r"^[\$A-Z\d]", t) or len(t) > 7]
            distinctive = distinctive[:5]
            for sid, d in docs.items():
                hits = sum(1 for t in distinctive if term_present(t, d["content"]))
                if hits >= max(2, len(distinctive) - 1):  # almost all distinctive terms present
                    term_doc_hits[sid] = hits
            # Rank; exclude the expected source itself
            alts = sorted(
                [(sid, h) for sid, h in term_doc_hits.items() if sid not in expected_ids],
                key=lambda x: -x[1],
            )[:5]
            record["checks"]["alternate_candidate_sources"] = [
                {"source_id": sid, "title": docs[sid]["title"], "term_hits": h} for sid, h in alts
            ]
            if alts and len(alts) >= 1:
                # Only flag as candidate expansion if alt has as many hits as expected source would
                stats["has_alternate_candidates"] += 1

        issues.append(record)

    # Write detailed audit
    with open(OUT_PATH, "w") as f:
        json.dump({"stats": dict(stats), "records": issues}, f, indent=2)

    # Console summary
    print("=" * 70)
    print("STRUCTURAL AUDIT SUMMARY")
    print("=" * 70)
    print(f"  Total queries:                       {len(queries)}")
    print(f"  Missing expected source ID in DB:    {stats['missing_source']}")
    print(f"  No source_id specified (multi-doc):  {stats['no_source_id']}")
    print(f"  Query subject term missing in src:   {stats['query_subject_missing_in_source']}")
    print(f"  Has alternate candidate sources:     {stats['has_alternate_candidates']}")
    print()
    print("FLAGGED — query subject term missing from expected source:")
    for r in issues:
        if r["checks"].get("FLAG_subject_missing"):
            qsi = r["checks"]["query_subject_in_source"]
            print(f"  id={r['id']:>3}  src={r['expected_source_ids']}  subj_hit={qsi['hit_rate']:.2f}")
            print(f"    Q: {r['query'][:110]}")
            print(f"    missing subject terms: {qsi['missing']}")
            print()
    print(f"Full audit written to {OUT_PATH}")


if __name__ == "__main__":
    main()
