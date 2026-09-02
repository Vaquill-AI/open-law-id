# The registry

Three tables, held as files in version control. Not a database, not an API, not
a standards body.

That is deliberate. ECLI, the one legal identifier standard that actually
achieved adoption, delegates exactly two things to each jurisdiction — the list
of courts that get a code, and how the ordinal is composed — and publishes both
as a table maintained by a named person. It reached roughly 14.7 million indexed
decisions on that basis. ARK's NAAN registry is the same shape: a small central
list of authorities, each minting freely in its own namespace, 15 billion
identifiers, and nobody has ever paid a fee to mint one.

A registry you can read in a text editor and change by pull request is a registry
other people can trust and audit. A registry behind an API is a dependency on us.

## The files

| File | What it fixes | Additions |
|---|---|---|
| `jurisdictions.json` | the 53 jurisdiction codes | rare; a new US jurisdiction |
| `corpora.json` | the closed corpus vocabulary, 13 slugs | by pull request, see below |
| `kinds.json` | the `~kind` discriminators | **permanent once used** |

## Why the vocabularies are closed

ELI made every URI component optional and orderable to taste. The consequence,
in the words of its own technical guide, is that components *"are all optional,
and can be used in any order"* — so **no single parser can read an ELI**, and
France publishes two canonical identifiers for the same act on purpose.

ECLI fixed five mandatory ordered components and forbade extension. One regex
validates a Bulgarian ECLI without knowing anything about Bulgaria.

We are copying ECLI. A closed vocabulary is the price.

## Adding a corpus slug

Open a pull request against `corpora.json` with:

1. The proposed slug: lowercase, hyphenated, `[a-z-]+`.
2. What body of law it names, and which publisher issues it.
3. Why an existing slug does not fit. **This is the part that gets scrutiny.**
4. At least twenty real example identifiers under the proposed slug.

Two rules that will be applied to your proposal, both learned from the
AKN4Africa recommendation, which had to live with getting them wrong:

- **Never both a singular and a plural form.** Once `court-rules` exists,
  `court-rule` can never exist. Map out the whole vocabulary before proposing,
  because the first spelling wins forever.
- **A slug must not repeat what the jurisdiction already says.** This is why
  there is one `agency-guidance` and not a separate `state-agency-guidance`: the
  jurisdiction field already distinguishes `federal` from `mn`. Fifteen internal
  vocabulary tokens collapse to thirteen public slugs for exactly this reason.

## Adding a `~kind`

`~kind` disambiguates parallel series inside one container, where a publisher
issues both "Rule 3" and "Form 3" and both are genuinely different documents.

**A `~kind` value is permanent from the first identifier that uses it.** There is
no deprecation path, because a deprecated kind would break every citation of
every identifier carrying it.

So kinds must be enumerated per corpus **before** minting begins for that corpus,
not discovered as collisions appear. This is the AKN4Africa lesson stated
plainly: once `pn` is taken by Provincial Notice, Premier's Notice has to become
`premn` forever.

## What the registry does NOT contain

- **Anything derivable.** If a value can be computed from the citation by the
  published rules, it does not belong here. The registry fixes vocabularies, not
  data.
- **Container paths.** Those come from the publisher's own structure, per
  specification §4.3.
- **Any mapping to Vaquill's internal identifiers.** That crosswalk is published
  separately and is not needed to mint or validate an identifier. Nobody should
  need our data to use this scheme.

## Provenance of the current tables

`jurisdictions.json` and `corpora.json` were derived on 2026-08-31 by
enumerating a live 4,093,000-document corpus, not by hand. Jurisdiction codes
carry their OCD division id (`ocd-division/country:us/state:XX`), which is the de
facto US jurisdiction key in civic data, so this table can be joined against
Open States and related datasets without a mapping step.

`kinds.json` is **not yet populated**. It is an open gate: minting cannot begin
for a corpus until its kinds are enumerated.
