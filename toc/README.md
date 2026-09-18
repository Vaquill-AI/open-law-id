# The holdings table of contents

The full title → chapter → subchapter → section tree of every provision in the corpus, for all 52 US jurisdictions and federal law, as one file you can grep.

**Around 5M rows: 4.5M+ sections and 390K+ containers.** The corpus grows, so the exact counts live in `toc-manifest.json` beside the artifact rather than here.

```text
toc.jsonl.gz        the tree, one JSON object per row
toc-manifest.json   per-jurisdiction, per-corpus counts
```

Rebuild it yourself from the published concordance, which is the point:

```bash
python toc/build_toc.py \
    --concordance concordance/dist/concordance.jsonl.gz \
    --out toc/dist
```

## What it answers

*"Do you have Montana Title 10, Chapter 1?"*

```bash
zcat toc.jsonl.gz | grep '"path":"mt/statutes/title-10/chapter-1"'
```

```json
{"kind":"container","path":"mt/statutes/title-10/chapter-1","sections_held":91,"children":12}
```

Ninety-one sections across twelve parts. Drill further and every leaf carries its official citation, its heading, and the publisher's own URL, so any row can be checked against the source:

```json
{"kind":"section","law_id":"us1:mt/statutes/title-10/chapter-1/part-10/10-1-1001",
 "citation":"Mont. Code Ann. § 10-1-1001","heading":"10-1-1001 Short title",
 "source_url":"https://mca.legmt.gov/bills/mca/title_0100/chapter_0010/..."}
```

## What it does not answer

🔴 **This proves holdings, not completeness, and the difference matters.**

Every row is derived from our own corpus. A gap in the corpus is therefore also a gap here: the file cannot report what it never saw. Read as *"here is what exists"*, it is circular reasoning. Read as *"here is what we hold, at this identifier, from this source URL"*, every row is checkable against the publisher by anyone who wants to.

Closing that loop needs a diff against each publisher's own table of contents, jurisdiction by jurisdiction and corpus by corpus. That is a separate artifact and a much larger build. Until it lands, nothing here should be described as proof that a corpus is complete.

## Container labels are not filled yet

`label` is `null` on every container in this build.

The identifier carries a container's slug and nothing else. For named corpora that is already readable (`alaska-rules-of-court`), but statutes and regulations are 74% of the leaves and their containers are bare numbers: `title-1/chapter-01.10`, `agency-100/chapter-100-x-1`. *"Title 1"* is weaker evidence than *"Title 1 - General Provisions"* for a reader checking whether their title is covered.

Those labels live in the corpus payloads rather than the concordance, so filling them takes a separate pass. The field is emitted as `null` now so that pass is a fill rather than a schema change, and so a consumer can tell *unlabelled* from *labelled empty*.

## Row shapes

**Container** — a title, chapter, subchapter or part.

| field | meaning |
| --- | --- |
| `path` | `<jurisdiction>/<corpus>/<slug>/...`, the identifier without the `us1:` scheme |
| `depth` | levels below the corpus root |
| `sections_held` | sections in the whole subtree, not just direct children |
| `children` | direct child containers |
| `label` | human-readable name, `null` until the fill pass |

**Section** — a leaf, one per provision, carrying `law_id`, `citation`, `heading`, `status` and `source_url`.

`sections_held` counts the entire subtree deliberately. Someone asking how much of Title 10 you hold means all of it, and a count that stopped at direct children would answer a question nobody asks.
