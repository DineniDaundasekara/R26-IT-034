const DEFAULT_API_URL = "http://localhost:5000";

export function getApiBaseUrl() {
  return (import.meta.env.VITE_API_URL || DEFAULT_API_URL).replace(/\/+$/, "");
}

async function request(path, options) {
  const base = getApiBaseUrl();
  const resp = await fetch(`${base}${path}`, options);
  const contentType = resp.headers.get("content-type") || "";

  let data;
  if (contentType.includes("application/json")) data = await resp.json();
  else data = await resp.text();

  if (!resp.ok) {
    const message =
      typeof data === "object" && data
        ? data.error || data.message || "Request failed"
        : String(data || "Request failed");
    const err = new Error(message);
    err.status = resp.status;
    throw err;
  }

  return data;
}

export async function healthCheck() {
  return request("/", { method: "GET" });
}

export async function analyzeText({ transcript, jobRole, jobDescription, question }) {
  return request("/api/analyze/text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ transcript, jobRole, jobDescription, question })
  });
}

export async function analyzeAudio({ file, jobRole, jobDescription, question }) {
  const form = new FormData();
  form.append("audio", file);
  if (jobRole) form.append("jobRole", jobRole);
  if (jobDescription) form.append("jobDescription", jobDescription);
  if (question) form.append("question", question);

  return request("/api/analyze/audio", {
    method: "POST",
    body: form
  });
}

export async function getHistory() {
  return request("/api/analyze/history", { method: "GET" });
}

export async function getTrainingSummary() {
  return request("/api/analyze/training-summary", { method: "GET" });
}

