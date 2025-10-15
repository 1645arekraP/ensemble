//app/providers.tsx
"use client";

import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@/context/auth-context";
import { AuthError } from "@/lib/apiClient";

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Set a global retry function
      retry: (failureCount, error) => {
        // If the error is our custom AuthError, do not retry
        if (error instanceof AuthError) {
          return false;
        }
        // Otherwise, retry up to 2 times (for a total of 3 attempts)
        return failureCount < 2;
      },
      // global staleTime
      staleTime: 1000 * 60 * 5, // 5 minutes
    },
  },
});

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  );
}