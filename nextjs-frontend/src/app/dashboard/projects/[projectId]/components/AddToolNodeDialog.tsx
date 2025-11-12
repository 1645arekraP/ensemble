"use client"

import { useState } from 'react';
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '@/components/ui/dialog';
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from "@/components/ui/textarea";
import { NewToolNodePayload } from '@/lib/types'; // Make sure this type is defined

// --- Create a TypeScript enum to match your Django model ---
enum ToolType {
  WEB_SEARCH = 'web_search',
  DISCORD_WEBHOOK = 'discord_webhook',
  SLACK_WEBHOOK = 'slack_webhook',
  TEAMS_WEBHOOK = 'teams_webhook',
}

interface AddToolNodeDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  // Use the payload type for the form data
  onSubmit: (formData: NewToolNodePayload) => void; 
}

export const AddToolNodeDialog = ({ isOpen, onOpenChange, onSubmit }: AddToolNodeDialogProps) => {
  const [name, setName] = useState('New Tool');
  const [description, setDescription] = useState('A new tool for my library.');
  const [toolType, setToolType] = useState<ToolType>(ToolType.WEB_SEARCH);
  
  // --- Add state for the config ---
  // This will store the webhook URL or API key
  const [config, setConfig] = useState('');

  const resetForm = () => {
    setName('New Tool');
    setDescription('A new tool for my library.');
    setToolType(ToolType.WEB_SEARCH);
    setConfig('');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // --- Build the config JSON based on the tool type ---
    let toolConfig = {};
    if (toolType === ToolType.WEB_SEARCH) {
      toolConfig = { "placeholder": "API key will be pulled from credentials" };
    } else if (
      toolType === ToolType.DISCORD_WEBHOOK ||
      toolType === ToolType.SLACK_WEBHOOK ||
      toolType === ToolType.TEAMS_WEBHOOK
    ) {
      toolConfig = { "webhook_url": config };
    }

    onSubmit({
      name,
      description,
      tool_type: toolType,
      config: toolConfig,
    });
    
    onOpenChange(false);
    resetForm();
  };

  const handleClose = (open: boolean) => {
    onOpenChange(open);
    if (!open) {
      resetForm();
    }
  };
  
  // Helper to determine what label to show for the config input
  const getConfigLabel = () => {
    switch(toolType) {
      case ToolType.DISCORD_WEBHOOK:
      case ToolType.SLACK_WEBHOOK:
      case ToolType.TEAMS_WEBHOOK:
        return 'Webhook URL';
      case ToolType.WEB_SEARCH:
        return 'API Key (Handled by Credentials)';
      default:
        return 'Configuration';
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Add New Tool</DialogTitle>
          <DialogDescription>
            Add a new tool to your personal library. It will then be available in the sidebar.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="tool-name" className="text-right">Name</Label>
            <Input
              id="tool-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="col-span-3"
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="tool-description" className="text-right">Description</Label>
            <Textarea
              id="tool-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="col-span-3"
              placeholder="Describes what this tool does..."
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="tool-type" className="text-right">Tool Type</Label>
            <Select value={toolType} onValueChange={(value: ToolType) => setToolType(value)}>
              <SelectTrigger className="col-span-3">
                <SelectValue placeholder="Select a type" />
              </SelectTrigger>
              <SelectContent>
                {/* --- 4. Map over the new enum --- */}
                <SelectItem value={ToolType.WEB_SEARCH}>Web Search</SelectItem>
                <SelectItem value={ToolType.DISCORD_WEBHOOK}>Discord Webhook</SelectItem>
                <SelectItem value={ToolType.SLACK_WEBHOOK}>Slack Webhook</SelectItem>
                <SelectItem value={ToolType.TEAMS_WEBHOOK}>Microsoft Teams Webhook</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          {/* --- Add a conditional input for the config --- */}
          {toolType !== ToolType.WEB_SEARCH && (
             <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="tool-config" className="text-right">
                {getConfigLabel()}
              </Label>
              <Input
                id="tool-config"
                value={config}
                onChange={(e) => setConfig(e.target.value)}
                className="col-span-3"
                type="password"
                placeholder="Enter your secret URL or key"
              />
            </div>
          )}
          {toolType === ToolType.WEB_SEARCH && (
            <p className="text-xs text-muted-foreground col-span-4 text-center">
              Web Search API keys are managed on the 'Connections' page.
            </p>
          )}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => handleClose(false)}>
              Cancel
            </Button>
            <Button type="submit">Create Tool</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};