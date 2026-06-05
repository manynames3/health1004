import {
  AdminIngestResponse,
  AdminReviewTagResponse,
  AdminStatus,
  DocumentListResponse,
  DocumentSummary,
  PassageListResponse,
  QueryResponse,
  ResolvedQuery,
  TaxonomyResponse,
  TopicDetail,
  TopicListResponse
} from "../types";

const DEPLOYED_API_BASE_URL = "https://aehcnrpvn6k72yujza47cam43a0jervq.lambda-url.us-east-1.on.aws";
const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL || DEPLOYED_API_BASE_URL).replace(/\/+$/, "");

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

export async function fetchDocuments({
  query = "",
  limit = 25,
  offset = 0
}: {
  query?: string;
  limit?: number;
  offset?: number;
} = {}): Promise<DocumentListResponse> {
  ensureApiConfigured();
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (query.trim()) params.set("q", query.trim());
  const response = await fetch(`${API_BASE_URL}/documents?${params}`, { cache: "no-store" });
  if (!response.ok) {
    const detail = await readError(response);
    throw new Error(detail || `Document fetch failed with status ${response.status}`);
  }
  const payload = await response.json();
  const documents = payload.documents || [];
  return {
    documents,
    total: typeof payload.total === "number" ? payload.total : documents.length,
    limit: typeof payload.limit === "number" ? payload.limit : limit,
    offset: typeof payload.offset === "number" ? payload.offset : offset
  };
}

export async function fetchDocument(documentId: string): Promise<DocumentSummary> {
  ensureApiConfigured();
  const response = await fetch(`${API_BASE_URL}/documents/${encodeURIComponent(documentId)}`, { cache: "no-store" });
  if (!response.ok) {
    const detail = await readError(response);
    throw new Error(detail || `Document fetch failed with status ${response.status}`);
  }
  return response.json();
}

export async function fetchTaxonomy(): Promise<TaxonomyResponse> {
  ensureApiConfigured();
  const response = await fetch(`${API_BASE_URL}/taxonomy`);
  if (!response.ok) {
    const detail = await readError(response);
    throw new Error(detail || `Taxonomy fetch failed with status ${response.status}`);
  }
  return response.json();
}

export async function fetchTopics(path = "/topics"): Promise<TopicListResponse> {
  ensureApiConfigured();
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    const detail = await readError(response);
    throw new Error(detail || `Topic fetch failed with status ${response.status}`);
  }
  return response.json();
}

export async function fetchTopic(slug: string): Promise<TopicDetail> {
  ensureApiConfigured();
  const response = await fetch(`${API_BASE_URL}/topics/${encodeURIComponent(slug)}`, { cache: "no-store" });
  if (!response.ok) {
    const detail = await readError(response);
    throw new Error(detail || `Topic detail failed with status ${response.status}`);
  }
  return response.json();
}

export async function fetchPassages(topic: string, limit = 20): Promise<PassageListResponse> {
  ensureApiConfigured();
  const params = new URLSearchParams({ topic, limit: String(limit) });
  const response = await fetch(`${API_BASE_URL}/passages?${params}`, { cache: "no-store" });
  if (!response.ok) {
    const detail = await readError(response);
    throw new Error(detail || `Passage fetch failed with status ${response.status}`);
  }
  return response.json();
}

export async function resolveArchiveQuery(query: string): Promise<ResolvedQuery> {
  ensureApiConfigured();
  const response = await fetch(`${API_BASE_URL}/query/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query })
  });
  if (!response.ok) {
    const detail = await readError(response);
    throw new Error(detail || `Query resolution failed with status ${response.status}`);
  }
  return response.json();
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

export async function fetchLowConfidencePassages(adminPassword: string): Promise<PassageListResponse> {
  ensureApiConfigured();
  const response = await fetch(`${API_BASE_URL}/admin/low-confidence-passages`, {
    headers: adminPassword ? { "X-Admin-Password": adminPassword } : {},
    cache: "no-store"
  });
  if (!response.ok) {
    const detail = await readError(response);
    throw new Error(detail || `Review queue fetch failed with status ${response.status}`);
  }
  return response.json();
}

export async function reviewTag({
  adminPassword,
  chunkId,
  topicSlugs,
  confidenceScore,
  needsHumanReview
}: {
  adminPassword: string;
  chunkId: string;
  topicSlugs: string[];
  confidenceScore: number;
  needsHumanReview: boolean;
}): Promise<AdminReviewTagResponse> {
  ensureApiConfigured();
  const response = await fetch(`${API_BASE_URL}/admin/review-tag`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(adminPassword ? { "X-Admin-Password": adminPassword } : {})
    },
    body: JSON.stringify({
      chunk_id: chunkId,
      topic_slugs: topicSlugs,
      confidence_score: confidenceScore,
      needs_human_review: needsHumanReview
    })
  });
  if (!response.ok) {
    const detail = await readError(response);
    throw new Error(detail || `Review update failed with status ${response.status}`);
  }
  return response.json();
}

function adminHeaders(adminToken: string): HeadersInit {
  return {
    "X-Admin-Token": adminToken
  };
}

function ensureApiConfigured(): void {
  if (!API_BASE_URL) {
    throw new Error("API endpoint is unavailable.");
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
