"""What the resolver must get right.

Two kinds of test here, and the split matters.

The first kind builds a tiny index from fixtures and pins BEHAVIOUR: how a
citation is folded, that an ambiguous citation returns every match rather than a
winner, that a missing source URL is reported rather than hidden.

The second kind runs against the REAL index when one has been built, and pins
facts that only the real data can prove: that `Pub. L. 106-1` and
`Priv. L. 106-1` resolve apart, that a `~form` citation reaches the form and not
the rule. Those two were live defects earlier the same week, and a fixture
cannot demonstrate they are fixed in the shipped artifact.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

_RESOLVER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_RESOLVER))

from lawid_resolver import Resolver, citation_key

_REAL_INDEX = _RESOLVER / "dist/resolver.sqlite"
needs_real = pytest.mark.skipif(
    not _REAL_INDEX.exists(), reason="real index not built; run resolver/build_index.py"
)


@pytest.fixture(scope="module")
def tiny(tmp_path_factory) -> Resolver:
    path = tmp_path_factory.mktemp("idx") / "t.sqlite"
    db = sqlite3.connect(path)
    db.executescript(
        "CREATE TABLE identifier (law_id TEXT PRIMARY KEY, jurisdiction TEXT NOT NULL,"
        " corpus TEXT NOT NULL, citation TEXT, cite_key TEXT, heading TEXT,"
        " status TEXT, source_url TEXT) WITHOUT ROWID;"
    )
    rows = [
        (
            "us1:mt/statutes/t/c/1",
            "mt",
            "statutes",
            "Mont. Code Ann. 10-1-1001",
            citation_key("Mont. Code Ann. 10-1-1001"),
            "Short title",
            "in_force",
            "https://leg.mt.gov/x",
        ),
        # Same citation, two jurisdictions. Abbreviations collide across states.
        (
            "us1:aa/statutes/t/c/1",
            "aa",
            "statutes",
            "Mont. Code Ann. 10-1-1001",
            citation_key("Mont. Code Ann. 10-1-1001"),
            "Elsewhere",
            "in_force",
            None,
        ),
        (
            "us1:pr/regulations/r/1",
            "pr",
            "regulations",
            "Reglamento Num. 5622, Art. 1",
            citation_key("Reglamento Num. 5622, Art. 1"),
            "Titulo",
            "in_force",
            None,
        ),
    ]
    db.executemany("INSERT INTO identifier VALUES (?,?,?,?,?,?,?,?)", rows)
    db.commit()
    db.close()
    return Resolver(path)


def test_punctuation_case_and_spacing_stop_mattering():
    forms = [
        "Mont. Code Ann. § 10-1-1001",
        "MONT. CODE ANN. 10-1-1001",
        "mont code ann 10 1 1001",
        "Mont.Code.Ann.§10-1-1001",
    ]
    assert len({citation_key(f) for f in forms}) == 1


def test_the_section_sign_is_not_identity():
    assert citation_key("Alaska Stat. § 01.05.006") == citation_key("Alaska Stat. 01.05.006")


def test_an_ambiguous_citation_returns_every_match(tiny):
    hits = tiny.resolve("Mont. Code Ann. 10-1-1001")
    assert len(hits) == 2, "returning one would answer a question nobody asked"
    assert {h.jurisdiction for h in hits} == {"mt", "aa"}


def test_a_jurisdiction_disambiguates(tiny):
    hits = tiny.resolve("Mont. Code Ann. 10-1-1001", jurisdiction="mt")
    assert [h.jurisdiction for h in hits] == ["mt"]


def test_a_missing_official_url_is_reported_not_hidden(tiny):
    hit = tiny.resolve("Reglamento Num. 5622, Art. 1")[0]
    assert hit.source_url is None
    assert hit.is_official is False, "absence must be stated, never implied"


def test_an_unknown_citation_returns_empty_not_a_guess(tiny):
    assert tiny.resolve("Totally Made Up Reporter 999") == []
    assert tiny.resolve("") == []


def test_forward_lookup_is_exact(tiny):
    assert tiny.lookup("us1:mt/statutes/t/c/1").jurisdiction == "mt"
    assert tiny.lookup("us1:mt/statutes/t/c/1 ").jurisdiction == "mt", "whitespace"
    assert tiny.lookup("us1:nope") is None


def test_a_missing_index_fails_loudly_not_empty():
    with pytest.raises(FileNotFoundError):
        Resolver("/nonexistent/resolver.sqlite")


# --- against the real published index ----------------------------------------


@pytest.fixture(scope="module")
def real() -> Resolver:
    return Resolver(_REAL_INDEX)


@needs_real
def test_a_public_and_a_private_law_resolve_apart(real):
    # These shared one identifier until 2026-09-02, because the session-law
    # breadcrumb hardcoded `Pub. L.` for both. They are different acts.
    public = real.resolve("Pub. L. 106-1, sec. 1")
    private = real.resolve("Priv. L. 106-1, sec. 1")
    assert public and private
    assert public[0].law_id != private[0].law_id
    assert "priv" in private[0].law_id


@needs_real
def test_a_form_citation_reaches_the_form_and_not_the_rule(real):
    form = real.resolve("Ala. R. Videotape Equip., Form 3")
    rule = real.resolve("Ala. R. Videotape Equip. 3")
    assert form and rule
    assert form[0].law_id.endswith("~form")
    assert not rule[0].law_id.endswith("~form")


@needs_real
@pytest.mark.parametrize(
    "citation",
    [
        "Alaska Stat. § 01.05.006",
        "Mont. Code Ann. § 10-1-1001",
        "Minn. R. Civ. App. P. 129",
    ],
)
def test_real_citations_resolve_to_an_official_source(real, citation):
    hits = real.resolve(citation)
    assert hits, citation
    assert hits[0].is_official, f"{citation} resolved but has no official URL"
