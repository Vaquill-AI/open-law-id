# The US Law Identifier, v0.1

**Status: draft. Not published. Not frozen.**

A uniform, derivable, permanent identifier for any provision of United States law.

---

## 0. What this is, and what it is not

**It is** a machine address for a legal provision, uniform across every US jurisdiction (the 50 states, DC, Puerto Rico and the federal government) and every corpus type, computable offline from the official citation, and permanent once minted.

**It is not** a replacement for `Mont. Code Ann. § 10-1-1001`. The official citation is court-mandated, Bluebook-governed, and stays exactly where it is. This identifier fills the two layers that have no incumbent: a **cross-jurisdiction machine address**, and a **point-in-time selector**.

### The three promises

1. **Derivable.** Anyone can compute an identifier from a citation using the rules below, offline, with no API call and no registry lookup. A scheme you must ask us to use is a scheme nobody uses.
2. **Permanent.** Once minted, an identifier resolves forever. This survives corrections to this specification (see §1).
3. **Checkable by eye.** You can look at one and see that it is wrong. A hash cannot do this.

---

## 1. Versioning: why the identifier carries `us1:`

```
us1:mt/statutes/title-10/chapter-1/part-10/10-1-1001
^^^
```

The prefix declares which version of **these rules** minted the string.

This exists because of a documented failure. Crossref instructs members to make DOI suffixes opaque, and its empirical argument is that *"when people register DOI suffixes with human-readable patterns, they will inevitably change those patterns over time, thus compromising the persistence of the DOI itself."* The artifact is real: one article carrying both `10.1002/mmng.4860070108` and `10.1002/mmng.20040070108` after a member reformatted.

We have replicated that failure ourselves. Washington served 807 phantom `2026` amendment years harvested from a page banner. A Texas regex tail-match permanently minted `TX_INS_B_00` from `B-0046B-00`.

The version prefix converts "we might get the normalization wrong" from a reason to delay into a versioning problem already solved. `us1:` and a future `us2:` coexist with no flag day, exactly as multicodec-prefixed CIDs do.

**The separable promises, and this distinction is load-bearing:**

| | Guarantee |
|---|---|
| **This specification** | May be revised. v0.1 is a draft. |
| **A minted identifier** | **Resolves forever.** Never re-minted, never re-pointed, even if v2 would mint a different string for that provision. |

A revision that would change an existing string increments the prefix. Identifiers already minted under `us1:` keep resolving under `us1:` in perpetuity.

---

## 2. Grammar

```abnf
law-id        = scheme ":" work-path [ "@" point-in-time ]

scheme        = country-code 1*DIGIT          ; "us1", and a future "us2"

work-path     = jurisdiction "/" corpus
                *( "/" container ) "/" leaf

country-code  = "us"                          ; the SCHEME names the country,
                                              ; so it is not repeated in the path
jurisdiction  = 2ALPHA / "federal"
corpus        = 1*( ALPHA / "-" )
container     = segment
leaf          = segment [ "~" kind ]
kind          = 1*( ALPHA )

segment       = 1*( DIGIT / lcalpha / "." / "-" )
lcalpha       = %x61-7A                      ; a-z only, never uppercase

point-in-time = date / label
date          = 4DIGIT "-" 2DIGIT "-" 2DIGIT ; ISO 8601 calendar date
label         = lcalpha *( lcalpha / "-" )   ; MUST NOT begin with a digit
```

Every component is **mandatory and ordered**. There are no optional components and no alternative orderings.

This is deliberate and it is the single highest-value design decision available. ECLI fixed five mandatory ordered components and forbade extension; it is regex-parseable across every jurisdiction with no registry lookup, and it reached ~14.7 million indexed decisions. ELI made every component optional and usable "in any order"; **no single parser can read an ELI**, and France publishes two canonical identifiers for the same act on purpose.

**If any component of this scheme becomes optional, we have built ELI.**

### 2.1 Extension is forbidden

Borrowed verbatim in spirit from ECLI: *"So as not to compromise its use or comprehensibility an ECLI must not be extended with any other components."*

A `us1:` identifier MUST NOT carry a format suffix, a language tag, a pinpoint beyond `~kind`, a publisher, or any other component. Everything variable belongs in metadata beside the identifier, never inside it.

### 2.2 The `label` rule

A non-date point-in-time value MUST NOT begin with a digit, so it can never be mistaken for a date. This rule is taken directly from USLM, which states it for the same reason.

Reserved labels: `enacted`, `original`, `current`, `prospective`.

---

## 3. Work and Expression

The requirement "immutable, yet reveals amendment" is self-contradictory in one string. URN:LEX and Akoma Ntoso both resolve it the same way, through FRBR, and so do we.

```
Work        us1:mt/statutes/title-10/chapter-1/part-10/10-1-1001
Expression  us1:mt/statutes/title-10/chapter-1/part-10/10-1-1001@2019-03-03
```

- The **Work** is the provision as a continuing thing, across every version it has ever had. It carries **no** point-in-time component. It never changes, including when the text changes.
- An **Expression** is one version. Each amendment mints a new one.
- **Two Expressions sharing a Work is the amendment signal.** That is how you tell a provision has changed by looking at identifiers alone.

⚠️ **Absence of `@` means the current version**, resolved at dereference time. It does **not** mean the original.

This matters because AKN and USLM disagree here, and getting it backwards silently serves the wrong point in time:

| | AKN | USLM | **us1** |
|---|---|---|---|
| `@` with no value | **original** | **current** | *not permitted* |
| no `@` at all | current | current | **current** |
| the original | `@` (dangling) | `@enacted` | `@enacted` |

We forbid a dangling `@` outright rather than inherit either reading.

### 3.1 The Expression layer is NOT YET MINTABLE

**Measured 2026-08-31: 1,001,464 documents, 24.5% of the corpus, carried no usable amendment year.** You cannot mint `@2019-03-03` for a provision whose amendment history you do not hold, and a wrong date baked into a permanent identifier is unfixable.

The Expression layer is therefore **blocked on the amendment-history backfill** and ships in a later revision. The Work layer ships now.

### 3.2 Content hash is an attribute, never the name

Publish `sha256` of the canonical text beside each Expression. It proves the bytes we served.

It cannot be the identifier: it is not derivable offline (you must hold the text first), not checkable by eye, and it changes on every whitespace fix and OCR correction, which would mint a new "provision" for a typo. Identifier for addressing, hash for verification. Do not conflate the jobs.

---

## 4. Normalization

### 4.1 Character set

Measured over **1,204,556 section numbers** in the live corpus: **88 distinct characters** appear, including `:` (61,943), space (58,981), `,` (9,269), `(` and `)` (~4,150 each), and `_` (6,432).

The output alphabet is `[a-z0-9.-]`. Every other character is a decision this section must state explicitly.

**Rules, in order:**

1. Apply Unicode NFKD normalization.
2. **Casefold to lowercase.**
3. Replace every run of characters outside `[a-z0-9.-]` with a single `-`.
4. Collapse runs of `-` to one.
5. Strip leading and trailing `-`.

### 4.2 Why casefold, given that it collides

Casefolding is not free. Measured: **769 casefold groups hold more than one distinct spelling**: `8A` and `8a`, `30-B` and `30-b`, `17-C` and `17-c` all exist as separate stored section numbers.

We casefold anyway, for two reasons.

**A case-sensitive identifier is hostile.** ECLI took the same view explicitly: *"at the very least there must not be a difference in meaning as to their capitalization."* Live German ECLIs are lowercase and live Dutch ones are uppercase, and both resolve. An identifier a human retypes must not break on shift.

**The container path absorbs the ambiguity.** A casefold collision only matters if two provisions collide *within the same jurisdiction, corpus and container path*. Measured across 323,757 documents in the adversarial states, that leaves **18 collisions, 0.006%**, all named in §5.

The differing spellings are also overwhelmingly ingest artifacts rather than publisher distinctions: the same provision captured by two generations of scraper. Preserving case would preserve our own inconsistency in a permanent public identifier.

### 4.3 Container path

The container path is the full ancestor chain, outermost first, each segment normalized per §4.1.

It is recovered from the publisher's own structure, and the recovery method is recorded per document (`breadcrumb_typed`, `breadcrumb_flat`, `display_path`). A document whose structure cannot be recovered **MUST NOT** be minted an identifier under this version.

**The path is required, not optional.** Measured collision cost as context is removed:

| Shape | Documents lost |
|---|---|
| `{jurisdiction}/{corpus}/{section}` | 51,558 (15.9%) |
| + top container | 38,495 (11.9%) |
| + title/chapter | 2,398 (0.741%) |
| **+ full container path** | **18 (0.006%)** |

### 4.4 What MUST NOT enter the identifier

Absolutely excluded, each for a reason we have already been bitten by:

- **Dates, amendment years, edition markers.** WA's 807 phantom 2026 years.
- **Chapter or Cap numbers that renumber.** The AKN4Africa rule: *"Do not put Chapter or Cap numbers in the URI, because they change over time."* Link them as metadata.
- **Page numbers or publisher pagination.** Vendor-proprietary and the thing this scheme exists to route around.
- **Our internal `act_id`.** It re-mints: Arkansas's 2025 recodification produced **zero overlap** between generations, and NJ's two generations cannot be told apart by act_id at all. `vaquill_id` maps to act_id; it is never derived from it.
- **Synthetic routing keys.** `title_number` carries `9300` (IRS), `9400` (Federal Register) and `9500` (Sentencing Guidelines). Publishing "Title 9400" would be a fabricated container in an artifact whose entire value is that it is checkable.

---

## 5. The collision classes, named

Measured over 323,757 documents in the adversarial jurisdictions (al, mt, va, wa, wi), shape D leaves 18 collisions. They fall into exactly three classes. Each gets a deterministic rule.

### Class A: versioned prior copies (3 of 18). NOT a collision.

```
us/mt/regulation/title-44/chapter-44.3/subchapter-44.3.10/44.3.1001
    STATE_MT_ARM_T44_C3_S44_3_1001
    STATE_MT_ARM_T44_C3_S44_3_1001_Valt19961220_unknown_14768ce0
```

These are the **same Work at different versions**. Merging them at Work level is correct behaviour, not a defect. They separate at Expression level once §3.1 unblocks.

**Rule: none needed.** Do not "fix" this.

### Class B: unnumbered documents sharing a date (10 of 18)

```
us/wi/state_agency_guidance/.../wi-oci-bulletin-2000-02-28
    WI_INS_B_20000228_INS367
    WI_INS_B_20000228_INS9
```

Agency bulletins with **no publisher-assigned number**, where the leaf is derived from the issue date. Two bulletins issued the same day collide.

**Rule B1.** Where the publisher assigns no number, the leaf is a slug derived from the document's title, not from its date. (AKN's own rule for this case: *"Where a number is genuinely unavailable, use a slug."*)

**Rule B2.** Where B1 still collides, append `-b`, `-c`, … in publisher order, **leaving the first identifier untouched**. Taken from AKN4Africa, which adopted it for clerical duplicates for the same reason: renumbering the original would break every citation of it.

### Class C: different document kinds at the same number (5 of 18)

```
us/al/state_rules/.../alabama-rules-for-using-videotape-equipment.../3
    SRULES_AL_ARVE_FORM3      <- Form 3
    SRULES_AL_ARVE_R3         <- Rule 3
```

Genuinely different documents that share a number inside one container, because the publisher issues parallel series (Rule 3 and Form 3).

**Rule C1.** Where a container holds parallel series, the leaf carries a `~kind` discriminator derived from the publisher's own series name:

```
us/al/state_rules/.../3~rule
us/al/state_rules/.../3~form
```

`kind` is lowercase alpha, taken from the publisher's vocabulary, and **fixed before first mint**. AKN4Africa's warning applies: once `pn` is taken by Provincial Notice, Premier's Notice must be `premn` forever. Enumerate every kind before minting any.

### Class D: our own duplicate-marker suffixes

```
SRULES_GA_SCT_R20_VPRE20240101
SRULES_GA_SCT_R20_VPRE20240101_2      <- trailing _2
STATE_WY_WYAR_A045_P0007_C2_S1
STATE_WY_WYAR_A045_P0007_C2_S1__N2    <- trailing __N2
```

These are not two provisions. They are **one provision stored twice**, distinguished only by a dedup suffix an ingester appended.

**Rule D1.** The identifier is correct to merge them. The duplicate is a corpus defect and belongs in the gap register, not in this specification. Minting MUST NOT be blocked on it, and a suffix like `_2` or `__N2` MUST NOT be carried into the identifier.

### Class E: the same document stored under two spellings

```
STATE_AR_CAR_A007_SRULES_AND_REGULATIONS_PERTAINING_TO_REST
STATE_AR_CAR_A007_SRules_and_Regulations_Pertaining_to_Rest    <- case only

STATE_MI_C390_ATerritorial-Laws-of-1833,-Vol-III_S390.757
STATE_MI_C390_ATerritorial-Laws-of-1833-Vol-III_S390.757       <- comma only
```

Same as Class D: one document, two act_ids, differing only by case or punctuation. **The identifier scheme is functioning as a duplicate detector here**, which is a feature.

**Rule E1.** Merge, and file the duplicate as a corpus defect.

### 5.1 Full-corpus measurement

Audited across **all 260 passes, 4,093,000 documents**, in 23 minutes.

| Shape | Documents lost |
|---|---|
| `{jurisdiction}/{corpus}/{section}` | 960,783 (23.472%) |
| + top container | 451,630 (11.034%) |
| + title/chapter | 267,052 (6.524%) |
| **+ full container path** | **10,240 (0.250%)** |

⚠️ **The 5-jurisdiction sample understated shape D by 40x** (0.006% → 0.250%). Do not size a corpus-wide property from a convenience sample.

#### The measured number, 2026-09-02: 0.00244%

The 0.250% above is superseded and was never the real figure. **The corrections were measurement defects, not scheme defects**, and most were in our own code:

1. **The audit was not measuring the published scheme.** `collision_audit.py` carried its own copy of `normalize` whose character class kept `_`, while `lawid.normalize` folds `_` to `-`. It now imports `normalize` and defines none.
2. **The Work-level fold was over-eager, and would have deleted law.** A repeating bare-number suffix pattern read `DE_INS_PA_40_20260112` (Delaware insurance bulletin 40 of 2026-01-12) as a version marker and folded an entire bulletin series into one document: 294 of 303 `de` agency-guidance documents and 1,129 of 1,164 `de` regulations. Version markers and bare numbers are now separate classes with separate evidentiary rules.
3. **Reissues were counted as collisions.** See rule A1 below.
4. **Rules B1, B2, C1 and E1 were specified but not implemented.** All four now are.

Measured with `lawid.mint` over **4,139,923 documents in 260 groups**:

| | Documents |
|---|---|
| minted and published | 4,039,901 |
| folded as versioned copies (class A) | 98,535 |
| folded as reissues (class A, rule A1) | 909 |
| merged as one document, two spellings (class D/E, rule E1) | 62 |
| disambiguated from a shared heading (class B, rule B2) | 134 |
| carrying a `~kind` discriminator (class C, rule C1) | 27,127 |
| leaf taken from a heading, no publisher number (class B, rule B1) | 11,407 |
| **lost to collisions** | **101 (0.00244%)** |

95.6% carry an official publisher URL.

**Rule B1 is the single largest recovery in the table.** 11,407 documents mint only because of it, over 10,000 of them the unnumbered blocks of federal appropriations acts, which the publisher addresses by the agency they fund rather than by a number.

#### What the last 27 collision groups are, and why they are not fixed here

They are one defect family, and none of them is an identifier problem: **the publisher assigns a number that our ingester did not store in `section_number`.**

| Documents | Where | What the publisher assigns | What we stored |
|---|---|---|---|
| 41 | `ms/regulations` | `7 MAC Pt. 100`, `Pt. 118`, ... | `section_number: None`, so 41 parts fall back to one shared heading |
| 34 | `pr/regulations` | nothing: the parser mis-split an article, see below | a mid-sentence fragment as a provision |
| 11 | `ca/agency-guidance` | an annually reissued notice | act_ids that do not relate |
| 9 | `federal/agency-guidance` | DFARS PGI `242.302-72`; two NLRB memos per case | `242.302`, losing the `-72`; one case number for both memos |
| 6 | `wy/regulations` | `Appendix A`, `Appendix B` | one section number `037.0001.0` for both |

Each could be closed by deriving a leaf from the publisher's navigation label. **That is deliberately not done.** It would add a derivation rule this specification does not contain, to a PERMANENT identifier, in order to work around ingesters that dropped a number they already had. The fix belongs in those ingesters. Mississippi is the clearest case: those 41 documents are unaddressable by section anywhere in the product, not merely here.

**One of them is worse than a collision, and it is the strongest argument in this document.** In Puerto Rico, `1390(c)-1` is a real article while `1390(c)(1)` carries a mid-sentence fragment as its title and its text begins mid-word. A parser had split an article's prose at a `(1)` marker and minted the fragment as a provision, because the guard that rejects a cross-reference spelled the Spanish contraction `del` as `de el` and so never matched it. Both normalize to `1390-c-1`, which is how they became visible.

The general lesson is the one worth carrying: **a collision count is a lower bound on a parser defect, not a measure of it.** A mis-parsed provision only shows up as a collision when it happens to land on a real sibling, so the visible number understated the actual defect by more than an order of magnitude. Anyone using an identifier scheme as a corpus check should expect the same ratio and go looking for the rest.

**So the scheme's failure rate on genuinely distinct provisions is effectively zero**, and everything it still flags is the corpus reporting a defect through it.

#### The identifier layer as a corpus check

Four serving defects have now been found this way, none of which any other check was looking for:

1. `mn/court-rules`: 33 rule sets served under 11 citations. Fixed and cut over.
2. `federal/session-laws`: 77 private laws labelled `Pub. L.` in navigation. Fixed and repaired.
3. `pr/regulations`: provisions carved out of other provisions' prose by a cross-reference guard that missed a contraction. Parser fixed; corpus repair in progress.
4. `ms`, `wy`, `federal` agency guidance: publisher numbers dropped at ingest, so a container number is doing a document number's job. Under repair.

The pattern is consistent: **a uniform address space is a consistency check that reads every document and fails wherever two documents are being served as one.** That is a reason to mint identifiers over our own corpus whether or not anyone else ever adopts them.

#### Rule A1: a shared publisher citation is evidence of one Work

Delaware issues `DE Domestic/Foreign Bulletin No. 138` in March 2023, 2024, 2025 and 2026, under one citation and one title. Four documents mint one identifier, and that is correct: the state addresses all four with a single reference, and the dates belong on the Expression layer.

**Where documents mint the same identifier AND share one non-empty publisher citation, they are one Work.** The most recent is published as the Work and the rest are recorded as superseded issues.

Nothing weaker qualifies. Not a shared heading, which sibling provisions routinely share; not a shared date; and never a blank citation, since absence of a citation is not agreement between citations. If the citations differ, all members are dropped under §6 rule 4 rather than the builder picking a winner by guess.

#### The corpus defect this surfaced: private laws labelled as public

`Pub. L. 106-1` and `Priv. L. 106-1` are different acts. The session-law ingester built its breadcrumb label with a hardcoded `Pub. L.` while the `display_path` and `citation` on the same payload correctly derived public versus private, so all 77 private-law documents were presented in navigation as public laws, and the two were collapsed onto one container path.

This is the second time an identifier collision has surfaced a serving defect that nothing else was checking, after `mn/STATE_RULES` in §5.2. **That is the argument for minting identifiers over our own corpus regardless of whether anyone else adopts them:** a uniform address space is a consistency check that reads every document, and it finds the places where two documents are being served as one.

Fixed by extracting one `law_label()` used by both the citation and the breadcrumb, and the 86 affected points were repaired in place on 2026-09-02. A re-ingest was deliberately NOT used: the defect is one payload field, `act_id` and `point_id` do not change, and the embedded text was already correct, so rebuilding 110,287 documents to correct 86 points would have been both wasteful and, per the `--resume` trap, likely to repair nothing at all. `federal/session-laws` now mints with zero collisions.

### 5.2 Two structural defects the audit found

The audit surfaced 762 documents colliding for reasons that were **not** the scheme's fault. They turned out to be two different things, and only one was fixable in the recovery layer.

#### Fixed: positional container numbers (`federal/AGENCY_GUIDANCE`, 491 → 49)

The USCIS Policy Manual's breadcrumb carries its real structure:

```json
[{"label": "Agency Guidance",       "type": "corpus"},
 {"label": "USCIS Policy Manual",   "type": "source",    "num": "uscis_pm"},
 {"label": "Volume 10 - Employment Authorization", "type": "container", "num": "0"},
 {"label": "Part A - Policies and Procedures",     "type": "container", "num": "1"},
 {"label": "USCIS Policy Manual, Vol. 10, Pt. A, Ch. 1", "type": "section", "num": "1"}]
```

Recovery produced `Agency Guidance / source uscis_pm / container 0`, losing both Volume and Part. Two bugs, both in `container_path()`:

1. **Any ancestor whose `num` matched the section number was deleted as a leaf.** The section is `1` and `Part A` carries `num=1`, so Part A was dropped for every chapter 1 in the manual. Only the *final* node may be the leaf.
2. **`type num` was preferred over `label` unconditionally.** For a `container` numbered 0, 1, 2 within its parent, the number is a positional index carrying no identity, and the label is the only thing separating Volume 10 from Volume 11.

Fixed by scoping the leaf test to the last node, and by preferring `label`/`name` for the positional types `container`, `corpus`, `source`, `doc`, `document`. A real publisher number (`title 44`) still wins over its name, so ordinary paths do not churn.

**Measured after the fix: 491 → 49.** Guarded by five regression tests.

#### Fixed and cut over on 2026-09-02: `mn/STATE_RULES` (271)

Minnesota's professional-rule sets are genuinely different documents that our payload could not distinguish:

```
SRULES_MN_PR_ADMI_R4   name: "Professional Rules (admi)"   chapter: pr   citation: Minn. R. Prof. 4
SRULES_MN_PR_BOAR_R4   name: "Professional Rules (boar)"   chapter: pr   citation: Minn. R. Prof. 4
SRULES_MN_PR_CLSB_R4   name: "Professional Rules (clsb)"   chapter: pr   citation: Minn. R. Prof. 4
```

`display_path`, `chapter`, `section_number` and **`citation` were byte-identical across all three**. The only discriminator was a parenthetical inside `name`.

**This was a corpus defect, not an identifier defect, and its consequence ran well beyond identifiers: distinct Minnesota rule sets were served under one citation, so our own citation resolution could not tell them apart either.**

Recovery MUST NOT be hacked to parse parentheticals out of a display string. That is exactly the fragile inference this specification forbids elsewhere. The fix belonged in the MN court-rules ingester, and it landed there: the citable unit is now the `(code, subtype)` pair, and the set's name is read from the publisher's own `<h2 class="subtype_header">` rather than tabulated or invented.

Two corrections to the finding as first written, both from fixing it:

- **The scale was understated.** This was described as three rule sets under one code. Enumerating the corpus found **33 distinct rule sets under 11 codes**, affecting 536 rules across `ap`, `dc`, `ju`, `ms` and `pr`. A code is a shelf, not a citable set.
- **`ju` was wrong, not merely ambiguous.** Every juvenile subtype was cited `Minn. R. Juv. P.`, the delinquency-rules form, so rules of juvenile *protection* procedure carried a citation belonging to a different set. An ambiguous identifier and an incorrect one are different failures, and only the second is silent.

The abbreviated citation form for a subtype is **not derivable**, and the fix does not invent one. Sets with no verified abbreviation cite by their full published name, which is longer but correct and traceable to the publisher's page.

**Landed 2026-09-02.** The re-ingest rewrote 2,397 points and a reconcile removed 126 superseded chunks of rules whose text had changed at the publisher. The corpus now carries all 33 rule sets as distinct chapters, and `mn/court-rules` mints 958 documents with **zero collisions**, where it had previously been blocked from minting entirely.

Two things the cutover taught, both worth carrying to the next corpus:

- **A missing sub-heading was the publisher being correct, not a parse failure.** `ap/rcap` has no `<h2 class="subtype_header">` because it IS the shelf's primary series, the Rules of Civil Appellate Procedure themselves, exactly as `kinds.json` says the primary series takes the bare leaf. A pre-flight over all 33 sets caught this before any write; treating it as a failure would have dropped 42 live appellate rules.
- **A 404 and an unreachable page are different events.** The ingester's `fetch` returned `None` for both, so a URL the publisher says does not exist was counted as a lost rule and the corpus fail-closed over two URLs that have never been rules. A 404 is evidence of absence and may be skipped; a timeout is not and must still fail the run.

---

## 6. Stability rules

1. **Never re-mint.** A corrective re-scrape, a re-source onto a new publisher, or a change of ingester MUST NOT change an identifier. This is the defect `act_id` has and the reason this layer exists.
2. **Recodification mints a new identifier and keeps the old one resolving.** When a publisher recodifies, the provision has a new address. The old identifier MUST continue to resolve, to a crosswalk record naming its successor. Arkansas 2025 is the worked example.
3. **Repeal does not delete an identifier.** A repealed provision keeps its identifier and gains a status. Absence of a provision is not absence of its address.
4. **A failed measurement never mints.** If the container path cannot be recovered, or the leaf cannot be derived, emit nothing. A wrong permanent identifier is worse than none.

---

## 7. Relationship to existing schemes

This scheme is deliberately shaped so that a deterministic mapping exists in both directions.

**USLM** (GPO, the US federal reference model) publishes `/us/usc/t17/s101` and versioned `/us/usc/t51@2013-02-01/s101`, live in every enrolled bill as `href` values. Open Law Library already serves the official DC Code at `/us/dc/council/code/sections/1-301.01`.

**Our `us/{jurisdiction}/{corpus}/...` shape is deliberately USLM-compatible**, and the `@date` and no-leading-digit-version rules are taken from it directly. USLM covers no state codes, no state regulations, no court rules and no agency guidance, which is precisely the gap this fills.

**The open question that decides extension-versus-fork:** whether GPO considers `/us/{state}/...` in scope, out of scope, or unclaimed. That is one email to the USLM maintainer and it should be sent before v1.0.

**Akoma Ntoso.** A deterministic two-way mapping to AKN FRBR URIs SHOULD be published alongside this spec. If a `us1:` identifier can emit a valid AKN expression URI on request, every AKN tool becomes a downstream consumer at zero cost and the "why another standard" objection dissolves.

Note the separator hazard when mapping: AKN uses `!` for component and `~` for portion; **USLM uses `!` for language**. We use `~` for kind and nothing for component. Detect the dialect before parsing anything foreign.

---

## 8. What ships with this specification

A specification alone is a document. Every dead effort in the prior-art survey published one. What makes this real:

1. **The concordance**, a CC0 mapping from every citation form we can parse to the canonical identifier and the official source URL.
2. **A free, unmetered, permanent resolver.**
3. **A conformance test corpus**, generated from the live corpus, including every collision named in §5.
4. **This document**, as ABNF plus a regex.

In that order. Crossref shipped a working linking service to twelve publishers before Crossref legally existed; the DOI sat unused for three years without one.

---

## 9. Open questions before v1.0

- [ ] Full-corpus collision audit across all 260 passes; name any class beyond A, B, C
- [ ] Enumerate every `~kind` value before first mint (they are permanent)
- [ ] Fix the corpus token vocabulary (15 public tokens today) and freeze it
- [ ] Decide `federal` versus a two-letter code for the federal jurisdiction
- [ ] GPO: is `/us/{state}/...` in scope, out of scope, or unclaimed?
- [ ] Publish the AKN FRBR URI mapping
- [ ] Governance: CC0 dedication drafted against successors; who may replace us as registrar; certified-provider prefixes; data escrow

## Changelog

**v0.1** (2026-08-31): first draft. Work layer only; Expression layer blocked on amendment history. Grammar, normalization and collision classes derived from a 5-jurisdiction audit of 323,757 documents. Not published.
