"use client"

import { useState, useCallback, useEffect, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Node,
  Edge,
  addEdge,
  applyEdgeChanges,
  applyNodeChanges,
  Connection,
  EdgeChange,
  NodeChange,
} from '@xyflow/react';
import {
  getProjectById,
  updateProjectGraph,
  createAgentNode,
  createToolNode,
  runProjectGraph,
  RunGraphPayload,
  RunGraphResult,
  ApiToolNode,
} from '@/lib/api';
import { apiClient } from '@/lib/apiClient';
import {
  Project,
  AgentNodeData,
  ToolNodeData,
  AddAgentFormState,
  AddToolFormState,
  NewAgentNodePayload,
  NewToolNodePayload
} from '../lib/types';

import { toast } from "sonner";


export const useProjectGraph = (projectId: string) => {
  const queryClient = useQueryClient();

  // --- Local State ---
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [isAddToolDialogOpen, setIsAddToolDialogOpen] = useState(false);
  const [isAddAgentDialogOpen, setIsAddAgentDialogOpen] = useState(false);

  // --- Data Fetching ---
  const { data: project, isLoading, error } = useQuery<Project, Error>({
    queryKey: ['project', projectId],
    queryFn: () => getProjectById(projectId),
  });

  // --- Callbacks for Nodes (Memoized) ---
  const updateNodeData = useCallback((nodeId: string, newData: Partial<AgentNodeData | ToolNodeData>) => {
    setNodes((prevNodes) =>
      prevNodes.map((node) =>
        node.id === nodeId ? { ...node, data: { ...node.data, ...newData } } : node
      )
    );
  }, [setNodes]);

  const deleteNode = useCallback((nodeIdToDelete: string) => {
    setNodes((prevNodes) => {
      const nodeToDelete = prevNodes.find(n => n.id === nodeIdToDelete);
      let updatedNodes = prevNodes.filter((node) => node.id !== nodeIdToDelete);

      // If a tool is deleted, remove it from any agent that was using it
      if (nodeToDelete && nodeToDelete.type === 'tool') {
        const deletedToolId = nodeToDelete.id;
        updatedNodes = updatedNodes.map(node => {
          if (node.type === 'agent' && Array.isArray(node.data.tools) && node.data.tools.includes(deletedToolId)) {
            const newTools = (node.data.tools as string[]).filter((toolId: string) => toolId !== deletedToolId);
            return { ...node, data: { ...node.data, tools: newTools } };
          }
          return node;
        });
      }
      return updatedNodes;
    });

    setEdges((prevEdges) =>
      prevEdges.filter((edge) => edge.source !== nodeIdToDelete && edge.target !== nodeIdToDelete)
    );
  }, [setNodes, setEdges]);

  // --- Effects to Sync State ---

  // load initial graph data
  useEffect(() => {
    if (project?.graph_data?.nodes) {
      const initialNodes = project.graph_data.nodes;
      // Inject the frontend-only callbacks into the nodes from the server
      const nodesWithUpdaters = initialNodes.map(node => ({
        ...node,
        data: {
          ...node.data,
          updateNodeData,
          deleteNode,
          allNodes: initialNodes
        }
      }));
      setNodes(nodesWithUpdaters);
      setEdges(project.graph_data.edges || []);
    }
  }, [project, updateNodeData, deleteNode]); // Dependencies are stable callbacks

  const nodeDependencies = useMemo(() =>
    JSON.stringify(nodes.map(n => ({ id: n.id, name: n.data.name }))),
    [nodes]
  );

  useEffect(() => {
    if (nodes.length > 0) {
      setNodes(currentNodes =>
        currentNodes.map(n => ({
          ...n,
          data: {
            ...n.data,
            allNodes: currentNodes, // Inject the full, current list
          }
        }))
      );
    }
  }, [nodeDependencies]); // Re-runs only when the ID or name of any node changes


  // --- React Flow Callbacks ---
  const onNodesChange = useCallback((changes: NodeChange[]) => {
    const changesWithData = changes.map(change => {
      if (change.type === 'add' && change.item) {
        // Intercept the 'add' change (e.g., from drag-and-drop)
        const newNode = change.item;
        return {
          ...change,
          item: {
            ...newNode,
            data: {
              ...newNode.data,
              updateNodeData, // Inject callbacks
              deleteNode,     // Inject callbacks
              allNodes: nodes,  // Inject current node list
            }
          }
        };
      }
      return change;
    });

    setNodes((nds) => applyNodeChanges(changesWithData, nds));
  }, [setNodes, updateNodeData, deleteNode, nodes]);

  const onEdgesChange = useCallback((changes: EdgeChange[]) => setEdges((eds) => applyEdgeChanges(changes, eds)), [setEdges]);
  const onConnect = useCallback((params: Connection) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

  // --- API Mutations ---
  const { mutate: handleSaveProject, isPending: isSaving } = useMutation({
    mutationFn: () => {
      // Clean nodes for serialization (remove functions and injected state)
      const nodesToSave = nodes.map(node => {
        const { updateNodeData, deleteNode, allNodes, ...restData } = node.data;
        return { ...node, data: restData };
      });

      return updateProjectGraph({ projectId, graphData: { nodes: nodesToSave, edges } });
    },
    onSuccess: (updatedProject) => {
      console.log('Project saved successfully!');
      queryClient.setQueryData(['project', projectId], updatedProject);
    },
    onError: (err) => {
      console.error('Failed to save project:', err);
      // TODO: Add user-facing toast notification
      toast.error("Saving Failed", {
        description: err.message || "Could not save the project. Please try again.",
      });
    },
  });

  const { mutate: runGraph, isPending: isExecuting } = useMutation<RunGraphResult, Error, RunGraphPayload, { onSuccess?: (data: RunGraphResult) => void; onError?: (error: Error) => void; }>({
    mutationFn: runProjectGraph,
    onSuccess: (data, _variables, context) => {
      toast.success("Graph executed successfully!");
      // Call the success callback passed from the component
      context?.onSuccess?.(data);
    },
    onError: (err: Error, _variables, context) => {
      console.error('Failed to run graph:', err);
      toast.error("Graph Execution Failed", {
        description: err.message || "Could not run the graph. Check server logs.",
      });
      // Call the error callback passed from the component
      context?.onError?.(err);
    }
  });


  const {
    mutate: createAgentNodeMutation,
    isPending: isCreatingAgent
  } = useMutation({
    mutationFn: createAgentNode,
    onSuccess: () => {
      toast.success("Agent created successfully!");
      queryClient.invalidateQueries({ queryKey: ['agents'] }); // This refetches for the sidebar
      setIsAddAgentDialogOpen(false); // Close the dialog
    },
    onError: (err: Error) => {
      console.error("Failed to create agent node:", err);
      toast.error("Creation Failed", {
        description: err.message || "Could not create the new agent. Please try again.",
      });
    }
  });

  const {
    mutate: createToolNodeMutation,
    isPending: isCreatingTool
  } = useMutation({
    mutationFn: createToolNode,
    onSuccess: () => {
      toast.success("Tool created successfully!");
      queryClient.invalidateQueries({ queryKey: ['tools'] });
      setIsAddToolDialogOpen(false);
    },
    onError: (err: Error) => {
      console.error("Failed to create tool node:", err);
      toast.error("Tool Creation Failed", {
        description: err.message || "Could not create the new tool. Please try again.",
      });
    }
  });

  const handleOpenAddAgentDialog = () => setIsAddAgentDialogOpen(true);
  const handleOpenAddToolDialog = () => setIsAddToolDialogOpen(true);


  const handleCreateAgentNode = (formData: AddAgentFormState) => {
    const newPosition = { x: Math.random() * 400, y: Math.random() * 400 };

    const payload: NewAgentNodePayload = {
      project: projectId,
      ...formData,
      tools: [],
      metadata: {
        position: newPosition,
      },
    };
    createAgentNodeMutation(payload);
  };

  const handleCreateToolNode = (formData: AddToolFormState) => {
    const newPosition = { x: Math.random() * 400, y: Math.random() * 400 };


    const payload: NewToolNodePayload = {
      project: projectId,
      ...formData,
      metadata: {
        position: newPosition,
      },
    };

    // Call the mutation function directly
    createToolNodeMutation(payload);
  };

  // --- Streaming Execution ---
  const runGraphStream = useCallback(async (payload: RunGraphPayload, callbacks?: {
    onMessage?: (msg: any) => void,
    onComplete?: () => void,
    onError?: (err: any) => void
  }) => {
    // Fix: RunGraphPayload might not have 'project' if it's just { input: string }
    // We need to ensure we have the projectId from the hook's scope
    const { input } = payload;

    try {
      const response = await apiClient(`/api/graphs/${projectId}/stream/`, {
        method: 'POST',
        body: JSON.stringify({ input }),
      }) as Response;

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error("No reader available");
      }

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.trim()) {
            try {
              const data = JSON.parse(line);
              callbacks?.onMessage?.(data);

              if (data.type === 'complete' || data.type === 'error') {
                // You might want to handle completion logic here
              }
            } catch (e) {
              console.error("Error parsing JSON chunk", e);
            }
          }
        }
      }
      callbacks?.onComplete?.();

    } catch (error) {
      console.error("Stream error:", error);
      callbacks?.onError?.(error);
      toast.error("Execution Failed", {
        description: "Stream connection failed."
      });
    }
  }, [projectId]); // Add projectId dependency

  // --- Return Values ---
  return {
    project,
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    setNodes,
    setEdges,
    isSaving,
    handleSaveProject,
    isAddAgentDialogOpen,
    setIsAddAgentDialogOpen,
    handleOpenAddAgentDialog,
    handleCreateAgentNode,
    isAddToolDialogOpen,
    setIsAddToolDialogOpen,
    handleOpenAddToolDialog,
    handleCreateToolNode,
    runGraph,
    runGraphStream, // Expose the new function
    isExecuting,
    updateNodeData,
    deleteNode,
    isCreatingAgent,
    isCreatingTool,
  }
}