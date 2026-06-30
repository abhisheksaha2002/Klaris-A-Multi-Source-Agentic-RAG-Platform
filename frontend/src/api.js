const API_BASE = "http://localhost:8000/api/v1";

export async function registerUser(email, password) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Registration failed");
  }
  return res.json();
}

export async function loginUser(email, password) {
  const body = new URLSearchParams();
  body.append("username", email);
  body.append("password", password);

  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Login failed");
  }
  return res.json();
}

export async function ingestUrl(token, url) {
  const res = await fetch(`${API_BASE}/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ url }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Ingestion failed");
  }
  return res.json();
}

export async function queryKnowledgeBase(token, question) {
  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ question, top_k: 5 }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Query failed");
  }
  return res.json();
}

// NEW in Phase 4

export async function getMySources(token) {
  const res = await fetch(`${API_BASE}/sources`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Could not load sources");
  }
  return res.json(); // array of { source_url, source_type, chunk_count }
}

export async function synthesizeAcrossSources(token, question, sourceUrls = []) {
  const res = await fetch(`${API_BASE}/synthesize`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ question, source_urls: sourceUrls }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Synthesis failed");
  }
  return res.json();
}
