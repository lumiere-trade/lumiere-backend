'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAdminAuth } from '@/contexts/AdminAuthContext';
import { Lock, AlertCircle } from 'lucide-react';

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
        <div className="rounded-2xl border-2 border-primary/30 bg-background/95 shadow-2xl backdrop-blur-sm p-8">
          <div className="mb-8 text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/20">
              <Lock className="h-8 w-8 text-primary" />
            </div>
            <h1 className="text-3xl font-bold text-primary">LUMIERE</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Site under development
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Input
                type="text"
                placeholder="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="rounded-full border-primary/30 bg-card"
                disabled={isLoading}
                autoComplete="username"
              />
            </div>

            <div>
              <Input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="rounded-full border-primary/30 bg-card"
                disabled={isLoading}
                autoComplete="current-password"
              />
            </div>

            {error && (
              <div className="flex items-center gap-2 rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-500">
                <AlertCircle className="h-4 w-4" />
                <span>{error}</span>
              </div>
            )}

            <Button
              type="submit"
              className="w-full rounded-full py-6 text-lg font-bold"
              disabled={isLoading || !username || !password}
            >
              {isLoading ? 'Authenticating...' : 'Enter'}
            </Button>
          </form>

          <p className="mt-6 text-center text-xs text-muted-foreground">
            Access restricted to authorized personnel
          </p>
        </div>
      </div>
    </div>
  );
}
