import { AuthProvider } from "@/context/AuthContext";
import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "SaaS Support Copilot",
  description: "AI-powered support assistant",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">
        {/* Wrap children with AuthProvider to share user state globally */}
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}