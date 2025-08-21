"use client";

import { Button } from "./ui/button";
import Link from "next/link";
import { useAuth } from "@/context/auth-context"; // Import the custom hook

export function Navbar() {
  const { isLoggedIn, logout } = useAuth(); // Use the hook to get the state and functions

  return (
    <div className="grid grid-cols-3 sticky top-0">
      <div></div>
      <div className="flex itemscenter justify-self-center">
        <Button asChild variant="ghost">
          <Link href="/home">Home</Link>
        </Button>

        {isLoggedIn && (
          <Button asChild variant="ghost">
            <Link href="/dashboard">Dashboard</Link>
          </Button>
        )}

        <Button asChild variant="ghost">
          <Link href="/aboutus">About Us</Link>
        </Button>
      </div>
      <div className="flex itemscenter justify-self-end">
        {!isLoggedIn ? (
          <>
            <Button asChild variant="ghost">
              <Link href="/login">Login</Link>
            </Button>
            <Button asChild variant="ghost">
              <Link href="/register">Register</Link>
            </Button>
          </>
        ) : (
          <Button variant="ghost" onClick={logout}>
            Logout
          </Button>
        )}
      </div>
    </div>
  );
}