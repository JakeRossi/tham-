"""
"Map" = a shareable drillset identity, either one of the builtin drills
(content/builtin-drills/*.json) or a user-uploaded textbook that's been
parsed into content/textbook-maps/{hash}/.

Everyone who uploads the same textbook edition converges on the same map
hash, so they land on the same leaderboard -- see docs/MAP_HASHING.md.

TODO: this is a stub returning builtin drills only. Wire up textbook-maps/
once app/ingestion/map_builder.py is implemented.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter()

CONTENT_DIR = Path(__file__).resolve().parents[3] / "content"


@router.get("/builtin")
def list_builtin_maps():
    drill_dir = CONTENT_DIR / "builtin-drills"
    maps = []
    for f in sorted(drill_dir.glob("*.json")):
        maps.append(json.loads(f.read_text()))
    return {"maps": maps}


@router.get("/textbook/{map_hash}")
def get_textbook_map(map_hash: str):
    meta_path = CONTENT_DIR / "textbook-maps" / map_hash / "meta.json"
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="Unknown map_hash.")
    return json.loads(meta_path.read_text())
