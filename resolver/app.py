#!/usr/bin/env python3
"""The resolver as a running service. Free, unmetered, no account.

    uvicorn resolver.app:app --port 8080

    GET /resolve?citation=Mont.+Code+Ann.+10-1-1001
    GET /id/vq1:us/mt/statutes/title-10/chapter-1/part-10/10-1-1001
    GET /healthz

THREE THINGS THIS DELIBERATELY DOES NOT HAVE
* **No API key, no quota, no rate limit tied to identity.** Governance
  commitment 4: resolution is free and unmetered, not a free tier. Metering the
  resolver is the CUSIP path, which ended in an antitrust complaint and a
  federal statute requiring non-proprietary identifiers.
* **No write path.** The index is opened immutable. A resolver that can be
  written to is a resolver whose answers can be changed.
* **No dependency on our corpus.** It serves a SQLite file built from the
  published CC0 concordance, so anyone can run an identical one.

A 404 IS A REAL ANSWER
An unresolvable citation returns 404 with the normalized key that was looked up,
because "we hold no such provision" and "your citation did not parse the way you
expected" are different problems and the caller needs to tell them apart.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

sys.path.insert(0, str(Path(__file__).resolve().parent))

from vqresolve import Resolver, citation_key

INDEX = Path(
    os.environ.get(
        "VQ_RESOLVER_INDEX", str(Path(__file__).resolve().parent / "dist/resolver.sqlite")
    )
)

app = FastAPI(
    title="Vaquill Law Identifier resolver",
    description=(
        "Resolve a United States legal citation to its canonical identifier and "
        "the official publisher URL. Free and unmetered. The identifier itself is "
        "computable offline with `vqlaw.mint`; this service is only the crosswalk."
    ),
    version="0.1",
)

_resolver: Resolver | None = None


def resolver() -> Resolver:
    global _resolver
    if _resolver is None:
        _resolver = Resolver(INDEX)
    return _resolver


def _payload(hit: Any) -> dict[str, Any]:
    return {
        "id": hit.vq,
        "jurisdiction": hit.jurisdiction,
        "corpus": hit.corpus,
        "citation": hit.citation,
        "heading": hit.heading,
        "status": hit.status,
        "sourceUrl": hit.source_url,
        # Stated, not implied. A null sourceUrl means we hold no OFFICIAL
        # publisher link, never that the provision does not exist.
        "sourceIsOfficial": hit.is_official,
    }


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {"ok": True, "index": str(INDEX), **resolver().stats()}


@app.get("/resolve")
def resolve(
    citation: str = Query(..., min_length=2, description="A US legal citation, any spelling."),
    jurisdiction: str | None = Query(None, min_length=2, max_length=8),
) -> JSONResponse:
    """A citation to every provision that matches it.

    Always a LIST. A citation is not always unique, and returning the first
    match would answer a question the caller did not ask.
    """
    hits = resolver().resolve(citation, jurisdiction=jurisdiction)
    if not hits:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "no provision matches that citation",
                "citation": citation,
                "normalizedKey": citation_key(citation),
            },
        )
    return JSONResponse({"count": len(hits), "results": [_payload(h) for h in hits]})


@app.get("/id/{identifier:path}")
def by_id(identifier: str) -> dict[str, Any]:
    """An identifier to its provision."""
    hit = resolver().lookup(identifier)
    if hit is None:
        raise HTTPException(
            status_code=404, detail={"message": "unknown identifier", "id": identifier}
        )
    return _payload(hit)
