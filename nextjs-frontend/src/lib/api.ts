import { apiClient, setAccessToken } from './apiClient';
import { LoginResponse, NewUserData, User } from './interfaces';
import { Project } from './types';

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


export interface NewAgentNodePayload {
  project: number | string; // Project ID
  name: string;
  description: string;
  system_instruction_prompt: string;
  role: string; 
  provider: string; 
  model: string;
  tools: number[]; // Array of Tool node primary keys
  metadata: {
    position: { x: number; y: number };
  };
}


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