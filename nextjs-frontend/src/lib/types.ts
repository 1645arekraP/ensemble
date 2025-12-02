import { type Node, type Edge } from '@xyflow/react';

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

export interface NewAgentNodePayload {
  project: string;
  name: string;
  description: string;
  role: AgentRole;
  provider: AgentProvider;
  model: string;
  system_instruction_prompt: string;
  tools: string[];
  metadata: {
    position: { x: number; y: number };
  };
}

export interface NewToolNodePayload {
  project: string;
  name: string;
  description: string;
  tool_type: ToolType;
  metadata: {
    position: { x: number; y: number };
  };
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
  role: AgentRole;
  system_instruction_prompt: string;
  provider: AgentProvider;
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

export enum ToolType {
  WEB_SEARCH = 'web_search',
  CUSTOM = 'custom'
}

export interface BaseNodeData {
  updateNodeData: (nodeId: string, data: any) => void;
  deleteNode: (nodeId: string) => void;
}

export interface AgentNodeData extends BaseNodeData {
  // Core agent properties
  id: number; // The database ID
  name: string;
  role: AgentRole;
  provider: AgentProvider;
  model: string;
  system_instruction_prompt: string;
  description: string;
  tools: string[]; // Array of Tool Node IDs
  allNodes: any[]; // List of all nodes for the tool selector (using any[] to avoid circular dependency with Node)

  // Frontend-only callbacks
  // updateNodeData and deleteNode are inherited from BaseNodeData
}

export interface ToolNodeData extends BaseNodeData {
  name: string;
  description: string;
  tool_type: ToolType;
}

export interface ChatMessage {
  role: 'user' | 'ai';
  content: string;
}