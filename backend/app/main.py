from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import leaderboards, maps, problems, profile, sessions, uploads

app = FastAPI(title="math-osu", version="0.1.0")

# Loosen this before shipping -- fine for local dev against a Lovable/Vite frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(problems.router, prefix="/api/problems", tags=["problems"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(maps.router, prefix="/api/maps", tags=["maps"])
app.include_router(leaderboards.router, prefix="/api/leaderboards", tags=["leaderboards"])
app.include_router(uploads.router, prefix="/api/uploads", tags=["uploads"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])


@app.get("/api/health")
def health():
    return {"status": "ok"}
