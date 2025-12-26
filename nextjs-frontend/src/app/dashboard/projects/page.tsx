"use client"

import { SiteHeader } from "@/components/site-header"
import { useState, FormEvent } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ProjectCard } from "@/components/project-card";
import { getProjects, createProject } from "@/lib/api";
import { type Project } from "@/lib/types";


export default function ProjectsPage() {
  const queryClient = useQueryClient();
  const [projectName, setProjectName] = useState("");
  const [projectDescription, setProjectDescription] = useState("");


  const { data: projects, isLoading, error } = useQuery<Project[], Error>({
    queryKey: ['projects'],
    queryFn: getProjects,
  });

  
  const { mutate: createProjectMutation, isPending: isCreating, error: createError } = useMutation({
    mutationFn: createProject,
    onSuccess: () => {
      console.log("Project created successfully!");
      // This automatically refetches the projects list after a new one is created.
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      // Reset form fields
      setProjectName("");
      setProjectDescription("");
    },
    onError: (err) => {
      console.error("Failed to create project:", err);
    }
  });

  const handleCreateProject = (e: FormEvent) => {
    e.preventDefault();
    if (!projectName) return;
    createProjectMutation({ name: projectName, description: projectDescription });
  };
  
  // 3. Removed all manual auth checks (isLoggedIn, useEffect, etc.)
  // The DashboardAuthWrapper in your layout already handles this!

  // Helper to render the main content based on the query state
  const renderContent = () => {
    if (isLoading) {
      return <p>Loading projects...</p>;
    }
    if (error) {
      return <p className="text-red-500">Error: {error.message}</p>;
    }
    if (projects && projects.length > 0) {
      return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      );
    }
    return <p>No projects found. Create one to get started!</p>
  };

  return (
    <>
      <SiteHeader name="Projects" />
      <div className="flex flex-1 flex-col gap-6 p-4 md:p-6">
        
        <div className="p-4 border rounded-lg bg-card">
          <h2 className="text-lg font-semibold mb-3">Create a New Project</h2>
          <form onSubmit={handleCreateProject} className="flex flex-col gap-4">
            <Input
              type="text"
              placeholder="Project Name"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              required
              disabled={isCreating}
            />
            <Input
              type="text"
              placeholder="Project Description (Optional)"
              value={projectDescription}
              onChange={(e) => setProjectDescription(e.target.value)}
              disabled={isCreating}
            />
            <Button type="submit" disabled={isCreating}>
              {isCreating ? "Creating..." : "Create Project"}
            </Button>
            {createError && (
              <p className="text-sm text-red-500">Failed to create project: {createError.message}</p>
            )}
          </form>
        </div>
        
        <div className="flex flex-col gap-2">
          {renderContent()}
        </div>
      </div>
    </>
  );
}
