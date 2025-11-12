import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Users, Wrench } from 'lucide-react';

interface ToolboxProps {
  isOpen: boolean;
}

export function Toolbox({ isOpen }: ToolboxProps) {
  const [isAgentsExpanded, setIsAgentsExpanded] = useState(true);
  const [isToolsExpanded, setIsToolsExpanded] = useState(true);

  const agents = [
    'New Agent',
    'testing',
    'Agent number 3',
    'Gemini',
    'Joker',
    'Poet',
    'Pokemon Trivia',
    'Pokemon',
    "Captain 'Short-Hand' Scallywag",
  ];

  const tools = ['Default'];

  if (!isOpen) return null;

  return (
    <div className="h-full bg-white border-r border-neutral-200 flex flex-col overflow-hidden">
      <div className="h-14 border-b border-neutral-200 px-4 flex items-center flex-shrink-0">
        <h2 className="text-neutral-900">Toolbox</h2>
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
            <div className="pb-2">
              {agents.map((agent, index) => (
                <button
                  key={index}
                  className="w-full px-4 py-2 pl-10 text-left text-neutral-600 hover:bg-neutral-50 transition-colors"
                  draggable
                  onDragStart={(e) => {
                    e.dataTransfer.setData('agent', agent);
                  }}
                >
                  {agent}
                </button>
              ))}
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
            <div className="pb-2">
              {tools.map((tool, index) => (
                <button
                  key={index}
                  className="w-full px-4 py-2 pl-10 text-left text-neutral-600 hover:bg-neutral-50 transition-colors"
                  draggable
                  onDragStart={(e) => {
                    e.dataTransfer.setData('tool', tool);
                  }}
                >
                  {tool}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}