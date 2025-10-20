/**
 * Auth Repository Implementation (Adapter).
 * Implements IAuthRepository using HttpClient.
 */

import type {
  IAuthRepository,
  VerifyWalletResult,
  LoginResult,
  CreateAccountResult,
  ComplianceResult,
} from '@/lib/domain/interfaces/auth.repository.interface';
import { User } from '@/lib/domain/entities/user.entity';
import { LegalDocument } from '@/lib/domain/entities/legal-document.entity';
import { PendingDocument } from '@/lib/domain/entities/pending-document.entity';
import { HttpClient } from './http-client';
import type {
  VerifyWalletRequest,
  VerifyWalletResponse,
  CreateAccountRequest,
  CreateAccountResponse,
  LoginRequest,
  LoginResponse,
  ComplianceResponse,
  LegalDocumentDto,
  AcceptDocumentsRequest,
} from '@/types/api.types';

export class AuthRepository implements IAuthRepository {
  constructor(private readonly httpClient: HttpClient) {}

  async verifyWallet(
    walletAddress: string,
    message: string,
    signature: string
  ): Promise<VerifyWalletResult> {
    const request: VerifyWalletRequest = {
      wallet_address: walletAddress,
      message,
      signature,
    };

    const response = await this.httpClient.post<VerifyWalletResponse>(
      '/api/auth/verify',
      request
    );

    return {
      signatureValid: response.signature_valid,
      userExists: response.user_exists,
      userId: response.user_id,
      walletAddress: response.wallet_address,
    };
  }

  async login(
    walletAddress: string,
    message: string,
    signature: string
  ): Promise<LoginResult> {
    const request: LoginRequest = {
      wallet_address: walletAddress,
      message,
      signature,
    };

    const response = await this.httpClient.post<LoginResponse>(
      '/api/auth/login',
      request
    );

    const user = User.fromApi({
      id: response.user_id,
      wallet_address: response.wallet_address,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });

    const pendingDocuments = response.pending_documents.map((doc) =>
      PendingDocument.fromApi(doc)
    );

    return {
      user,
      accessToken: response.access_token,
      isCompliant: response.is_compliant,
      pendingDocuments,
    };
  }

  async createAccount(
    walletAddress: string,
    message: string,
    signature: string,
    acceptedDocumentIds: string[]
  ): Promise<CreateAccountResult> {
    const request: CreateAccountRequest = {
      wallet_address: walletAddress,
      message,
      signature,
      accepted_documents: acceptedDocumentIds,
    };

    const response = await this.httpClient.post<CreateAccountResponse>(
      '/api/auth/create-account',
      request
    );

    const user = User.fromApi({
      id: response.user_id,
      wallet_address: response.wallet_address,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });

    return {
      user,
      accessToken: response.access_token,
    };
  }

  async checkCompliance(): Promise<ComplianceResult> {
    const response = await this.httpClient.get<ComplianceResponse>(
      '/api/legal/compliance'
    );

    const missingDocuments = response.missing_documents.map((doc) =>
      PendingDocument.fromApi(doc)
    );

    return {
      isCompliant: response.is_compliant,
      missingDocuments,
    };
  }

  async acceptDocuments(documentIds: string[]): Promise<void> {
    const request: AcceptDocumentsRequest = {
      document_ids: documentIds,
    };

    await this.httpClient.post('/api/legal/accept', request);
  }

  async getLegalDocuments(): Promise<LegalDocument[]> {
    const response = await this.httpClient.get<LegalDocumentDto[]>(
      '/api/legal/documents'
    );

    return response.map((doc) => LegalDocument.fromApi(doc));
  }
}
