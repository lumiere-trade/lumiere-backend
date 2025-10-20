/**
 * Storage Interface (Port).
 * Abstracts token storage operations.
 */

export interface IStorage {
  setToken(token: string): void;
  getToken(): string | null;
  removeToken(): void;
  hasToken(): boolean;
}
