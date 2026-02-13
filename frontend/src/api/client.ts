import type {
  PaperListItem,
  PaperDetail,
  SubmitPaperRequest,
  SubmitPaperResponse,
  ChatRequest,
  ChatResponse,
} from "../types/paper";

const BASE = "/api/v1";

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json();
}

export async function fetchPapers(params: {
  page?: number;
  page_size?: number;
  category?: string;
  status?: string;
}): Promise<PaperListItem[]> {
  const query = new URLSearchParams();
  if (params.page) query.set("page", String(params.page));
  if (params.page_size) query.set("page_size", String(params.page_size));
  if (params.category) query.set("category", params.category);
  if (params.status) query.set("status", params.status);
  return request<PaperListItem[]>(`${BASE}/papers?${query}`);
}

export async function fetchPaper(id: number): Promise<PaperDetail> {
  return request<PaperDetail>(`${BASE}/papers/${id}`);
}

export async function submitPapers(
  body: SubmitPaperRequest,
): Promise<SubmitPaperResponse> {
  return request<SubmitPaperResponse>(`${BASE}/papers/submit`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function triggerCrawl(): Promise<{
  status: string;
  task_id: string;
}> {
  return request(`${BASE}/tasks/crawl`, { method: "POST" });
}

export async function fetchTaskStatus(
  taskId: string,
): Promise<{ task_id: string; status: string; result?: string; error?: string }> {
  return request(`${BASE}/tasks/${taskId}`);
}

export async function chat(body: ChatRequest): Promise<ChatResponse> {
  return request<ChatResponse>(`${BASE}/chat`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}
