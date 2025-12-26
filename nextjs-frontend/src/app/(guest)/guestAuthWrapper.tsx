// components/GuestAuthWrapper.tsx

"use client";

import React, { useEffect } from 'react';
import { useAuth } from '@/context/auth-context';
import { useRouter } from 'next/navigation';


export default function GuestAuthWrapper({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // If loading is finished and a user exists, redirect to the dashboard.
    if (!isLoading && user) {
      router.replace('/dashboard');
    }
  }, [isLoading, user, router]);

  // While checking, you can show a loading state.
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        Loading
      </div>
    );
  }

  // If there's no user, render the children (the guest page).
  if (!user) {
    return <>{children}</>;
  }

  // Return null while redirecting.
  return null;
}