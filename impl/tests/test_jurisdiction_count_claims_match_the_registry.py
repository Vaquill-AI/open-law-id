"""A published "N jurisdictions" claim must agree with the registry.

The README and the specification both said "all 51 jurisdictions" while
`registry/jurisdictions.json` held 53 and `registry/README.md` correctly said
53. Nothing was broken by it, which is exactly why it survived: a wrong count in
prose fails no build, and the two documents a reader meets first were the two
that were wrong.

The registry is the source of truth, so this derives the number rather than
restating it. Adding a jurisdiction updates one JSON file and this test starts
failing everywhere the old number is written down, which is the point.

THE PREFERRED FIX IS TO ENUMERATE, NOT TO CORRECT
"the 50 states, DC, Puerto Rico and the federal government" cannot drift into a
wrong number, and it tells the reader what is actually covered. A bare count
only tells them how many. Both pass here; only one stays true by construction.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]

#: Every document a reader meets before the registry itself.
_DOCS = ["README.md", "spec/SPEC-v0.1.md", "GOVERNANCE.md", "registry/README.md"]

#: "51 jurisdictions", "all 53 jurisdictions", "52 jurisdiction codes".
_CLAIM = re.compile(r"\b(\d{2})\s+jurisdiction", re.I)


def _registry_count() -> int:
    data = json.loads((_ROOT / "registry" / "jurisdictions.json").read_text())
    return len(data["jurisdictions"])


def test_the_registry_covers_every_state_plus_dc_pr_and_federal():
    """Pins the shape the prose enumerates, so the enumeration cannot go stale."""
    codes = {
        j["code"] for j in json.loads((_ROOT / "registry" / "jurisdictions.json").read_text())["jurisdictions"]
    }
    assert {"federal", "dc", "pr"} <= codes, "expected federal, DC and Puerto Rico in the registry"
    assert len(codes - {"federal", "dc", "pr"}) == 50, "expected exactly 50 states beside them"


def test_no_published_document_states_a_jurisdiction_count_the_registry_denies():
    expected = _registry_count()
    offenders: list[str] = []
    for name in _DOCS:
        path = _ROOT / name
        if not path.exists():
            continue
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            for claimed in _CLAIM.findall(line):
                if int(claimed) != expected:
                    offenders.append(f"{name}:{lineno} claims {claimed}: {line.strip()}")
    assert not offenders, (
        f"the registry holds {expected} jurisdictions, but these say otherwise. "
        "Prefer enumerating (the 50 states, DC, Puerto Rico and the federal "
        "government) over restating a count:\n  " + "\n  ".join(offenders)
    )
