#!/usr/bin/env python3
"""Build the holdings table of contents from the published concordance.

    python toc/build_toc.py \\
        --concordance concordance/dist/concordance.jsonl.gz \\
        --out toc/dist

WHAT THIS IS, AND THE THING IT IS NOT
It is the full title -> chapter -> subchapter -> section tree of every provision
we hold, for all 52 jurisdictions and federal, as one greppable file. Somebody
asking "do you have Montana Title 10 Chapter 1" can answer it themselves, and
somebody asking "how much of the CFR" can count.

🔴 It proves HOLDINGS. It does not prove COMPLETENESS, and the difference is not
a quibble. Every row here is derived from our own corpus, so a gap in the corpus
is also a gap in this file: it cannot report what it never saw. Read as "here is
what exists", it is circular. Read as "here is what we hold, at this identifier,
from this source URL", it is checkable against the publisher by anyone who cares
to.

The artifact that closes that loop is a diff against each publisher's own table
of contents, which is a separate and much larger build. Until it exists, nothing
in this file should be described as proof of completeness.

WHY IT IS DERIVED FROM THE CONCORDANCE RATHER THAN THE CORPUS
The concordance is published, so this script reads only public data and anybody
can rebuild the tree and get the same answer. Reading the corpus directly would
make the TOC something only we can produce, which defeats the point of handing
it to a customer as evidence.

The hierarchy needs no reconstruction: it is already carried in the identifier.
`us1:mt/statutes/title-10/chapter-1/part-10/10-1-1001` names its own ancestors,
so the tree is a parse rather than a join, and the tree cannot disagree with the
identifiers because it is computed from them.

CONTAINER LABELS ARE LEFT NULL BY THIS PASS, DELIBERATELY
A container's slug is all the identifier carries. For named corpora that is
enough (`alaska-rules-of-court`), but statutes and regulations are 74% of the
leaves and their containers are bare numbers: `title-1/chapter-01.10`,
`agency-100/chapter-100-x-1`. "Title 1" is weaker evidence than
"Title 1 - General Provisions" for a reader checking whether their title is
covered.

Those labels live in the corpus payloads, not in the concordance, so filling
them needs a pass over the corpus. `label` is emitted as null here so that pass
is a FILL rather than a schema change, and so a consumer can tell "unlabelled"
from "labelled empty".
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any


def build(concordance: Path, out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)

    # path -> [leaf_count, set of direct children]. Held in memory because the
    # container tree is ~400k nodes against ~4.6M leaves: three orders of
    # magnitude smaller, and the leaves never need to be resident.
    leaf_count: dict[str, int] = defaultdict(int)
    children: dict[str, set[str]] = defaultdict(set)
    corpora: set[tuple[str, str]] = set()
    leaves = 0

    with gzip.open(concordance, "rt", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            body = record["law_id"].split(":", 1)[1]
            parts = body.split("/")
            if len(parts) < 3:
                continue
            jurisdiction, corpus, rest = parts[0], parts[1], parts[2:]
            corpora.add((jurisdiction, corpus))
            leaves += 1

            root = f"{jurisdiction}/{corpus}"
            # Credit the leaf to EVERY ancestor, not just its parent. A reader
            # asking "how much of Title 10 do you hold" means the whole subtree,
            # and a count that stopped at the immediate parent would answer a
            # question nobody asks.
            prefix = root
            for depth, slug in enumerate(rest[:-1]):
                parent = prefix
                prefix = f"{prefix}/{slug}"
                children[parent].add(prefix)
                leaf_count[prefix] += 1
            leaf_count[root] += 1
            children[root]  # touch, so a corpus with only leaves still appears

    containers = sorted(leaf_count)
    tmp = out_dir / f"toc.jsonl.gz.{os.getpid()}.tmp"
    written = 0
    with gzip.open(tmp, "wt", encoding="utf-8") as sink:
        for path in containers:
            parts = path.split("/")
            sink.write(
                json.dumps(
                    {
                        "kind": "container",
                        "path": path,
                        "jurisdiction": parts[0],
                        "corpus": parts[1],
                        "slug": parts[-1],
                        "depth": len(parts) - 2,
                        "parent": "/".join(parts[:-1]) if len(parts) > 2 else None,
                        # Filled by the corpus pass; see the module docstring.
                        "label": None,
                        "sections_held": leaf_count[path],
                        "children": len(children.get(path, ())),
                    },
                    sort_keys=True,
                )
                + "\n"
            )
            written += 1

        with gzip.open(concordance, "rt", encoding="utf-8") as handle:
            for line in handle:
                record = json.loads(line)
                body = record["law_id"].split(":", 1)[1]
                parts = body.split("/")
                if len(parts) < 3:
                    continue
                sink.write(
                    json.dumps(
                        {
                            "kind": "section",
                            "law_id": record["law_id"],
                            "parent": "/".join(parts[:-1]),
                            "citation": record.get("citation"),
                            "heading": record.get("heading"),
                            "status": record.get("status"),
                            "source_url": record.get("source_url"),
                        },
                        sort_keys=True,
                    )
                    + "\n"
                )
                written += 1
    os.replace(tmp, out_dir / "toc.jsonl.gz")

    by_corpus: dict[str, dict[str, int]] = defaultdict(dict)
    for jurisdiction, corpus in sorted(corpora):
        root = f"{jurisdiction}/{corpus}"
        by_corpus[jurisdiction][corpus] = leaf_count[root]

    manifest = {
        "rows": written,
        "sections": leaves,
        "containers": len(containers),
        "jurisdictions": len({j for j, _ in corpora}),
        "proves": "holdings",
        "does_not_prove": (
            "completeness: every row is derived from our own corpus, so a gap in "
            "the corpus is also a gap here. Diffing against each publisher's own "
            "table of contents is a separate artifact."
        ),
        "labels_filled": False,
        "by_jurisdiction": dict(by_corpus),
    }
    (out_dir / "toc-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True)
    )
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--concordance",
        type=Path,
        default=Path("concordance/dist/concordance.jsonl.gz"),
    )
    ap.add_argument("--out", type=Path, default=Path("toc/dist"))
    args = ap.parse_args()

    if not args.concordance.exists():
        raise SystemExit(
            f"{args.concordance} not found; build or download the concordance first."
        )

    manifest = build(args.concordance, args.out)
    print(f"  sections     {manifest['sections']:>12,}")
    print(f"  containers   {manifest['containers']:>12,}")
    print(f"  TOTAL rows   {manifest['rows']:>12,}")
    print(f"  jurisdictions{manifest['jurisdictions']:>12,}")
    print(f"\n  -> {args.out}/toc.jsonl.gz")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
