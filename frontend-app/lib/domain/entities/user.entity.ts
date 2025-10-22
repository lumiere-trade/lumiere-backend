/**
 * User domain entity.
 * Pure business logic, no external dependencies.
 */

import { LegalDocument } from './legal-document.entity';

export class User {
  constructor(
    public readonly id: string,
    public readonly walletAddress: string,
    public readonly walletType: string,
    public readonly createdAt: Date,
    public readonly updatedAt: Date,
    public readonly pendingDocuments: LegalDocument[] = []
  ) {}

  static fromApi(data: {
    id: string;
    wallet_address: string;
    wallet_type?: string;
    created_at: string;
    updated_at: string;
    pending_documents?: Array<{
      id: string;
      document_type: string;
      version: string;
      title: string;
      content: string;
      status: string;
      effective_date: string;
      created_at: string;
      updated_at: string;
    }>;
  }): User {
    const pendingDocuments = data.pending_documents
      ? data.pending_documents.map((doc) => LegalDocument.fromApi(doc))
      : [];

    return new User(
      data.id,
      data.wallet_address,
      data.wallet_type || 'Unknown Wallet',
      new Date(data.created_at),
      new Date(data.updated_at),
      pendingDocuments
    );
  }

  get shortAddress(): string {
    return `${this.walletAddress.slice(0, 4)}...${this.walletAddress.slice(-4)}`;
  }

  isEqual(other: User): boolean {
    return this.id === other.id;
  }

  hasPendingDocuments(): boolean {
    return this.pendingDocuments.length > 0;
  }

  get pendingDocumentCount(): number {
    return this.pendingDocuments.length;
  }
}
