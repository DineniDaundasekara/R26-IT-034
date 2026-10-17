const API_BASE = (import.meta.env.VITE_API_URL || "").replace(/\/+$/, "");
const TOKEN_KEY = "pathready.auth.token";
const USER_KEY = "pathready.auth.user";

async function readJson(response) {
  try {
    return await response.json();
  } catch {
    throw new Error("The authentication service returned an invalid response.");
  }
}

function detailMessage(body, fallback) {
  const detail = body?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
  return fallback;
}

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

export function getStoredUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || "null");
  } catch {
    return null;
  }
}

export function persistSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export async function registerAccount({ fullName, email, password }) {
  const response = await fetch(`${API_BASE}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fullName, email, password }),
  });
  const body = await readJson(response);
  if (!response.ok) {
    throw new Error(detailMessage(body, "Unable to create your account."));
  }
  persistSession(body.token, body.user);
  return body.user;
}

export async function loginAccount({ email, password }) {
  const response = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const body = await readJson(response);
  if (!response.ok) {
    throw new Error(detailMessage(body, "Unable to sign in."));
  }
  persistSession(body.token, body.user);
  return body.user;
}

export async function restoreSession() {
  const token = getStoredToken();
  if (!token) return null;

  const response = await fetch(`${API_BASE}/api/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const body = await readJson(response);
  if (!response.ok) {
    clearSession();
    return null;
  }
  persistSession(token, body.user);
  return body.user;
}

export async function logoutAccount() {
  const token = getStoredToken();
  try {
    if (token) {
      await fetch(`${API_BASE}/api/auth/logout`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
    }
  } finally {
    clearSession();
  }
}
