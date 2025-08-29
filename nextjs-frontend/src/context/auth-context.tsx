"use client";

import { createContext, useState, useEffect, useContext, ReactNode } from 'react';
import { useRouter } from 'next/navigation';

// Create the context
interface AuthContextType {
    isLoggedIn: boolean;
    isPageLoading: boolean;
    login: (accessToken: string, refreshToken: string) => void;
    logout: () => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Create the provider component
interface AuthProviderProps {
    children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [isPageLoading, setIsLoading] = useState(true);
    const router = useRouter();

    // Check for tokens on initial load
    useEffect(() => {
        try {
            const accessToken = localStorage.getItem("access_token");
            const refreshToken = localStorage.getItem("refresh_token");
            if (accessToken && refreshToken) {
                setIsLoggedIn(true);
            }
        } catch (error) {
            console.error("Could not access localStorage:", error);
            // Handle cases where localStorage is not available
            setIsLoggedIn(false);
        } finally {
            // Set loading to false after the check is complete
            setIsLoading(false);
        }
        
    }, []);

    // Define login/logout functions
    const login = (accessToken: string, refreshToken: string) => {
        localStorage.setItem("access_token", accessToken);
        localStorage.setItem("refresh_token", refreshToken);
        setIsLoggedIn(true);
        router.push('/dashboard')
    };

    const logout = () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        setIsLoggedIn(false);
        router.push('/login')
    };

    return (
        <AuthContext.Provider value={{ isLoggedIn, isPageLoading, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

//  Create a custom hook for easy access
export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
};