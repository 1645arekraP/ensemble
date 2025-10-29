"use client"

import { memo, useMemo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command';
import { XIcon, CheckIcon, ChevronsUpDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import { AgentNodeData, AgentRole, AgentProvider } from '../lib/types';

const AgentNode = memo(({ id, data }: NodeProps<AgentNodeData>) => {
  const { name, role, provider, model, system_instruction_prompt, tools, updateNodeData, deleteNode, allNodes } = data;

  const handleInputChange = (field: keyof Omit<AgentNodeData, 'tools' | 'allNodes' | 'updateNodeData' | 'deleteNode'>, value: string) => {
    updateNodeData(id, { [field]: value });
  };
  
  const availableTools = useMemo(() => 
    allNodes.filter(node => node.type === 'tool').map(node => ({
      value: node.id,
      label: node.data.name,
    })),
    [allNodes]
  );
  
  const handleToolToggle = (toolId: string) => {
    const newTools = tools.includes(toolId)
      ? tools.filter(t => t !== toolId)
      : [...tools, toolId];
    updateNodeData(id, { tools: newTools });
  };

  return (
    <Card className="w-80 shadow-lg border-blue-500 border-2 relative group">
      <Button onClick={() => deleteNode(id)} variant="ghost" size="icon" className="absolute -top-3 -right-3 h-6 w-6 rounded-full bg-destructive text-destructive-foreground opacity-0 group-hover:opacity-100 transition-opacity">
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
        <div>
          <Label>Tools</Label>
            <Popover>
                <PopoverTrigger asChild>
                    <Button variant="outline" role="combobox" className="w-full justify-between">
                        <span className="truncate">
                            {tools.length > 0 ? `${tools.length} selected` : 'Select tools...'}
                        </span>
                        <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                    </Button>
                </PopoverTrigger>
                <PopoverContent className="w-[--radix-popover-trigger-width] p-0">
                    <Command>
                        <CommandInput placeholder="Search tools..." />
                        <CommandList>
                            <CommandEmpty>No tools found.</CommandEmpty>
                            <CommandGroup>
                                {availableTools.map((tool) => (
                                    <CommandItem
                                        key={tool.value}
                                        onSelect={() => handleToolToggle(tool.value)}
                                    >
                                        <CheckIcon
                                            className={cn(
                                                "mr-2 h-4 w-4",
                                                tools.includes(tool.value) ? "opacity-100" : "opacity-0"
                                            )}
                                        />
                                        {tool.label}
                                    </CommandItem>
                                ))}
                            </CommandGroup>
                        </CommandList>
                    </Command>
                </PopoverContent>
            </Popover>
        </div>
      </CardContent>
      <Handle type="source" position={Position.Bottom} />
    </Card>
  );
});
AgentNode.displayName = 'AgentNode';
export default AgentNode;