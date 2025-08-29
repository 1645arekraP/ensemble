// This file will hold shared type definitions for your application.

export type User = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
};

export type Project = {
  id: string; // The ID is a string (UUID)
  name: string;
  description: string | null; // Description can be null
  graph_data: any; // Use 'any' or a more specific object type
  created_at: string; // ISO date string
  owner: User;
};