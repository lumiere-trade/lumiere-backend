'use client';

import { useState } from 'react';
import { useAdminAuth } from '@/src/contexts/AdminAuthContext';

export function AdminLoginWall({ children }: { children: React.ReactNode }) {
  const { isAdminAuthenticated, adminLogin } = useAdminAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    await new Promise(resolve => setTimeout(resolve, 500));

    const success = adminLogin(username, password);
    
    if (!success) {
      setError('Invalid credentials');
      setPassword('');
    }
    
    setIsLoading(false);
  };

  if (isAdminAuthenticated) {
    return <>{children}</>;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md">
      <div className="w-full max-w-md mx-4">
        <div className="rounded-2xl border-2 border-[#d4a574]/30 bg-[#1a1410]/95 shadow-2xl backdrop-blur-sm p-8">
          <div className="mb-8 text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-[#d4a574]/20">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-[#d4a574]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h1 className="text-3xl font-bold text-[#d4a574]">LUMIERE</h1>
            <p className="mt-2 text-sm text-[#a0826d]">Site under development</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full rounded-full border border-[#d4a574]/30 bg-[#2a2420] px-4 py-3 text-white placeholder-[#a0826d] focus:border-[#d4a574] focus:outline-none"
              disabled={isLoading}
              autoComplete="username"
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-full border border-[#d4a574]/30 bg-[#2a2420] px-4 py-3 text-white placeholder-[#a0826d] focus:border-[#d4a574] focus:outline-none"
              disabled={isLoading}
              autoComplete="current-password"
            />
            {error && (
              <div className="flex items-center gap-2 rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-500">
                <span>{error}</span>
              </div>
            )}
            <button
              type="submit"
              className="w-full rounded-full bg-[#d4a574] py-3 text-lg font-bold text-black hover:bg-[#c49564] disabled:opacity-50 transition-colors"
              disabled={isLoading || !username || !password}
            >
              {isLoading ? 'Authenticating...' : 'Enter'}
            </button>
          </form>
          <p className="mt-6 text-center text-xs text-[#a0826d]">
            Access restricted to authorized personnel
          </p>
        </div>
      </div>
    </div>
  );
}
