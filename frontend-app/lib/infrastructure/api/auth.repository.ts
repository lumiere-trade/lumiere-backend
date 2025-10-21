import { IAuthRepository } from '@/lib/domain/interfaces/auth.repository.interface';
import { HttpClient } from './http-client';
import {
  VerifyWalletRequest,
  VerifyWalletResponse,
  LoginRequest,
  LoginResponse,
  CreateAccountRequest,
  CreateAccountResponse,
  CheckComplianceResponse,
  AcceptDocumentsRequest,
} from '@/types/api.types';
import { User } from '@/lib/domain/entities/user.entity';
import { PendingDocument } from '@/lib/domain/entities/pending-document.entity';
import { LegalDocument } from '@/lib/domain/entities/legal-document.entity';
import {
  InvalidSignatureError,
  UserNotFoundError,
  UserAlreadyExistsError,
} from '@/lib/domain/errors/auth.errors';

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
      created_at: response.created_at,
      updated_at: response.updated_at,
      pending_documents: response.pending_documents,
    });

    const pendingDocuments = (response.pending_documents || []).map((doc) =>
      PendingDocument.fromApi(doc)
    );

    return {
      user,
      accessToken: response.access_token,
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
      ip_address: '127.0.0.1',
      user_agent: navigator.userAgent,
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
      pending_documents: [],
    });

    return {
      user,
      accessToken: response.access_token,
    };
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.httpClient.get<any>('/api/users/me');

    return User.fromApi({
      id: response.id,
      wallet_address: response.wallet_address,
      created_at: response.created_at,
      updated_at: response.updated_at,
      pending_documents: response.pending_documents || [],
    });
  }

  async checkCompliance(): Promise<CheckComplianceResult> {
    const response = await this.httpClient.get<CheckComplianceResponse>(
      '/api/auth/compliance'
    );

    const missingDocuments = (response.pending_documents || []).map((doc) =>
      PendingDocument.fromApi(doc)
    );

    return {
      missingDocuments,
    };
  }

  async acceptDocuments(documentIds: string[]): Promise<void> {
    const request: AcceptDocumentsRequest = {
      document_ids: documentIds,
    };

    await this.httpClient.post('/api/auth/accept-documents', request);
  }

  async getLegalDocuments(): Promise<LegalDocument[]> {
    const response = await this.httpClient.get<any[]>(
      '/api/legal/documents'
    );

    return response.map((doc) => LegalDocument.fromApi(doc));
  }
}
