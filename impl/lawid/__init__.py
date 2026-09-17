"""lawid: the reference implementation of the US Law Identifier.

A uniform, derivable, permanent identifier for any provision of United States
law. See ../../spec/SPEC-v0.1.md for the normative rules.

    >>> mint("mt", "statutes", ["title 10", "chapter 1", "part 10"], "10-1-1001")
    'us1:mt/statutes/title-10/chapter-1/part-10/10-1-1001'

    >>> parse("us1:mt/statutes/title-10/chapter-1/part-10/10-1-1001").jurisdiction
    'mt'

DESIGN CONSTRAINTS, all deliberate:

* **Zero dependencies, standard library only.** An identifier scheme you need to
  install a stack to compute is a scheme nobody computes. This module must stay
  importable from anywhere.

* **Knows nothing about any corpus, database or vendor.** It takes a
  jurisdiction, a corpus, a container path and a leaf, and returns a string.
  Mapping some particular store's records onto those arguments is the caller's
  job, and keeping that mapping out of here is what lets a competitor use this
  without using us.

* **Pure and total.** No IO, no network, no clock, no randomness. The same
  inputs always produce the same identifier, on any machine, forever. That is
  the whole basis of the derivability promise.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

__all__ = [
    "VERSION",
    "LawId",
    "corpora",
    "jurisdictions",
    "kinds",
    "mint",
    "normalize",
    "parse",
    "validate",
]

#: The identifier format version. It is part of every identifier, so that a
#: future revision of the rules can mint `us2:` without invalidating anything
#: already minted under `us1:`. Borrowed from multiformats/CID self-description.
#:
#: The scheme names the JURISDICTION FAMILY, never the vendor that built it.
#: A vendor-named prefix asks every competitor to write a rival's name into
#: their own database forever, and it cannot survive the handover this project
#: commits to: GRID was free, CC0, good and widely adopted, and its own vendor
#: retired it because "two open organisation identifiers could be perceived as
#: competing against each other". FIGI is the counter-example and the model
#: followed here: a neutral scheme name, with any minter marking itself in a
#: provider slot that every other minter can occupy too.
VERSION = 1

_REGISTRY = Path(__file__).resolve().parents[2] / "registry"

# Characters permitted in a path segment. Everything else is replaced.
# Derived from a census of 1,204,556 real section numbers, which contained 88
# distinct characters including ":", " ", ",", "(", ")" and "_".
_ALLOWED = re.compile(r"[^a-z0-9.-]+")
_DASHES = re.compile(r"-{2,}")

_SEGMENT = r"[a-z0-9.-]+"
_ID_RE = re.compile(
    rf"^us(?P<version>\d+):"
    rf"(?P<jurisdiction>[a-z]{{2}}|federal)"
    rf"/(?P<corpus>[a-z-]+)"
    rf"/(?P<rest>{_SEGMENT}(?:/{_SEGMENT})*?)"
    rf"(?:~(?P<kind>[a-z]+))?"
    rf"(?:@(?P<point_in_time>\d{{4}}-\d{{2}}-\d{{2}}|[a-z][a-z-]*))?$"
)


class InvalidIdentifier(ValueError):
    """Raised when a string is not a well-formed identifier."""


@dataclass(frozen=True)
class LawId:
    """A parsed identifier."""

    version: int
    jurisdiction: str
    corpus: str
    containers: tuple[str, ...]
    leaf: str
    kind: str | None = None
    point_in_time: str | None = None

    @property
    def work(self) -> str:
        """This identifier with any point-in-time removed.

        The Work is the provision as a continuing thing, across every version it
        has ever had. It never changes, including when the text changes.
        """
        return _render(self, point_in_time=None)

    @property
    def is_work(self) -> bool:
        return self.point_in_time is None

    def at(self, point_in_time: str) -> str:
        """Return the Expression identifier for a given point in time."""
        return _render(self, point_in_time=point_in_time)

    def __str__(self) -> str:
        return _render(self, point_in_time=self.point_in_time)


def _render(parts: LawId, *, point_in_time: str | None) -> str:
    body = (
        "/".join((parts.leaf,))
        if not parts.containers
        else "/".join((*parts.containers, parts.leaf))
    )
    out = f"us{parts.version}:{parts.jurisdiction}/{parts.corpus}/{body}"
    if parts.kind:
        out += f"~{parts.kind}"
    if point_in_time:
        out += f"@{point_in_time}"
    return out


def normalize(text: str) -> str:
    """Fold arbitrary publisher text into one URL-safe path segment.

    The rules, in order, per spec §4.1:

    1. Unicode NFKD normalization.
    2. Casefold to lowercase.
    3. Replace every run of characters outside ``[a-z0-9.-]`` with a single ``-``.
    4. Collapse runs of ``-``.
    5. Strip leading and trailing ``-``.

    Casefolding is not free: 769 groups in a real corpus census held more than
    one spelling that differs only by case (``8A`` and ``8a``, ``30-B`` and
    ``30-b``). It is done anyway, because a case-sensitive identifier breaks
    when a human retypes it, and because the container path resolves the
    ambiguity. ECLI made the same call: "there must not be a difference in
    meaning as to their capitalization".

        >>> normalize("Mont. Code Ann. § 10-1-1001")
        'mont.-code-ann.-10-1-1001'
        >>> normalize("Title 13A")
        'title-13a'
    """
    folded = unicodedata.normalize("NFKD", text or "").casefold().strip()
    return _DASHES.sub("-", _ALLOWED.sub("-", folded)).strip("-")


def mint(
    jurisdiction: str,
    corpus: str,
    containers: list[str] | tuple[str, ...],
    leaf: str,
    *,
    kind: str | None = None,
    point_in_time: str | None = None,
    version: int = VERSION,
) -> str:
    """Build an identifier. Raises rather than guessing.

    ``containers`` is the full ancestor chain, outermost first. It is REQUIRED
    and must be non-empty. Measured over 4,093,000 documents, dropping it costs
    23.472% of the corpus to collisions; carrying it in full costs 0.250%, and
    most of that residue is versioned copies of one provision, which a Work
    identifier is supposed to merge.

    ``kind`` disambiguates parallel series inside one container, where a
    publisher issues both "Rule 3" and "Form 3". Values are PERMANENT once any
    identifier uses them.

    Raises ``InvalidIdentifier`` when an argument cannot yield a segment. A
    wrong permanent identifier is worse than no identifier, so this never
    substitutes a placeholder.
    """
    j = normalize(jurisdiction)
    c = normalize(corpus)
    if not j:
        raise InvalidIdentifier("jurisdiction is required")
    if not c:
        raise InvalidIdentifier("corpus is required")
    if not containers:
        raise InvalidIdentifier(
            "containers is required and must be non-empty; a leaf alone collides "
            "on 23.5% of a real corpus"
        )

    path = [normalize(x) for x in containers]
    if not all(path):
        raise InvalidIdentifier(f"a container normalized to nothing: {containers!r}")
    leaf_seg = normalize(leaf)
    if not leaf_seg:
        raise InvalidIdentifier(f"leaf normalized to nothing: {leaf!r}")

    if kind is not None and not re.fullmatch(r"[a-z]+", kind):
        raise InvalidIdentifier(f"kind must be lowercase alpha: {kind!r}")
    if point_in_time is not None:
        _check_point_in_time(point_in_time)

    return _render(
        LawId(version, j, c, tuple(path), leaf_seg, kind, None),
        point_in_time=point_in_time,
    )


def _check_point_in_time(value: str) -> None:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return
    # A non-date label MUST NOT begin with a digit, so it can never be mistaken
    # for a date. This rule is taken directly from USLM, which states it for the
    # same reason.
    if re.fullmatch(r"[a-z][a-z-]*", value):
        return
    raise InvalidIdentifier(
        f"point_in_time must be an ISO date or a label starting with a letter: {value!r}"
    )


def parse(identifier: str) -> LawId:
    """Parse an identifier, or raise ``InvalidIdentifier``."""
    match = _ID_RE.match(identifier or "")
    if not match:
        raise InvalidIdentifier(f"not a well-formed identifier: {identifier!r}")
    segments = match.group("rest").split("/")
    if len(segments) < 2:
        raise InvalidIdentifier(
            f"identifier needs at least one container and a leaf: {identifier!r}"
        )
    return LawId(
        version=int(match.group("version")),
        jurisdiction=match.group("jurisdiction"),
        corpus=match.group("corpus"),
        containers=tuple(segments[:-1]),
        leaf=segments[-1],
        kind=match.group("kind"),
        point_in_time=match.group("point_in_time"),
    )


def validate(identifier: str) -> bool:
    """True when the string is well formed AND its vocabulary is registered."""
    try:
        parsed = parse(identifier)
    except InvalidIdentifier:
        return False
    if parsed.jurisdiction not in {j["code"] for j in jurisdictions()}:
        return False
    if parsed.corpus not in {c["slug"] for c in corpora()}:
        return False
    # An unregistered kind is invalid, not merely unusual: kinds are permanent
    # from first use, so accepting an unknown one would let a typo become a
    # permanent part of the vocabulary.
    return parsed.kind is None or parsed.kind in {k["kind"] for k in kinds()}


@lru_cache(maxsize=1)
def jurisdictions() -> list[dict]:
    """The registered jurisdiction codes."""
    return json.loads((_REGISTRY / "jurisdictions.json").read_text())["jurisdictions"]


@lru_cache(maxsize=1)
def corpora() -> list[dict]:
    """The registered corpus vocabulary. Closed: additions go through the registry."""
    return json.loads((_REGISTRY / "corpora.json").read_text())["corpora"]


@lru_cache(maxsize=1)
def kinds() -> list[dict]:
    """The registered ~kind discriminators.

    Permanent from first use. Only two families exist corpus-wide: `form` for
    court rules that also issue forms at the same number, and `section` for
    statutes that number articles and sections in overlapping sequences.
    """
    return json.loads((_REGISTRY / "kinds.json").read_text())["kinds"]
