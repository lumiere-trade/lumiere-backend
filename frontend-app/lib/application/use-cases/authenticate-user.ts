/**
 * Authenticate User Use Case.
 * Handles complete authentication flow.
 */

import { AuthService, type AuthState } from '../services/auth.service';

export class AuthenticateUser {
  constructor(private readonly authService: AuthService) {}

  async execute(): Promise<AuthState> {
    return await this.authService.verifyAndLogin();
  }
}
