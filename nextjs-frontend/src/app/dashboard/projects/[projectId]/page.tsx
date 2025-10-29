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
import { Label } from '@/components/ui/label';

type RunGraphResult = {
  success: boolean;
  execution_id: number | null;
  final_state: any;
  messages: string[];
  context: any;
  agent_outputs: {
    [key: string]: {
      response: string;
      [key: string]: any;
    };
  };
  error?: string;
};
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
  const [graphOutput, setGraphOutput] = useState<RunGraphResult | { error: string } | null>(null);

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
    setGraphOutput("");

    // Call saveProject, and in its onSuccess, call runGraph
    handleSaveProject(undefined, {
      onSuccess: (savedProject) => {
        // Now that save is successful, call runGraph
        toast.info("Project saved. Running graph...");
        runGraph(
          { projectId, input: graphInput },
          {
            // --- UPDATED: Robust parsing logic ---
            onSuccess: (runResult: any) => { // Accept 'any' to be safe
              let data: RunGraphResult | { error: string };
              
              if (typeof runResult === 'string') {
                try {
                  data = JSON.parse(runResult);
                } catch (e) {
                  console.error("Failed to parse graph output:", e);
                  data = { error: "Failed to parse server response." };
                }
              } else {
                data = runResult; // Assume it's already an object
              }

              setGraphOutput(data);
              
              if (!data.error) {
                toast.success("Graph run successful.");
              } else {
                toast.error("Graph run failed.");
              }
            },
            onError: (runError: Error) => {
              // 5. Set the ERROR object to state
              setGraphOutput({ error: runError.message });
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
      
      {/* --- UPDATED: Flex layout --- */}
      <div className="flex flex-grow overflow-hidden">
        {/* Left Sidebar */}
        <CanvasSidebar 
          onAddAgentNode={() => setIsAddAgentDialogOpen(true)} 
          onAddToolNode={() => setIsAddToolDialogOpen(true)} 
          agents={agents || []} 
          onAgentDragStart={onAgentDragStart} 
        />
        
        {/* Main Canvas */}
        <main className="flex-grow h-full">
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
            {/* --- REMOVED: Panel was here --- */}
            
            <Controls />
            <MiniMap />
            <Background variant="dots" gap={12} size={1} />
          </ReactFlow>
        </main>
        
        {/* --- ADDED: Right Sidebar --- */}
        <aside className="w-80 border-l bg-background p-4 flex flex-col gap-4 overflow-y-auto">
          <h2 className="text-lg font-semibold">Controls & Output</h2>
          
          {/* Input */}
          <div className="flex flex-col gap-2">
            <Label htmlFor="graph-input">Input</Label>
            <Textarea
              id="graph-input"
              placeholder="Enter input for the graph..."
              value={graphInput}
              onChange={(e) => setGraphInput(e.target.value)}
              rows={3}
            />
          </div>

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

          {/* Output */}
          <div className="flex-grow overflow-auto">
            <h3 className="text-md font-semibold mb-2">Execution Output</h3>
            {/* --- UPDATED: Output rendering --- */}
            {graphOutput ? (
              // --- UPDATED: Removed h-full, added min-h-0 ---
              <div className="p-2 bg-muted rounded-md w-full overflow-auto shadow-inner flex flex-col gap-2 min-h-0"> 
                {/* Check for error first */ console.log(graphOutput.success)}
                {graphOutput.error && (
                  <div className="p-2 bg-red-100 text-red-700 rounded-md">
                    <strong>Error:</strong> {graphOutput.error}
                  </div>
                )}
                
                {/* If no error, check for agent outputs */}
                {graphOutput.agent_outputs && Object.entries(graphOutput.agent_outputs).map(([agentName, output]) => (
                  <div key={agentName} className="p-2 border bg-card rounded-md">
                    <strong className="text-sm text-primary">{agentName}</strong>
                    <pre className="text-xs whitespace-pre-wrap font-sans mt-1">
                      {/* Display the clean 'response' string */ console.log(output)}
                      {output.response}
                    </pre>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-muted-foreground italic h-full flex items-center justify-center p-4 bg-muted rounded-md">
                Run the graph to see the output.
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}