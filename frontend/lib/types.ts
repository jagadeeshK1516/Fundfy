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
