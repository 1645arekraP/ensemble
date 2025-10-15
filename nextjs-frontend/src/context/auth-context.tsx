// context/AuthContext.tsx
"use client";

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchCurrentUser, loginUser as apiLogin } from '@/lib/api';
import { User } from '@/lib/interfaces'
import { setAccessToken, logout as apiLogout, initializeAuth } from '@/lib/apiClient';

interface AuthContextType {
  user: User | null | undefined;
  login: (user: User, accessToken: string) => void;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const queryClient = useQueryClient();
  const [isInitialized, setIsInitialized] = useState(false);

  const { data: user, isLoading, isError } = useQuery({
    queryKey: ['currentUser'],
    queryFn: fetchCurrentUser, 
    retry: false,
    staleTime: Infinity, 
    refetchOnWindowFocus: false, 
  });

  const login = (userData: User, token: string) => {
    setAccessToken(token);
    queryClient.setQueryData(['currentUser'], userData);
  };

  const logout = async () => {
    await apiLogout(); 
    queryClient.setQueryData(['currentUser'], null);
    console.log("User cleared")
  };

  const value = {
    user: isError ? null : user,
    login,
    logout,
    isLoading,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
};