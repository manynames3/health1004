import { DocumentSummary, QueryResponse } from "../types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function askQuestion(question: string, topK: number): Promise<QueryResponse> {
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
  const response = await fetch(`${API_BASE_URL}/documents`, { cache: "no-store" });
  if (!response.ok) {
    const detail = await readError(response);
    throw new Error(detail || `Document fetch failed with status ${response.status}`);
  }
  const payload = await response.json();
  return payload.documents || [];
}

async function readError(response: Response): Promise<string> {
  try {
    const payload = await response.json();
    return payload.detail || payload.message || "";
  } catch {
    return response.statusText;
  }
}
