// components/Toolbox.tsx
"use client"

import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Users, Wrench, UserPlus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ApiAgentNode, ApiToolNode } from '@/lib/types'; // Import your types

interface ToolboxProps {
  isOpen: boolean;
  agents: ApiAgentNode[];
  tools: ApiToolNode[];
  onAddAgentNode: () => void;
  onAddToolNode: () => void;
  onAgentDragStart: (event: React.DragEvent, agent: ApiAgentNode) => void;
  onToolDragStart: (event: React.DragEvent, tool: ApiToolNode) => void;
}

export function Toolbox({
  isOpen,
  agents = [],
  tools = [],
  onAddAgentNode,
  onAddToolNode,
  onAgentDragStart,
  onToolDragStart,
}: ToolboxProps) {
  const [isAgentsExpanded, setIsAgentsExpanded] = useState(true);
  const [isToolsExpanded, setIsToolsExpanded] = useState(true);

  if (!isOpen) return null;

  return (
    <div className="h-full bg-white border-r border-neutral-200 flex flex-col overflow-hidden">
      {/* Header with Add Buttons */}
      <div className="h-14 border-b border-neutral-200 px-4 flex items-center justify-between flex-shrink-0">
        <h2 className="text-neutral-900 font-semibold">Toolbox</h2>
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

      <div className="flex-1 overflow-y-auto">
        {/* Agents Section */}
        <div className="border-b border-neutral-200">
          <button
            onClick={() => setIsAgentsExpanded(!isAgentsExpanded)}
            className="w-full px-4 py-3 flex items-center gap-2 hover:bg-neutral-50 transition-colors"
          >
            {isAgentsExpanded ? (
              <ChevronDown className="w-4 h-4 text-neutral-500" />
            ) : (
              <ChevronRight className="w-4 h-4 text-neutral-500" />
            )}
            <Users className="w-4 h-4 text-neutral-600" />
            <span className="text-neutral-700">Agents</span>
          </button>

          {isAgentsExpanded && (
            <div className="pb-2 px-2 space-y-1">
              {agents.length > 0 ? (
                agents.map((agent) => (
                  <div
                    key={agent.id}
                    draggable
                    onDragStart={(event) => onAgentDragStart(event, agent)}
                    className="w-full px-4 py-2 text-left text-neutral-600 hover:bg-neutral-50 transition-colors rounded-md cursor-grab active:cursor-grabbing border bg-card"
                  >
                    {agent.name}
                  </div>
                ))
              ) : (
                <p className="text-xs text-muted-foreground text-center p-4">
                  No agents created yet.
                </p>
              )}
            </div>
          )}
        </div>

        {/* Tools Section */}
        <div className="border-b border-neutral-200">
          <button
            onClick={() => setIsToolsExpanded(!isToolsExpanded)}
            className="w-full px-4 py-3 flex items-center gap-2 hover:bg-neutral-50 transition-colors"
          >
            {isToolsExpanded ? (
              <ChevronDown className="w-4 h-4 text-neutral-500" />
            ) : (
              <ChevronRight className="w-4 h-4 text-neutral-500" />
            )}
            <Wrench className="w-4 h-4 text-neutral-600" />
            <span className="text-neutral-700">Tools</span>
          </button>

          {isToolsExpanded && (
            <div className="pb-2 px-2 space-y-1">
              {tools.length > 0 ? (
                tools.map((tool) => (
                  <div
                    key={tool.id}
                    draggable
                    onDragStart={(event) => onToolDragStart(event, tool)}
                    className="w-full px-4 py-2 text-left text-neutral-600 hover:bg-neutral-50 transition-colors rounded-md cursor-grab active:cursor-grabbing border bg-card"
                  >
                    {tool.name}
                  </div>
                ))
              ) : (
                <p className="text-xs text-muted-foreground text-center p-4">
                  No tools created yet.
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}