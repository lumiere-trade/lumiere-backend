'use client';

/**
 * Client-side providers wrapper.
 * All providers that need 'use client' directive.
 */

import { WalletProvider } from '@/providers/WalletProvider';
import { AuthProvider } from '@/providers/AuthProvider';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <WalletProvider>
      <AuthProvider>
        {children}
      </AuthProvider>
    </WalletProvider>
  );
}
