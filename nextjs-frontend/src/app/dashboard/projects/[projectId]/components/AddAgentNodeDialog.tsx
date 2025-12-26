import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogClose
} from '@/components/ui/dialog';
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { AddAgentFormState, Mcp } from '@/lib/types';
import { generateAgentConfig, getMcps } from '@/lib/api';
import { Sparkles } from 'lucide-react';
import LoadingSpinner from '@/components/LoadingSpinner';
import { toast } from 'sonner';


enum AgentRole {
  GENERAL = 'general',
  SUPERVISOR = 'supervisor',
}


enum AgentProvider {
  OPENAI = 'openai',
  ANTHROPIC = 'anthropic',
  GOOGLE = 'google',
  CUSTOM = 'custom'
}

interface AddAgentNodeDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (formData: AddAgentFormState) => void;
}

export const AddAgentNodeDialog = ({
  isOpen,
  onOpenChange,
  onSubmit
}: AddAgentNodeDialogProps) => {
  const [generationPrompt, setGenerationPrompt] = useState('');

  // Form state with default values
  const [name, setName] = useState('New Agent');
  const [description, setDescription] = useState('A new AI agent.');
  const [role, setRole] = useState<AgentRole>(AgentRole.GENERAL);

  const [provider, setProvider] = useState<AgentProvider>(AgentProvider.GOOGLE);
  const [model, setModel] = useState('gemini-2.5-flash');
  const [selectedMcps, setSelectedMcps] = useState<number[]>([]);

  const [systemPrompt, setSystemPrompt] = useState('You are a helpful AI assistant.');

  // Fetch available MCPs
  const { data: mcps } = useQuery<Mcp[]>({
    queryKey: ['mcps'],
    queryFn: getMcps,
    enabled: isOpen, // Only fetch when dialog is open
  });

  const resetForm = () => {
    setGenerationPrompt('');
    setName('New Agent');
    setDescription('A new AI agent.');
    setRole(AgentRole.GENERAL);
    setProvider(AgentProvider.OPENAI); // Reset provider
    setModel('gpt-4o'); // Reset model
    setSystemPrompt('You are a helpful AI assistant.');
    setSelectedMcps([]);
  };

  // --- Add the mutation for generating the config ---
  const { mutate: generateConfig, isPending: isGenerating } = useMutation({
    mutationFn: generateAgentConfig,
    onSuccess: (data) => {
      // Pre-fill the form fields with the AI's response
      setName(data.name);
      setDescription(data.description);
      setSystemPrompt(data.system_instruction_prompt);
      toast.success("Agent config generated!");
    },
    onError: (err: Error) => {
      toast.error("Generation Failed", { description: err.message });
    },
  });

  const handleGenerateClick = () => {
    if (!generationPrompt) {
      toast.error("Please enter a prompt to generate from.");
      return;
    }
    generateConfig({ prompt: generationPrompt });
  };

  const handleMcpToggle = (mcpId: number) => {
    setSelectedMcps(prev =>
      prev.includes(mcpId)
        ? prev.filter(id => id !== mcpId)
        : [...prev, mcpId]
    );
  };

  // This is the final "Create" button submit
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      name,
      description,
      role,
      system_instruction_prompt: systemPrompt,
      provider,
      model,
      mcp_ids: selectedMcps,
    });
  };

  const handleClose = (open: boolean) => {
    onOpenChange(open);
    if (!open) {
      setTimeout(resetForm, 300); // Reset after closing
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Add New Agent</DialogTitle>
          <DialogDescription>
            Create a new agent in your library. It will then be available in the sidebar.
          </DialogDescription>
        </DialogHeader>

        {/* --- "Generate" UI --- */}
        <div className="space-y-2">
          <Label htmlFor="generate-prompt">Generate from a prompt</Label>
          <div className="flex gap-2">
            <Textarea
              id="generate-prompt"
              placeholder="e.g., 'A snarky pirate researcher who finds information'"
              value={generationPrompt}
              onChange={(e) => setGenerationPrompt(e.target.value)}
              rows={2}
            />
            <Button
              variant="outline"
              size="icon"
              onClick={handleGenerateClick}
              disabled={isGenerating}
              aria-label="Generate config"
            >
              {isGenerating ? <LoadingSpinner /> : <Sparkles className="h-4 w-4" />}
            </Button>
          </div>
        </div>

        <div className="h-px bg-border my-4" /> {/* Separator */}

        {/* --- Main Agent Form --- */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="agent-name" className="text-right">Name</Label>
            <Input
              id="agent-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="col-span-3"
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="agent-desc" className="text-right">Description</Label>
            <Input
              id="agent-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="col-span-3"
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="agent-role" className="text-right">Role</Label>
            <Select value={role} onValueChange={(value: AgentRole) => setRole(value)}>
              <SelectTrigger className="col-span-3"><SelectValue /></SelectTrigger>
              <SelectContent>
                {Object.values(AgentRole).map(r => (
                  <SelectItem key={r} value={r}>{r}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* --- Provider Select --- */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="agent-provider" className="text-right">Provider</Label>
            <Select value={provider} onValueChange={(value: AgentProvider) => setProvider(value)}>
              <SelectTrigger className="col-span-3"><SelectValue /></SelectTrigger>
              <SelectContent>
                {Object.values(AgentProvider).map(p => (
                  <SelectItem key={p} value={p}>{p}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* --- Model Input --- */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="agent-model" className="text-right">Model</Label>
            <Input
              id="agent-model"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="col-span-3"
              placeholder="e.g., gpt-4o, gemini-1.5-flash"
            />
          </div>

          <div className="grid grid-cols-4 items-start gap-4">
            <Label htmlFor="agent-prompt" className="text-right pt-2">
              System Prompt
            </Label>
            <Textarea
              id="agent-prompt"
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              className="col-span-3"
              rows={6}
            />
          </div>

          {/* --- MCP Selection --- */}
          {mcps && mcps.length > 0 && (
            <div className="grid grid-cols-4 items-start gap-4">
              <Label className="text-right pt-2">MCP Integrations</Label>
              <div className="col-span-3 space-y-2 border rounded-md p-3">
                {mcps.map((mcp) => (
                  <div key={mcp.id} className="flex items-center space-x-2">
                    <Checkbox
                      id={`mcp-${mcp.id}`}
                      checked={selectedMcps.includes(mcp.id)}
                      onCheckedChange={() => handleMcpToggle(mcp.id)}
                    />
                    <Label htmlFor={`mcp-${mcp.id}`} className="text-sm font-normal cursor-pointer">
                      {mcp.name}
                    </Label>
                  </div>
                ))}
              </div>
            </div>
          )}

          <DialogFooter>
            <DialogClose asChild>
              <Button type="button" variant="outline">Cancel</Button>
            </DialogClose>
            <Button type="submit">
              Create Agent
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};