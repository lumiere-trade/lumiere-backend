/**
 * Auth Repository Interface (Port in Hexagonal Architecture).
 * Defines contract for authentication operations.
 */
import type { User } from '../entities/user.entity';
import type { LegalDocument } from '../entities/legal-document.entity';
import type { PendingDocument } from '../entities/pending-document.entity';

export interface VerifyWalletResult {
  signatureValid: boolean;
  userExists: boolean;
  userId: string | null;
  walletAddress: string;
}

export interface LoginResult {
  user: User;
  accessToken: string;
  isCompliant: boolean;
  pendingDocuments: PendingDocument[];
}

export interface CreateAccountResult {
  user: User;
  accessToken: string;
}

export interface ComplianceResult {
  isCompliant: boolean;
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
    signature: string
  ): Promise<LoginResult>;

  createAccount(
    walletAddress: string,
    message: string,
    signature: string,
    acceptedDocumentIds: string[]
  ): Promise<CreateAccountResult>;

  getCurrentUser(): Promise<User>;

  checkCompliance(): Promise<ComplianceResult>;

  acceptDocuments(documentIds: string[]): Promise<void>;

  getLegalDocuments(): Promise<LegalDocument[]>;
}
