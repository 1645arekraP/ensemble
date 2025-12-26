// components/AddCredentialDialog.tsx

"use client"

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
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
import { getTools } from '@/lib/api'; // We use getTools to get tool names
import { NewCredentialPayload, ApiTool } from '@/lib/types';
import LoadingSpinner from './LoadingSpinner';

interface AddCredentialDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (formData: NewCredentialPayload) => void;
  isPending: boolean;
  defaultCredentialType?: string; // This is the new prop
}

export const AddCredentialDialog = ({
  isOpen,
  onOpenChange,
  onSubmit,
  isPending,
  defaultCredentialType
}: AddCredentialDialogProps) => {
  const [credentialType, setCredentialType] = useState('');
  const [accessToken, setAccessToken] = useState('');
  const [toolName, setToolName] = useState('this connection'); // For the dialog title

  // Fetch tools to get the human-readable names
  const { data: tools, isLoading: isLoadingTools } = useQuery({
    queryKey: ['tools'],
    queryFn: getTools,
  });

  // This effect pre-fills the form when the dialog opens
  // with a defaultCredentialType
  useEffect(() => {
    if (isOpen && defaultCredentialType) {
      setCredentialType(defaultCredentialType);
      
      // Find the tool's display name
      const tool = tools?.find(t => t.tool_type === defaultCredentialType);
      setToolName(tool ? tool.tool_type_display : 'this connection');
    }
  }, [isOpen, defaultCredentialType, tools]);

  const resetForm = () => {
    setCredentialType('');
    setAccessToken('');
    setToolName('this connection');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!credentialType) return; // Should be blocked by UI
    
    onSubmit({
      credential_type: credentialType,
      access_token: accessToken,
    });
  };

  const handleClose = (open: boolean) => {
    onOpenChange(open);
    if (!open) {
      setTimeout(resetForm, 300);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Add API Key for {toolName}</DialogTitle>
          <DialogDescription>
            Securely save your API key. It will be encrypted and never shown again.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="credential-type" className="text-right">
              Type
            </Label>
            {/* The Select is now disabled, as it's pre-selected */}
            <Select
              value={credentialType}
              onValueChange={setCredentialType}
              disabled={true} // Always disable, as it's set by the button
            >
              <SelectTrigger className="col-span-3">
                <SelectValue placeholder="Select a credential type..." />
              </SelectTrigger>
              <SelectContent>
                {isLoadingTools && <div className="p-4">Loading...</div>}
                {tools?.map((tool) => (
                  <SelectItem key={tool.tool_type} value={tool.tool_type}>
                    {tool.tool_type_display}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="access-token" className="text-right">
              API Key
            </Label>
            <Input
              id="access-token"
              value={accessToken}
              onChange={(e) => setAccessToken(e.target.value)}
              className="col-span-3"
              type="password"
              placeholder="Your secret key (e.g., tvly-...)"
            />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => handleClose(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isPending || !credentialType || !accessToken}>
              {isPending ? <LoadingSpinner /> : 'Save Connection'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};