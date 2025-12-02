import { apiClient, setAccessToken } from './apiClient';
import { LoginResponse, NewUserData, User } from './interfaces';
import {
  type Project,
  type ApiTool,
  GraphGeneratePayload,
  GraphGenerateResponse,
  AgentNodeData,
  ToolNodeData,
  ChatMessage,
  NewAgentNodePayload,
  NewToolNodePayload,
  AgentRole,
  AgentProvider,
  ToolType
} from '@/lib/types';
import { UserCredential, NewCredentialPayload } from './types';

/**
 * The single function to restore a user's session.
 * It first tries to get a new access token, and if successful,
 * it then fetches the user's data.
 */
export const fetchCurrentUser = async (): Promise<User> => {
  try {
    const refreshResponse = await fetch('/api/auth/refresh/', {
      method: 'POST',
      credentials: 'include',
    });

    if (!refreshResponse.ok) {
      throw new Error('No valid session.');
    }

    const { access: newAccessToken } = await refreshResponse.json();
    setAccessToken(newAccessToken); // Store the new token in memory

    const userResponse = await apiClient('/api/users/me/');
    if (!userResponse.ok) {
      throw new Error('Failed to fetch user data with new token.');
    }

    return userResponse.json();

  } catch (error) {
    setAccessToken(null);
    throw error;
  }
};


export const loginUser = async (email, password): Promise<LoginResponse> => {
  const response = await fetch(`/api/auth/login/`, { // The initial login doesn't use the client
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Invalid username or password.');
  }

  const data: LoginResponse = await response.json();

  // Save the access token in our in-memory store
  setAccessToken(data.access);

  return data;
};


/**
 * Creates a new user.
 */
export const createUser = async (userData: NewUserData): Promise<User> => {
  const response = await apiClient('/api/auth/create/', {
    method: 'POST',
    body: JSON.stringify(userData),
  });

  if (!response.ok) {
    const errorData = await response.json();
    // Use a more specific error message if the backend provides one
    throw new Error(errorData.detail || 'Failed to create user.');
  }
  return response.json();
};


/**
 * Fetches all projects for the authenticated user.
 */
export const getProjects = async (): Promise<Project[]> => {
  // We use the apiClient which automatically handles auth headers and token refreshing.
  const response = await apiClient('/api/graphs/');
  if (!response.ok) {
    throw new Error('Failed to fetch projects.');
  }
  return response.json();
};

/**
 * Creates a new project.
 */
export const createProject = async (newProject: { name: string; description: string }): Promise<Project> => {
  const response = await apiClient('/api/graphs/', {
    method: 'POST',
    body: JSON.stringify(newProject),
  });
  if (!response.ok) {
    // A more specific error can be thrown if the backend provides details
    const errorData = await response.json().catch(() => ({ detail: 'Failed to create project.' }));
    throw new Error(errorData.detail);
  }
  return response.json();
};

/**
 * Fetches a single project by its ID.
 */
export const getProjectById = async (projectId: string): Promise<Project> => {
  const response = await apiClient(`/api/graphs/${projectId}/`);
  if (!response.ok) {
    throw new Error('Failed to fetch project details.');
  }
  return response.json();
};

/**
 * Updates the graph data (nodes and edges) for a specific project.
 */
export const updateProjectGraph = async ({ projectId, graphData }: { projectId: string; graphData: { nodes: any[]; edges: any[] } }): Promise<Project> => {
  const response = await apiClient(`/api/graphs/${projectId}/`, {
    method: 'PATCH', // Use PATCH to update only a part of the project
    body: JSON.stringify({ graph_data: graphData }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to save project.' }));
    throw new Error(errorData.detail);
  }
  return response.json();
};







export interface ApiAgentNode {
  id: number; // The database primary key
  name: string;
  description: string;
  system_instruction_prompt: string;
  role: AgentRole;
  provider: AgentProvider;
  model: string;
  tools: number[]; // Array of Tool node primary keys
  metadata: {
    position: { x: number; y: number };
  };
}

// We'll also need one for Tools
export interface ApiToolNode {
  id: number; // The database primary key
  name: string;
  description: string;
  tool_type: ToolType;
  metadata: {
    position: { x: number; y: number };
  };
}

export type ApiNode =
  | ({ type: 'agent' } & ApiAgentNode)
  | ({ type: 'tool' } & ApiToolNode);


/**
 * Creates a new agent node on the backend.
 */
export const createAgentNode = async (payload: NewAgentNodePayload): Promise<ApiAgentNode> => {
  const response = await apiClient('/api/agents/', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({
      detail: 'Failed to create agent node.'
    }));
    throw new Error(errorData.detail);
  }

  return response.json();
};

/**
 * Fetches all agents available to user
 */
export const getAgents = async (): Promise<ApiAgentNode[]> => {
  const response = await apiClient(`/api/agents/`);
  if (!response.ok) {
    throw new Error('Failed to fetch agents details.');
  }
  return response.json();
};


export interface RunGraphPayload {
  projectId: string;
  input: string;
}

export interface RunGraphResult {
  result: any;
  [key: string]: any; // To allow for other data like intermediate steps
}

/**
 * Sends the graph execution request to the backend.
 * This just triggers the run; it assumes the graph is already saved.
 */
export const runProjectGraph = async (payload: RunGraphPayload): Promise<RunGraphResult> => {
  const { projectId, input } = payload;

  // This endpoint is consistent with your getProjectById and updateProjectGraph
  // and matches the backend file structure (`apps/executions` or `apps/graph`)
  const response = await apiClient(`/api/graphs/${projectId}/run/`, {
    method: 'POST',
    body: JSON.stringify({
      input: input, // Send the user's input
    }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ message: 'Failed to run graph' }));
    throw new Error(err.message || 'Failed to run graph. Check server logs.');
  }

  return response.json();
};

export async function getTools(): Promise<ApiTool[]> {
  // We'll assume your apiClient handles the auth token
  const response = await apiClient('/api/tools/');
  if (!response.ok) {
    throw new Error('Failed to fetch tools');
  }
  return response.json();
}

/**
 * Creates a new Tool node in the backend's "tool library".
 */
export async function createToolNode(payload: NewToolNodePayload): Promise<ApiToolNode> {
  const response = await apiClient('/api/tools/', { // Assumes your API endpoint is /api/tools/
    method: 'POST',
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to create tool');
  }

  return response.json();
}

export async function getCredentials(): Promise<UserCredential[]> {
  const response = await apiClient('/api/credentials/');
  if (!response.ok) {
    throw new Error('Failed to fetch credentials');
  }
  return response.json();
}

/**
 * Creates a new, encrypted credential in the backend.
 */
export async function createCredential(payload: NewCredentialPayload): Promise<UserCredential> {
  const response = await apiClient('/api/credentials/', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to save credential');
  }
  return response.json();
}

/**
 * Deletes a credential.
 */
export async function deleteCredential(id: number): Promise<void> {
  const response = await apiClient(`/api/credentials/${id}/`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('Failed to delete credential');
  }
}

/**
 * Calls the backend to get a Google OAuth redirect URL.
 */
export async function getGoogleConnectUrl(): Promise<{ authorization_url: string }> {
  const response = await apiClient('/api/auth/google/connect/');
  if (!response.ok) {
    throw new Error('Failed to get Google connect URL');
  }
  return response.json();
}


export interface AgentConfigPayload {
  prompt: string;
}

export interface AgentConfigResponse {
  name: string;
  description: string;
  system_instruction_prompt: string;
}

/**
 * Calls the backend to generate an agent's configuration from a prompt.
 */
export async function generateAgentConfig(
  payload: AgentConfigPayload
): Promise<AgentConfigResponse> {
  const response = await apiClient('/api/agents/generate-config/', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to generate agent config');
  }

  return response.json();
}

/**
 * Calls the backend to generate a full graph_data JSON from a prompt.
 */
export async function generateGraphFromPrompt(
  payload: GraphGeneratePayload
): Promise<GraphGenerateResponse> {
  const response = await apiClient('/api/graphs/generate/', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to generate graph from prompt');
  }

  return response.json();
}

/**
 * Validates the graph's credentials before execution.
 */
export const validateGraph = async (projectId: string): Promise<{ valid: boolean; errors: string[] }> => {
  const response = await apiClient(`/api/graphs/${projectId}/validate/`);
  if (!response.ok) {
    throw new Error('Failed to validate graph.');
  }
  return response.json();
};

export interface ExecutionLog {
  id: number;
  graph: number;
  user: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at: string | null;
  final_output: string;
  logs: any[];
  initial_input: any;
}

export const getProjectExecutions = async (projectId: string): Promise<ExecutionLog[]> => {
  const response = await apiClient(`/api/executions/?graph_id=${projectId}`); // Assuming apiClient can handle relative paths or base URL is set
  if (!response.ok) {
    throw new Error('Failed to fetch project executions.');
  }
  return response.json();
};

export const deleteExecution = async (executionId: number): Promise<void> => {
  const response = await apiClient(`/api/executions/${executionId}/`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('Failed to delete execution.');
  }
};