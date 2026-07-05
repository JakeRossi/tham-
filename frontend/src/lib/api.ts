// Minimal typed client stub for the backend API.
// Point BASE_URL at your local FastAPI server (default: http://localhost:8000).
// Fill this in as you build each screen -- shapes here match backend/app/api/*.py responses.

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface GeneratedProblem {
  drill_id: string;
  prompt: string;
  answer: string;
  difficulty: number;
  hints: string[];
}

export async function generateProblem(
  drillId: string,
  difficulty = 0.3
): Promise<GeneratedProblem> {
  const res = await fetch(`${BASE_URL}/api/problems/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ drill_id: drillId, difficulty }),
  });
  if (!res.ok) throw new Error(`generateProblem failed: ${res.status}`);
  return res.json();
}

export async function submitAnswer(
  problem: GeneratedProblem,
  submitted: string
): Promise<{ correct: boolean; feedback: string | null }> {
  const res = await fetch(`${BASE_URL}/api/problems/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      drill_id: problem.drill_id,
      prompt: problem.prompt,
      answer: problem.answer,
      submitted,
    }),
  });
  if (!res.ok) throw new Error(`submitAnswer failed: ${res.status}`);
  return res.json();
}

// TODO: startWarmup / nextWarmupProblem / recordWarmupAttempt,
// matching backend/app/api/sessions.py
// TODO: getLeaderboard / submitScore, matching backend/app/api/leaderboards.py
// TODO: uploadTextbook, matching backend/app/api/uploads.py
