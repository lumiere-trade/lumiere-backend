# Pourtier API Reference

**Version:** 1.0  
**Base URL:** `https://api.lumiere.trade`  
**Last Updated:** October 27, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Error Handling](#error-handling)
4. [Rate Limiting](#rate-limiting)
5. [Endpoints](#endpoints)
   - [Authentication](#authentication-endpoints)
   - [Users](#user-endpoints)
   - [Legal](#legal-endpoints)
   - [Escrow](#escrow-endpoints)
   - [Subscriptions](#subscription-endpoints)
6. [WebSocket Events](#websocket-events)
7. [Data Models](#data-models)

---

## Overview

Pourtier is the **API Gateway** for the Lumiere platform. It handles:
- User authentication via wallet signatures
- Legal compliance management
- Escrow operations proxy to Passeur
- User profile management
- Subscription management

**Architecture:**
```
Frontend → Pourtier (API Gateway) → Backend Services
                ↓
            PostgreSQL
                ↓
            Passeur (Solana Bridge)
```

**Key Responsibilities:**
- Request validation
- JWT authentication
- Rate limiting
- Request routing
- Response formatting
- Error handling

---

## Authentication

Pourtier uses **JWT (JSON Web Tokens)** with wallet signature authentication.

### Authentication Flow
```
1. Frontend: User connects wallet (Phantom/Solflare)
2. Frontend: Request nonce → POST /api/auth/verify
3. Backend: Generate nonce, return to frontend
4. Frontend: Sign nonce with wallet
5. Frontend: Submit signature → POST /api/auth/login
6. Backend: Verify signature, check legal compliance
7. Backend: Return JWT token
8. Frontend: Store token, use in Authorization header
```

### Using JWT Token

Include token in **Authorization header** for all authenticated endpoints:
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Token Payload
```json
{
  "wallet_address": "kshy5yns5FGGXcFVfjT2fTzVsQLFnbZzL9zuh1ZKR2y",
  "wallet_type": "Phantom",
  "exp": 1698451200,
  "iat": 1698364800
}
```

**Token Expiration:** 24 hours

---

## Error Handling

### Standard Error Response
```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| `200` | OK | Request successful |
| `201` | Created | Resource created successfully |
| `400` | Bad Request | Invalid request parameters |
| `401` | Unauthorized | Missing or invalid authentication |
| `403` | Forbidden | Authenticated but not authorized |
| `404` | Not Found | Resource not found |
| `409` | Conflict | Resource already exists |
| `422` | Unprocessable Entity | Validation error |
| `500` | Internal Server Error | Server error |
| `502` | Bad Gateway | Upstream service error |
| `503` | Service Unavailable | Service temporarily unavailable |

### Error Examples

**400 Bad Request:**
```json
{
  "detail": "Invalid wallet address format"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Invalid or expired token"
}
```

**403 Forbidden:**
```json
{
  "detail": "User has not accepted Terms of Service"
}
```

---

## Rate Limiting

**Current Status:** Not implemented (TODO)

**Planned Limits:**
- Unauthenticated: 10 requests/minute
- Authenticated: 100 requests/minute
- Escrow operations: 20 requests/minute

**Headers (when implemented):**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1698364800
```

---

## Endpoints

### Authentication Endpoints

#### POST /api/auth/verify

Request nonce for wallet signature.

**Authentication:** None required

**Request:**
```json
{
  "wallet_address": "kshy5yns5FGGXcFVfjT2fTzVsQLFnbZzL9zuh1ZKR2y",
  "wallet_type": "Phantom"
}
```

**Response:** `200 OK`
```json
{
  "nonce": "lumiere-auth-1698364800-abc123",
  "message": "Please sign this message to authenticate with Lumiere:\n\nNonce: lumiere-auth-1698364800-abc123\nTimestamp: 2025-10-27T10:00:00Z"
}
```

**Errors:**
- `400` - Invalid wallet address format
- `500` - Failed to generate nonce

---

#### POST /api/auth/create-account

Create new user account (first-time users).

**Authentication:** None required

**Request:**
```json
{
  "wallet_address": "kshy5yns5FGGXcFVfjT2fTzVsQLFnbZzL9zuh1ZKR2y",
  "wallet_type": "Phantom",
  "signature": "3Z7J8K..."
}
```

**Response:** `201 Created`
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "wallet_address": "kshy5yns5FGGXcFVfjT2fTzVsQLFnbZzL9zuh1ZKR2y",
    "wallet_type": "Phantom",
    "escrow_account": null,
    "escrow_balance": "0.00",
    "escrow_token_mint": null,
    "created_at": "2025-10-27T10:00:00Z",
    "updated_at": "2025-10-27T10:00:00Z",
    "pending_documents": [
      {
        "id": "legal-doc-123",
        "document_type": "TERMS_OF_SERVICE",
        "version": "1.0",
        "title": "Terms of Service",
        "content": "...",
        "status": "ACTIVE",
        "effective_date": "2025-10-01T00:00:00Z",
        "created_at": "2025-10-01T00:00:00Z",
        "updated_at": "2025-10-01T00:00:00Z"
      }
    ]
  }
}
```

**Errors:**
- `400` - Invalid signature or wallet address
- `409` - User already exists
- `500` - Failed to create user

---

#### POST /api/auth/login

Login existing user.

**Authentication:** None required

**Request:**
```json
{
  "wallet_address": "kshy5yns5FGGXcFVfjT2fTzVsQLFnbZzL9zuh1ZKR2y",
  "wallet_type": "Phantom",
  "signature": "3Z7J8K..."
}
```

**Response:** `200 OK`
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "wallet_address": "kshy5yns5FGGXcFVfjT2fTzVsQLFnbZzL9zuh1ZKR2y",
    "wallet_type": "Phantom",
    "escrow_account": "EscrowPDA123...",
    "escrow_balance": "1250.50",
    "escrow_token_mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "created_at": "2025-10-20T10:00:00Z",
    "updated_at": "2025-10-27T10:00:00Z",
    "pending_documents": []
  }
}
```

**Errors:**
- `400` - Invalid signature
- `403` - User has pending legal documents
- `404` - User not found
- `500` - Authentication failed

---

### User Endpoints

#### GET /api/users/me

Get current authenticated user profile.

**Authentication:** Required (JWT)

**Response:** `200 OK`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "wallet_address": "kshy5yns5FGGXcFVfjT2fTzVsQLFnbZzL9zuh1ZKR2y",
  "wallet_type": "Phantom",
  "escrow_account": "EscrowPDA123...",
  "escrow_balance": "1250.50",
  "escrow_token_mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
  "created_at": "2025-10-20T10:00:00Z",
  "updated_at": "2025-10-27T10:00:00Z",
  "pending_documents": []
}
```

**Errors:**
- `401` - Invalid or missing token
- `404` - User not found

---

#### POST /api/users/

Create new user (alternative endpoint).

**Authentication:** None required

**Request:**
```json
{
  "wallet_address": "kshy5yns5FGGXcFVfjT2fTzVsQLFnbZzL9zuh1ZKR2y"
}
```

**Response:** `201 Created`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "wallet_address": "kshy5yns5FGGXcFVfjT2fTzVsQLFnbZzL9zuh1ZKR2y",
  "wallet_type": "Unknown",
  "escrow_account": null,
  "escrow_balance": "0.00",
  "escrow_token_mint": null,
  "created_at": "2025-10-27T10:00:00Z",
  "updated_at": "2025-10-27T10:00:00Z",
  "pending_documents": []
}
```

**Errors:**
- `400` - Invalid wallet address
- `500` - Failed to create user

---

#### GET /api/users/{user_id}

Get user by ID.

**Authentication:** Required (JWT)

**Parameters:**
- `user_id` (UUID) - User unique identifier

**Response:** `200 OK`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "wallet_address": "kshy5yns5FGGXcFVfjT2fTzVsQLFnbZzL9zuh1ZKR2y",
  "wallet_type": "Unknown",
  "escrow_account": null,
  "escrow_balance": "0.00",
  "escrow_token_mint": null,
  "created_at": "2025-10-27T10:00:00Z",
  "updated_at": "2025-10-27T10:00:00Z",
  "pending_documents": []
}
```

**Errors:**
- `401` - Invalid or missing token
- `404` - User not found

---

#### GET /api/users/wallet/{wallet_address}

Get user by wallet address.

**Authentication:** Required (JWT)

**Parameters:**
- `wallet_address` (string) - Solana wallet address

**Response:** `200 OK`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "wallet_address": "kshy5yns5FGGXcFVfjT2fTzVsQLFnbZzL9zuh1ZKR2y",
  "wallet_type": "Unknown",
  "escrow_account": null,
  "escrow_balance": "0.00",
  "escrow_token_mint": null,
  "created_at": "2025-10-27T10:00:00Z",
  "updated_at": "2025-10-27T10:00:00Z",
  "pending_documents": []
}
```

**Errors:**
- `401` - Invalid or missing token
- `404` - User not found

---

### Legal Endpoints

#### GET /api/legal/documents

Get all active legal documents.

**Authentication:** None required

**Query Parameters:**
- `document_type` (optional) - Filter by type (TERMS_OF_SERVICE, PRIVACY_POLICY, RISK_DISCLOSURE, etc.)
- `version` (optional) - Filter by version

**Response:** `200 OK`
```json
{
  "documents": [
    {
      "id": "legal-doc-123",
      "document_type": "TERMS_OF_SERVICE",
      "version": "1.0",
      "title": "Terms of Service",
      "content": "Full legal text...",
      "status": "ACTIVE",
      "effective_date": "2025-10-01T00:00:00Z",
      "created_at": "2025-10-01T00:00:00Z",
      "updated_at": "2025-10-01T00:00:00Z"
    }
  ]
}
```

**Errors:**
- `500` - Failed to retrieve documents

---

#### POST /api/legal/accept

Accept legal document (user signs agreement).

**Authentication:** Required (JWT)

**Request:**
```json
{
  "document_id": "legal-doc-123"
}
```

**Response:** `200 OK`
```json
{
  "message": "Legal document accepted successfully",
  "acceptance": {
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "document_id": "legal-doc-123",
    "document_type": "TERMS_OF_SERVICE",
    "version": "1.0",
    "accepted_at": "2025-10-27T10:00:00Z"
  }
}
```

**Errors:**
- `401` - Invalid or missing token
- `404` - Document not found
- `409` - Document already accepted
- `500` - Failed to record acceptance

---

#### GET /api/legal/compliance

Check user's legal compliance status.

**Authentication:** Required (JWT)

**Response:** `200 OK`
```json
{
  "is_compliant": false,
  "pending_documents": [
    {
      "id": "legal-doc-123",
      "document_type": "TERMS_OF_SERVICE",
      "version": "1.0",
      "title": "Terms of Service",
      "content": "...",
      "status": "ACTIVE",
      "effective_date": "2025-10-01T00:00:00Z",
      "created_at": "2025-10-01T00:00:00Z",
      "updated_at": "2025-10-01T00:00:00Z"
    }
  ]
}
```

**Errors:**
- `401` - Invalid or missing token
- `404` - User not found

---

### Escrow Endpoints

#### POST /api/escrow/initialize

Initialize user's escrow account.

**Authentication:** Required (JWT)

**Request:**
```json
{
  "token_mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
}
```

**Response:** `200 OK`
```json
{
  "transaction": {
    "serialized_transaction": "base64_encoded_transaction...",
    "escrow_pda": "EscrowPDA123..."
  }
}
```

**Flow:**
1. Backend creates escrow account on Solana
2. Returns unsigned transaction
3. Frontend signs with wallet
4. Frontend submits signed transaction to blockchain

**Errors:**
- `401` - Invalid or missing token
- `409` - Escrow already initialized
- `500` - Failed to create escrow
- `502` - Passeur service unavailable

---

#### POST /api/escrow/deposit

Deposit funds into escrow.

**Authentication:** Required (JWT)

**Request:**
```json
{
  "amount": "100.50"
}
```

**Response:** `200 OK`
```json
{
  "transaction": {
    "serialized_transaction": "base64_encoded_transaction...",
    "amount": "100.50",
    "escrow_account": "EscrowPDA123..."
  }
}
```

**Flow:**
1. Backend creates deposit transaction
2. Returns unsigned transaction
3. Frontend signs with wallet
4. Frontend submits to blockchain
5. Backend updates escrow balance

**Errors:**
- `401` - Invalid or missing token
- `400` - Invalid amount or escrow not initialized
- `500` - Failed to create deposit
- `502` - Passeur service unavailable

---

#### POST /api/escrow/withdraw

Withdraw funds from escrow.

**Authentication:** Required (JWT)

**Request:**
```json
{
  "amount": "50.25"
}
```

**Response:** `200 OK`
```json
{
  "transaction": {
    "serialized_transaction": "base64_encoded_transaction...",
    "amount": "50.25",
    "escrow_account": "EscrowPDA123..."
  }
}
```

**Flow:**
1. Backend creates withdrawal transaction
2. Returns unsigned transaction
3. Frontend signs with wallet
4. Frontend submits to blockchain
5. Backend updates escrow balance

**Errors:**
- `401` - Invalid or missing token
- `400` - Invalid amount or insufficient balance
- `500` - Failed to create withdrawal
- `502` - Passeur service unavailable

---

#### GET /api/escrow/balance

Get current escrow balance.

**Authentication:** Required (JWT)

**Query Parameters:**
- `sync` (boolean, optional) - If true, sync from blockchain before returning (default: false)

**Response:** `200 OK`
```json
{
  "escrow_account": "EscrowPDA123...",
  "balance": "1250.50",
  "token_mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
  "is_initialized": true,
  "initialized_at": "2025-10-20T10:00:00Z",
  "last_synced_at": "2025-10-27T10:00:00Z"
}
```

**When Not Initialized:**
```json
{
  "escrow_account": null,
  "balance": "0.00",
  "token_mint": "USDC",
  "is_initialized": false,
  "initialized_at": null,
  "last_synced_at": null
}
```

**Errors:**
- `401` - Invalid or missing token
- `404` - User not found
- `502` - Blockchain sync failed (if sync=true)

---

#### GET /api/escrow/transactions

Get escrow transaction history.

**Authentication:** Required (JWT)

**Query Parameters:**
- `limit` (integer, optional) - Max transactions to return (default: 50, max: 100)
- `offset` (integer, optional) - Pagination offset (default: 0)
- `type` (string, optional) - Filter by type (DEPOSIT, WITHDRAWAL, TRADE)

**Response:** `200 OK`
```json
{
  "transactions": [
    {
      "id": "tx-123",
      "transaction_type": "DEPOSIT",
      "amount": "100.50",
      "status": "CONFIRMED",
      "signature": "5J8K9L...",
      "created_at": "2025-10-27T10:00:00Z",
      "confirmed_at": "2025-10-27T10:00:15Z"
    }
  ],
  "total": 10,
  "limit": 50,
  "offset": 0
}
```

**Errors:**
- `401` - Invalid or missing token
- `404` - User not found

---

### Subscription Endpoints

#### POST /api/subscriptions/

Create new subscription.

**Authentication:** Required (JWT)

**Request:**
```json
{
  "tier": "GENESIS_ACCESS",
  "payment_method": "CRYPTO"
}
```

**Response:** `201 Created`
```json
{
  "id": "sub-123",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "tier": "GENESIS_ACCESS",
  "status": "PENDING_PAYMENT",
  "start_date": null,
  "end_date": null,
  "auto_renew": true,
  "created_at": "2025-10-27T10:00:00Z",
  "updated_at": "2025-10-27T10:00:00Z"
}
```

**Errors:**
- `401` - Invalid or missing token
- `400` - Invalid subscription tier
- `409` - Active subscription already exists

---

#### GET /api/subscriptions/

Get user's subscriptions.

**Authentication:** Required (JWT)

**Query Parameters:**
- `status` (optional) - Filter by status (ACTIVE, EXPIRED, CANCELLED, etc.)

**Response:** `200 OK`
```json
{
  "subscriptions": [
    {
      "id": "sub-123",
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "tier": "GENESIS_ACCESS",
      "status": "ACTIVE",
      "start_date": "2025-10-20T00:00:00Z",
      "end_date": "2025-11-20T00:00:00Z",
      "auto_renew": true,
      "created_at": "2025-10-20T10:00:00Z",
      "updated_at": "2025-10-20T10:05:00Z"
    }
  ]
}
```

**Errors:**
- `401` - Invalid or missing token

---

#### GET /api/subscriptions/check

Check subscription access for current user.

**Authentication:** Required (JWT)

**Response:** `200 OK`
```json
{
  "has_access": true,
  "subscription": {
    "id": "sub-123",
    "tier": "GENESIS_ACCESS",
    "status": "ACTIVE",
    "expires_at": "2025-11-20T00:00:00Z"
  }
}
```

**When No Access:**
```json
{
  "has_access": false,
  "subscription": null
}
```

**Errors:**
- `401` - Invalid or missing token

---

#### GET /api/subscriptions/{subscription_id}

Get subscription by ID.

**Authentication:** Required (JWT)

**Parameters:**
- `subscription_id` (UUID) - Subscription unique identifier

**Response:** `200 OK`
```json
{
  "id": "sub-123",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "tier": "GENESIS_ACCESS",
  "status": "ACTIVE",
  "start_date": "2025-10-20T00:00:00Z",
  "end_date": "2025-11-20T00:00:00Z",
  "auto_renew": true,
  "created_at": "2025-10-20T10:00:00Z",
  "updated_at": "2025-10-20T10:05:00Z"
}
```

**Errors:**
- `401` - Invalid or missing token
- `404` - Subscription not found

---

#### PATCH /api/subscriptions/{subscription_id}

Update subscription (e.g., toggle auto-renew).

**Authentication:** Required (JWT)

**Parameters:**
- `subscription_id` (UUID) - Subscription unique identifier

**Request:**
```json
{
  "auto_renew": false
}
```

**Response:** `200 OK`
```json
{
  "id": "sub-123",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "tier": "GENESIS_ACCESS",
  "status": "ACTIVE",
  "start_date": "2025-10-20T00:00:00Z",
  "end_date": "2025-11-20T00:00:00Z",
  "auto_renew": false,
  "created_at": "2025-10-20T10:00:00Z",
  "updated_at": "2025-10-27T10:00:00Z"
}
```

**Errors:**
- `401` - Invalid or missing token
- `404` - Subscription not found

---

## WebSocket Events

**Status:** Not yet implemented (TODO)

**Planned Events:**
- `escrow.deposit.confirmed` - Deposit confirmed on blockchain
- `escrow.withdrawal.confirmed` - Withdrawal confirmed on blockchain
- `strategy.execution.started` - Strategy started trading
- `trade.executed` - Trade executed
- `strategy.stopped` - Strategy stopped

---

## Data Models

### User
```typescript
interface User {
  id: string                    // UUID
  wallet_address: string        // Solana address
  wallet_type: string           // "Phantom" | "Solflare" | "Backpack"
  escrow_account: string | null // Escrow PDA address
  escrow_balance: string        // Decimal as string
  escrow_token_mint: string | null
  created_at: string            // ISO 8601
  updated_at: string            // ISO 8601
  pending_documents: LegalDocument[]
}
```

### LegalDocument
```typescript
interface LegalDocument {
  id: string                   // UUID
  document_type: string        // "TERMS_OF_SERVICE" | "PRIVACY_POLICY" | etc.
  version: string              // Semantic version
  title: string
  content: string              // Full legal text
  status: string               // "ACTIVE" | "INACTIVE"
  effective_date: string       // ISO 8601
  created_at: string           // ISO 8601
  updated_at: string           // ISO 8601
}
```

### EscrowTransaction
```typescript
interface EscrowTransaction {
  id: string                   // UUID
  user_id: string              // UUID
  transaction_type: string     // "DEPOSIT" | "WITHDRAWAL" | "TRADE"
  amount: string               // Decimal as string
  status: string               // "PENDING" | "CONFIRMED" | "FAILED"
  signature: string            // Solana transaction signature
  created_at: string           // ISO 8601
  confirmed_at: string | null  // ISO 8601
}
```

### Subscription
```typescript
interface Subscription {
  id: string                   // UUID
  user_id: string              // UUID
  tier: string                 // "GENESIS_ACCESS" | "PREMIUM" | etc.
  status: string               // "ACTIVE" | "EXPIRED" | "CANCELLED"
  start_date: string | null    // ISO 8601
  end_date: string | null      // ISO 8601
  auto_renew: boolean
  created_at: string           // ISO 8601
  updated_at: string           // ISO 8601
}
```

---

## Upcoming Endpoints (TODO)

### Wallet Balance (High Priority)
```
GET /api/wallet/balance?wallet={address}
```

Returns USDC balance in user's Solana wallet (not escrow).

**See:** `todo/add_wallet_balance_endpoint.md`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-27 | Initial API documentation |

---

**END OF DOCUMENT**
