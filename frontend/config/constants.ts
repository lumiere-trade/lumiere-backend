/**
 * Application-wide constants.
 */

export const API_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9000',
  TIMEOUT: 30000,
} as const;

export const AUTH_CONFIG = {
  TOKEN_KEY: 'lumiere_auth_token',
  MESSAGE: process.env.NEXT_PUBLIC_AUTH_MESSAGE || 'Sign this message to authenticate with Lumiere',
} as const;

export const SOLANA_CONFIG = {
  NETWORK: process.env.NEXT_PUBLIC_SOLANA_NETWORK || 'devnet',
  RPC_URL: process.env.NEXT_PUBLIC_SOLANA_RPC_URL || 'https://api.devnet.solana.com',
} as const;

export const ROUTES = {
  HOME: '/',
  DASHBOARD: '/dashboard',
  ONBOARDING: '/onboarding',
  TERMS: '/terms',
} as const;
