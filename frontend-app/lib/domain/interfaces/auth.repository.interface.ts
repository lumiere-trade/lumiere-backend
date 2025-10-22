/**
 * Auth Repository Interface (Port).
 * Defines contract for authentication operations.
 */

import { User } from '../entities/user.entity';
import { PendingDocument } from '../entities/pending-document.entity';
import { LegalDocument } from '../entities/legal-document.entity';

export interface VerifyWalletResult {
  signatureValid: boolean;
  userExists: boolean;
}

export interface LoginResult {
  user: User;
  accessToken: string;
  pendingDocuments: PendingDocument[];
}

export interface CreateAccountResult {
  user: User;
  accessToken: string;
}

export interface CheckComplianceResult {
  missingDocuments: PendingDocument[];
}

export interface IAuthRepository {
  verifyWallet(
    walletAddress: string,
    message: string,
    signature: string
  ): Promise<VerifyWalletResult>;

  login(
    walletAddress: string,
    message: string,
    signature: string,
    walletType: string
  ): Promise<LoginResult>;

  createAccount(
    walletAddress: string,
    message: string,
    signature: string,
    walletType: string,
    acceptedDocumentIds: string[]
  ): Promise<CreateAccountResult>;

  getCurrentUser(): Promise<User>;

  checkCompliance(): Promise<CheckComplianceResult>;

  acceptDocuments(documentIds: string[]): Promise<void>;

  getLegalDocuments(): Promise<LegalDocument[]>;
}
