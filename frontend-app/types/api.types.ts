/**
 * API Data Transfer Objects (DTOs).
 * Matches Pourtier backend schema exactly.
 */

export interface LegalDocumentDto {
  id: string;
  document_type: 'terms_of_service' | 'privacy_policy' | 'cookie_policy';
  version: string;
  title: string;
  content: string;
  status: 'draft' | 'active' | 'archived';
  effective_date: string;
  created_at: string;
  updated_at: string;
}

export interface PendingDocumentDto {
  id: string;
  document_type: string;
  version: string;
  title: string;
}

export interface UserDto {
  id: string;
  wallet_address: string;
  created_at: string;
  updated_at: string;
}

export interface VerifyWalletRequest {
  wallet_address: string;
  message: string;
  signature: string;
}

export interface VerifyWalletResponse {
  signature_valid: boolean;
  user_exists: boolean;
  user_id: string | null;
  wallet_address: string;
}

export interface CreateAccountRequest {
  wallet_address: string;
  message: string;
  signature: string;
  wallet_type: string;
  accepted_documents: string[];
  ip_address?: string;
  user_agent?: string;
}

export interface CreateAccountResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  wallet_address: string;
}

export interface LoginRequest {
  wallet_address: string;
  message: string;
  signature: string;
  wallet_type: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  wallet_address: string;
  is_compliant: boolean;
  pending_documents: PendingDocumentDto[];
}

export interface ComplianceResponse {
  is_compliant: boolean;
  missing_documents: PendingDocumentDto[];
}

export interface AcceptDocumentsRequest {
  document_ids: string[];
}

export interface HealthResponse {
  status: string;
  timestamp: string;
}

export interface CheckComplianceResponse {
  is_compliant: boolean;
  pending_documents: PendingDocumentDto[];
}
