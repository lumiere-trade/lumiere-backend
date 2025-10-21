/**
 * Create Account Use Case.
 * Handles new user registration with legal acceptance.
 */

import { AuthService, type AuthState } from '../services/auth.service';
import { LegalService } from '../services/legal.service';

export class CreateAccount {
  constructor(
    private readonly authService: AuthService,
    private readonly legalService: LegalService
  ) {}

  async execute(acceptedDocumentIds: string[]): Promise<AuthState> {
    const activeDocs = await this.legalService.getActiveLegalDocuments();
    const activeDocIds = activeDocs.map((doc) => doc.id);

    const missingDocs = activeDocIds.filter(
      (id) => !acceptedDocumentIds.includes(id)
    );

    if (missingDocs.length > 0) {
      throw new Error('All legal documents must be accepted');
    }

    return await this.authService.createAccount(acceptedDocumentIds);
  }
}
