import type { Paper, PaperDetail, PaperSummary, UploadResponse } from "./types";

// Set NEXT_PUBLIC_API_URL in .env.local when deploying; defaults to local dev backend.
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
    this.name = "ApiError";
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(
      body.detail ?? `Request failed with status ${res.status}`,
      res.status
    );
  }
  return res.json();
}

export async function uploadPaper(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/papers/upload`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<UploadResponse>(res);
}

export async function listPapers(): Promise<Paper[]> {
  const res = await fetch(`${API_BASE}/papers`, { cache: "no-store" });
  return handleResponse<Paper[]>(res);
}

export async function getPaper(paperId: string): Promise<PaperDetail> {
  const res = await fetch(`${API_BASE}/papers/${paperId}`, {
    cache: "no-store",
  });
  return handleResponse<PaperDetail>(res);
}

export async function getPaperSummary(paperId: string): Promise<PaperSummary> {
  const res = await fetch(`${API_BASE}/papers/${paperId}/summary`, {
    cache: "no-store",
  });
  return handleResponse<PaperSummary>(res);
}

export async function askAboutPaper(
  paperId: string,
  question: string
): Promise<{ answer: string }> {
  const res = await fetch(`${API_BASE}/papers/${paperId}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  return handleResponse<{ answer: string }>(res);
}

export { ApiError };
