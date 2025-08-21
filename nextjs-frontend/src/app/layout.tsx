import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import {Navbar} from "../components/navbar"
import { AuthProvider } from '@/context/auth-context';

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Ensemble",
  description: "Generated Ensemble",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased mx-auto max-w-7xl px-4 sm:px-6 lg:px-8`}
      >
        <AuthProvider>
        {/* NAVBAR */}
        <Navbar />

        {children}

        {/* FOOTER */}

        </AuthProvider>
      </body>
    </html>
  );
}
