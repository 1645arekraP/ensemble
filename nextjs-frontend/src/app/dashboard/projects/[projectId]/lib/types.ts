// [projectId]/lib/types.ts
import { type Node, type Edge } from '@xyflow/react';

// --- Enums ---
export enum AgentProvider { OPENAI = 'openai', ANTHROPIC = 'anthropic', GOOGLE = 'google', CUSTOM = 'custom' }
export enum AgentRole { GENERAL = 'general', SUPERVISOR = 'supervisor' }
export enum ToolType { WEB_SEARCH = 'web_search', POSTGRES = 'postgres', CUSTOM = 'custom' }

// --- Node Data Interfaces ---
export interface BaseNodeData {
  updateNodeData: (nodeId: string, data: any) => void;
  deleteNode: (nodeId: string) => void;
}

export interface ToolNodeData extends BaseNodeData {
  name: string;
  description: string;
  tool_type: ToolType;
}

export interface AgentNodeData extends BaseNodeData {
  name: string;
  role: AgentRole;
  provider: AgentProvider;
  model: string;
  system_instruction_prompt: string;
  tools: string[]; // Array of Tool Node IDs
  allNodes: Node[]; // List of all nodes for the tool selector
  description: string;
}

// --- API Payload Types (Inferred from your code) ---

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

// --- Dialog Form State Types ---
export interface AddAgentFormState {
  name: string;
  description: string;
  role: AgentRole;
  provider: AgentProvider;
  model: string;
  system_instruction_prompt: string;
}

export interface AddToolFormState {
  name: string;
  description: string;
  tool_type: ToolType;
}

// --- Main Project Type ---
// You might already have this in a global `@/lib/types`
export interface ProjectGraphData {
  nodes: Node[];
  edges: Edge[];
}
export interface Project {
  id: string;
  name: string;
  graph_data: ProjectGraphData;
}