"use client"

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { SiteHeader } from "@/components/site-header";
import { AddCredentialDialog } from '@/components/AddCredentialDialog'; // Adjust path as needed
import { AddDatabaseDialog } from '@/components/AddDatabaseDialog';
import { 
  getCredentials, 
  createCredential, 
  deleteCredential,
  getGoogleConnectUrl 
} from '@/lib/api';
import { UserCredential, NewCredentialPayload } from '@/lib/types';
import LoadingSpinner from '@/components/LoadingSpinner';
import { Plus, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

// Define the services your platform can connect to
const SERVICE_CONNECTIONS = [
  {
    name: "Tavily Web Search",
    type: "api_key",
    credential_type: "web_search",
  },
  {
    name: "Google (Gmail, etc.)",
    type: "oauth",
    connect_url: "/api/auth/google/connect/",
  },
  {
    name: "PostgreSQL Database",
    type: "database",
    credential_type: "postgres",
  },
];

export default function ConnectionsPage() {
  const queryClient = useQueryClient();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isDatabaseDialogOpen, setIsDatabaseDialogOpen] = useState(false);
  const [selectedCredentialType, setSelectedCredentialType] = useState<string | undefined>();

  // Query to fetch all *existing* credentials
  const { data: credentials, isLoading, error } = useQuery<UserCredential[], Error>({
    queryKey: ['credentials'],
    queryFn: getCredentials,
  });

  // Mutation to create a new credential (for API keys)
  const { mutate: createCredMutate, isPending: isCreating } = useMutation({
    mutationFn: createCredential,
    onSuccess: () => {
      toast.success("Connection saved!");
      queryClient.invalidateQueries({ queryKey: ['credentials'] });
      setIsDialogOpen(false); // Close the dialog
    },
    onError: (err: Error) => {
      toast.error("Failed to save:", { description: err.message });
    },
  });

  // Mutation to delete a credential
  const { mutate: deleteCredMutate } = useMutation({
    mutationFn: deleteCredential,
    onSuccess: () => {
      toast.success("Connection deleted.");
      queryClient.invalidateQueries({ queryKey: ['credentials'] });
    },
    onError: (err: Error) => {
      toast.error("Failed to delete:", { description: err.message });
    },
  });

  // Mutation to handle Google OAuth connection
  const { mutate: connectGoogle, isPending: isConnecting } = useMutation({
    mutationFn: getGoogleConnectUrl,
    onSuccess: (data) => {
      // Once we get the URL, manually navigate the browser to Google
      window.location.href = data.authorization_url;
    },
    onError: (err: Error) => {
      toast.error("Failed to connect:", { description: err.message });
    },
  });

  // Handler for the dialog form submission
  const handleCreateSubmit = (formData: NewCredentialPayload) => {
    createCredMutate(formData);
  };

  // Handler for the "Add API Key" button
  const handleOpenApiKeyDialog = (credentialType: string) => {
    setSelectedCredentialType(credentialType);
    setIsDialogOpen(true);
  };

  // Handler for the "Add Database" button
  const handleOpenDatabaseDialog = () => {
    setIsDatabaseDialogOpen(true);
  };
  
  // Handler for the delete button
  const handleDeleteClick = (id: number) => {
    if (window.confirm("Are you sure you want to delete this connection?")) {
      deleteCredMutate(id);
    }
  };

  return (
    <>
      <SiteHeader name="My Connections" />

      {/* Render the dialog, passing the selected type */}
      <AddCredentialDialog
        isOpen={isDialogOpen}
        onOpenChange={setIsDialogOpen}
        onSubmit={handleCreateSubmit}
        isPending={isCreating}
        defaultCredentialType={selectedCredentialType}
      />

      {/* Database connection dialog */}
      <AddDatabaseDialog
        isOpen={isDatabaseDialogOpen}
        onOpenChange={setIsDatabaseDialogOpen}
        onSubmit={handleCreateSubmit}
        isPending={isCreating}
      />
      
      <main className="container max-w-5xl mx-auto p-4 md:p-8">
        <h1 className="text-2xl font-bold mb-6">Manage Connections</h1>

        {/* --- List of *available* services to connect --- */}
        <h2 className="text-lg font-semibold mb-4">Available Connections</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          {SERVICE_CONNECTIONS.map((service) => (
            <Card key={service.name}>
              <CardHeader>
                <CardTitle>{service.name}</CardTitle>
              </CardHeader>
              <CardContent>
                {service.type === 'oauth' ? (
                  // OAUTH: Button triggers the connectGoogle mutation
                  <Button
                    className="w-full"
                    onClick={() => connectGoogle()}
                    disabled={isConnecting}
                  >
                    {isConnecting ? "Connecting..." : "Connect"}
                  </Button>
                ) : service.type === 'database' ? (
                  // DATABASE: Button opens the database dialog
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => handleOpenDatabaseDialog()}
                  >
                    Add Database
                  </Button>
                ) : (
                  // API KEY: Button opens the dialog
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => handleOpenApiKeyDialog(service.credential_type)}
                  >
                    Add API Key
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        {/* --- List of *active* user connections --- */}
        <h2 className="text-lg font-semibold mb-4">Your Active Connections</h2>
        {isLoading && (
          <div className="flex justify-center p-12">
            <LoadingSpinner />
          </div>
        )}
        
        {error && (
          <div className="p-8 text-red-500 bg-red-50 rounded-md">
            <strong>Error:</strong> {error.message}
          </div>
        )}

        {credentials && credentials.length === 0 && (
          <div className="text-center p-12 bg-muted/50 rounded-md">
            <p className="text-muted-foreground">You haven't added any connections yet.</p>
          </div>
        )}

        {credentials && credentials.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {credentials.map((cred) => (
              <Card key={cred.id}>
                <CardHeader className="flex flex-row justify-between items-start">
                  <div>
                    <CardTitle>{cred.credential_type_display}</CardTitle>
                    <CardDescription>
                      Added on {new Date(cred.created_at).toLocaleDateString()}
                    </CardDescription>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDeleteClick(cred.id)}
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    {cred.expires_at ? `Expires: ${new Date(cred.expires_at).toLocaleDateString()}` : "Does not expire"}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>
    </>
  );
}