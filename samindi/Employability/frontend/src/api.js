// Unified API Client for PathReady AI Suite

import { getStoredToken } from "./authApi.js";

const API_BASE = (import.meta.env.VITE_API_URL || "").replace(/\/+$/, "");

async function readJson(response) {
  try {
    return await response.json();
  } catch {
    throw new Error("The backend returned an invalid response.");
  }
}

function authHeaders() {
  const token = getStoredToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function healthCheck() {
  const response = await fetch(`${API_BASE}/api/health`);
  const body = await readJson(response);
  if (!response.ok) {
    throw new Error(body?.detail || "Backend health check failed.");
  }
  return body;
}

export async function getModules() {
  const response = await fetch(`${API_BASE}/api/modules`);
  const body = await readJson(response);
  if (!response.ok) {
    throw new Error(body?.detail || "Failed to fetch modules list.");
  }
  return body.modules || [];
}

// ---------------------------------------------------------------------------
// Component 1: InterviewReady (Communication Skill Guidance)
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// Component 2: CareerLens (CV Based Career Path Guidance)
// ---------------------------------------------------------------------------

export async function analyzeCv({ file, jobRole, location = "Sri Lanka" }) {
  const formData = new FormData();
  formData.append("cv", file);
  formData.append("job_role", jobRole);
  formData.append("location", location);
  formData.append("max_jobs", "5");

  const response = await fetch(`${API_BASE}/api/analyze-cv`, {
    method: "POST",
    body: formData,
  });

  const body = await readJson(response);
  if (!response.ok) {
    const detail = body?.detail || body?.message || `CV Analysis failed (HTTP ${response.status})`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return body;
}

export async function getJobs(jobRole, location = "Sri Lanka", limit = 5) {
  const params = new URLSearchParams({
    job_role: jobRole,
    location: location,
    limit: String(limit),
  });

  const response = await fetch(`${API_BASE}/api/jobs?${params.toString()}`);
  const body = await readJson(response);
  if (!response.ok) {
    throw new Error(body?.detail || "Job retrieval failed.");
  }
  return body;
}

// ---------------------------------------------------------------------------
// Component 3: Career Risk (Career Safety & Industry Stability Analysis)
// ---------------------------------------------------------------------------

export async function predictCareerRisk(profile) {
  const response = await fetch(`${API_BASE}/api/career-risk/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });

  const body = await readJson(response);
  if (!response.ok) {
    throw new Error(body?.detail || "Career risk estimation failed.");
  }
  return body;
}

export async function getCareerRiskHistory(limit = 50) {
  const response = await fetch(`${API_BASE}/api/career-risk/history?limit=${limit}`);
  const body = await readJson(response);
  if (!response.ok) {
    throw new Error(body?.detail || "Unable to load career risk history.");
  }
  return body.items || [];
}

export async function getCareerRiskHistoryItem(id) {
  const response = await fetch(`${API_BASE}/api/career-risk/history/${id}`);
  const body = await readJson(response);
  if (!response.ok) {
    throw new Error(body?.detail || "Unable to open this saved assessment.");
  }
  return body;
}

export async function deleteCareerRiskHistoryItem(id) {
  const response = await fetch(`${API_BASE}/api/career-risk/history/${id}`, {
    method: "DELETE",
  });
  const body = await readJson(response);
  if (!response.ok) {
    throw new Error(body?.detail || "Unable to delete this assessment.");
  }
  return body;
}

// ---------------------------------------------------------------------------
// Component 5: Employability Simulator (Behaviour-Aware Career Simulation)
// ---------------------------------------------------------------------------

export async function checkEmployabilityHealth(phaseId) {
  const response = await fetch(`${API_BASE}/api/employability/${phaseId}/health`);
  const body = await readJson(response);
  if (!response.ok) {
    throw new Error(body?.detail || "Employability model health check failed.");
  }
  return body;
}

export async function predictEmployability(phaseId, responses) {
  const response = await fetch(`${API_BASE}/api/employability/${phaseId}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(responses),
  });
  const body = await readJson(response);
  if (!response.ok) {
    throw new Error(body?.detail || "Employability prediction failed.");
  }
  return body;
}

export async function simulateEmployability(phaseId, responses, overrides) {
  const response = await fetch(`${API_BASE}/api/employability/${phaseId}/what-if`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ responses, overrides }),
  });
  const body = await readJson(response);
  if (!response.ok) {
    throw new Error(body?.detail || "Employability what-if failed.");
  }
  return body;
}

// ---------------------------------------------------------------------------
// Component 6: HR Candidate Selection (admin-only candidate verification)
// ---------------------------------------------------------------------------

export async function checkHRCandidatesHealth() {
  const response = await fetch(`${API_BASE}/api/hr-candidates/health`, {
    headers: { ...authHeaders() },
  });
  const body = await readJson(response);
  if (!response.ok) {
    throw new Error(body?.detail || "HR candidate service health check failed.");
  }
  return body;
}

export async function getHRCandidateRoles() {
  const response = await fetch(`${API_BASE}/api/hr-candidates/roles`, {
    headers: { ...authHeaders() },
  });
  const body = await readJson(response);
  if (!response.ok) {
    throw new Error(body?.detail || "Unable to load job role profiles.");
  }
  return body;
}

export async function assessHRCandidate(formData) {
  const response = await fetch(`${API_BASE}/api/hr-candidates/candidates/assess`, {
    method: "POST",
    headers: { ...authHeaders() },
    body: formData,
  });
  const body = await readJson(response);
  if (!response.ok) {
    throw new Error(body?.detail || "Candidate verification failed.");
  }
  return body;
}

export async function getHRCandidates() {
  const response = await fetch(`${API_BASE}/api/hr-candidates/candidates`, {
    headers: { ...authHeaders() },
  });
  const body = await readJson(response);
  if (!response.ok) {
    throw new Error(body?.detail || "Unable to load candidate history.");
  }
  return body;
}

export async function getHRCandidateDetail(assessmentId) {
  const response = await fetch(`${API_BASE}/api/hr-candidates/candidates/${assessmentId}`, {
    headers: { ...authHeaders() },
  });
  const body = await readJson(response);
  if (!response.ok) {
    throw new Error(body?.detail || "Unable to load candidate detail.");
  }
  return body;
}

export async function recordHRCandidateDecision(assessmentId, payload) {
  const response = await fetch(`${API_BASE}/api/hr-candidates/candidates/${assessmentId}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(payload),
  });
  const body = await readJson(response);
  if (!response.ok) {
    throw new Error(body?.detail || "Failed to save decision.");
  }
  return body;
}

export async function deleteHRCandidate(assessmentId) {
  const response = await fetch(`${API_BASE}/api/hr-candidates/candidates/${assessmentId}`, {
    method: "DELETE",
    headers: { ...authHeaders() },
  });
  const body = await readJson(response);
  if (!response.ok) {
    throw new Error(body?.detail || "Failed to delete candidate.");
  }
  return body;
}

export async function getHRCandidatesAblationResults() {
  const response = await fetch(`${API_BASE}/api/hr-candidates/ablation`, {
    headers: { ...authHeaders() },
  });
  const body = await readJson(response);
  if (!response.ok) {
    throw new Error(body?.detail || "Failed to load ablation metrics.");
  }
  return body;
}

