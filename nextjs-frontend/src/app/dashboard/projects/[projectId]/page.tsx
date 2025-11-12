"use client"

import { use, useState, useRef, useCallback, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { 
  ApiAgentNode, 
  ApiToolNode, 
  getAgents, 
  getTools, 
  getProjectById, 
  RunGraphResult,
  generateGraphFromPrompt
} from '@/lib/api';
import { 
  type Project, 
  GraphGenerateResponse, 
  AgentNodeData, 
  ToolNodeData,
  ChatMessage
} from '@/lib/types'; 

import {
  ReactFlowInstance,
  Node,
  Edge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { SiteHeader } from "@/components/site-header";
import LoadingSpinner from '@/components/LoadingSpinner';
import { toast } from "sonner";

// --- Local Imports ---
import AgentNode from './components/AgentNode';
import ToolNode from './components/ToolNode';
import { AddAgentNodeDialog } from './components/AddAgentNodeDialog';
import { AddToolNodeDialog } from './components/AddToolNodeDialog';
import { useProjectGraph } from './hooks/useProjectGraph';
import { Toolbox } from './components/ToolBox'; // <-- Your new component
import { Canvas } from './components/Canvas';   // <-- Your new component
import { ControlPanel } from './components/ControlPanel'; // <-- Your new component

// Define node types for React Flow
const nodeTypes = { agent: AgentNode, tool: ToolNode };

type AsyncProps<T> = T | Promise<T>;

export default function ProjectCanvasPage({ params }: { params: AsyncProps<{ projectId: string }> }) {
  const resolvedParams = use(params);
  const { projectId } = resolvedParams;

  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);
  
  // --- Layout State ---
  const [isToolboxOpen, setIsToolboxOpen] = useState(true);
  const [isControlPanelOpen, setIsControlPanelOpen] = useState(true);

  // --- STATE FOR RUNNING GRAPH ---
  const [graphInput, setGraphInput] = useState("");
  const [graphOutput, setGraphOutput] = useState<RunGraphResult | { error: string } | null>(null);
  
  // --- STATE FOR CHAT GENERATION ---
  const [chatInput, setChatInput] = useState("");
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);

  // --- Data Fetching ---
  const { data: project, isLoading: isLoadingProject, error: projectError } = useQuery<Project, Error>({
    queryKey: ['project', projectId],
    queryFn: () => getProjectById(projectId),
  });
  
  const {data: agents, isLoading: isLoadingAgents, error: agentsError } = useQuery<ApiAgentNode[], Error> ({
    queryKey: ['agents'],
    queryFn: () => getAgents(),
  });

  const {data: tools, isLoading: isLoadingTools, error: toolsError } = useQuery<ApiToolNode[], Error> ({
    queryKey: ['tools'],
    queryFn: () => getTools(),
  });

  // --- Graph State Management ---
  const {
    nodes,
    edges,
    onNodesChange, 
    onEdgesChange,
    onConnect,
    handleCreateAgentNode,
    handleCreateToolNode,
    handleSaveProject,
    isSaving,
    runGraph,
    isExecuting,
    isAddToolDialogOpen, 
    setIsAddToolDialogOpen,
    isAddAgentDialogOpen,
    setIsAddAgentDialogOpen,
    setNodes,
    setEdges,
    updateNodeData,
    deleteNode,
    isCreatingAgent, // <-- 1. Get the loading state
    isCreatingTool,  // <-- 1. Get the loading state
  } = useProjectGraph(projectId);

  // --- Mutation for graph generation (NLP-to-Workflow) ---
  const { mutate: generateGraph, isPending: isGenerating } = useMutation({
    mutationFn: generateGraphFromPrompt,
    onSuccess: (data: GraphGenerateResponse) => {
      toast.success("Workflow Updated!", { description: data.explanation });
      setChatHistory(prev => [...prev, { role: 'ai', content: data.explanation }]);
      
      const nodesWithUpdaters = data.graph.nodes.map((node) => ({
        ...node,
        data: { 
          ...node.data, 
          updateNodeData, 
          deleteNode, 
          allNodes: data.graph.nodes 
        }
      }));
      setNodes(nodesWithUpdaters);
      setEdges(data.graph.edges);
      
      if (reactFlowInstance) {
        reactFlowInstance.fitView();
      }
    },
    onError: (err: Error) => {
      const errorMessage = err.message || "An unknown error occurred.";
      toast.error("Generation Failed", { description: errorMessage });
      setChatHistory(prev => [...prev, { role: 'ai', content: `Sorry, I ran into an error: ${errorMessage}` }]);
    },
  });

  // --- Handlers ---
  const handleChatSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const prompt = chatInput.trim();
    if (!prompt) return;
    setChatHistory(prev => [...prev, { role: 'user', content: prompt }]);
    setChatInput("");
    const cleanNodes = nodes.map(node => {
      const { updateNodeData, deleteNode, allNodes, ...restData } = node.data;
      return { ...node, data: restData };
    });
    const current_graph_data = { nodes: cleanNodes, edges: edges };
    generateGraph({ prompt, current_graph_data });
  };
  
  const handleSaveAndRun = () => {
    setGraphOutput(null);
    handleSaveProject(undefined, {
      onSuccess: (savedProject) => {
        toast.info("Project saved. Running graph...");
        runGraph(
          { projectId, input: graphInput },
          {
            onSuccess: (runResult: any) => {
              let data: RunGraphResult | { error: string };
              try {
                data = typeof runResult === 'string' ? JSON.parse(runResult) : runResult;
              } catch (e) {
                data = { error: "Failed to parse server response." };
              }
              setGraphOutput(data);
              toast.success("Graph run complete.");
            },
            onError: (runError: Error) => {
              setGraphOutput({ error: runError.message });
              toast.error("Graph run failed.");
            }
          }
        );
      },
      onError: (saveError: Error) => {
        setGraphOutput({ error: `Failed to save before run: ${saveError.message}` });
        toast.error("Failed to save project.");
      }
    });
  };

  const onAgentDragStart = useCallback((event: React.DragEvent, agent: ApiAgentNode) => {
    const nodeData = { type: 'agent', data: agent };
    event.dataTransfer.setData('application/reactflow', JSON.stringify(nodeData));
    event.dataTransfer.effectAllowed = 'move';
  }, []);

  const onToolDragStart = useCallback((event: React.DragEvent, tool: ApiToolNode) => {
    const nodeData = { type: 'tool', data: tool };
    event.dataTransfer.setData('application/reactflow', JSON.stringify(nodeData));
    event.dataTransfer.effectAllowed = 'move';
  }, []);

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    const nodeDataString = event.dataTransfer.getData('application/reactflow');
    if (!nodeDataString || !reactFlowInstance) return;
    
    const { type, data } = JSON.parse(nodeDataString);
    const position = reactFlowInstance.screenToFlowPosition({ 
      x: event.clientX, 
      y: event.clientY 
    });

    const newNode: Node = {
      id: `${type}_instance_${crypto.randomUUID()}`,
      type,
      position,
      data: {
        ...data,
        updateNodeData,
        deleteNode,
        allNodes: nodes,
      }
    };
    onNodesChange([{ type: 'add', item: newNode }]);
  }, [reactFlowInstance, onNodesChange, updateNodeData, deleteNode, nodes]);

  // --- Render Logic ---
  const isLoading = isLoadingProject || isLoadingAgents || isLoadingTools;
  const pageError = projectError || agentsError || toolsError;
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <LoadingSpinner /><p className="ml-4">Loading Project Canvas...</p>
      </div>
    );
  }
  if (pageError) { 
    return <div className="p-8 text-red-500">Error: {pageError.message}</div>;
  }
  
  return (
    <div className="h-screen w-screen flex flex-col bg-neutral-50 overflow-hidden">
      <SiteHeader name={`Canvas: ${project?.name || '...'}`} />

      {/* --- 2. Pass the isPending prop to the dialogs --- */}
      <AddToolNodeDialog
        isOpen={isAddToolDialogOpen}
        onOpenChange={setIsAddToolDialogOpen}
        onSubmit={handleCreateToolNode}
        isPending={isCreatingTool} 
      />
      <AddAgentNodeDialog
        isOpen={isAddAgentDialogOpen}
        onOpenChange={setIsAddAgentDialogOpen}
        onSubmit={handleCreateAgentNode}
        isPending={isCreatingAgent}
      />
      
      {/* Main 3-Column Layout */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Sidebar - Toolbox */}
        <div
          className={`flex-shrink-0 transition-all duration-300 ease-in-out bg-white ${
            isToolboxOpen ? 'w-64' : 'w-0'
          }`}
        >
          <Toolbox 
            isOpen={isToolboxOpen}
            agents={agents || []}
            tools={tools || []}
            onAddAgentNode={() => setIsAddAgentDialogOpen(true)}
            onAddToolNode={() => setIsAddToolDialogOpen(true)}
            onAgentDragStart={onAgentDragStart}
            onToolDragStart={onToolDragStart}
          />
        </div>

        {/* Toggle Button for Toolbox */}
        <button
          onClick={() => setIsToolboxOpen(!isToolboxOpen)}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-white border border-neutral-200 rounded-r-lg p-2 hover:bg-neutral-50 transition-colors shadow-sm"
          style={{ transform: `translateX(${isToolboxOpen ? '256px' : '0px'})` }}
        >
          {isToolboxOpen ? (
            <ChevronLeft className="w-4 h-4 text-neutral-600" />
          ) : (
            <ChevronRight className="w-4 h-4 text-neutral-600" />
          )}
        </button>

        {/* Central Canvas */}
        <div className="flex-1 flex flex-col min-w-0 h-full">
          <Canvas 
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onInit={setReactFlowInstance}
            onDragOver={onDragOver}
            onDrop={onDrop}
          />
        </div>

        {/* Toggle Button for Control Panel */}
        <button
          onClick={() => setIsControlPanelOpen(!isControlPanelOpen)}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-10 bg-white border border-neutral-200 rounded-l-lg p-2 hover:bg-neutral-50 transition-colors shadow-sm"
          style={{ transform: `translateX(${isControlPanelOpen ? '-384px' : '0px'})` }}
        >
          {isControlPanelOpen ? (
            <ChevronRight className="w-4 h-4 text-neutral-600" />
          ) : (
            <ChevronLeft className="w-4 h-4 text-neutral-600" />
          )}
        </button>

        {/* Right Sidebar - Control Panel */}
        <div
          className={`flex-shrink-0 transition-all duration-300 ease-in-out bg-white ${
            isControlPanelOpen ? 'w-96' : 'w-0'
          }`}
        >
          <ControlPanel 
            isOpen={isControlPanelOpen}
            chatHistory={chatHistory}
            chatInput={chatInput}
            setChatInput={setChatInput}
            handleChatSubmit={handleChatSubmit}
            isGenerating={isGenerating}
            graphInput={graphInput}
            setGraphInput={setGraphInput}
            graphOutput={graphOutput}
            handleSaveProject={() => handleSaveProject()}
            handleSaveAndRun={handleSaveAndRun}
            isSaving={isSaving}
            isExecuting={isExecuting}
          />
        </div>
      </div>
    </div>
  );
}