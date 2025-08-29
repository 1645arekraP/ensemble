"use client"

import { use, useState, useCallback } from 'react';
import { useAuth } from "@/context/auth-context";
import useSWR from 'swr';
import { type Project } from "@/lib/types";
import { SiteHeader } from "@/components/site-header";
import { ReactFlow, applyNodeChanges, applyEdgeChanges, addEdge } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
 
const initialNodes = [
  { id: '1', position: { x: 0, y: 0 }, data: { label: 'Start Node' } },
];

type AsyncProps<T> = T | Promise<T>;

// This is the page component for a single project canvas
export default function ProjectCanvasPage({ params }: { params: AsyncProps<{ projectId: string }> }) {
    // 2. Unwrap the params Promise with the `use()` hook
    const resolvedParams = use(params);
    const projectId = resolvedParams.projectId;
    const { logout } = useAuth(); // We'll need the fetcher logic again
    const [nodes, setNodes] = useState(initialNodes);
    const [edges, setEdges] = useState([]);

    // --- React Flow callbacks ---
    const onNodesChange = useCallback((changes) => setNodes((nds) => applyNodeChanges(changes, nds)), []);
    const onEdgesChange = useCallback((changes) => setEdges((eds) => applyEdgeChanges(changes, eds)), []);
    const onConnect = useCallback((params) => setEdges((eds) => addEdge(params, eds)), []);

    // --- Data Fetching Logic (same as before) ---
    const fetcher = useCallback(async (url: string) => {
      // ... (copy your full fetcher logic with token refresh here)
      let accessToken = localStorage.getItem("access_token");
      const res = await fetch(url, { headers: { 'Authorization': `Bearer ${accessToken}` } });
      if (!res.ok) throw new Error("Failed to fetch");
      return res.json();
    }, [logout]);
    
    // 1. Fetch data for this specific project using the ID from the URL
    const apiUrl = `http://127.0.0.1:8000/api/dashboard/projects/${projectId}/`;
    const { data: project, error, isLoading } = useSWR<Project>(apiUrl, fetcher);

    if (isLoading) return <div>Loading Project...</div>;
    if (error) return <div>Failed to load project.</div>;
    if (!project) return <div>Project not found.</div>;

    // TODO: Later, you will load nodes and edges from `project.graph_data`
    // useEffect(() => {
    //   if (project?.graph_data) {
    //     setNodes(project.graph_data.nodes || initialNodes);
    //     setEdges(project.graph_data.edges || []);
    //   }
    // }, [project]);

    return (
        <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
            <SiteHeader name={`Canvas: ${project.name}`} />
            <div style={{ flexGrow: 1 }}>
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    onConnect={onConnect}
                    fitView
                />
            </div>
        </div>
    );
}