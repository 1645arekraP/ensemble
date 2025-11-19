// components/Toolbox.tsx
"use client"

import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Users, Wrench, UserPlus, Box, GripVertical } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ApiAgentNode, ApiToolNode } from '@/lib/api'; // Import from api, not types
import { cn } from '@/lib/utils';

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
    <div className="h-full bg-white border-r border-neutral-200 flex flex-col overflow-hidden shadow-xl z-10">
      {/* Header with Add Buttons */}
      <div className="h-14 border-b border-neutral-200 px-4 flex items-center justify-between flex-shrink-0 bg-neutral-50/50">
        <div className="flex items-center gap-2">
          <Box className="w-4 h-4 text-primary" />
          <h2 className="text-sm font-semibold text-neutral-900">Components</h2>
        </div>
        <div className="flex gap-1">
          <Button
            onClick={onAddAgentNode}
            variant="ghost"
            size="icon"
            className="h-8 w-8 hover:bg-white hover:shadow-sm transition-all"
            title="Add new agent"
          >
            <UserPlus className="h-4 w-4 text-neutral-600" />
          </Button>
          <Button
            onClick={onAddToolNode}
            variant="ghost"
            size="icon"
            className="h-8 w-8 hover:bg-white hover:shadow-sm transition-all"
            title="Add new tool"
          >
            <Wrench className="h-4 w-4 text-neutral-600" />
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        {/* Agents Section */}
        <div className="space-y-2">
          <button
            onClick={() => setIsAgentsExpanded(!isAgentsExpanded)}
            className="w-full flex items-center justify-between text-xs font-semibold text-neutral-500 uppercase tracking-wider hover:text-neutral-800 transition-colors group"
          >
            <div className="flex items-center gap-2">
              <Users className="w-3 h-3" />
              <span>Agents</span>
            </div>
            <ChevronDown className={cn("w-3 h-3 transition-transform", !isAgentsExpanded && "-rotate-90")} />
          </button>

          {isAgentsExpanded && (
            <div className="space-y-2">
              {agents.length > 0 ? (
                agents.map((agent) => (
                  <div
                    key={agent.id}
                    draggable
                    onDragStart={(event) => onAgentDragStart(event, agent)}
                    className="group flex items-center gap-3 p-3 bg-white border border-neutral-200 rounded-lg shadow-sm hover:border-primary/50 hover:shadow-md transition-all cursor-grab active:cursor-grabbing"
                  >
                    <div className="p-2 bg-blue-50 text-blue-600 rounded-md">
                      <Users className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-neutral-900 truncate">{agent.name}</p>
                      <p className="text-xs text-neutral-500 truncate">{agent.role || 'General Agent'}</p>
                    </div>
                    <GripVertical className="w-4 h-4 text-neutral-300 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                ))
              ) : (
                <div className="text-center p-4 border border-dashed border-neutral-200 rounded-lg bg-neutral-50/50">
                  <p className="text-xs text-neutral-400">No agents available</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Tools Section */}
        <div className="space-y-2">
          <button
            onClick={() => setIsToolsExpanded(!isToolsExpanded)}
            className="w-full flex items-center justify-between text-xs font-semibold text-neutral-500 uppercase tracking-wider hover:text-neutral-800 transition-colors group"
          >
            <div className="flex items-center gap-2">
              <Wrench className="w-3 h-3" />
              <span>Tools</span>
            </div>
            <ChevronDown className={cn("w-3 h-3 transition-transform", !isToolsExpanded && "-rotate-90")} />
          </button>

          {isToolsExpanded && (
            <div className="space-y-2">
              {tools.length > 0 ? (
                tools.map((tool) => (
                  <div
                    key={tool.id}
                    draggable
                    onDragStart={(event) => onToolDragStart(event, tool)}
                    className="group flex items-center gap-3 p-3 bg-white border border-neutral-200 rounded-lg shadow-sm hover:border-primary/50 hover:shadow-md transition-all cursor-grab active:cursor-grabbing"
                  >
                    <div className="p-2 bg-purple-50 text-purple-600 rounded-md">
                      <Wrench className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-neutral-900 truncate">{tool.name}</p>
                      <p className="text-xs text-neutral-500 truncate capitalize">{tool.tool_type.replace('_', ' ')}</p>
                    </div>
                    <GripVertical className="w-4 h-4 text-neutral-300 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                ))
              ) : (
                <div className="text-center p-4 border border-dashed border-neutral-200 rounded-lg bg-neutral-50/50">
                  <p className="text-xs text-neutral-400">No tools available</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}