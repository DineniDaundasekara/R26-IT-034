const API_BASE = (
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

async function readJson(response) {
  try {
    return await response.json();
  } catch {
    throw new Error("The backend returned an invalid response.");
  }
}

export async function healthCheck() {
  const response = await fetch(`${API_BASE}/health`);
  const body = await readJson(response);
  if (!response.ok) {
    throw new Error(body?.detail || "Backend health check failed.");
  }
  return body;
}

export async function analyzeAudio(file, context = {}) {
  const formData = new FormData();
  formData.append("audio", file);
  formData.append("target_role", context.targetRole || "");
  formData.append("experience_level", context.experienceLevel || "");
  formData.append("practice_goal", context.practiceGoal || "");

  const response = await fetch(`${API_BASE}/api/analyze/audio`, {
    method: "POST",
    body: formData,
  });

  const body = await readJson(response);
  if (!response.ok) {
    throw new Error(body?.detail || "Interview audio analysis failed.");
  }
  return body.data;
}

export async function askCoach(payload) {
  const response = await fetch(`${API_BASE}/api/coach/follow-up`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const body = await readJson(response);
  if (!response.ok) {
    throw new Error(body?.detail || "AI coach request failed.");
  }
  return body;
}
