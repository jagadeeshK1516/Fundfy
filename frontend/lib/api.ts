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

let _sessionToken: string | null = null;

export function setSessionToken(token: string | null) {
  _sessionToken = token;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string> || {}),
  };

  if (_sessionToken) {
    headers["Authorization"] = `Bearer ${_sessionToken}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
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

// --- Phase C API Functions ---

// Google OAuth
export async function getGoogleAuthUrl() {
  return request<{ auth_url: string }>("/integrations/google/auth-url");
}

export async function googleCallback(code: string, state?: string) {
  return request("/integrations/google/callback", {
    method: "POST",
    body: JSON.stringify({ code, state }),
  });
}

export async function getGoogleStatus() {
  return request<{ connected: boolean; scopes?: string[] }>("/integrations/google/status");
}

export async function disconnectGoogle() {
  return request("/integrations/google/disconnect", { method: "DELETE" });
}

// Email Approvals
export async function getPendingEmails() {
  return request<any[]>("/emails/pending");
}

export async function approveEmail(emailId: string) {
  return request(`/emails/${emailId}/approve`, { method: "POST" });
}

export async function rejectEmail(emailId: string) {
  return request(`/emails/${emailId}/reject`, { method: "POST" });
}

// Calendar
export async function getCalendarEvents(timeMin?: string, timeMax?: string) {
  const params = new URLSearchParams();
  if (timeMin) params.set("time_min", timeMin);
  if (timeMax) params.set("time_max", timeMax);
  return request<{ events: any[]; connected: boolean }>(`/calendar/events?${params}`);
}

export async function createCalendarEvent(payload: { summary: string; start: string; end: string; attendees?: string[]; meet_link?: boolean }) {
  return request("/calendar/events", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function checkCalendarAvailability(timeMin: string, timeMax: string) {
  return request<{ busy_slots: any[] }>(`/calendar/availability?time_min=${timeMin}&time_max=${timeMax}`);
}

// CRM
export async function getCRMContacts(filters?: { type?: string; pipeline_stage?: string; query?: string }) {
  const params = new URLSearchParams();
  if (filters?.type) params.set("type", filters.type);
  if (filters?.pipeline_stage) params.set("pipeline_stage", filters.pipeline_stage);
  if (filters?.query) params.set("query", filters.query);
  return request<{ contacts: any[]; count: number }>(`/crm/contacts?${params}`);
}

export async function addCRMContact(data: { name: string; email?: string; company?: string; role?: string; type?: string }) {
  return request("/crm/contacts", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateCRMContact(contactId: string, data: Record<string, any>) {
  return request(`/crm/contacts/${contactId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function getCRMPipeline() {
  return request<{ pipeline: Record<string, number> }>("/crm/pipeline");
}

export async function getContactInteractions(contactId: string) {
  return request<{ interactions: any[] }>(`/crm/contacts/${contactId}/interactions`);
}

export async function logContactInteraction(contactId: string, data: { type: string; summary: string; details?: string }) {
  return request(`/crm/contacts/${contactId}/interactions`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// Investors
export async function searchInvestors(filters?: { stage?: string; industry?: string; location?: string }) {
  const params = new URLSearchParams();
  if (filters?.stage) params.set("stage", filters.stage);
  if (filters?.industry) params.set("industry", filters.industry);
  if (filters?.location) params.set("location", filters.location);
  return request<{ investors: any[]; count: number }>(`/investors?${params}`);
}

export async function getInvestor(investorId: string) {
  return request(`/investors/${investorId}`);
}

export async function addInvestor(data: Record<string, any>) {
  return request("/investors", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// Grants
export async function searchGrants(filters?: { industry?: string; region?: string; status?: string }) {
  const params = new URLSearchParams();
  if (filters?.industry) params.set("industry", filters.industry);
  if (filters?.region) params.set("region", filters.region);
  if (filters?.status) params.set("status", filters.status || "open");
  return request<{ grants: any[]; count: number }>(`/grants?${params}`);
}

export async function getGrant(grantId: string) {
  return request(`/grants/${grantId}`);
}

export async function matchGrants(businessId: string) {
  return request("/grants/match", {
    method: "POST",
    body: JSON.stringify({ business_id: businessId }),
  });
}

export async function getGrantApplications() {
  return request<{ applications: any[] }>("/grants/applications");
}

export async function createGrantApplication(data: { grant_id: string; business_id?: string; notes?: string }) {
  return request("/grants/applications", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateGrantApplication(appId: string, data: { status?: string; notes?: string }) {
  return request(`/grants/applications/${appId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

// Notifications
export async function getNotifications(limit = 50) {
  return request<{ notifications: any[]; count: number }>(`/notifications?limit=${limit}`);
}

export async function markNotificationRead(notificationId: string) {
  return request(`/notifications/${notificationId}/read`, { method: "PATCH" });
}

// Drive
export async function uploadToDrive(fileId: string) {
  return request(`/drive/upload/${fileId}`, { method: "POST" });
}
