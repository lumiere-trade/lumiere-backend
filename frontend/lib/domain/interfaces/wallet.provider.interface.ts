/**
 * Wallet Provider Interface (Port).
 * Abstracts Solana wallet operations.
 */

export interface SignatureResult {
  address: string;
  signature: string;
}

export interface IWalletProvider {
  connect(): Promise<string>;
  disconnect(): Promise<void>;
  signMessage(message: string): Promise<SignatureResult>;
  isConnected(): boolean;
  getAddress(): string | null;
}
