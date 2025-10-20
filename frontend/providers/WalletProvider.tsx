'use client';

/**
 * Wallet Provider.
 * Manages Solana wallet connection state.
 */

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { container } from '@/lib/infrastructure/di/container';
import type { SolanaWalletAdapter } from '@/lib/infrastructure/wallet/solana-wallet-provider';
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
  adapter?: SolanaWalletAdapter;
}

export function WalletProvider({ children, adapter }: WalletProviderProps) {
  const [address, setAddress] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const walletProvider = container.walletProvider;

  useEffect(() => {
    if (adapter) {
      walletProvider.setWallet(adapter);
      
      if (adapter.connected && adapter.publicKey) {
        setAddress(adapter.publicKey.toString());
      }
    }
  }, [adapter, walletProvider]);

  const connect = useCallback(async () => {
    setIsConnecting(true);
    setError(null);

    try {
      const connectedAddress = await walletProvider.connect();
      setAddress(connectedAddress);
    } catch (err) {
      const errorMessage =
        err instanceof WalletConnectionError
          ? err.message
          : 'Failed to connect wallet';
      setError(errorMessage);
      throw err;
    } finally {
      setIsConnecting(false);
    }
  }, [walletProvider]);

  const disconnect = useCallback(async () => {
    try {
      await walletProvider.disconnect();
      setAddress(null);
      setError(null);
    } catch (err) {
      console.error('Disconnect error:', err);
    }
  }, [walletProvider]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return (
    <WalletContext.Provider
      value={{
        address,
        isConnected: address !== null,
        isConnecting,
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
