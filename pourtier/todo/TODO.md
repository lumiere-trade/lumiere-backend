# TODO: Complete Deposit Flow Implementation

## Date: October 28, 2025
## Status: Backend Partially Complete, Frontend Ready, Initialize Flow Missing

---

## What Was Completed Today

### Backend (Pourtier)

#### 1. Added `/api/escrow/prepare-deposit` Endpoint
**File:** `src/pourtier/presentation/api/routes/escrow.py`
**Lines:** 114-168

**What it does:**
- Accepts deposit amount from authenticated user
- Validates user has initialized escrow account
- Calls Passeur Bridge to generate unsigned transaction
- Returns base64 unsigned transaction for wallet signing

**Request:**
```json
POST /api/escrow/prepare-deposit
{
  "amount": "5.00"
}
```

**Response:**
```json
{
  "transaction": "base64_unsigned_tx...",
  "escrow_account": "escrow_pda_address",
  "amount": "5.00"
}
```

#### 2. Added `PrepareDepositToEscrow` Use Case
**File:** `src/pourtier/application/use_cases/prepare_deposit_to_escrow.py`

**What it does:**
- Business logic for preparing deposit
- Validates amount > 0
- Checks user exists in database
- Validates escrow is initialized
- Calls Passeur Bridge `prepare_deposit()` method

**Dependencies:**
- `IUserRepository` - to get user data
- `IPasseurBridge` - to prepare unsigned transaction

#### 3. Updated Schemas
**File:** `src/pourtier/presentation/schemas/escrow_schemas.py`

**Added:**
- `PrepareDepositRequest` (lines 35-43)
- `PrepareDepositResponse` (lines 88-107)

#### 4. Updated DI Container
**File:** `src/pourtier/di/dependencies.py`

**Added:**
- `get_prepare_deposit_to_escrow()` dependency function (lines 217-233)

#### 5. Passeur Bridge Already Had Method
**File:** `src/pourtier/infrastructure/blockchain/passeur_bridge_client.py`

**Existing method:**
- `prepare_deposit()` (lines 239-262) - already implemented, no changes needed

### Frontend

#### 1. Implemented Full Deposit Flow in EscrowService
**File:** `app/lib/application/services/escrow.service.ts`

**What it does:**
```typescript
async depositToEscrow(amount: string): Promise<DepositResult> {
  // 1. Validate amount and wallet balance
  // 2. Check if escrow initialized (calls initializeEscrow if not)
  // 3. Call prepareDeposit() to get unsigned transaction
  // 4. Sign transaction with wallet
  // 5. Submit signed transaction via submitDeposit()
  // 6. Return updated escrow state
}
```

#### 2. Updated Repository Interface
**File:** `app/lib/domain/interfaces/escrow.repository.interface.ts`

**Added:**
- `PrepareDepositResponse` interface
- `prepareDeposit(amount: string)` method
- `submitDeposit(amount: string, signedTx: string)` method (renamed from depositToEscrow)

#### 3. Implemented Repository Methods
**File:** `app/lib/infrastructure/api/escrow.repository.ts`

**Added:**
- `prepareDeposit()` - calls `/api/escrow/prepare-deposit`
- `submitDeposit()` - calls `/api/escrow/deposit` with signed transaction

#### 4. Implemented Transaction Signing
**File:** `app/lib/infrastructure/wallet/solana-wallet-provider.ts`

**Added:**
- `signTransaction(transactionBase64: string)` method
- Handles both `Transaction` and `VersionedTransaction` formats
- Decodes base64 → deserializes → signs → serializes → encodes base64

#### 5. Removed Passeur from Frontend
- Deleted `PasseurRepository` files
- Removed passeur injection from DI container
- All blockchain operations now go through Pourtier API Gateway

### Commits
**Backend:**
```
feat: add prepare-deposit endpoint for deposit flow

- Add PrepareDepositToEscrow use case
- Add /api/escrow/prepare-deposit endpoint in Pourtier
- Generate unsigned deposit transaction via Passeur Bridge
```

**Frontend:**
```
refactor: remove Passeur from frontend, use Pourtier API Gateway
feat: implement deposit flow with transaction signing
```

---

## What Needs to Be Done Tomorrow

### Priority 1: Add Tests for New Endpoints (CRITICAL)

#### Test File Location
`~/lumiere/lumiere-backend/pourtier/tests/integration/test_escrow_prepare_deposit.py`

#### Tests to Write

##### 1. Test `POST /api/escrow/prepare-deposit` - Success Case
**What to test:**
- Authenticated user with initialized escrow
- Valid amount (e.g., 5.00 USDC)
- Returns 200 OK
- Response contains `transaction` (base64 string)
- Response contains `escrow_account` (matches user's escrow)
- Response contains `amount` (matches request)

**Mock Requirements:**
- Mock `IPasseurBridge.prepare_deposit()` to return fake base64 transaction
- Mock user with `escrow_account` set in database

**Expected Response:**
```python
{
    "transaction": "fake_base64_transaction...",
    "escrow_account": "user_escrow_pda_address",
    "amount": "5.00"
}
```

##### 2. Test `POST /api/escrow/prepare-deposit` - Unauthenticated
**What to test:**
- Request without JWT token
- Returns 403 Forbidden
- Error message: "Not authenticated"

##### 3. Test `POST /api/escrow/prepare-deposit` - Escrow Not Initialized
**What to test:**
- Authenticated user with `escrow_account = NULL`
- Returns 400 Bad Request
- Error contains: "Escrow not initialized"

##### 4. Test `POST /api/escrow/prepare-deposit` - Invalid Amount (Zero)
**What to test:**
- Amount = 0.00
- Returns 400 Bad Request
- Error contains: "Amount must be greater than 0"

##### 5. Test `POST /api/escrow/prepare-deposit` - Invalid Amount (Negative)
**What to test:**
- Amount = -5.00
- Returns 400 Bad Request
- Pydantic validation error

##### 6. Test `POST /api/escrow/prepare-deposit` - User Not Found
**What to test:**
- Valid JWT but user deleted from database
- Returns 404 Not Found
- Error contains: "User not found"

##### 7. Test `POST /api/escrow/prepare-deposit` - Passeur Bridge Failure
**What to test:**
- Mock `IPasseurBridge.prepare_deposit()` to raise `BridgeError`
- Returns 502 Bad Gateway
- Error contains: "Failed to prepare deposit"

##### 8. Test `PrepareDepositToEscrow` Use Case - Unit Test
**File:** `tests/unit/test_prepare_deposit_to_escrow.py`

**What to test:**
- Use case logic in isolation
- Mock both `IUserRepository` and `IPasseurBridge`
- Test all validation logic
- Test error handling

#### Test Patterns to Follow

**Example Test Structure:**
```python
async def test_prepare_deposit_success(
    client: AsyncClient,
    auth_headers: dict,
    mock_user_with_escrow,
    mock_passeur_bridge
):
    """Test successful prepare deposit."""
    # Arrange
    mock_passeur_bridge.prepare_deposit.return_value = "fake_base64_tx"
    
    # Act
    response = await client.post(
        "/api/escrow/prepare-deposit",
        json={"amount": "5.00"},
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "transaction" in data
    assert data["amount"] == "5.00"
    assert data["escrow_account"] == mock_user_with_escrow.escrow_account
    
    # Verify bridge was called correctly
    mock_passeur_bridge.prepare_deposit.assert_called_once_with(
        user_wallet=mock_user_with_escrow.wallet_address,
        escrow_account=mock_user_with_escrow.escrow_account,
        amount=Decimal("5.00")
    )
```

**Fixtures Needed:**
```python
@pytest.fixture
async def mock_user_with_escrow(db_session):
    """Create test user with initialized escrow."""
    user = User(
        wallet_address="test_wallet_address",
        escrow_account="test_escrow_pda",
        escrow_balance=Decimal("0.00"),
        escrow_token_mint="USDC_mint_address"
    )
    db_session.add(user)
    await db_session.commit()
    return user

@pytest.fixture
def mock_passeur_bridge(mocker):
    """Mock Passeur Bridge client."""
    bridge = mocker.Mock(spec=IPasseurBridge)
    return bridge
```

### Priority 2: Implement Initialize Escrow Flow

#### Backend: Add `POST /api/escrow/prepare-initialize` Endpoint

**What it should do:**
1. Accept request from authenticated user (no body needed)
2. Check if already initialized (return error if yes)
3. Call Passeur Bridge `/escrow/prepare-initialize` endpoint
4. Return unsigned transaction for wallet signing

**File:** `src/pourtier/presentation/api/routes/escrow.py`

**Add endpoint:**
```python
@router.post(
    "/prepare-initialize",
    response_model=PrepareInitializeResponse,
    status_code=status.HTTP_200_OK,
    summary="Prepare initialize escrow transaction",
    description="Generate unsigned initialize transaction for user to sign",
)
async def prepare_initialize_escrow(
    current_user: User = Depends(get_current_user),
    use_case: PrepareInitializeEscrow = Depends(get_prepare_initialize_escrow),
):
    """
    Prepare initialize escrow transaction.
    
    Flow:
    1. User calls this endpoint
    2. Backend generates unsigned transaction via Passeur
    3. User signs transaction in wallet (frontend)
    4. User calls POST /api/escrow/initialize with signature
    """
    try:
        result = await use_case.execute(user_id=current_user.id)
        
        return PrepareInitializeResponse(
            transaction=result.transaction,
            token_mint=result.token_mint,
        )
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except EscrowAlreadyInitializedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except BlockchainError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to prepare initialize: {str(e)}",
        )
```

**Add schema:**
```python
class PrepareInitializeResponse(BaseModel):
    """Response for prepare initialize escrow."""
    
    transaction: str = Field(
        ...,
        description="Unsigned transaction (base64) for user to sign",
    )
    token_mint: str = Field(
        ...,
        description="Token mint address (USDC)",
    )
```

**Create use case:** `src/pourtier/application/use_cases/prepare_initialize_escrow.py`

**Passeur endpoint already exists:** `/escrow/prepare-initialize` (line 359 in passeur/bridge/server.js)

#### Frontend: Implement Initialize Flow

**Update:** `app/lib/application/services/escrow.service.ts`
```typescript
async initializeEscrow(): Promise<InitializeEscrowResult> {
  const walletAddress = this.walletProvider.getAddress()
  if (!walletAddress) {
    throw new Error('Wallet not connected')
  }

  // Check if already initialized
  const currentEscrow = await this.escrowRepository.getEscrowBalance(false)
  if (currentEscrow.isInitialized) {
    return {
      escrow: currentEscrow,
      txSignature: '',
    }
  }

  // Step 1: Prepare unsigned transaction
  const prepareResult = await this.escrowRepository.prepareInitializeEscrow()

  // Step 2: Sign transaction with wallet
  const signedTx = await this.walletProvider.signTransaction(
    prepareResult.transaction
  )

  // Step 3: Submit signed transaction to Pourtier
  await this.escrowRepository.submitInitializeEscrow(signedTx)

  // Step 4: Get updated escrow state
  const updatedEscrow = await this.escrowRepository.getEscrowBalance(true)

  return {
    escrow: updatedEscrow,
    txSignature: signedTx,
  }
}
```

**Add repository methods:**
```typescript
// app/lib/infrastructure/api/escrow.repository.ts

async prepareInitializeEscrow(): Promise<PrepareInitializeEscrowResponse> {
  const response = await this.apiClient.request<{
    transaction: string
    token_mint: string
  }>('/api/escrow/prepare-initialize', {
    method: 'POST',
  })

  return {
    transaction: response.transaction,
    tokenMint: response.token_mint,
  }
}

async submitInitializeEscrow(signedTx: string): Promise<InitializeEscrowResponse> {
  const response = await this.apiClient.request<{
    escrow_account: string
    balance: string
    token_mint: string
  }>('/api/escrow/initialize', {
    method: 'POST',
    body: JSON.stringify({
      tx_signature: signedTx,
    }),
  })

  return {
    escrowAccount: response.escrow_account,
    userId: '', // Not returned by API
    initializedAt: new Date().toISOString(),
  }
}
```

#### Tests for Initialize Flow

**Backend tests:** `tests/integration/test_escrow_prepare_initialize.py`

Similar structure to prepare-deposit tests:
1. Success case
2. Already initialized (409 Conflict)
3. Unauthenticated (403)
4. Passeur bridge failure (502)

---

## Current System State

### Working
- ✅ Backend: `/api/wallet/balance` endpoint returns wallet USDC balance
- ✅ Backend: `/api/escrow/balance` endpoint returns escrow status
- ✅ Backend: `/api/escrow/prepare-deposit` endpoint generates unsigned deposit transaction
- ✅ Backend: `/api/escrow/deposit` endpoint accepts signed transaction
- ✅ Frontend: Deposit modal shows wallet balance (10 USDC)
- ✅ Frontend: Full deposit flow implemented (prepare → sign → submit)
- ✅ Frontend: Transaction signing works in SolanaWalletProvider
- ✅ Passeur Bridge: All prepare methods exist and work

### Not Working
- ❌ Initialize escrow flow (missing prepare-initialize endpoint)
- ❌ Deposit fails because escrow not initialized
- ❌ No tests for new endpoints

### Database State
**User:** `kshy5yns5FGGXcFVfjT2fTzVsQLFnbZzL9zuh1ZKR2y`
- `escrow_account`: NULL ❌
- `escrow_balance`: 0.000000
- `escrow_token_mint`: NULL

**Needs:** Initialize escrow first

---

## Architecture Notes

### Deposit Flow (Complete)
```
1. User clicks "Deposit" with amount
   ↓
2. Frontend: EscrowService.depositToEscrow()
   ↓
3. Check if escrow initialized
   ↓ (if not initialized)
4. Initialize escrow (MISSING - implement tomorrow)
   ↓ (if initialized)
5. Frontend → POST /api/escrow/prepare-deposit
   ↓
6. Backend: PrepareDepositToEscrow use case
   ↓
7. Backend → Passeur: /escrow/prepare-deposit
   ↓
8. Passeur generates unsigned transaction
   ↓
9. Backend ← Passeur: returns base64 unsigned tx
   ↓
10. Frontend ← Backend: returns unsigned tx
   ↓
11. Frontend: wallet.signTransaction()
   ↓
12. User signs in Phantom wallet
   ↓
13. Frontend → POST /api/escrow/deposit (with signature)
   ↓
14. Backend: DepositToEscrow use case
   ↓
15. Backend: Verify transaction on Solana
   ↓
16. Backend: Update user's escrow_balance in DB
   ↓
17. Frontend ← Backend: Success response
   ↓
18. Frontend: Refresh escrow balance
```

### Initialize Flow (To Be Implemented)
```
1. User attempts first deposit
   ↓
2. Frontend detects escrow not initialized
   ↓
3. Frontend → POST /api/escrow/prepare-initialize
   ↓
4. Backend → Passeur: /escrow/prepare-initialize
   ↓
5. Passeur generates unsigned init transaction
   ↓
6. Frontend ← Backend: unsigned transaction
   ↓
7. Frontend: wallet.signTransaction()
   ↓
8. User signs in Phantom wallet
   ↓
9. Frontend → POST /api/escrow/initialize (with signature)
   ↓
10. Backend: Verify transaction on Solana
   ↓
11. Backend: Update user's escrow_account in DB
   ↓
12. Frontend: Continue with deposit
```

---

## Files Modified Today

### Backend
```
~/lumiere/lumiere-backend/pourtier/
├── src/pourtier/application/use_cases/
│   └── prepare_deposit_to_escrow.py                  [NEW]
├── src/pourtier/di/
│   └── dependencies.py                               [MODIFIED - added get_prepare_deposit_to_escrow]
├── src/pourtier/presentation/api/routes/
│   └── escrow.py                                     [MODIFIED - added /prepare-deposit endpoint]
└── src/pourtier/presentation/schemas/
    └── escrow_schemas.py                             [MODIFIED - added PrepareDepositRequest/Response]
```

### Frontend
```
~/lumiere/lumiere-frontend/
├── app/lib/application/services/
│   └── escrow.service.ts                             [MODIFIED - implemented depositToEscrow]
├── app/lib/domain/interfaces/
│   ├── escrow.repository.interface.ts                [MODIFIED - added prepareDeposit, submitDeposit]
│   └── wallet.provider.interface.ts                  [MODIFIED - added signTransaction]
├── app/lib/infrastructure/api/
│   ├── escrow.repository.ts                          [MODIFIED - implemented new methods]
│   └── passeur.repository.ts                         [DELETED]
├── app/lib/infrastructure/di/
│   └── container.ts                                  [MODIFIED - removed passeurRepository]
└── app/lib/infrastructure/wallet/
    └── solana-wallet-provider.ts                     [MODIFIED - implemented signTransaction]
```

---

## Key Decisions Made

1. **Architecture:** Frontend no longer talks directly to Passeur. All blockchain operations go through Pourtier API Gateway.

2. **Transaction Signing:** Implemented proper base64 handling with support for both `Transaction` and `VersionedTransaction` formats.

3. **Two-Step Flow:** Prepare (unsigned) → Sign (wallet) → Submit (signed). This is proper non-custodial design where backend never sees private keys.

4. **Initialize on First Deposit:** When user attempts deposit without initialized escrow, automatically trigger initialize flow first.

---

## Testing Checklist for Tomorrow

- [ ] Write integration tests for `/api/escrow/prepare-deposit`
- [ ] Write unit tests for `PrepareDepositToEscrow` use case
- [ ] Test all error cases (401, 400, 404, 409, 502)
- [ ] Test Passeur bridge mocking
- [ ] Implement `/api/escrow/prepare-initialize` endpoint
- [ ] Write use case `PrepareInitializeEscrow`
- [ ] Write integration tests for prepare-initialize
- [ ] Update frontend to call prepare-initialize
- [ ] End-to-end test: Initialize → Deposit flow
- [ ] Verify database updates correctly
- [ ] Test with real Phantom wallet on devnet

---

## Commands for Tomorrow's AI

### Run existing tests
```bash
cd ~/lumiere/lumiere-backend/pourtier
make test
```

### Create new test file
```bash
cd ~/lumiere/lumiere-backend/pourtier
touch tests/integration/test_escrow_prepare_deposit.py
touch tests/unit/test_prepare_deposit_to_escrow.py
```

### Check test coverage
```bash
make coverage
```

### Rebuild and restart services
```bash
cd ~/lumiere/lumiere-backend
docker build -f pourtier/Dockerfile --target development -t pourtier:development .
docker-compose -f docker-compose.development.yaml restart pourtier
```

---

## Notes

- Development backend runs on port 9000 and is publicly accessible as `https://api.lumiere.trade`
- Frontend is deployed on Vercel at `https://app.lumiere.trade`
- CORS is properly configured to allow frontend origin
- All code follows Clean Architecture with proper separation of concerns
- No emojis in code (per project standards)
- Tests use Laborant framework, not pytest
- Test coverage target: 98%+

---

**End of TODO Document**
