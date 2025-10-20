/**
 * Legal Document domain entity.
 */

export type DocumentType = 'terms_of_service' | 'privacy_policy' | 'cookie_policy';
export type DocumentStatus = 'draft' | 'active' | 'archived';

export class LegalDocument {
  constructor(
    public readonly id: string,
    public readonly documentType: DocumentType,
    public readonly version: string,
    public readonly title: string,
    public readonly content: string,
    public readonly status: DocumentStatus,
    public readonly effectiveDate: Date,
    public readonly createdAt: Date,
    public readonly updatedAt: Date
  ) {}

  static fromApi(data: {
    id: string;
    document_type: string;
    version: string;
    title: string;
    content: string;
    status: string;
    effective_date: string;
    created_at: string;
    updated_at: string;
  }): LegalDocument {
    return new LegalDocument(
      data.id,
      data.document_type as DocumentType,
      data.version,
      data.title,
      data.content,
      data.status as DocumentStatus,
      new Date(data.effective_date),
      new Date(data.created_at),
      new Date(data.updated_at)
    );
  }

  isActive(): boolean {
    return this.status === 'active';
  }

  get shortVersion(): string {
    return `v${this.version}`;
  }
}
