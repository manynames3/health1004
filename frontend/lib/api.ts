import { AdminIngestResponse, AdminStatus, DocumentSummary, QueryResponse } from "../types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function askQuestion(question: string, topK: number): Promise<QueryResponse> {
  ensureApiConfigured();
  const response = await fetch(`${API_BASE_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, top_k: topK, include_sources: true })
  });
  if (!response.ok) {
    const detail = await readError(response);
    throw new Error(detail || `Query failed with status ${response.status}`);
  }
  return response.json();
}

export async function fetchDocuments(): Promise<DocumentSummary[]> {
  ensureApiConfigured();
  const response = await fetch(`${API_BASE_URL}/documents`, { cache: "no-store" });
  if (!response.ok) {
    const detail = await readError(response);
    throw new Error(detail || `Document fetch failed with status ${response.status}`);
  }
  const payload = await response.json();
  return payload.documents || [];
}

export async function fetchAdminStatus(adminToken: string): Promise<AdminStatus> {
  ensureApiConfigured();
  const response = await fetch(`${API_BASE_URL}/admin/status`, {
    headers: adminHeaders(adminToken),
    cache: "no-store"
  });
  if (!response.ok) {
    const detail = await readError(response);
    throw new Error(detail || `Admin status failed with status ${response.status}`);
  }
  return response.json();
}

export async function ingestAdminFiles({
  adminToken,
  files,
  force,
  s3Prefix
}: {
  adminToken: string;
  files: File[];
  force: boolean;
  s3Prefix: string;
}): Promise<AdminIngestResponse> {
  ensureApiConfigured();
  const form = new FormData();
  files.forEach((file) => form.append("files", file));
  form.append("force", String(force));
  form.append("s3_prefix", s3Prefix);

  const response = await fetch(`${API_BASE_URL}/admin/ingest`, {
    method: "POST",
    headers: adminHeaders(adminToken),
    body: form
  });
  if (!response.ok) {
    const detail = await readError(response);
    throw new Error(detail || `Admin ingestion failed with status ${response.status}`);
  }
  return response.json();
}

function adminHeaders(adminToken: string): HeadersInit {
  return {
    "X-Admin-Token": adminToken
  };
}

function ensureApiConfigured(): void {
  if (!process.env.NEXT_PUBLIC_API_BASE_URL) {
    throw new Error("API endpoint is not configured. Set NEXT_PUBLIC_API_BASE_URL to the deployed FastAPI backend URL.");
  }
}

async function readError(response: Response): Promise<string> {
  try {
    const payload = await response.json();
    return payload.detail || payload.message || "";
  } catch {
    return response.statusText;
  }
}
