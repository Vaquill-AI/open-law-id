# vaquill-law-id

Working directory for a universal, permanent identifier for United States law, and for the concordance that maps existing citations onto it.

This is **research, drafting and working code**, not a published standard.
What eventually ships to a public repo in the `Vaquill-AI` org is a subset of this, and nothing here has been published or offered to anyone.

## The goal

Every US legal provision we hold, and every one we do not yet hold, gets one identifier that is:

* **uniform** across all 51 jurisdictions and every corpus type (statutes, regulations, court rules, constitutions, agency guidance, and whatever is added later);
* **immutable**, so a reference made today still resolves in ten years;
* **derivable** from the official citation, so anyone can compute one without asking us;
* **temporal**, so a specific historical version of a provision can be cited;
* **open**, published as a spec plus a registry plus a free resolver, so other vendors, courts and lawyers can adopt it.

The starting model was what SCC OnLine and Manupatra achieved for Indian case law.
The research found that model already ended: the Supreme Court of India minted its own neutral citation in February 2023, and both incumbents pivoted to giving the **crosswalk** away free.
That finding reordered the whole plan, and it is why the concordance ships before the specification.
See [PLAN.md](PLAN.md).

## Why this might work, and why it might not

**The gap is real.**
Each US jurisdiction has its own citation grammar.
There is no common machine identity for "a provision of US law", so addressing the corpus uniformly needs 51 parsers.
That gap is felt hardest by machines: developers, vendors cross-referencing corpora, and AI agents that must reference a provision unambiguously.

**The risk is real too.**
The literature on identifier standards is blunt that adding an identifier where one already exists usually fails, and that a scheme controlled by one commercial vendor is harder for competitors to adopt.
`Mont. Code Ann. § 10-1-1001` already exists and is court-mandated.
We are not replacing it.

So the bet is narrow and deliberate: supply the **cross-jurisdiction layer** and the **point-in-time layer**, both of which have no incumbent, and leave the official citation exactly where it is.

## Layout

```text
spec/               the specification
impl/vqlaw/         reference implementation: zero dependencies, pure, no IO
impl/tests/         conformance tests against conformance/conformance.json
conformance/        the adversarial fixture corpus
registry/           the three closed vocabularies: jurisdictions, corpora, kinds
resolver/           citation -> identifier -> official source URL, as a service
GOVERNANCE.md       the five commitments made before anyone is asked to adopt
```

## Two things ship as downloads, not as files in this repository

The **concordance** (`concordance.jsonl.gz`) maps every provision we can address to its identifier, its publisher citation and its official source URL. It is CC0. It is ~4 million rows and rebuilt from a corpus, so it is a release asset.

The **resolver index** (`resolver.sqlite`) is built from the concordance by `resolver/build_index.py` in a few minutes. It is published for convenience only; it contains nothing the concordance does not, so you never have to trust ours.

The pipeline that derives the concordance from our own corpus is deliberately not here. It hardcodes paths into a private repository and imports its application code, so it could not run for anyone else, and nobody should need our data to use this scheme.

## Using it

```bash
# Compute an identifier. No network, no account, no index.
python -c "import vqlaw; print(vqlaw.mint('mt','statutes',['title 10','chapter 1'],'10-1-1001'))"

# Run the conformance corpus against the reference implementation.
python -m pytest impl/tests/

# Resolve a citation, from your own copy.
python resolver/build_index.py --concordance concordance.jsonl.gz --out resolver.sqlite
uvicorn resolver.app:app --port 8080
curl 'localhost:8080/resolve?citation=Mont.+Code+Ann.+10-1-1001'
```

Minting is offline and needs nothing from us. That separation is load-bearing: a scheme you must ask us to use is a scheme nobody uses. The resolver only saves you from holding four million rows yourself.

## One rule holds this together

**Nothing outside `impl/vqlaw/` and `registry/` may decide what an identifier looks like.**

The audit broke this rule and it cost us the headline number.
`audit/collision_audit.py` carried its own copy of `normalize` whose character class kept `_`, while the published `vqlaw.normalize` folds `_` to `-`.
So the collision rate quoted in the specification was measured against an identifier space that would never have been minted, and the published implementation merges documents the audit counted as distinct.
The audit now imports `normalize` rather than defining one.

The same rule is why `concordance/build_concordance.py` imports `vqlaw.mint`, reads the corpus slug from `registry/corpora.json`, and recovers the container path with the shipped `container_path`.
It decides only which documents are **eligible**, and records every one it rejected.

## The gate

Before any spec is published, one thing must be true: **the normalization must not collide.**
Two distinct provisions mapping to one identifier kills the scheme outright.

The corpus is adversarial on exactly this point.
Alabama has an alphanumeric title `13A`.
Washington has `458-20-24001A`.
Virginia writes `9VAC25-720-60`.
Wisconsin writes `NR 10.06`.
Federal OSHA has `1910.16-3`.

The gate passed, provided the identifier carries the **full container path**.
Dropping it costs 23.472% of the corpus to collisions; carrying it costs a fraction of a percent, most of which is versioned copies of one provision that a Work identifier is supposed to merge.
See specification §5.

Two rules follow from the audit and are not negotiable:

* **A document whose identity cannot be established emits nothing.** Colliding documents are dropped and named in a ledger, never disambiguated by an invented suffix.
* **A corpus whose container path is known to be collapsed is blocked from minting** until the ingester is fixed and re-run. `mn/court-rules` is blocked today.

## Status

Research started 2026-08-31.
The specification is a draft at v0.1, the reference implementation and registry exist, and the concordance builder is written but has not been run over the full corpus.
Nothing has been published, and no external body has been approached.
`GOVERNANCE.md` records what must be settled first.
