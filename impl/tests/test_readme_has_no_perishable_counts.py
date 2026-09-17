"""The README must not state a count that goes stale.

The corpus grows continuously. This repository published "4,039,901 provisions"
and the corpus grew by more than half within two weeks, so the front page of a
standard was advertising a number that was wrong almost immediately and that
nobody would think to re-check.

The rule is about WHERE a number lives, not whether precision is good:

  * a LIVE CLAIM ("we hold N provisions") belongs in the release notes and the
    manifest that ships beside each artifact, which are versioned and dated;
  * a DATED MEASUREMENT ("measured 2026-09-03, shape D left 101 collisions") is
    evidence for a design decision, is true forever about that moment, and
    belongs in the specification with its date attached.

So this guards the README only, and it asks for a date rather than banning
digits.
"""

from __future__ import annotations

import re
from pathlib import Path

_README = Path(__file__).resolve().parents[2] / "README.md"

#: Any number with two or more thousands separators: 1,000,000 and up.
_BIG = re.compile(r"\b\d{1,3}(?:,\d{3}){2,}\b")


def test_the_readme_states_no_bare_perishable_count():
    offenders = [
        line.strip()
        for line in _README.read_text().splitlines()
        if _BIG.search(line) and not re.search(r"measured\s+\d{4}-\d{2}-\d{2}", line, re.I)
    ]
    assert not offenders, (
        "the README states a count that will go stale. Move it to the release "
        "notes, or attach the date it was measured:\n  " + "\n  ".join(offenders)
    )
