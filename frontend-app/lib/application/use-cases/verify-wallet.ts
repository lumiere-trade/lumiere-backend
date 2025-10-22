/**
 * Verify Wallet Use Case.
 * Checks if wallet signature is valid and if user exists.
 */

import type { IAuthRepository } from '@/lib/domain/interfaces/auth.repository.interface';
import type { IWalletProvider } from '@/lib/domain/interfaces/wallet.provider.interface';
import { AUTH_CONFIG } from '@/config/constants';

export interface VerifyWalletResult {
  isValid: boolean;
  userExists: boolean;
  walletAddress: string;
}

export class VerifyWallet {
  constructor(
    private readonly authRepository: IAuthRepository,
    private readonly walletProvider: IWalletProvider
  ) {}

  async execute(): Promise<VerifyWalletResult> {
    const address = this.walletProvider.getAddress();
    if (!address) {
      throw new Error('Wallet not connected');
    }

    const message = AUTH_CONFIG.MESSAGE;
    const { signature } = await this.walletProvider.signMessage(message);

    const result = await this.authRepository.verifyWallet(
      address,
      message,
      signature
    );

    return {
      isValid: result.signatureValid,
      userExists: result.userExists,
      walletAddress: address,
    };
  }
}
