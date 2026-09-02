#!/usr/bin/env python3
"""Build the resolver index from the published concordance.

    python resolver/build_index.py \\
        --concordance concordance/dist/concordance.jsonl.gz \\
        --out resolver/dist/resolver.sqlite

Reads the CC0 concordance and nothing else. It does not touch Qdrant, and it
holds no credential, which is the point: anybody who downloads the concordance
can build a byte-identical index and run their own resolver. "Run your own"
should be a download, not a deployment.

ONE FILE, AND WHY
SQLite rather than a search engine. The index is ~4 million rows, it is
read-only, and every query is an equality lookup on a key. A server would add
an operational dependency to something whose whole promise is free, unmetered
and permanent resolution.

THE INDEX IS BUILT ATOMICALLY
Written to a temporary path and moved into place, so a reader always sees either
the whole previous index or the whole new one. The concordance builder learned
this the hard way: a run that was killed left a valid gzip member followed by
124,314 bytes of an older file, which `gzip -t` reported and Python refused.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from vqresolve import citation_key

_SCHEMA = """
CREATE TABLE identifier (
    vq           TEXT PRIMARY KEY,
    jurisdiction TEXT NOT NULL,
    corpus       TEXT NOT NULL,
    citation     TEXT,
    cite_key     TEXT,
    heading      TEXT,
    status       TEXT,
    source_url   TEXT
) WITHOUT ROWID;
"""

#: Built AFTER the insert, not before. Building an index while writing 4M rows
#: costs more than building it once at the end over sorted data.
_INDEXES = """
CREATE INDEX idx_cite_key ON identifier(cite_key);
CREATE INDEX idx_jurisdiction ON identifier(jurisdiction, corpus);
"""


def rows(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            citation = record.get("citation")
            yield (
                record["vq"],
                record["jurisdiction"],
                record["corpus"],
                citation,
                citation_key(citation) if citation else None,
                record.get("heading"),
                record.get("status"),
                record.get("source_url"),
            )


def build(concordance: Path, out: Path) -> dict[str, int]:
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(f"{out.name}.{os.getpid()}.tmp")
    tmp.unlink(missing_ok=True)

    db = sqlite3.connect(tmp)
    # Durability is irrelevant for a rebuildable artifact, and turning it off is
    # the difference between minutes and an hour on 4M inserts.
    db.executescript("PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;")
    db.executescript(_SCHEMA)
    written = 0
    batch: list[tuple] = []
    for row in rows(concordance):
        batch.append(row)
        if len(batch) >= 50_000:
            db.executemany("INSERT OR REPLACE INTO identifier VALUES (?,?,?,?,?,?,?,?)", batch)
            written += len(batch)
            batch.clear()
            print(f"  {written:,} rows", flush=True)
    if batch:
        db.executemany("INSERT OR REPLACE INTO identifier VALUES (?,?,?,?,?,?,?,?)", batch)
        written += len(batch)
    db.executescript(_INDEXES)
    db.commit()
    counted = db.execute(
        "SELECT COUNT(*), COUNT(source_url), COUNT(DISTINCT cite_key),"
        " COUNT(DISTINCT jurisdiction) FROM identifier"
    ).fetchone()
    stats = dict(
        zip(
            ("rows", "with_official_url", "distinct_citations", "jurisdictions"),
            counted,
            strict=True,
        )
    )
    db.execute("VACUUM")
    db.close()
    os.replace(tmp, out)
    stats["bytes"] = out.stat().st_size
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--concordance",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "concordance/dist/concordance.jsonl.gz",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent / "dist/resolver.sqlite",
    )
    args = ap.parse_args()
    if not args.concordance.exists():
        raise SystemExit(f"{args.concordance} not found. Build the concordance first.")
    stats = build(args.concordance, args.out)
    print()
    for key, value in stats.items():
        print(f"  {key:20} {value:>14,}")
    print(f"\nindex: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
