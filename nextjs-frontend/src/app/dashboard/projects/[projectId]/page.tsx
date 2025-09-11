"use client"

import { use, useState, useCallback, useEffect } from 'react';
import { useAuth } from "@/context/auth-context";
import useSWR from 'swr';
import { type Project } from "@/lib/types";
import { SiteHeader } from "@/components/site-header";
import { 
  Background,
  Controls,
  Panel,
  MiniMap,
  ReactFlow,
  addEdge,
  applyEdgeChanges,
  applyNodeChanges } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Button } from "@/components/ui/button";

type AsyncProps<T> = T | Promise<T>;

// This is the page component for a single project canvas
export default function ProjectCanvasPage({ params }: { params: AsyncProps<{ projectId: string }> }) {
    // 2. Unwrap the params Promise with the `use()` hook
    const resolvedParams = use(params);
    const projectId = resolvedParams.projectId;
    const { logout } = useAuth(); // We'll need the fetcher logic again
    const [nodes, setNodes] = useState([]);
    const [edges, setEdges] = useState([]);
    const [isSaving, setIsSaving] = useState(false);

    // --- React Flow callbacks ---
    const onNodesChange = useCallback((changes) => setNodes((nds) => applyNodeChanges(changes, nds)), []);
    const onEdgesChange = useCallback((changes) => setEdges((eds) => applyEdgeChanges(changes, eds)), []);
    const onConnect = useCallback((params) => setEdges((eds) => addEdge(params, eds)), []);

    // --- Data Fetching Logic (same as before) ---
    const fetcher = useCallback(async (url: string) => {
        let accessToken = localStorage.getItem("access_token");

        const res = await fetch(url, {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });

        if (!res.ok) {
            if (res.status === 401) {
                const refreshToken = localStorage.getItem("refresh_token");
                if (!refreshToken) {
                    logout();
                    throw new Error("Session expired. Please log in again.");
                }

                try {
                    // NOTE: Ensure this is your correct refresh endpoint
                    const refreshRes = await fetch('http://127.0.0.1:8000/api/token/refresh/', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ refresh: refreshToken }),
                    });

                    if (!refreshRes.ok) {
                        logout();
                        throw new Error("Session expired. Please log in again.");
                    }
                    
                    const { access: newAccessToken } = await refreshRes.json();
                    localStorage.setItem("access_token", newAccessToken);

                    const retryRes = await fetch(url, {
                        headers: { 'Authorization': `Bearer ${newAccessToken}` }
                    });
                    
                    if (!retryRes.ok) throw new Error('Failed after refreshing token.');
                    
                    return retryRes.json();
                } catch (e) {
                    throw e;
                }
            }
            throw new Error('An error occurred while fetching the data.');
        }

        return res.json();
    }, [logout]);
    
    const apiUrl = `http://127.0.0.1:8000/api/dashboard/projects/${projectId}/`;
    const { data: project, error, isLoading } = useSWR<Project>(apiUrl, fetcher);

    useEffect(() => {
      // Check if project and graph_data exist
      if (project?.graph_data) {
        // It's good practice to validate the data, but for now we'll trust it
        setNodes(project.graph_data.nodes || []);
        setEdges(project.graph_data.edges || []);
      }
    }, [project]);

    const handleSave = async () => {
        setIsSaving(true);
        const accessToken = localStorage.getItem("access_token");

        const payload = {
            graph_data: {
                nodes,
                edges,
            }
        };

        try {
            const response = await fetch(apiUrl, {
                method: 'PATCH', // PATCH updates a part of the resource
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                throw new Error('Failed to save project.');
            }
            
            alert('Project saved successfully!');

        } catch (err) {
            console.error(err);
            alert('An error occurred while saving.');
        } finally {
            setIsSaving(false);
        }
    };
    const addNode = () => {
        const newNodeId = `node_${Date.now()}`;
        const newNode = {
            id: newNodeId,
            position: {
            x: 0,
            y: 0,
            },
            data: {
            label: `New Node`,
            },
        };
        setNodes((nodes) => [...nodes, newNode]);
    };


    if (isLoading) return <div>Loading Project...</div>;
    if (error) return <div>Failed to load project.</div>;
    if (!project) return <div>Project not found.</div>;

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
                >
                    <Panel position="top-center">
                        <div className="flex">
                            <Button type="submit" onClick={handleSave}>Save Project</Button> 
                            <Button type="submit" onClick={addNode}>Add Node</Button>
                        </div>
                        
                    </Panel>
                    <Controls />
                    <MiniMap />
                    <Background variant="dots" gap={12} size={1} />
                </ ReactFlow>
            </div>
        </div>
    );
}