// components/DashboardAuthWrapper.tsx

"use client";

import React, { useEffect } from 'react';
import { useAuth } from '@/context/auth-context';
import { useRouter } from 'next/navigation';

export default function DashboardAuthWrapper({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // If loading is finished and there's still no user, redirect to login.
    if (!isLoading && !user) {
      router.replace('/login');
    }
  }, [isLoading, user, router]);

  // While the auth state is loading, show a spinner.
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        Loading
      </div>
    );
  }

  // If the user is authenticated, render the page.
  if (user) {
    return <>{children}</>;
  }

  // Return null while redirecting to prevent flashing of content.
  return null;
}