/**
 * Authentication domain errors.
 */

export class AuthError extends Error {
  constructor(message: string, public readonly code?: string) {
    super(message);
    this.name = 'AuthError';
  }
}

export class InvalidSignatureError extends AuthError {
  constructor(message = 'Invalid wallet signature') {
    super(message, 'INVALID_SIGNATURE');
    this.name = 'InvalidSignatureError';
  }
}

export class UserNotFoundError extends AuthError {
  constructor(message = 'User not found') {
    super(message, 'USER_NOT_FOUND');
    this.name = 'UserNotFoundError';
  }
}

export class UserAlreadyExistsError extends AuthError {
  constructor(message = 'User already exists') {
    super(message, 'USER_EXISTS');
    this.name = 'UserAlreadyExistsError';
  }
}

export class TokenExpiredError extends AuthError {
  constructor(message = 'Authentication token expired') {
    super(message, 'TOKEN_EXPIRED');
    this.name = 'TokenExpiredError';
  }
}

export class UnauthorizedError extends AuthError {
  constructor(message = 'Unauthorized') {
    super(message, 'UNAUTHORIZED');
    this.name = 'UnauthorizedError';
  }
}
