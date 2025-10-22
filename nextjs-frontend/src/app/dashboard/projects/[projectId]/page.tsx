"use client"

import { use, useState, useCallback, useEffect, memo, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { SiteHeader } from "@/components/site-header";
import { type Project } from "@/lib/types";
import { getProjectById, updateProjectGraph } from '@/lib/api';

import {
  Background,
  Controls,
  Panel,
  MiniMap,
  ReactFlow,
  addEdge,
  applyEdgeChanges,
  applyNodeChanges,
  Node,
  Edge,
  Handle,
  Position,
  NodeProps,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from "@/components/ui/textarea";
import LoadingSpinner from '@/components/LoadingSpinner';
import { XIcon, CheckIcon, ChevronsUpDown } from 'lucide-react';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command';
import { cn } from '@/lib/utils';

// --- TYPE DEFINITIONS ---

type AsyncProps<T> = T | Promise<T>;

enum AgentProvider { OPENAI = 'openai', ANTHROPIC = 'anthropic', GOOGLE = 'google', CUSTOM = 'custom' }
enum AgentRole { GENERAL = 'general', SUPERVISOR = 'supervisor' }
enum ToolType { WEB_SEARCH = 'web_search', CUSTOM = 'custom' }

interface AgentNodeData {
  name: string;
  role: AgentRole;
  provider: AgentProvider;
  model: string;
  system_instruction_prompt: string;
  tools: string[]; // An array of tool node IDs
  updateNodeData: (nodeId: string, data: Partial<AgentNodeData>) => void;
  deleteNode: (nodeId: string) => void;
  allNodes: Node[]; // Pass all nodes to allow tool selection
}

interface ToolNodeData {
  name: string;
  description: string;
  tool_type: ToolType;
  updateNodeData: (nodeId: string, data: Partial<ToolNodeData>) => void;
  deleteNode: (nodeId: string) => void;
}


// --- CUSTOM NODE COMPONENTS ---

const AgentNode = memo(({ id, data }: NodeProps<AgentNodeData>) => {
  const { name, role, provider, model, system_instruction_prompt, tools, updateNodeData, deleteNode, allNodes } = data;

  const handleInputChange = (field: keyof Omit<AgentNodeData, 'tools' | 'allNodes' | 'updateNodeData' | 'deleteNode'>, value: string) => {
    updateNodeData(id, { [field]: value });
  };
  
  // The list of available tools now maps the display name (label) to the stable ID (value)
  const availableTools = useMemo(() => 
    allNodes.filter(node => node.type === 'tool').map(node => ({
      value: node.id,
      label: node.data.name,
    })),
    [allNodes]
  );
  
  // This function now toggles the presence of the tool's ID in the tools array
  const handleToolToggle = (toolId: string) => {
    const newTools = tools.includes(toolId)
      ? tools.filter(t => t !== toolId)
      : [...tools, toolId];
    updateNodeData(id, { tools: newTools });
  };

  return (
    <Card className="w-80 shadow-lg border-blue-500 border-2 relative group">
      <Button onClick={() => deleteNode(id)} variant="ghost" size="icon" className="absolute -top-3 -right-3 h-6 w-6 rounded-full bg-destructive text-destructive-foreground opacity-0 group-hover:opacity-100 transition-opacity">
        <XIcon className="h-4 w-4" />
      </Button>
      <Handle type="target" position={Position.Top} />
      <CardHeader className="bg-muted p-3">
        <CardTitle className="text-md">
          <Input 
            value={name}
            onChange={(e) => handleInputChange('name', e.target.value)}
            placeholder="Agent Name"
            className="text-md font-bold border-none !ring-0 !shadow-none p-0 h-auto"
          />
        </CardTitle>
      </CardHeader>
      <CardContent className="p-3 grid gap-2 text-sm">
        <div className="grid grid-cols-2 gap-2">
          <div>
            <Label>Role</Label>
            <Select value={role} onValueChange={(value: AgentRole) => handleInputChange('role', value)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {Object.values(AgentRole).map(r => <SelectItem key={r} value={r}>{r}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Provider</Label>
            <Select value={provider} onValueChange={(value: AgentProvider) => handleInputChange('provider', value)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {Object.values(AgentProvider).map(p => <SelectItem key={p} value={p}>{p}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
        </div>
        <div>
          <Label>Model</Label>
          <Input 
            value={model}
            onChange={(e) => handleInputChange('model', e.target.value)}
            placeholder="e.g., gpt-4o"
          />
        </div>
        <div>
          <Label>System Prompt</Label>
          <Textarea 
            value={system_instruction_prompt}
            onChange={(e) => handleInputChange('system_instruction_prompt', e.target.value)}
            placeholder="You are a helpful assistant..."
            rows={4}
          />
        </div>
        <div>
          <Label>Tools</Label>
            <Popover>
                <PopoverTrigger asChild>
                    <Button variant="outline" role="combobox" className="w-full justify-between">
                        <span className="truncate">
                            {tools.length > 0 ? `${tools.length} selected` : 'Select tools...'}
                        </span>
                        <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                    </Button>
                </PopoverTrigger>
                <PopoverContent className="w-[--radix-popover-trigger-width] p-0">
                    <Command>
                        <CommandInput placeholder="Search tools..." />
                        <CommandList>
                            <CommandEmpty>No tools found.</CommandEmpty>
                            <CommandGroup>
                                {availableTools.map((tool) => (
                                    <CommandItem
                                        key={tool.value} // Key is now the stable ID
                                        onSelect={() => handleToolToggle(tool.value)} // Handler uses the ID
                                    >
                                        <CheckIcon
                                            className={cn(
                                                "mr-2 h-4 w-4",
                                                // Check for inclusion is now based on the ID
                                                tools.includes(tool.value) ? "opacity-100" : "opacity-0"
                                            )}
                                        />
                                        {tool.label} {/* Display name is just for the UI */}
                                    </CommandItem>
                                ))}
                            </CommandGroup>
                        </CommandList>
                    </Command>
                </PopoverContent>
            </Popover>
        </div>
      </CardContent>
      <Handle type="source" position={Position.Bottom} />
    </Card>
  );
});
AgentNode.displayName = 'AgentNode';

const ToolNode = memo(({ id, data }: NodeProps<ToolNodeData>) => {
  const { name, description, tool_type, updateNodeData, deleteNode } = data;
  
  return (
    <Card className="w-72 shadow-lg border-green-500 border-2 relative group">
      <Button onClick={() => deleteNode(id)} variant="ghost" size="icon" className="absolute -top-3 -right-3 h-6 w-6 rounded-full bg-destructive text-destructive-foreground opacity-0 group-hover:opacity-100 transition-opacity">
        <XIcon className="h-4 w-4" />
      </Button>
      <Handle type="target" position={Position.Top} />
      <CardHeader className="bg-muted p-3">
        <CardTitle className="text-md">
          <Input 
            value={name}
            onChange={(e) => updateNodeData(id, { name: e.target.value })}
            placeholder="Tool Name"
            className="text-md font-bold border-none !ring-0 !shadow-none p-0 h-auto"
          />
        </CardTitle>
      </CardHeader>
      <CardContent className="p-3 grid gap-2 text-sm">
        <div>
            <Label>Tool Type</Label>
            <Select value={tool_type} onValueChange={(value: ToolType) => updateNodeData(id, { tool_type: value })}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {Object.values(ToolType).map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}
              </SelectContent>
            </Select>
        </div>
        <div>
          <Label>Description</Label>
          <Textarea 
            value={description}
            onChange={(e) => updateNodeData(id, { description: e.target.value })}
            placeholder="Describes what this tool does..."
            rows={3}
          />
        </div>
      </CardContent>
      <Handle type="source" position={Position.Bottom} />
    </Card>
  );
});
ToolNode.displayName = 'ToolNode';

const nodeTypes = { agent: AgentNode, tool: ToolNode };


// --- SIDEBAR COMPONENT ---

const CanvasSidebar = ({ onAddAgentNode, onAddToolNode }: { onAddAgentNode: () => void; onAddToolNode: () => void; }) => {
  return (
    <aside className="w-64 bg-background border-r p-4 flex flex-col gap-4">
      <h2 className="text-lg font-semibold">Nodes</h2>
      <Button onClick={onAddAgentNode} variant="outline">Add Agent</Button>
      <Button onClick={onAddToolNode} variant="outline">Add Tool</Button>
    </aside>
  );
};


// --- MAIN PAGE COMPONENT ---

export default function ProjectCanvasPage({ params }: { params: AsyncProps<{ projectId: string }> }) {
  const resolvedParams = use(params);
  const { projectId } = resolvedParams;
  const queryClient = useQueryClient();

  const [nodes, setNodes] = useState<Node<any, string | undefined>[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);

  // --- Data Fetching and Saving ---
  const { data: project, isLoading, error } = useQuery<Project, Error>({
    queryKey: ['project', projectId],
    queryFn: () => getProjectById(projectId),
  });

  const { mutate: saveProject, isPending: isSaving } = useMutation({
    // **THE FIX**: The mutation function now cleans the data before sending.
    mutationFn: () => {
      // Create a "clean" version of nodes for serialization.
      const nodesToSave = nodes.map(node => {
        // Destructure the data to remove frontend-only properties
        const { updateNodeData, deleteNode, allNodes, ...restData } = node.data;
        return { ...node, data: restData };
      });

      return updateProjectGraph({ projectId, graphData: { nodes: nodesToSave, edges } });
    },
    onSuccess: (updatedProject) => {
      console.log('Project saved successfully!');
      // Update the cache with the full data from the server response
      queryClient.setQueryData(['project', projectId], updatedProject);
    },
    onError: (err) => {
      console.error('Failed to save project:', err);
      // Here you could add a user-facing error message (e.g., a toast notification)
    },
  });

  // --- Node State Management Callbacks ---
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

      if (nodeToDelete && nodeToDelete.type === 'tool') {
        const deletedToolId = nodeToDelete.id;
        updatedNodes = updatedNodes.map(node => {
          if (node.type === 'agent' && node.data.tools?.includes(deletedToolId)) {
            const newTools = node.data.tools.filter((toolId: string) => toolId !== deletedToolId);
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
  
  
  // Effect to load initial graph data from the server
  useEffect(() => {
    if (project?.graph_data?.nodes) {
      const initialNodes = project.graph_data.nodes;
      // Inject the frontend-only callbacks and properties into the nodes from the server
      const nodesWithUpdaters = initialNodes.map(node => ({
        ...node,
        data: { ...node.data, updateNodeData, deleteNode, allNodes: initialNodes }
      }));
      setNodes(nodesWithUpdaters);
      setEdges(project.graph_data.edges || []);
    }
  }, [project, updateNodeData, deleteNode]);

  // This effect ensures that every node has the most up-to-date list of all other nodes.
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
            allNodes: currentNodes,
          }
        }))
      );
    }
  }, [nodeDependencies]);


  // --- UI Action Handlers ---
  const addAgentNode = () => {
    const newNodeId = `agent_${Date.now()}`;
    const newNode: Node<AgentNodeData> = {
      id: newNodeId,
      type: 'agent',
      position: { x: Math.random() * 400, y: Math.random() * 400 },
      data: {
        name: 'New Agent',
        role: AgentRole.GENERAL,
        provider: AgentProvider.OPENAI,
        model: 'gpt-4o',
        system_instruction_prompt: 'You are a helpful AI assistant.',
        tools: [],
        updateNodeData,
        deleteNode,
        allNodes: [], // Will be populated by the useEffect
      },
    };
    setNodes((nds) => [...nds, newNode]);
  };
  
  const addToolNode = () => {
    const newNodeId = `tool_${Date.now()}`;
    const newNode: Node<ToolNodeData> = {
      id: newNodeId,
      type: 'tool',
      position: { x: Math.random() * 400, y: Math.random() * 400 },
      data: {
        name: 'New Tool',
        description: 'A tool for performing a specific action.',
        tool_type: ToolType.CUSTOM,
        updateNodeData,
        deleteNode,
      },
    };
    setNodes((nds) => [...nds, newNode]);
  };

  const onNodesChange = useCallback((changes) => setNodes((nds) => applyNodeChanges(changes, nds)), [setNodes]);
  const onEdgesChange = useCallback((changes) => setEdges((eds) => applyEdgeChanges(changes, eds)), [setEdges]);
  const onConnect = useCallback((params) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

  // --- Render Logic ---
  if (isLoading) { 
    return (
      <div className="flex items-center justify-center h-screen">
        <LoadingSpinner /><p className="ml-4">Loading Project Canvas...</p>
      </div>
    );
  }
  if (error) { 
    return <div className="p-8 text-red-500">Error: Failed to load project. {error.message}</div>;
  }
  
  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <SiteHeader name={`Canvas: ${project?.name || '...'}`} />
      <div className="flex flex-grow">
        <CanvasSidebar onAddAgentNode={addAgentNode} onAddToolNode={addToolNode} />
        <main className="flex-grow">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            fitView
          >
            <Panel position="top-right">
              <Button onClick={() => saveProject()} disabled={isSaving}>
                {isSaving ? 'Saving...' : 'Save Project'}
              </Button>
            </Panel>
            <Controls />
            <MiniMap />
            <Background variant="dots" gap={12} size={1} />
          </ReactFlow>
        </main>
      </div>
    </div>
  );
}

