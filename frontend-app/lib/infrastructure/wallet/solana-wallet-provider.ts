/**
 * Solana Wallet Provider Implementation (Adapter).
 * Wraps Solana wallet adapter with our IWalletProvider interface.
 */

import type {
  IWalletProvider,
  SignatureResult,
} from '@/lib/domain/interfaces/wallet.provider.interface';
import {
  WalletNotConnectedError,
  WalletSignatureError,
  WalletConnectionError,
} from '@/lib/domain/errors/wallet.errors';
import bs58 from 'bs58';

export interface SolanaWalletAdapter {
  publicKey: { toString(): string } | null;
  signMessage(message: Uint8Array): Promise<Uint8Array>;
  connected: boolean;
  connect(): Promise<void>;
  disconnect(): Promise<void>;
  name?: string;
}

export class SolanaWalletProvider implements IWalletProvider {
  constructor(private wallet: SolanaWalletAdapter | null = null) {}

  setWallet(wallet: SolanaWalletAdapter): void {
    this.wallet = wallet;
  }

  async connect(): Promise<string> {
    if (!this.wallet) {
      throw new WalletConnectionError('No wallet adapter available');
    }

    try {
      await this.wallet.connect();

      if (!this.wallet.publicKey) {
        throw new WalletConnectionError('Failed to get public key');
      }

      return this.wallet.publicKey.toString();
    } catch (error) {
      throw new WalletConnectionError(
        error instanceof Error ? error.message : 'Connection failed'
      );
    }
  }

  async disconnect(): Promise<void> {
    if (!this.wallet) return;

    try {
      await this.wallet.disconnect();
    } catch (error) {
      console.error('Disconnect error:', error);
    }
  }

  async signMessage(message: string): Promise<SignatureResult> {
    if (!this.wallet || !this.wallet.connected || !this.wallet.publicKey) {
      throw new WalletNotConnectedError();
    }

    try {
      const messageBytes = new TextEncoder().encode(message);
      const signatureBytes = await this.wallet.signMessage(messageBytes);
      const signature = bs58.encode(signatureBytes);
      const address = this.wallet.publicKey.toString();

      return { address, signature };
    } catch (error) {
      throw new WalletSignatureError(
        error instanceof Error ? error.message : 'Signature failed'
      );
    }
  }

  isConnected(): boolean {
    return this.wallet?.connected ?? false;
  }

  getAddress(): string | null {
    return this.wallet?.publicKey?.toString() ?? null;
  }

  getWalletType(): string {
    return this.wallet?.name ?? 'Unknown';
  }
}
