# open-law-id

A uniform, derivable, permanent identifier for any provision of United States law, and the crosswalk that maps existing citations onto it.

```
vq1:us/mt/statutes/title-10/chapter-1/part-10/10-1-1001
```

**4,039,901 provisions across 53 jurisdictions and 13 corpora**, published as a CC0 download.
The specification is a draft at v0.1. A minted identifier is not: it resolves forever.

## What it looks like

One shape for every kind of US law, so you address a court rule the same way you address a statute.

| Citation | Identifier |
|---|---|
| `ORS 1.001` | `vq1:us/or/statutes/title-1/chapter-1/1.001` |
| `14 C.F.R. § 3 (2026)` | `vq1:us/federal/cfr/title-14/chapter-ii/part-241/3` |
| `CR 1` (Kentucky) | `vq1:us/ky/court-rules/kentucky-court-rules/kentucky-rules-of-civil-procedure/1` |
| `U.S. Const. pmbl.` | `vq1:us/federal/constitution/us-constitution/preamble` |
| `Pub. L. 106-1, sec. 1` | `vq1:us/federal/session-laws/pub.-l.-106-1/1` |

### It separates things that look the same

Alabama issues a Rule 3 and a Form 3 in one container. Puerto Rico numbers articles and sections in overlapping sequences. A public law and a private law share a number and are different acts.

```
Ala. R. Videotape Equip. 3          ->  .../alabama-rules-for-using-videotape-.../3
Ala. R. Videotape Equip., Form 3    ->  .../alabama-rules-for-using-videotape-.../3~form

Ley 230-2004 art. 1                 ->  .../ley-del-centro-comprensivo-de-ca-ncer-de/1
Ley 230-2004 sec. 1                 ->  .../ley-del-centro-comprensivo-de-ca-ncer-de/1~section

Pub. L. 106-1, sec. 1               ->  vq1:us/federal/session-laws/pub.-l.-106-1/1
Priv. L. 106-1, sec. 1              ->  vq1:us/federal/session-laws/priv.-l.-106-1/1
```

The `~kind` discriminator comes from the publisher's own citation, never from a structural label. Puerto Rico stores `level_classifier: article` for **both** sides of that collision, so a structural label would give the two colliding documents the same answer.

### Amendment is two identifiers, not a changing one

```
Work        vq1:us/mt/statutes/title-10/chapter-1/part-10/10-1-1001
Expression  vq1:us/mt/statutes/title-10/chapter-1/part-10/10-1-1001@2019-03-03
```

The Work never changes, including when the text does. Each amendment mints an Expression, and **two Expressions sharing a Work is the amendment signal**. Absence of `@` means the current version, not the original. The Expression layer is specified but not yet mintable: you cannot date a provision whose amendment history you do not hold, and a wrong date baked into a permanent identifier is unfixable.

## The goal

Every US legal provision gets one identifier that is:

* **uniform** across all 51 jurisdictions and every corpus type (statutes, regulations, court rules, constitutions, agency guidance, and whatever is added later);
* **immutable**, so a reference made today still resolves in ten years;
* **derivable** from the official citation, so anyone can compute one without asking us;
* **temporal**, so a specific historical version of a provision can be cited;
* **open**, published as a spec plus a registry plus a free resolver, so other vendors, courts and lawyers can adopt it.

The starting model was what SCC OnLine and Manupatra achieved for Indian case law.
That model has already ended: the Supreme Court of India minted its own neutral citation in February 2023, and both incumbents pivoted to giving the **crosswalk** away free.
Which is why the concordance and the resolver ship ahead of the specification, rather than after it.

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

**Mint one.** No network, no account, no index, nothing from us.

```python
>>> import vqlaw
>>> vqlaw.mint("mt", "statutes", ["title 10", "chapter 1", "part 10"], "10-1-1001")
'vq1:us/mt/statutes/title-10/chapter-1/part-10/10-1-1001'

>>> vqlaw.parse(_).jurisdiction
'mt'
>>> vqlaw.normalize("Mont. Code Ann. § 10-1-1001")
'mont.-code-ann.-10-1-1001'
```

That separation is load-bearing. A scheme you must ask us to use is a scheme nobody uses, so minting is pure, offline and total: same inputs, same identifier, on any machine, forever. `mint` raises rather than guessing, because a wrong permanent identifier is worse than no identifier.

**Run the conformance corpus** against the reference implementation, or against your own:

```bash
python -m pytest impl/tests/          # 39 cases, all drawn from real adversarial data
```

**Resolve a citation**, from your own copy of the data:

```bash
curl -LO https://github.com/Vaquill-AI/open-law-id/releases/download/v0.1/concordance-v0.1.jsonl.gz
python resolver/build_index.py --concordance concordance-v0.1.jsonl.gz --out resolver.sqlite
uvicorn resolver.app:app --port 8080
```

```console
$ curl -s 'localhost:8080/resolve?citation=Mont.+Code+Ann.+%C2%A7+10-1-1001' | jq
{
  "count": 1,
  "results": [
    {
      "id": "vq1:us/mt/statutes/title-10/chapter-1/part-10/10-1-1001",
      "jurisdiction": "mt",
      "corpus": "statutes",
      "citation": "Mont. Code Ann. 10-1-1001",
      "heading": "Short title",
      "status": "in_force",
      "sourceUrl": "https://mca.legmt.gov/bills/mca/title_0100/chapter_0010/...",
      "sourceIsOfficial": true
    }
  ]
}
```

Or in Python, without the service:

```python
>>> from vqresolve import Resolver
>>> r = Resolver("resolver.sqlite")
>>> r.resolve("MONT. CODE ANN. 10 1 1001")[0].source_url      # case and punctuation do not matter
'https://mca.legmt.gov/bills/mca/title_0100/...'
>>> r.lookup("vq1:us/or/statutes/title-1/chapter-1/1.001").heading
'State policy for courts'
```

Three things the resolver does deliberately:

* **`resolve` always returns a list.** A citation is not always unique, two jurisdictions abbreviate alike, and returning the first match would answer a question you did not ask. Pass `jurisdiction=` to narrow it.
* **`sourceUrl` is null when we hold no OFFICIAL publisher link**, which is 4.4% of the corpus. A link to an aggregator verifies nothing, so absence is stated rather than filled in.
* **No API key, no quota, no rate limit tied to identity.** Resolution is free and unmetered, not a free tier. See `GOVERNANCE.md`.

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
