"use client"

import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from "@/components/ui/button";
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from "@/components/ui/textarea";
import { AgentRole, AgentProvider, AddAgentFormState } from '../lib/types';

interface AddAgentNodeDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (formData: AddAgentFormState) => void;
}

const defaultState: AddAgentFormState = {
  name: 'New Agent',
  description: 'A new AI agent.',
  role: AgentRole.GENERAL,
  provider: AgentProvider.OPENAI,
  model: 'gpt-4o',
  system_instruction_prompt: 'You are a helpful AI assistant.',
};

export const AddAgentNodeDialog = ({ isOpen, onOpenChange, onSubmit }: AddAgentNodeDialogProps) => {
  const [formState, setFormState] = useState(defaultState);

  const handleChange = (field: keyof AddAgentFormState, value: string) => {
    setFormState(prev => ({ ...prev, [field]: value as any })); // Use 'as any' for simplicity with enum/string union
  };

  const resetForm = () => {
    setFormState(defaultState);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formState);
    onOpenChange(false);
    resetForm();
  };

  const handleClose = (open: boolean) => {
    onOpenChange(open);
    if (!open) {
      resetForm();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Add New Agent Node</DialogTitle>
          <DialogDescription>
            Configure the details for your new AI agent.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="agent-name" className="text-right">Name</Label>
            <Input id="agent-name" value={formState.name} onChange={(e) => handleChange('name', e.target.value)} className="col-span-3" />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="agent-desc" className="text-right">Description</Label>
            <Input id="agent-desc" value={formState.description} onChange={(e) => handleChange('description', e.target.value)} className="col-span-3" />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="agent-role" className="text-right">Role</Label>
            <Select value={formState.role} onValueChange={(value: AgentRole) => handleChange('role', value)}>
              <SelectTrigger className="col-span-3"><SelectValue /></SelectTrigger>
              <SelectContent>
                {Object.values(AgentRole).map(r => <SelectItem key={r} value={r}>{r}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="agent-provider" className="text-right">Provider</Label>
            <Select value={formState.provider} onValueChange={(value: AgentProvider) => handleChange('provider', value)}>
              <SelectTrigger className="col-span-3"><SelectValue /></SelectTrigger>
              <SelectContent>
                {Object.values(AgentProvider).map(p => <SelectItem key={p} value={p}>{p}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="agent-model" className="text-right">Model</Label>
            <Input id="agent-model" value={formState.model} onChange={(e) => handleChange('model', e.target.value)} className="col-span-3" />
          </div>
          <div className="grid grid-cols-4 items-start gap-4">
            <Label htmlFor="agent-prompt" className="text-right pt-2">System Prompt</Label>
            <Textarea id="agent-prompt" value={formState.system_instruction_prompt} onChange={(e) => handleChange('system_instruction_prompt', e.target.value)} className="col-span-3" rows={4} />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => handleClose(false)}>Cancel</Button>
            <Button type="submit">Create Agent</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};