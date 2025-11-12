// components/ControlPanel.tsx
"use client"

import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, ChevronUp, Send, Play, Save as SaveIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ChatMessage, RunGraphResult } from '@/lib/types';
import LoadingSpinner from '@/components/LoadingSpinner';

interface ControlPanelProps {
  isOpen: boolean;
  // Chat props
  chatHistory: ChatMessage[];
  chatInput: string;
  setChatInput: (value: string) => void;
  handleChatSubmit: (e: React.FormEvent) => void;
  isGenerating: boolean;
  // Run props
  graphInput: string;
  setGraphInput: (value: string) => void;
  graphOutput: RunGraphResult | { error: string } | null;
  handleSaveProject: () => void;
  handleSaveAndRun: () => void;
  isSaving: boolean;
  isExecuting: boolean;
}

export function ControlPanel({
  isOpen,
  chatHistory,
  chatInput,
  setChatInput,
  handleChatSubmit,
  isGenerating,
  graphInput,
  setGraphInput,
  graphOutput,
  handleSaveProject,
  handleSaveAndRun,
  isSaving,
  isExecuting,
}: ControlPanelProps) {
  const [isChatExpanded, setIsChatExpanded] = useState(true);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll chat
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [chatHistory, isGenerating]);

  if (!isOpen) return null;

  return (
    <div className="h-full bg-white border-l border-neutral-200 flex flex-col overflow-hidden">
      <div className="h-14 border-b border-neutral-200 px-4 flex items-center flex-shrink-0">
        <h2 className="text-neutral-900 font-semibold">Controls & Output</h2>
      </div>

      <div className="flex-1 overflow-y-auto flex flex-col">
        {/* AI Chat Section - Collapsible */}
        <div className="border-b border-neutral-200">
          <button
            onClick={() => setIsChatExpanded(!isChatExpanded)}
            className="w-full px-4 py-3 flex items-center justify-between hover:bg-neutral-50 transition-colors"
          >
            <span className="text-neutral-700">AI Chat</span>
            {isChatExpanded ? (
              <ChevronUp className="w-4 h-4 text-neutral-500" />
            ) : (
              <ChevronDown className="w-4 h-4 text-neutral-500" />
            )}
          </button>

          {isChatExpanded && (
            <div className="p-4 space-y-3">
              {/* Chat Messages */}
              <div
                ref={chatContainerRef}
                className="space-y-3 max-h-64 overflow-y-auto p-3 bg-muted/50 rounded-md border"
              >
                {chatHistory.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center p-4">
                    Describe the workflow you want to build...
                  </p>
                )}
                {chatHistory.map((msg, index) => (
                  <div
                    key={index}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`p-2 rounded-lg text-sm ${
                        msg.role === 'user'
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-secondary'
                      }`}
                    >
                      {msg.content}
                    </div>
                  </div>
                ))}
                {isGenerating && (
                  <div className="flex justify-start">
                    <div className="p-2 rounded-lg bg-secondary">
                      <LoadingSpinner />
                    </div>
                  </div>
                )}
              </div>

              {/* Chat Input */}
              <form onSubmit={handleChatSubmit} className="flex gap-2">
                <Input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder="e.g., 'Add a summarizer...'"
                  disabled={isGenerating || isExecuting}
                />
                <Button
                  type="submit"
                  size="icon"
                  className="flex-shrink-0"
                  disabled={isGenerating || isExecuting}
                >
                  <Send className="w-4 h-4" />
                </Button>
              </form>
            </div>
          )}
        </div>

        {/* Run Input Section */}
        <div className="flex-1 p-4 space-y-4">
          <div>
            <Label htmlFor="graph-input" className="block text-neutral-700 mb-2">
              Run Input
            </Label>
            <Textarea
              id="graph-input"
              value={graphInput}
              onChange={(e) => setGraphInput(e.target.value)}
              placeholder="Enter input for the graph..."
              className="w-full min-h-24 resize-none"
            />
          </div>

          {/* Save & Run Buttons */}
          <div className="flex gap-2">
            <Button
              variant="outline"
              className="flex-1 gap-2"
              onClick={handleSaveProject}
              disabled={isSaving || isExecuting}
            >
              {isSaving ? <LoadingSpinner /> : <SaveIcon className="w-4 h-4" />}
              Save
            </Button>
            <Button
              className="flex-1 gap-2"
              onClick={handleSaveAndRun}
              disabled={isSaving || isExecuting || !graphInput}
            >
              {isExecuting ? <LoadingSpinner /> : <Play className="w-4 h-4" />}
              {isSaving ? 'Saving...' : isExecuting ? 'Running...' : 'Save & Run'}
            </Button>
          </div>

          {/* Execution Output */}
          <div>
            <Label className="block text-neutral-700 mb-2">Execution Output</Label>
            <div className="w-full min-h-32 p-4 border rounded-lg bg-muted/50 overflow-y-auto max-h-64 shadow-inner">
              {graphOutput ? (
                <div className="flex flex-col gap-2">
                  {graphOutput.error && (
                    <div className="p-2 bg-red-100 text-red-700 rounded-md">
                      <strong>Error:</strong> {graphOutput.error}
                    </div>
                  )}
                  {graphOutput.agent_outputs &&
                    Object.entries(graphOutput.agent_outputs).map(([agentName, output]) => (
                      <div key={agentName} className="p-2 border bg-card rounded-md">
                        <strong className="text-sm text-primary">{agentName}</strong>
                        <pre className="text-xs whitespace-pre-wrap font-sans mt-1">
                          {output.response}
                        </pre>
                      </div>
                    ))}
                </div>
              ) : (
                <p className="text-neutral-400 text-sm italic">
                  Run the graph to see the output.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}