'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

interface AdminAuthContextType {
  isAdminAuthenticated: boolean;
  adminLogin: (username: string, password: string) => boolean;
  adminLogout: () => void;
}

const AdminAuthContext = createContext<AdminAuthContextType | undefined>(undefined);

const ADMIN_AUTH_KEY = 'lumiere_admin_auth';
const ADMIN_AUTH_TOKEN = 'lumiere_admin_token_2024';

export function AdminAuthProvider({ children }: { children: React.ReactNode }) {
  const [isAdminAuthenticated, setIsAdminAuthenticated] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(ADMIN_AUTH_KEY);
    if (stored === ADMIN_AUTH_TOKEN) {
      setIsAdminAuthenticated(true);
    }
  }, []);

  const adminLogin = (username: string, password: string): boolean => {
    const validUsername = process.env.NEXT_PUBLIC_ADMIN_USERNAME;
    const validPassword = process.env.NEXT_PUBLIC_ADMIN_PASSWORD;
    
    if (username === validUsername && password === validPassword) {
      localStorage.setItem(ADMIN_AUTH_KEY, ADMIN_AUTH_TOKEN);
      setIsAdminAuthenticated(true);
      return true;
    }
    return false;
  };

  const adminLogout = () => {
    localStorage.removeItem(ADMIN_AUTH_KEY);
    setIsAdminAuthenticated(false);
  };

  return (
    <AdminAuthContext.Provider value={{ isAdminAuthenticated, adminLogin, adminLogout }}>
      {children}
    </AdminAuthContext.Provider>
  );
}

export function useAdminAuth() {
  const context = useContext(AdminAuthContext);
  if (context === undefined) {
    throw new Error('useAdminAuth must be used within AdminAuthProvider');
  }
  return context;
}
