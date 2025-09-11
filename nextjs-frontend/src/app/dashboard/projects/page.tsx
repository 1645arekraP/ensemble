"use client"

import { SiteHeader } from "@/components/site-header"
import useSWR from 'swr'
import { useAuth } from "@/context/auth-context";
import { useState, FormEvent, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ProjectCard } from "@/components/project-card";



// --- Type definitions ---
type User = { id: number; username: string; };
import { type Project } from "@/lib/types";


export default function ProjectsPage() {
    const { isLoggedIn, isPageLoading, logout } = useAuth();
    const router = useRouter();
    const [projectName, setProjectName] = useState("");
    const [projectDescription, setProjectDescription] = useState("");

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

    useEffect(() => {
        if (!isLoggedIn && !isPageLoading) {
            router.push('/login');
        }
    }, [isLoggedIn, router]);

    const apiUrl = 'http://127.0.0.1:8000/api/dashboard/projects/';
    
    // FIXED: Changed memoizedFetcher to fetcher
    const { data: projects, error, isLoading, mutate } = useSWR<Project[]>(
        isLoggedIn ? apiUrl : null,
        fetcher
    );

    const handleCreateProject = async (e: FormEvent) => {
        e.preventDefault();
        const accessToken = localStorage.getItem("access_token");
        if (!projectName || !accessToken) {
            alert("Project name is required.");
            return;
        }

        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: projectName,
                    description: projectDescription,
                }),
            });

            if (!response.ok) {
                // This won't automatically refresh the token. 
                // A better approach would be to create a reusable `authedFetch` function.
                throw new Error('Failed to create project.');
            }

            mutate();
            setProjectName("");
            setProjectDescription("");

        } catch (err) {
            console.error(err);
            alert("An error occurred while creating the project.");
        }
    };

    if (!isLoggedIn) {
        return null; 
    }

    let content;
    if (isLoading) {
        content = <p>Loading projects...</p>;
    } else if (error) {
        content = <p className="text-red-500">Error: {error.message}</p>;
    } else if (projects) {
        content = (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {projects.map((project) => (
                    <ProjectCard key={project.id} project={project} />
                ))}
            </div>
        );
    }
    
    return (
        <>
            <SiteHeader name="Projects" />
            <div className="flex flex-1 flex-col gap-6 p-4 md:p-6">
                
                {/* ADDED: The form for creating a new project */}
                <div className="p-4 border rounded-lg bg-card">
                    <h2 className="text-lg font-semibold mb-3">Create a New Project</h2>
                    <form onSubmit={handleCreateProject} className="flex flex-col gap-4">
                        <Input
                            type="text"
                            placeholder="Project Name"
                            value={projectName}
                            onChange={(e) => setProjectName(e.target.value)}
                            required
                        />
                        <Input
                            type="text"
                            placeholder="Project Description (Optional)"
                            value={projectDescription}
                            onChange={(e) => setProjectDescription(e.target.value)}
                        />
                        <Button type="submit">Create Project</Button>
                    </form>
                </div>
                
                {/* The list of existing projects */}
                <div className="flex flex-col gap-2">
                   {content}
                </div>

            </div>
        </>
    );
}