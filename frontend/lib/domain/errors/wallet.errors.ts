/**
 * Wallet domain errors.
 */

export class WalletError extends Error {
  constructor(message: string, public readonly code?: string) {
    super(message);
    this.name = 'WalletError';
  }
}

export class WalletNotConnectedError extends WalletError {
  constructor(message = 'Wallet not connected') {
    super(message, 'WALLET_NOT_CONNECTED');
    this.name = 'WalletNotConnectedError';
  }
}

export class WalletSignatureError extends WalletError {
  constructor(message = 'Failed to sign message') {
    super(message, 'SIGNATURE_FAILED');
    this.name = 'WalletSignatureError';
  }
}

export class WalletConnectionError extends WalletError {
  constructor(message = 'Failed to connect wallet') {
    super(message, 'CONNECTION_FAILED');
    this.name = 'WalletConnectionError';
  }
}
