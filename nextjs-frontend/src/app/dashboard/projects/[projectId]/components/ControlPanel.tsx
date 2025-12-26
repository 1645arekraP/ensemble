// components/ControlPanel.tsx
"use client"

import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, ChevronUp, Send, Play, Save as SaveIcon, Terminal, MessageSquare, Activity } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ChatMessage } from '@/lib/types';
import LoadingSpinner from '@/components/LoadingSpinner';
import { cn } from '@/lib/utils';

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
  logs: any[]; // Array of log objects or strings
  handleSaveProject: () => void;
  handleSaveAndRun: () => void;
  isSaving: boolean;
  isExecuting: boolean;
  finalOutput?: string | null;
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
  logs,
  handleSaveProject,
  handleSaveAndRun,
  isSaving,
  isExecuting,
  finalOutput,
}: ControlPanelProps) {
  const [activeTab, setActiveTab] = useState<'chat' | 'run'>('run');
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const logsContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll chat
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [chatHistory, isGenerating]);

  // Auto-scroll logs
  useEffect(() => {
    if (logsContainerRef.current) {
      logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight;
    }
  }, [logs]);

  if (!isOpen) return null;

  return (
    <div className="h-full bg-white border-l border-neutral-200 flex flex-col overflow-hidden shadow-xl">
      {/* Header / Tabs */}
      <div className="flex items-center border-b border-neutral-200 bg-neutral-50">
        <button
          onClick={() => setActiveTab('run')}
          className={cn(
            "flex-1 py-3 text-sm font-medium flex items-center justify-center gap-2 transition-colors relative",
            activeTab === 'run'
              ? "text-primary bg-white"
              : "text-neutral-500 hover:text-neutral-700 hover:bg-neutral-100"
          )}
        >
          <Terminal className="w-4 h-4" />
          Run & Debug
          {activeTab === 'run' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
          )}
        </button>
        <div className="w-px h-6 bg-neutral-200" />
        <button
          onClick={() => setActiveTab('chat')}
          className={cn(
            "flex-1 py-3 text-sm font-medium flex items-center justify-center gap-2 transition-colors relative",
            activeTab === 'chat'
              ? "text-primary bg-white"
              : "text-neutral-500 hover:text-neutral-700 hover:bg-neutral-100"
          )}
        >
          <MessageSquare className="w-4 h-4" />
          AI Assistant
          {activeTab === 'chat' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
          )}
        </button>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-hidden flex flex-col bg-white">

        {/* --- RUN TAB --- */}
        {activeTab === 'run' && (
          <div className="flex-1 flex flex-col p-4 space-y-4 overflow-hidden">

            {/* Input Section */}
            <div className="flex-shrink-0 space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="graph-input" className="text-neutral-700 font-medium">
                  Input Data
                </Label>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 gap-1 text-xs"
                    onClick={handleSaveProject}
                    disabled={isSaving || isExecuting}
                  >
                    {isSaving ? <LoadingSpinner /> : <SaveIcon className="w-3 h-3" />}
                    Save
                  </Button>
                  <Button
                    size="sm"
                    className="h-8 gap-1 text-xs"
                    onClick={handleSaveAndRun}
                    disabled={isSaving || isExecuting || !graphInput}
                  >
                    {isExecuting ? <LoadingSpinner /> : <Play className="w-3 h-3" />}
                    Run
                  </Button>
                </div>
              </div>
              <Textarea
                id="graph-input"
                value={graphInput}
                onChange={(e) => setGraphInput(e.target.value)}
                placeholder="Enter the initial input for your workflow..."
                className="min-h-[100px] resize-none font-mono text-sm"
              />
            </div>

            {/* Terminal Output Section */}
            <div className="flex-1 flex flex-col min-h-0 border rounded-lg overflow-hidden bg-[#1e1e1e] text-white shadow-inner">
              <div className="flex items-center justify-between px-3 py-2 bg-[#2d2d2d] border-b border-[#3d3d3d]">
                <div className="flex items-center gap-2">
                  <Terminal className="w-3 h-3 text-neutral-400" />
                  <span className="text-xs font-mono text-neutral-300">Console Output</span>
                </div>
                {isExecuting && (
                  <div className="flex items-center gap-2">
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                    </span>
                    <span className="text-xs text-green-400 font-mono">Running...</span>
                  </div>
                )}
              </div>

              <div
                ref={logsContainerRef}
                className="flex-1 p-3 overflow-y-auto font-mono text-xs space-y-1"
              >
                {logs.length === 0 ? (
                  <div className="text-neutral-500 italic p-2">
                    Ready to execute. Logs will appear here...
                  </div>
                ) : (
                  logs.map((log, i) => (
                    <div key={i} className="break-words whitespace-pre-wrap border-b border-white/5 pb-1 mb-1 last:border-0">
                      {renderLogItem(log)}
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Final Output Section */}
            {finalOutput && (
              <div className="flex-shrink-0 border rounded-lg overflow-hidden bg-green-50 border-green-200 shadow-sm">
                <div className="flex items-center gap-2 px-3 py-2 bg-green-100 border-b border-green-200">
                  <Activity className="w-3 h-3 text-green-700" />
                  <span className="text-xs font-bold text-green-800 uppercase tracking-wider">Final Output</span>
                </div>
                <div className="p-3 max-h-[150px] overflow-y-auto text-sm text-neutral-800 whitespace-pre-wrap">
                  {finalOutput}
                </div>
              </div>
            )}

          </div>
        )}

        {/* --- CHAT TAB --- */}
        {activeTab === 'chat' && (
          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="flex-1 overflow-y-auto p-4 space-y-4" ref={chatContainerRef}>
              {chatHistory.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full text-center text-neutral-500 space-y-2">
                  <MessageSquare className="w-8 h-8 opacity-20" />
                  <p className="text-sm">Describe the workflow you want to build...</p>
                </div>
              )}
              {chatHistory.map((msg, index) => (
                <div
                  key={index}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={cn(
                      "max-w-[85%] p-3 rounded-2xl text-sm shadow-sm",
                      msg.role === 'user'
                        ? "bg-primary text-primary-foreground rounded-br-none"
                        : "bg-neutral-100 text-neutral-800 rounded-bl-none"
                    )}
                  >
                    {msg.content}
                  </div>
                </div>
              ))}
              {isGenerating && (
                <div className="flex justify-start">
                  <div className="p-3 rounded-2xl rounded-bl-none bg-neutral-100">
                    <LoadingSpinner />
                  </div>
                </div>
              )}
            </div>

            <div className="p-4 border-t border-neutral-200 bg-white">
              <form onSubmit={handleChatSubmit} className="flex gap-2">
                <Input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder="Ask AI to modify the graph..."
                  disabled={isGenerating || isExecuting}
                  className="flex-1"
                />
                <Button
                  type="submit"
                  size="icon"
                  disabled={isGenerating || isExecuting}
                  className="shrink-0"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function renderLogItem(log: any) {
  if (typeof log === 'string') return <span className="text-neutral-300">{log}</span>;

  if (log.type === 'start') {
    return <span className="text-blue-400 font-bold">🚀 {log.message}</span>;
  }
  if (log.type === 'agent_output') {
    return (
      <div>
        <span className="text-purple-400 font-bold">🤖 {log.node}:</span>
        <span className="text-neutral-300 ml-2">{log.output}</span>
      </div>
    );
  }
  if (log.type === 'update') {
    return <span className="text-yellow-500/80">⚡ {log.message}</span>;
  }
  if (log.type === 'tool_output') {
    return (
      <div className="mt-1 mb-2">
        <div className="text-blue-400 font-bold text-xs mb-1">🛠️ Tool Output ({log.node}):</div>
        <div className="bg-black/30 p-2 rounded border border-white/10 text-neutral-300 font-mono text-xs whitespace-pre-wrap">
          {log.output}
        </div>
      </div>
    );
  }
  if (log.type === 'complete') {
    return <span className="text-green-400 font-bold">✅ {log.message}</span>;
  }
  if (log.type === 'error') {
    return <span className="text-red-400 font-bold">❌ Error: {log.error}</span>;
  }

  return <span className="text-neutral-300">{JSON.stringify(log)}</span>;
}