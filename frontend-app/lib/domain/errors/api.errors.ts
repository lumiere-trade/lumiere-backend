/**
 * API communication errors.
 */

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly statusCode?: number,
    public readonly code?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export class NetworkError extends ApiError {
  constructor(message = 'Network error') {
    super(message, undefined, 'NETWORK_ERROR');
    this.name = 'NetworkError';
  }
}

export class ServerError extends ApiError {
  constructor(message = 'Server error', statusCode = 500) {
    super(message, statusCode, 'SERVER_ERROR');
    this.name = 'ServerError';
  }
}

export class ValidationError extends ApiError {
  constructor(message: string, public readonly field?: string) {
    super(message, 400, 'VALIDATION_ERROR');
    this.name = 'ValidationError';
  }
}
