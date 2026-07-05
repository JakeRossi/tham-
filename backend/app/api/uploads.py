"""
Textbook upload -> parsing pipeline entrypoint.

TODO: this is entirely a stub. The real pipeline (see app/ingestion/):
  1. textbook_parser.py   -- extract raw text/exercises from PDF/epub
  2. problem_extractor.py -- turn raw exercise text + answer key into
                              structured Problem-like objects (likely an
                              LLM call here, since exercise formatting
                              varies wildly across textbooks)
  3. map_builder.py        -- hash the structured problem set, write it to
                              content/textbook-maps/{hash}/, return the hash

This stub just accepts a file and returns a fake hash so the frontend has
something to integrate against before ingestion is built.
"""

from __future__ import annotations

import hashlib

from fastapi import APIRouter, UploadFile

router = APIRouter()


@router.post("")
async def upload_textbook(file: UploadFile):
    contents = await file.read()
    # Placeholder hash -- real implementation hashes the *parsed, structured*
    # problem set, not the raw file bytes (so re-scans/re-uploads of the same
    # edition still converge on one map -- see docs/MAP_HASHING.md).
    fake_hash = hashlib.sha256(contents).hexdigest()[:16]
    return {
        "status": "received",
        "filename": file.filename,
        "size_bytes": len(contents),
        "map_hash": fake_hash,
        "note": "Parsing pipeline not implemented yet -- see app/ingestion/",
    }
