# Governance

**Status: draft. Not adopted. Needs counsel review before publication.**

This document exists because of a specific finding: sophisticated adopters model
the mortality of a registry before they build on it, whether or not you address
it. ISO withdrew the ISTC standard in 2021 with the words *"in the absence of a
registration authority, existing registrations are inaccessible and new
registrations cannot be made."* No successor came forward, because there was no
going concern to inherit.

So the commitments below are made **before** anyone is asked to adopt anything.

## The problem this has to solve

Vaquill is a commercial vendor. Every competitor evaluating this identifier will
ask, correctly, why they should adopt an address space controlled by a rival.

The evidence says they are right to ask:

- **CUSIP** is what a vendor-run identifier becomes when it succeeds and is
  monetised: a licence fee for *storing the number in your own database*, an
  antitrust complaint alleging group boycott, and a federal statute now requiring
  agencies to use non-proprietary identifiers where practicable.
- **GRID** was free, CC0, genuinely good, and widely adopted, and it still hit a
  ceiling for exactly one reason, in Digital Science's own words: *"two open
  organisation identifiers could be perceived as competing against each other."*
  They donated it to ROR and retired their own identifier.

And one case shows a vendor *can* do this: **FIGI**. Bloomberg built it, still
operates it, and it is now written into SEC and CFTC filings. It works because
Bloomberg kept **operational** control and surrendered every form of **legal and
economic** control.

We copy FIGI.

## The five commitments

### 1. Public-domain dedication, not a licence

The identifier strings, the specification, and the registry are dedicated to the
public domain under CC0 1.0.

**CC0 is a waiver, not a licence**, and that distinction is the whole point.
Section 2 of the legal code has the Affirmer *"overtly, fully, permanently,
irrevocably and unconditionally"* waive, abandon and surrender the rights.
Surrendered rights cannot be reclaimed by a later owner of the company, because
there is nothing left to inherit. Standard CC0 already achieves what FIGI's
custom "successors and assigns" wording achieves; that language is emphasis, not
a different legal effect.

**The rights are therefore settled. What is not settled by any licence is the
service**, see commitment 5. CC0 cannot compel anyone to keep a resolver
running, and adopters know the difference.

### 2. A body other than Vaquill may replace us as registrar

**This is the clause that makes a competitor's adoption rational**, and it is
the one we must not water down.

FIGI's specification, held at the Object Management Group, states that *"the
organization that will serve as the Registration Authority shall be specified by
the Financial Services Domain Task Force of the OMG."* Bloomberg holds the role
at OMG's pleasure.

**We do not intend to found our own foundation.** The specification should be
donated to a body with pre-existing legitimacy in legal information. Candidates,
in rough order of fit:

- Cornell **Legal Information Institute**
- **Free Law Project**
- **AALL**, which already publishes the *Universal Citation Guide*
- a **NISO** workshop

Until such a body accepts it, this document is a unilateral commitment and should
be read as weaker than one.

### 3. Anyone may mint, without asking us

FIGI has Certified Providers who elect their own prefix and mint valid
identifiers with no involvement from Bloomberg. ARK has NAANs, where a tiny
central list of authorities each mint freely in their own namespace, 15 billion
identifiers, and nobody has ever paid an identifier fee.

Concretely: vLex, Fastcase, CourtListener, Casetext, Midpage or a state
legislature must be able to mint conformant identifiers using the published rules
and the published registry, with no key, no account, and no notification.

The rules are derivable by construction (see the specification, §0) precisely so
that this is true rather than merely permitted.

### 4. Free, unmetered, permanent resolution and bulk data

- Resolution is free and unmetered. Not a free tier.
- Bulk registry and crosswalk dumps are CC0 and published for download.
- **Neither the identifier nor the mapping table is ever monetised.**

Charging, if at all, is for the service layer around the registry, search,
change alerts, diffs, freshness guarantees, coverage SLAs, which is already our
business. This is Crossref's discipline: fees *"based on providing services not
metadata"* and *"independent of our members' own business models."*

Charging for the number is the CUSIP path.

### 5. A published succession plan and data escrow

Before the first external adopter is approached:

- A named escrow holder for the registry and the crosswalk.
- Published conditions under which the registrar role transfers.
- A commitment that if the role transfers, a **1:1 crosswalk is published in the
  final release**, and identifiers keep resolving through a documented,
  dated transition.

That last point is GRID's, and GRID is the model for how this should end. Every
GRID ID was mapped to a ROR ID in the final release, the transition was announced
and dated, and resolution continued until a stated cutoff. GRID died as a going
concern handed over. ISTC died as a liability nobody would take.

## Plan for the handover as the success case

If this works, one of two things happens:

1. A court, a uniform-law body, or a federal data mandate mints its own
   identifier and we become the crosswalk. This is what happened in India in
   February 2023, when the Supreme Court introduced neutral citation and both
   incumbent vendors pivoted to giving the crosswalk away free.
2. Governance pressure moves the registry to a neutral body, as with GRID.

**Both are good outcomes if we planned for them, and both are catastrophic if we
made product bets assuming otherwise.**

Accordingly: no product decision may depend on a competitor adopting this
identifier, and no revenue line may depend on exclusive control of it.

## What is deliberately NOT promised

- **That the specification will not change.** v0.1 is a draft. What is promised
  is that a *minted identifier* resolves forever; a revision that would change an
  existing string increments the version prefix instead. See specification §1.
- **That we will operate the registry indefinitely.** We will operate it until
  a better holder exists, and commitment 5 governs what happens then.
- **Formal standards-body status.** Not sought yet, and it costs nothing to
  defer. OASIS chartered a legal-citation committee in 2014 with the right
  people at the table; seven years later its page read *"This Committee has not
  produced technical work yet."* Working code and a running resolver come first.

## Open before publication

- [ ] Counsel drafts the CC0 dedication against successors and assigns
- [ ] Approach a candidate body about holding the specification
- [ ] Name the escrow holder
- [ ] Define the certified-provider prefix mechanism
- [ ] Decide whether the resolver is operated by Vaquill or jointly
