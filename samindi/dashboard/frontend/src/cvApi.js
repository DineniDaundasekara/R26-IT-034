const API_BASE = (import.meta.env.VITE_CV_API_URL || "http://127.0.0.1:8001").replace(/\/$/, "");

async function parseResponse(response) {
  let payload = {};
  try {
    payload = await response.json();
  } catch {
    // Keep the status-based fallback below.
  }

  if (!response.ok) {
    const detail = payload?.detail || payload?.message || `Request failed with HTTP ${response.status}`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return payload;
}

export async function analyzeCv({ file, jobRole, location = "Sri Lanka" }) {
  const formData = new FormData();
  formData.append("cv", file);
  formData.append("job_role", jobRole);
  formData.append("location", location);
  formData.append("max_jobs", "5");

  let response;
  try {
    response = await fetch(`${API_BASE}/api/analyze-cv`, {
      method: "POST",
      body: formData,
    });
  } catch (err) {
    throw new Error(
      "Cannot reach the CareerLens API. Start the backend on http://127.0.0.1:8001 and try again."
    );
  }
  return parseResponse(response);
}
