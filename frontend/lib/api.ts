import type {
  ChatResponse,
  Business,
  CreateBusinessPayload,
  ExecutePayload,
  ExecuteResponse,
  Workstream,
  Document,
  GenerateDocumentPayload,
  CommunicationPayload,
  CommunicationResponse,
  HealthResponse,
} from "./types";

const BASE_URL = "/api";

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
    ...options,
  });

  if (!res.ok) {
    const errorBody = await res.text().catch(() => "");
    throw new Error(
      `API Error ${res.status}: ${res.statusText}${errorBody ? ` - ${errorBody}` : ""}`
    );
  }

  return res.json() as Promise<T>;
}

export async function sendChat(
  founder_id: string,
  message: string,
  business_id?: string
): Promise<ChatResponse> {
  return request<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify({ founder_id, message, business_id }),
  });
}

export async function createBusiness(
  payload: CreateBusinessPayload
): Promise<Business> {
  return request<Business>("/business", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getBusiness(business_id: string): Promise<Business> {
  return request<Business>(`/business/${business_id}`);
}

export async function executeObjective(
  payload: ExecutePayload
): Promise<ExecuteResponse> {
  return request<ExecuteResponse>("/execute", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getWorkstreams(
  business_id: string
): Promise<Workstream[]> {
  return request<Workstream[]>(`/workstreams/${business_id}`);
}

export async function generateDocument(
  payload: GenerateDocumentPayload
): Promise<Document> {
  return request<Document>("/documents/generate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getDocument(doc_id: string): Promise<Document> {
  return request<Document>(`/documents/${doc_id}`);
}

export async function listDocuments(business_id: string): Promise<Document[]> {
  return request<Document[]>(`/documents?business_id=${business_id}`);
}

export async function startCommunicationSession(
  payload: CommunicationPayload
): Promise<CommunicationResponse> {
  return request<CommunicationResponse>("/communication/session", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function healthCheck(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}
