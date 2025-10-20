'use client';

import { AuthProvider } from '@/providers/AuthProvider';
import { WalletProvider } from '@/providers/WalletProvider';
import { ConnectionProvider, WalletProvider as SolanaWalletProvider } from '@solana/wallet-adapter-react';
import { PhantomWalletAdapter, SolflareWalletAdapter } from '@solana/wallet-adapter-wallets';
import { clusterApiUrl } from '@solana/web3.js';
import { useMemo } from 'react';

export function Providers({ children }: { children: React.ReactNode }) {
  // Get RPC URL from env or use devnet
  const endpoint = useMemo(() => {
    return process.env.NEXT_PUBLIC_SOLANA_RPC_URL || clusterApiUrl('devnet');
  }, []);

  // Configure wallets (only Phantom and Solflare for now)
  const wallets = useMemo(
    () => [
      new PhantomWalletAdapter(),
      new SolflareWalletAdapter(),
    ],
    []
  );

  return (
    <ConnectionProvider endpoint={endpoint}>
      <SolanaWalletProvider wallets={wallets} autoConnect={false}>
        <WalletProvider>
          <AuthProvider>
            {children}
          </AuthProvider>
        </WalletProvider>
      </SolanaWalletProvider>
    </ConnectionProvider>
  );
}
