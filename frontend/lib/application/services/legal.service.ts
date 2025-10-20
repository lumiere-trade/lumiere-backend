/**
 * Legal Service (Application Layer).
 * Handles legal document operations.
 */

import type { IAuthRepository } from '@/lib/domain/interfaces/auth.repository.interface';
import { LegalDocument } from '@/lib/domain/entities/legal-document.entity';

export class LegalService {
  constructor(private readonly authRepository: IAuthRepository) {}

  async getActiveLegalDocuments(): Promise<LegalDocument[]> {
    const documents = await this.authRepository.getLegalDocuments();
    return documents.filter((doc) => doc.isActive());
  }

  async getDocumentsByType(
    type: 'terms_of_service' | 'privacy_policy' | 'cookie_policy'
  ): Promise<LegalDocument[]> {
    const documents = await this.getActiveLegalDocuments();
    return documents.filter((doc) => doc.documentType === type);
  }
}
