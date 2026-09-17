"""lawid_resolver: turn a citation a lawyer typed into a law you can open.

    >>> r = Resolver("resolver.sqlite")
    >>> hit = r.resolve("Mont. Code Ann. 10-1-1001")
    >>> hit.law_id, hit.source_url            # doctest: +SKIP
    ('us1:mt/statutes/...', 'https://leg.mt.gov/...')

WHY A RESOLVER COMES BEFORE A SPECIFICATION
DOI existed for three years with no application and went nowhere. Crossref
shipped a working linking service to twelve publishers before Crossref existed
as a legal entity, and that service is what made the identifier matter. So this
is deliberately built and shipped ahead of asking anyone to adopt anything.

WHAT IT IS FOR, AND WHAT IT IS NOT FOR
It answers the crosswalk question: "here is a citation, what is the canonical
identifier and where is the official text". That genuinely needs data.

It is NOT needed to MINT an identifier. `lawid.mint` is pure and offline, and
that separation is load-bearing: a scheme you must ask us to use is a scheme
nobody uses. Anyone can compute an identifier with no network and no account;
the resolver only saves you from holding 4 million rows yourself.

DESIGN CONSTRAINTS
* **Standard library only.** sqlite3 ships with Python. A resolver that needs a
  server, a cluster or a paid index is one nobody can run, audit or fork.
* **One file.** The index is a single SQLite database, so "run your own
  resolver" is a download, not a deployment.
* **Reads only.** Nothing here writes to the index; `build_index.py` does that.
"""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from dataclasses import dataclass
from pathlib import Path

__all__ = ["Hit", "Resolver", "citation_key"]

#: Characters that carry no identity in a citation. `§` is the obvious one: a
#: reader types it or does not, and the two spellings are the same reference.
_STRIP = re.compile(r"[^0-9a-z]+")


def citation_key(citation: str) -> str:
    """Fold a citation to the key the index is built on.

    Aggressive on purpose. Everything outside `[0-9a-z]` collapses to a single
    space, so `Mont. Code Ann. § 10-1-1001`, `Mont Code Ann 10 1 1001` and
    `MONT. CODE ANN. §10-1-1001` are one key.

    This is a NORMALIZER, not a parser. It will not expand `MCA` to
    `Mont. Code Ann.`, and it is not meant to: abbreviation tables are a solved
    problem with a maintained solution (`reporters-db`, 1,167 reporters and
    2,102 variations), and re-deriving one badly would be worse than not having
    it. What this does is make punctuation, case and spacing stop mattering,
    which is what actually defeats an exact-match lookup.

        >>> citation_key("Mont. Code Ann. § 10-1-1001")
        '10 1 1001 ann code mont'
    """
    folded = unicodedata.normalize("NFKD", citation or "").casefold()
    # Sorting the tokens makes the key insensitive to the order a reader writes
    # the parts in, which is the other half of why exact match fails: some write
    # `Alaska Stat. 01.05.006` and some write `AS 01.05.006 (Alaska Statutes)`.
    return " ".join(sorted(t for t in _STRIP.split(folded) if t))


@dataclass(frozen=True)
class Hit:
    """One resolved provision."""

    law_id: str
    jurisdiction: str
    corpus: str
    citation: str | None
    heading: str | None
    status: str | None
    source_url: str | None

    @property
    def is_official(self) -> bool:
        """Whether an OFFICIAL publisher URL is known for this provision.

        False is a real answer and a common one. The concordance publishes a
        source URL only when it is the publisher's own, because a link to an
        aggregator verifies nothing and launders provenance.
        """
        return bool(self.source_url)


class Resolver:
    """Read-only lookups against a built index."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        if not self._path.exists():
            raise FileNotFoundError(
                f"{self._path} does not exist. Build it with resolver/build_index.py."
            )
        # `immutable=1` rather than plain read-only: it also tells SQLite the
        # file cannot change under it, so a resolver serving many readers does
        # no locking at all.
        self._db = sqlite3.connect(
            f"file:{self._path}?immutable=1", uri=True, check_same_thread=False
        )
        self._db.row_factory = sqlite3.Row

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> Resolver:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def lookup(self, law_id: str) -> Hit | None:
        """Forward: an identifier to its provision. Exact, and the fast path."""
        row = self._db.execute(
            "SELECT * FROM identifier WHERE law_id = ?", ((law_id or "").strip(),)
        ).fetchone()
        return _hit(row) if row else None

    def resolve(self, citation: str, *, jurisdiction: str | None = None) -> list[Hit]:
        """Reverse: a citation to every provision that matches it.

        Returns a LIST, and callers must handle more than one. A citation is not
        always unique: two jurisdictions abbreviate alike, and a reader who omits
        the jurisdiction is genuinely ambiguous. Returning the first match would
        answer a question the caller did not ask.
        """
        key = citation_key(citation)
        if not key:
            return []
        sql = "SELECT * FROM identifier WHERE cite_key = ?"
        params: list[str] = [key]
        if jurisdiction:
            sql += " AND jurisdiction = ?"
            params.append(jurisdiction.strip().casefold())
        return [_hit(r) for r in self._db.execute(sql + " ORDER BY law_id", params)]

    def stats(self) -> dict[str, int]:
        row = self._db.execute(
            "SELECT COUNT(*) AS n, COUNT(source_url) AS official,"
            " COUNT(DISTINCT jurisdiction) AS jurisdictions,"
            " COUNT(DISTINCT corpus) AS corpora FROM identifier"
        ).fetchone()
        return dict(row)


def _hit(row: sqlite3.Row) -> Hit:
    return Hit(
        law_id=row["law_id"],
        jurisdiction=row["jurisdiction"],
        corpus=row["corpus"],
        citation=row["citation"],
        heading=row["heading"],
        status=row["status"],
        source_url=row["source_url"],
    )
