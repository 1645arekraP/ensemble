// components/AddDatabaseDialog.tsx

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
import { NewCredentialPayload } from '@/lib/types';
import LoadingSpinner from './LoadingSpinner';

interface AddDatabaseDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (formData: NewCredentialPayload) => void;
  isPending: boolean;
}

export const AddDatabaseDialog = ({
  isOpen,
  onOpenChange,
  onSubmit,
  isPending,
}: AddDatabaseDialogProps) => {
  const [host, setHost] = useState('');
  const [port, setPort] = useState('5432');
  const [database, setDatabase] = useState('');
  const [user, setUser] = useState('');
  const [password, setPassword] = useState('');

  const resetForm = () => {
    setHost('');
    setPort('5432');
    setDatabase('');
    setUser('');
    setPassword('');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Package all connection details as JSON
    const connectionInfo = JSON.stringify({
      host,
      port: parseInt(port),
      database,
      user,
      password,
    });

    onSubmit({
      credential_type: 'postgres',
      access_token: connectionInfo,
    });
  };

  const handleClose = (open: boolean) => {
    onOpenChange(open);
    if (!open) {
      setTimeout(resetForm, 300);
    }
  };

  const isFormValid = host && port && database && user && password;

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Add PostgreSQL Database</DialogTitle>
          <DialogDescription>
            Enter your PostgreSQL connection details. All information will be encrypted.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="host" className="text-right">
              Host
            </Label>
            <Input
              id="host"
              value={host}
              onChange={(e) => setHost(e.target.value)}
              className="col-span-3"
              placeholder="localhost or db.example.com"
              required
            />
          </div>

          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="port" className="text-right">
              Port
            </Label>
            <Input
              id="port"
              type="number"
              value={port}
              onChange={(e) => setPort(e.target.value)}
              className="col-span-3"
              placeholder="5432"
              required
            />
          </div>

          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="database" className="text-right">
              Database
            </Label>
            <Input
              id="database"
              value={database}
              onChange={(e) => setDatabase(e.target.value)}
              className="col-span-3"
              placeholder="mydb"
              required
            />
          </div>

          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="user" className="text-right">
              User
            </Label>
            <Input
              id="user"
              value={user}
              onChange={(e) => setUser(e.target.value)}
              className="col-span-3"
              placeholder="postgres"
              required
            />
          </div>

          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="password" className="text-right">
              Password
            </Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="col-span-3"
              placeholder="Your database password"
              required
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => handleClose(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isPending || !isFormValid}>
              {isPending ? <LoadingSpinner /> : 'Save Connection'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
