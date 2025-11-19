"use client"

import { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { XIcon } from 'lucide-react';
import { ToolNodeData, ToolType } from '../lib/types';

const ToolNode = memo(({ id, data }: NodeProps<ToolNodeData>) => {
  const { name, description, tool_type, updateNodeData, deleteNode } = data;
  
  return (
    <Card className="w-72 shadow-lg border-green-500 border-2 relative group">
      <Button onClick={() => deleteNode(id)} variant="ghost" size="icon" className="absolute -top-3 -right-3 h-6 w-6 rounded-full bg-destructive text-destructive-foreground opacity-0 group-hover:opacity-100 transition-opacity">
        <XIcon className="h-4 w-4" />
      </Button>
      <Handle type="target" position={Position.Top} />
      <CardHeader className="bg-muted p-3">
        <CardTitle className="text-md">
          <Input 
            value={name}
            onChange={(e) => updateNodeData(id, { name: e.target.value })}
            placeholder="Tool Name"
            className="text-md font-bold border-none !ring-0 !shadow-none p-0 h-auto"
          />
        </CardTitle>
      </CardHeader>
      <CardContent className="p-3 grid gap-2 text-sm">
        <div>
            <Label>Tool Type</Label>
            <Select value={tool_type} onValueChange={(value: ToolType) => updateNodeData(id, { tool_type: value })}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {Object.values(ToolType).map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}
              </SelectContent>
            </Select>
        </div>
        <div>
          <Label>Description</Label>
          <Textarea 
            value={description}
            onChange={(e) => updateNodeData(id, { description: e.target.value })}
            placeholder="Describes what this tool does..."
            rows={3}
          />
        </div>
      </CardContent>
      <Handle type="source" position={Position.Bottom} />
    </Card>
  );
});
ToolNode.displayName = 'ToolNode';
export default ToolNode;