
export type User = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
};

export type Project = {
  id: string; // The ID is a string (UUID)
  name: string;
  description: string | null; // Description can be null
  graph_data: any; // Use 'any' or a more specific object type
  created_at: string; // ISO date string
  owner: User;
};

export type Tool = {
  
}

export type ApiToolNode = {

}

export type NewToolNodePayload = {

}

export interface ApiTool {
  id: number;
  name: string;
  description: string;
  tool_type: string;
  tool_type_display: string;
  is_active: boolean;
}

export interface UserCredential {
  id: number;
  user: string;
  credential_type: string;
  credential_type_display: string;
  expires_at: string | null;
  created_at: string;
}

export interface NewCredentialPayload {
  credential_type: string;
  access_token: string;
  refresh_token?: string | null;
  expires_at?: string | null;
}

export interface AddAgentFormState {
  name: string;
  description: string;
  role: string;
  system_instruction_prompt: string;
  provider: string; 
  model: string;  
}

export interface GraphGeneratePayload {
  prompt: string;
  current_graph_data: {
    nodes: Node[];
    edges: Edge[];
  };
}

/**
 * The expected JSON response from the graph generator.
 */
export interface GraphGenerateResponse {
  explanation: string;
  graph: {
    nodes: Node[];
    edges: Edge[];
  };
}


export enum AgentProvider { 
  OPENAI = 'openai', 
  ANTHROPIC = 'anthropic', 
  GOOGLE = 'google', 
  CUSTOM = 'custom' 
}
export enum AgentRole { 
  GENERAL = 'general', 
  SUPERVISOR = 'supervisor' 
}

export interface AgentNodeData {
  // Core agent properties
  id: number; // The database ID
  name: string;
  role: AgentRole;
  provider: AgentProvider;
  model: string;
  system_instruction_prompt: string;
  description: string;

  // Frontend-only callbacks
  updateNodeData: (nodeId: string, data: Partial<AgentNodeData>) => void;
  deleteNode: (nodeId: string) => void;
}

export interface ChatMessage {
  role: 'user' | 'ai';
  content: string;
}