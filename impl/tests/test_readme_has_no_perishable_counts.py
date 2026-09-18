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

_ROOT = Path(__file__).resolve().parents[2]

#: Any number with two or more thousands separators: 1,000,000 and up.
_BIG = re.compile(r"\b\d{1,3}(?:,\d{3}){2,}\b")

#: What makes a count safe is a DATE, not a particular verb.
#:
#: This first looked only for the word "measured", and immediately misjudged a
#: real line: registry/README.md says the tables were "derived on 2026-08-31 by
#: enumerating a live 4,093,000-document corpus". That count never goes stale,
#: because it is a claim about what was true on a stated day, which is exactly
#: the distinction this guard exists to draw. Matching the date rather than the
#: vocabulary keeps the rule about the property that matters.
_DATED = re.compile(r"\d{4}-\d{2}-\d{2}")


def _readmes() -> list[Path]:
    """Every README a reader meets, not just the front page.

    This guarded the root README alone, and the gap showed up the first time it
    mattered: `toc/README.md` was written opening on "4,987,018 rows:
    4,587,966 sections and 399,052 containers", which is three counts that go
    stale on the next corpus build, in a file the guard never looked at.

    Derived by walking the tree rather than listed, so a new README is covered
    the moment it exists.
    """
    return sorted(
        p
        for p in _ROOT.rglob("README.md")
        if ".git" not in p.parts and "dist" not in p.parts
    )


def _paragraphs(text: str) -> list[tuple[int, str]]:
    """Blocks of consecutive non-blank lines, with the line number each starts at.

    🔴 The unit has to be the PARAGRAPH, not the line, and this guard got that
    wrong first. `registry/README.md` reads "derived on 2026-08-31 by /
    enumerating a live 4,093,000-document corpus": the date sits on one line and
    the count wraps onto the next, so a line-by-line check sees a bare number
    and reports a dated, perfectly good sentence as an offender.

    The repo convention is one sentence per line, which would have hidden this,
    and that is precisely why the guard must not depend on it holding.
    """
    blocks: list[tuple[int, str]] = []
    start, buf = 0, []
    for lineno, line in enumerate(text.splitlines(), 1):
        if line.strip():
            if not buf:
                start = lineno
            buf.append(line)
        elif buf:
            blocks.append((start, " ".join(buf)))
            buf = []
    if buf:
        blocks.append((start, " ".join(buf)))
    return blocks


def test_no_readme_states_a_bare_perishable_count():
    offenders: list[str] = []
    for readme in _readmes():
        for lineno, block in _paragraphs(readme.read_text()):
            if not _BIG.search(block) or _DATED.search(block):
                continue
            offenders.append(f"{readme.relative_to(_ROOT)}:{lineno}: {block.strip()[:120]}")
    assert not offenders, (
        "a README states a count that will go stale. Use a magnitude (5M+), move "
        "it to the release notes or the artifact's own manifest, or attach the "
        "date it was measured:\n  " + "\n  ".join(offenders)
    )


def test_the_guard_actually_looks_at_more_than_the_front_page():
    """A guard that silently narrows to one file is worse than no guard."""
    found = {p.relative_to(_ROOT).as_posix() for p in _readmes()}
    assert "README.md" in found, "the root README must be covered"
    assert len(found) > 1, f"expected the guard to walk the tree, saw only {found}"
