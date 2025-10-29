"use client"

import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from "@/components/ui/button";
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from "@/components/ui/textarea";
import { ToolType, AddToolFormState } from '../lib/types';

interface AddToolNodeDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (formData: AddToolFormState) => void;
}

const defaultState: AddToolFormState = {
  name: 'New Tool',
  description: 'A tool for performing a specific action.',
  tool_type: ToolType.CUSTOM,
};

export const AddToolNodeDialog = ({ isOpen, onOpenChange, onSubmit }: AddToolNodeDialogProps) => {
  const [formState, setFormState] = useState(defaultState);

  const handleChange = (field: keyof AddToolFormState, value: string) => {
    setFormState(prev => ({ ...prev, [field]: value as any }));
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
          <DialogTitle>Add New Tool Node</DialogTitle>
          <DialogDescription>
            Configure the details for your new tool. It will be added to the canvas.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="tool-name" className="text-right">Name</Label>
              <Input id="tool-name" value={formState.name} onChange={(e) => handleChange('name', e.target.value)} className="col-span-3" />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="tool-description" className="text-right">Description</Label>
              <Textarea id="tool-description" value={formState.description} onChange={(e) => handleChange('description', e.target.value)} className="col-span-3" placeholder="Describes what this tool does..." />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="tool-type" className="text-right">Tool Type</Label>
              <Select value={formState.tool_type} onValueChange={(value: ToolType) => handleChange('tool_type', value)}>
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="Select a type" />
                </SelectTrigger>
                <SelectContent>
                  {Object.values(ToolType).map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => handleClose(false)}>Cancel</Button>
            <Button type="submit">Create Tool</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};