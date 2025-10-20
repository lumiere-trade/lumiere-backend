'use client';

/**
 * Wallet Provider.
 * Bridges Solana Wallet Adapter with our Clean Architecture.
 */

import React, { createContext, useContext, useCallback, useEffect, useState } from 'react';
import { useWallet as useSolanaWallet } from '@solana/wallet-adapter-react';
import { container } from '@/lib/infrastructure/di/container';
import {
  WalletNotConnectedError,
  WalletConnectionError,
} from '@/lib/domain/errors/wallet.errors';

interface WalletContextType {
  address: string | null;
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  connect: () => Promise<void>;
  disconnect: () => Promise<void>;
  clearError: () => void;
}

const WalletContext = createContext<WalletContextType | undefined>(undefined);

interface WalletProviderProps {
  children: React.ReactNode;
}

export function WalletProvider({ children }: WalletProviderProps) {
  const solanaWallet = useSolanaWallet();
  const [error, setError] = useState<string | null>(null);

  const walletProvider = container.walletProvider;

  // Sync Solana wallet with our adapter
  useEffect(() => {
    if (solanaWallet.wallet?.adapter) {
      walletProvider.setWallet(solanaWallet.wallet.adapter as any);
    }
  }, [solanaWallet.wallet, walletProvider]);

  const connect = useCallback(async () => {
    setError(null);

    try {
      // Wallet should already be selected by page.tsx
      // Solana adapter will handle the connection
      // We just expose the state here
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to connect wallet';
      setError(errorMessage);
      throw err;
    }
  }, []);

  const disconnect = useCallback(async () => {
    try {
      await solanaWallet.disconnect();
      setError(null);
    } catch (err) {
      console.error('Disconnect error:', err);
    }
  }, [solanaWallet]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return (
    <WalletContext.Provider
      value={{
        address: solanaWallet.publicKey?.toString() ?? null,
        isConnected: solanaWallet.connected,
        isConnecting: solanaWallet.connecting,
        error,
        connect,
        disconnect,
        clearError,
      }}
    >
      {children}
    </WalletContext.Provider>
  );
}

export function useWallet() {
  const context = useContext(WalletContext);
  if (context === undefined) {
    throw new Error('useWallet must be used within WalletProvider');
  }
  return context;
}
