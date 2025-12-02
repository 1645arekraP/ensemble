// components/AddToolNodeDialog.tsx

"use client"

import { useState, useEffect } from 'react';
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
import { NewToolNodePayload, AddToolFormState } from '@/lib/types';
import LoadingSpinner from '@/components/LoadingSpinner';

// This enum must match your backend 'ToolType' in models.py
enum ToolType {
  WEB_SEARCH = 'web_search',
  DISCORD_WEBHOOK = 'discord_webhook',
  SLACK_WEBHOOK = 'slack_webhook',
  TEAMS_WEBHOOK = 'teams_webhook',
  GMAIL = 'gmail',
  POSTGRES = 'postgres',
}

interface AddToolNodeDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (formData: AddToolFormState) => void;
  isPending: boolean; // We'll pass this from the parent
}

export const AddToolNodeDialog = ({
  isOpen,
  onOpenChange,
  onSubmit,
  isPending
}: AddToolNodeDialogProps) => {
  const [name, setName] = useState('New Tool');
  const [description, setDescription] = useState('A new tool for my library.');
  const [toolType, setToolType] = useState<ToolType>(ToolType.WEB_SEARCH);
  const [config, setConfig] = useState('');

  const resetForm = () => {
    setName('New Tool');
    setDescription('A new tool for my library.');
    setToolType(ToolType.WEB_SEARCH);
    setConfig('');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    let toolConfig: Record<string, any> = {};

    // Only set config for webhook tools
    if (
      toolType === ToolType.DISCORD_WEBHOOK ||
      toolType === ToolType.SLACK_WEBHOOK ||
      toolType === ToolType.TEAMS_WEBHOOK
    ) {
      toolConfig = { "webhook_url": config };
    }

    // Submit the form data
    onSubmit({
      name,
      description,
      tool_type: toolType,
      config: toolConfig,
    });
  };

  const handleClose = (open: boolean) => {
    onOpenChange(open);
    if (!open) {
      setTimeout(resetForm, 300); // Reset after closing animation
    }
  };

  const getConfigLabel = () => {
    switch (toolType) {
      case ToolType.DISCORD_WEBHOOK:
      case ToolType.SLACK_WEBHOOK:
      case ToolType.TEAMS_WEBHOOK:
        return 'Webhook URL';
      default:
        return 'Configuration';
    }
  };

  // Helper to determine if the config input should be shown
  const showConfigInput =
    toolType === ToolType.DISCORD_WEBHOOK ||
    toolType === ToolType.SLACK_WEBHOOK ||
    toolType === ToolType.TEAMS_WEBHOOK;

  // Helper to determine if auth is handled by Connections page
  const authHandledByConnections =
    toolType === ToolType.WEB_SEARCH ||
    toolType === ToolType.GMAIL ||
    toolType === ToolType.POSTGRES;

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add New Tool</DialogTitle>
          <DialogDescription>
            Add a new tool to your personal library. It will then be available in the sidebar.
          </DialogDescription>
        </DialogHeader>

        {/* --- THIS IS THE NEW, CLEANER LAYOUT --- */}
        <form onSubmit={handleSubmit} className="space-y-4 py-4">

          <div className="space-y-2">
            <Label htmlFor="tool-name">Name</Label>
            <Input
              id="tool-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., My Discord Bot"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="tool-description">Description</Label>
            <Textarea
              id="tool-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describes what this tool does..."
              rows={3}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="tool-type">Tool Type</Label>
            <Select value={toolType} onValueChange={(value: ToolType) => setToolType(value)}>
              <SelectTrigger id="tool-type">
                <SelectValue placeholder="Select a type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ToolType.WEB_SEARCH}>Web Search</SelectItem>
                <SelectItem value={ToolType.GMAIL}>Gmail</SelectItem>
                <SelectItem value={ToolType.DISCORD_WEBHOOK}>Discord Webhook</SelectItem>
                <SelectItem value={ToolType.SLACK_WEBHOOK}>Slack Webhook</SelectItem>
                <SelectItem value={ToolType.TEAMS_WEBHOOK}>Microsoft Teams Webhook</SelectItem>
                <SelectItem value={ToolType.POSTGRES}>PostgreSQL Database</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Conditional Input for Webhook URL */}
          {showConfigInput && (
            <div className="space-y-2">
              <Label htmlFor="tool-config">{getConfigLabel()}</Label>
              <Input
                id="tool-config"
                value={config}
                onChange={(e) => setConfig(e.target.value)}
                type="password"
                placeholder="Enter your secret URL"
              />
            </div>
          )}

          {/* Helper text for OAuth/Credential tools */}
          {authHandledByConnections && (
            <p className="text-xs text-muted-foreground text-center p-2">
              Authentication for this tool is managed on the 'Connections' page.
            </p>
          )}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => handleClose(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? <LoadingSpinner /> : "Create Tool"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};