"use client";
import React, { createContext, useContext, useState } from 'react';

// This context acts as the "memory" for who is logged in
const AuthContext = createContext<any>(null);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<string | null>(null);

  // When a user logs in, we save their name here
  const login = (username: string) => setUser(username);
  
  // When they logout, we clear it
  const logout = () => setUser(null);

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// This is a custom hook so other files can easily ask "Is anyone logged in?"
export const useAuth = () => useContext(AuthContext);