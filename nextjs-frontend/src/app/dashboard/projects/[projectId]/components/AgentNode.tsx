"use client"

import { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from "@/components/ui/textarea";
import { XIcon } from 'lucide-react';
import { AgentNodeData, AgentRole, AgentProvider } from '@/lib/types'; // Make sure types are imported

const AgentNode = memo(({ id, data }: NodeProps<AgentNodeData>) => {
  // 1. 'tools' and 'allNodes' are no longer part of the data prop
  const { 
    name, 
    role, 
    provider, 
    model, 
    system_instruction_prompt, 
    updateNodeData, 
    deleteNode 
  } = data;

  // 2. The handleInputChange function is the same
  const handleInputChange = (field: keyof Omit<AgentNodeData, 'updateNodeData' | 'deleteNode'>, value: string) => {
    updateNodeData(id, { [field]: value });
  };
  
  // 3. 'availableTools' and 'handleToolToggle' are deleted.

  return (
    <Card className="w-80 shadow-lg border-blue-500 border-2 relative group">
      <Button 
        onClick={() => deleteNode(id)} 
        variant="ghost" 
        size="icon" 
        className="absolute -top-3 -right-3 h-6 w-6 rounded-full bg-destructive text-destructive-foreground opacity-0 group-hover:opacity-100 transition-opacity"
      >
        <XIcon className="h-4 w-4" />
      </Button>
      
      <Handle type="target" position={Position.Top} />
      
      <CardHeader className="bg-muted p-3">
        <CardTitle className="text-md">
          <Input 
            value={name}
            onChange={(e) => handleInputChange('name', e.target.value)}
            placeholder="Agent Name"
            className="text-md font-bold border-none !ring-0 !shadow-none p-0 h-auto"
          />
        </CardTitle>
      </CardHeader>
      
      <CardContent className="p-3 grid gap-2 text-sm">
        <div className="grid grid-cols-2 gap-2">
          <div>
            <Label>Role</Label>
            <Select value={role} onValueChange={(value: AgentRole) => handleInputChange('role', value)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {Object.values(AgentRole).map(r => <SelectItem key={r} value={r}>{r}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Provider</Label>
            <Select value={provider} onValueChange={(value: AgentProvider) => handleInputChange('provider', value)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {Object.values(AgentProvider).map(p => <SelectItem key={p} value={p}>{p}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
        </div>
        <div>
          <Label>Model</Label>
          <Input 
            value={model}
            onChange={(e) => handleInputChange('model', e.target.value)}
            placeholder="e.g., gpt-4o"
          />
        </div>
        <div>
          <Label>System Prompt</Label>
          <Textarea 
            value={system_instruction_prompt}
            onChange={(e) => handleInputChange('system_instruction_prompt', e.target.value)}
            placeholder="You are a helpful assistant..."
            rows={4}
          />
        </div>
        
        {/* 4. The entire 'div' for the Tools Popover has been deleted. */}
        
      </CardContent>
      
      <Handle type="source" position={Position.Bottom} />
    </Card>
  );
});

AgentNode.displayName = 'AgentNode';

export default AgentNode;