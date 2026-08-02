// Chat
export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export interface ChatResponse {
  response: string;
  business_id?: string;
}

// Business
export interface Business {
  id: string;
  founder_id: string;
  name: string;
  industry: string;
  stage: string;
  goals: string;
  created_at?: string;
}

export interface CreateBusinessPayload {
  founder_id: string;
  name: string;
  industry: string;
  stage: string;
  goals: string;
}

// Execution
export interface ExecutePayload {
  business_id: string;
  objective: string;
  context?: string;
}

export interface ExecuteResponse {
  workstream_id: string;
  status: string;
  tasks: Task[];
}

export interface Task {
  id: string;
  type: string;
  status: "pending" | "running" | "completed" | "failed";
  result?: string;
  created_at?: string;
}

export interface Workstream {
  id: string;
  business_id: string;
  objective: string;
  status: string;
  tasks: Task[];
  created_at?: string;
}

// Documents
export interface Document {
  id: string;
  business_id: string;
  doc_type: string;
  title: string;
  content: string;
  created_at?: string;
}

export interface GenerateDocumentPayload {
  business_id: string;
  doc_type: string;
  context?: string;
}

// Communication
export interface CommunicationPayload {
  founder_id: string;
  mode: string;
  message: string;
  business_id?: string;
}

export interface CommunicationResponse {
  response: string;
  mode: string;
}

// Health
export interface HealthResponse {
  status: string;
}

// --- Phase C Types ---

// Google OAuth / Integrations
export interface GoogleAuthStatus {
  connected: boolean;
  scopes?: string[];
  expires_at?: string;
}

export interface GoogleAuthUrl {
  auth_url: string;
}

// Email Approvals
export interface EmailApproval {
  id: string;
  to: string;
  subject: string;
  body: string;
  status: "pending" | "approved" | "rejected" | "sent";
  created_at?: string;
}

// Calendar
export interface CalendarEvent {
  id: string;
  summary: string;
  start: { dateTime: string };
  end: { dateTime: string };
  htmlLink?: string;
  hangoutLink?: string;
  attendees?: { email: string }[];
}

export interface CreateEventPayload {
  summary: string;
  start: string;
  end: string;
  attendees?: string[];
  meet_link?: boolean;
}

// CRM
export interface CRMContact {
  id: string;
  founder_id: string;
  name: string;
  email?: string;
  company?: string;
  role?: string;
  type: "investor" | "mentor" | "partner" | "other";
  pipeline_stage: "lead" | "contacted" | "meeting" | "proposal" | "negotiation" | "closed_won" | "closed_lost";
  notes?: string;
  last_contacted_at?: string;
  created_at?: string;
}

export interface CRMInteraction {
  id: string;
  contact_id: string;
  founder_id: string;
  type: "email" | "meeting" | "call" | "note";
  summary: string;
  details?: string;
  occurred_at?: string;
  created_at?: string;
}

export interface PipelineSummary {
  lead: number;
  contacted: number;
  meeting: number;
  proposal: number;
  negotiation: number;
  closed_won: number;
  closed_lost: number;
}

// Investors
export interface Investor {
  id: string;
  name: string;
  firm?: string;
  email?: string;
  linkedin_url?: string;
  focus_areas: string[];
  stage_preference?: string;
  check_size_min?: number;
  check_size_max?: number;
  portfolio_companies: string[];
  location?: string;
  notes?: string;
  created_at?: string;
}

// Grants
export interface Grant {
  id: string;
  name: string;
  provider: string;
  amount_min?: number;
  amount_max?: number;
  deadline?: string;
  eligibility_criteria: string[];
  industry_focus: string[];
  application_url?: string;
  description?: string;
  region?: string;
  status: "open" | "closed";
  created_at?: string;
}

export interface GrantApplication {
  id: string;
  founder_id: string;
  grant_id: string;
  business_id?: string;
  status: "discovered" | "applying" | "submitted" | "approved" | "rejected";
  notes?: string;
  submitted_at?: string;
  created_at?: string;
}

// Notifications
export interface Notification {
  id: string;
  founder_id: string;
  type: "email_reply" | "meeting_reminder" | "grant_deadline" | "job_complete" | "document_ready";
  title: string;
  body: string;
  data: Record<string, unknown>;
  read: boolean;
  created_at?: string;
}
