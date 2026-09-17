"""Run the published conformance corpus against the reference implementation.

`conformance/conformance.json` is the artifact that makes this a specification
rather than a document. Any implementation claiming conformance must produce
these outputs and refuse these inputs, so the corpus has to be executable by a
third party with no access to our data. This file is how we run it ourselves.

Every case is drawn from real adversarial data in a 4,093,000-document corpus.
None are invented.
"""

from __future__ import annotations

import json
from pathlib import Path

import lawid
import pytest

_CORPUS = json.loads(
    (Path(__file__).resolve().parents[2] / "conformance" / "conformance.json").read_text()
)


@pytest.mark.parametrize("case", _CORPUS["mint"], ids=lambda c: c["name"])
def test_mint(case):
    assert lawid.mint(**case["mint"]) == case["expect"], case["why"]


@pytest.mark.parametrize("case", _CORPUS["refuse"], ids=lambda c: c["name"])
def test_refuse(case):
    # Refusing is the whole discipline: a wrong permanent identifier is worse
    # than no identifier, so an unidentifiable input must never be given a
    # placeholder.
    with pytest.raises(lawid.InvalidIdentifier):
        lawid.mint(**case["mint"])


@pytest.mark.parametrize("case", _CORPUS["parse"], ids=lambda c: c["name"])
def test_parse(case):
    try:
        lawid.parse(case["parse"])
        parsed = True
    except lawid.InvalidIdentifier:
        parsed = False
    assert parsed is case["valid"], case["why"]


@pytest.mark.parametrize("case", _CORPUS["mint"], ids=lambda c: c["name"])
def test_every_minted_identifier_round_trips(case):
    """parse(mint(x)) must reproduce mint(x) exactly, for every case."""
    minted = lawid.mint(**case["mint"])
    assert str(lawid.parse(minted)) == minted


def test_registered_kinds_validate_and_unregistered_ones_do_not():
    # Kinds are permanent from first use, so an unknown kind must be rejected
    # rather than silently accepted into the vocabulary.
    ok = lawid.mint("al", "court-rules", ["rules", "videotape"], "3", kind="form")
    assert lawid.validate(ok)
    bogus = lawid.mint("al", "court-rules", ["rules", "videotape"], "3", kind="widget")
    assert not lawid.validate(bogus)


def test_the_work_of_an_expression_drops_the_point_in_time():
    expression = lawid.mint("mt", "statutes", ["title 10"], "10-1-1001", point_in_time="2019-03-03")
    parsed = lawid.parse(expression)
    assert not parsed.is_work
    assert parsed.work == "us1:mt/statutes/title-10/10-1-1001"
    # Two Expressions sharing a Work is the amendment signal.
    other = lawid.parse(parsed.at("2023-10-01"))
    assert other.work == parsed.work and str(other) != expression
