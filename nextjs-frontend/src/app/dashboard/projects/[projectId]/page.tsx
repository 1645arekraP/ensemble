"use client"

import { use, useState, useMemo, useRef, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ApiAgentNode, getAgents, getProjectById, RunGraphResult } from '@/lib/api';
import { type Project } from '@/lib/types'; // Assuming global types

import {
  Background,
  Controls,
  Panel,
  MiniMap,
  ReactFlow,
  ReactFlowInstance,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { SiteHeader } from "@/components/site-header";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea"; 
import LoadingSpinner from '@/components/LoadingSpinner';
import { toast } from "sonner";

// --- Local Imports ---
import AgentNode from './components/AgentNode';
import ToolNode from './components/ToolNode';
import { AddAgentNodeDialog } from './components/AddAgentNodeDialog';
import { AddToolNodeDialog } from './components/AddToolNodeDialog';
import { CanvasSidebar } from './components/CanvasSidebar';
import { useProjectGraph } from './hooks/useProjectGraph';

// Define node types for React Flow
const nodeTypes = { agent: AgentNode, tool: ToolNode };

type AsyncProps<T> = T | Promise<T>;

export default function ProjectCanvasPage({ params }: { params: AsyncProps<{ projectId: string }> }) {
  const resolvedParams = use(params);
  const { projectId } = resolvedParams;

  //const [isAddToolDialogOpen, setIsAddToolDialogOpen] = useState(false);
  //const [isAddAgentDialogOpen, setIsAddAgentDialogOpen] = useState(false);

  const [reactFlowInstance, setReactFlowInstance] = useState<any | null>(null);
  const [graphInput, setGraphInput] = useState("");
  const [graphOutput, setGraphOutput] = useState("");

  // --- Data Fetching ---
  const { data: project, isLoading, error } = useQuery<Project, Error>({
    queryKey: ['project', projectId],
    queryFn: () => getProjectById(projectId),
  });
  const {data: agents, isLoadingAgents, errorFetchingAgents } = useQuery<ApiAgentNode[], Error> ({
    queryKey: ['agents'],
    queryFn: () => getAgents(),
  })


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
  } = useProjectGraph(projectId, project);

  const handleSaveAndRun = () => {
    // 1. Clear previous output
    setGraphOutput("");

    // 2. Call saveProject, and in its onSuccess, call runGraph
    handleSaveProject(undefined, {
      onSuccess: (savedProject) => {
        // 3. Now that save is successful, call runGraph
        toast.info("Project saved. Running graph...");
        runGraph(
          { projectId, input: graphInput },
          {
            onSuccess: (runResult: RunGraphResult) => {
              // 4. Set the result to the output box
              setGraphOutput(JSON.stringify(runResult, null, 2));
              toast.success("Graph run successful.");
            },
            onError: (runError: Error) => {
              // 5. Set the error to the output box
              setGraphOutput(JSON.stringify({ error: runError.message }, null, 2));
              toast.error("Graph run failed.");
            }
          }
        );
      },
      onError: (saveError: Error) => {
        // If saving fails, show that error
        setGraphOutput(JSON.stringify({ error: `Failed to save before run: ${saveError.message}` }, null, 2));
        toast.error("Failed to save project.");
      }
    });
  };

  const onAgentDragStart = useCallback((event: React.DragEvent, agent: ApiAgentNode) => {
    const nodeData = {
      type: 'agent', 
      data: { ...agent, label: `${agent.name}` } 
    };
    event.dataTransfer.setData('application/reactflow', JSON.stringify(nodeData));
    event.dataTransfer.effectAllowed = 'move';
  }, []);

  // --- onDragOver Handler ---
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  // --- onDrop Handler ---
  const onDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault();

    const nodeDataString = event.dataTransfer.getData('application/reactflow');
    // --- UPDATED: Check for onNodesChange ---
    if (!nodeDataString || !reactFlowInstance || !onNodesChange) {
      return;
    }
    
    const { type, data } = JSON.parse(nodeDataString);

    // --- UPDATED: Use the reactFlowInstance to get correct position ---
    const position = reactFlowInstance.screenToFlowPosition({ 
      x: event.clientX, 
      y: event.clientY 
    });

    const newNode = {
      id: `agent_instance_${crypto.randomUUID()}`,
      type,
      position,
      data,
    };

    // --- UPDATED: Use onNodesChange to add the new node ---
    onNodesChange([{ type: 'add', item: newNode }]);
    
  }, [reactFlowInstance, onNodesChange]);

  // --- Render Logic ---
  if (isLoading || isLoadingAgents) { // --- UPDATED: Combined loading state ---
    return (
      <div className="flex items-center justify-center h-screen">
        <LoadingSpinner /><p className="ml-4">Loading Project Canvas...</p>
      </div>
    );
  }
  if (error) { 
    return <div className="p-8 text-red-500">Error: Failed to load project. {error.message}</div>;
  }
  if (errorFetchingAgents) { // --- ADDED: Specific error for agents ---
    return <div className="p-8 text-red-500">Error: Failed to load agents. {errorFetchingAgents.message}</div>;
  }
  
  
  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <SiteHeader name={`Canvas: ${project?.name || '...'}`} />
      
      {/* Dialogs are mounted at the top level */}
      <AddToolNodeDialog
        isOpen={isAddToolDialogOpen}
        onOpenChange={setIsAddToolDialogOpen}
        onSubmit={handleCreateToolNode}
      />
      <AddAgentNodeDialog
        isOpen={isAddAgentDialogOpen}
        onOpenChange={setIsAddAgentDialogOpen}
        onSubmit={handleCreateAgentNode}
      />
      
      <div className="flex flex-grow">
        <CanvasSidebar 
          onAddAgentNode={() => setIsAddAgentDialogOpen(true)} 
          onAddToolNode={() => setIsAddToolDialogOpen(true)} 
          agents={agents || []} 
          onAgentDragStart={onAgentDragStart} 
        />
        <main className="flex-grow">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            fitView
            onInit={setReactFlowInstance} 
            onDragOver={onDragOver}       
            onDrop={onDrop}            
          >
            <Panel position="top-right" className="flex flex-col gap-2 w-72">
              {/* Input Textarea */}
              <Textarea
                placeholder="Enter input for the graph..."
                value={graphInput}
                onChange={(e) => setGraphInput(e.target.value)}
                rows={3}
              />
              
              {/* Buttons */}
              <div className="flex gap-2">
                <Button 
                  onClick={() => handleSaveProject()} 
                  disabled={isSaving || isExecuting} 
                  variant="outline"
                  className="flex-1"
                >
                  {isSaving ? 'Saving...' : 'Save'}
                </Button>
                <Button 
                  onClick={handleSaveAndRun} 
                  disabled={isSaving || isExecuting || !graphInput}
                  className="flex-1"
                >
                  {isSaving ? 'Saving...' : isExecuting ? 'Running...' : 'Save & Run'}
                </Button>
              </div>

              {/* Output Display */}
              {graphOutput && (
                <pre className="p-2 bg-muted text-xs rounded-md w-full max-h-48 overflow-auto shadow-inner">
                  {graphOutput}
                </pre>
              )}
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