"use client"

import { Button } from "@/components/ui/button";
import { UserPlus, Wrench } from "lucide-react"; // Using icons for the buttons

// Updated props to include the list of agents for the toolbox
interface CanvasSidebarProps {
  onAddAgentNode: () => void;
  onAddToolNode: () => void;
  agents: Array<{ id: string; name: string }>; // Pass in the agents from your useQuery
  onAgentDragStart: (event: React.DragEvent, agent: { id: string; name: string }) => void;
}

export const CanvasSidebar = ({ 
  onAddAgentNode, 
  onAddToolNode,
  agents = [], // Default to empty array
  onAgentDragStart
}: CanvasSidebarProps) => {
  return (
    <aside className="w-64 bg-background border-r p-4 flex flex-col gap-6">
      
      {/* Header: Title and round action buttons, aligned with flexbox */}
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold">Toolbox</h2>
        <div className="flex gap-2">
          <Button 
            onClick={onAddAgentNode} 
            variant="outline" 
            size="icon" 
            aria-label="Add new agent"
          >
            <UserPlus className="h-4 w-4" />
          </Button>
          <Button 
            onClick={onAddToolNode} 
            variant="outline" 
            size="icon" 
            aria-label="Add new tool"
          >
            <Wrench className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Agent Toolbox Section */}
      <div className="flex flex-col gap-3">
        <h3 className="text-sm font-medium text-muted-foreground px-1">Agents</h3>
        <div className="flex flex-col gap-2">
          {agents.length > 0 ? (
            agents.map((agent) => (
              <div
                key={agent.id}
                draggable
                onDragStart={(event) => onAgentDragStart(event, agent)}
                className="p-3 bg-card border rounded-md cursor-grab active:cursor-grabbing text-sm font-medium shadow-sm hover:bg-accent"
              >
                {agent.name}
              </div>
            ))
          ) : (
            <p className="text-xs text-muted-foreground text-center p-4 bg-muted/50 rounded-md">
              Click the <UserPlus className="inline h-3 w-3 -mt-0.5"/> icon to create your first agent.
            </p>
          )}
        </div>
      </div>
      
      {/* You could add a similar section for Tools here */}

    </aside>
  );
};
