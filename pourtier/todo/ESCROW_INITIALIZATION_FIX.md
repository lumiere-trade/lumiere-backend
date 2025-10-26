# Escrow Balance Endpoint Fix - Implementation Guide

## Problem Statement

**Current Behavior:**
When user attempts to deposit funds but doesn't have initialized escrow, the `/api/escrow/balance` endpoint returns `400 Bad Request`:
```
Validation failed for escrow_account: Escrow not initialized for user
```

**Expected Behavior:**
Endpoint should return `200 OK` with `is_initialized: false`, allowing frontend to automatically trigger escrow initialization.

## Root Cause

**File:** `pourtier/src/pourtier/application/use_cases/get_escrow_balance.py` (lines 64-68)
```python
# Current problematic code
if not user.escrow_account:
    raise ValidationError(
        field="escrow_account",
        reason="Escrow not initialized for user",
    )
```

The use case throws an error instead of returning status information.

## Solution Overview

Change the return type from `Decimal` to `EscrowBalanceResult` dataclass that includes initialization status. This allows the frontend to distinguish between "needs initialization" vs "actual error".

## Files to Modify

1. `src/pourtier/domain/entities/user.py` - Add `escrow_initialized_at` field
2. `src/pourtier/application/use_cases/get_escrow_balance.py` - Change return type & logic
3. `src/pourtier/presentation/schemas/escrow_schemas.py` - Update response schema
4. `src/pourtier/presentation/api/routes/escrow.py` - Update route handler
5. `src/pourtier/infrastructure/persistence/models.py` - Add DB column
6. `alembic/versions/XXXX_*.py` - Create migration
7. `tests/unit/application/test_get_escrow_balance.py` - Update tests

## Implementation Steps

### Step 1: Add escrow_initialized_at to User Entity

**File:** `src/pourtier/domain/entities/user.py`
```python
@dataclass
class User:
    id: UUID = field(default_factory=uuid4)
    wallet_address: str = field(default="")
    escrow_account: Optional[str] = field(default=None)
    escrow_balance: Decimal = field(default=Decimal("0"))
    escrow_token_mint: Optional[str] = field(default=None)
    escrow_initialized_at: Optional[datetime] = field(default=None)  # ADD THIS
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
```

Update `initialize_escrow()` method:
```python
def initialize_escrow(
    self,
    escrow_account: str,
    token_mint: str = "USDC",
) -> None:
    if self.escrow_account:
        raise ValueError("Escrow already initialized")
    
    self.escrow_account = escrow_account
    self.escrow_token_mint = token_mint
    self.escrow_balance = Decimal("0")
    self.escrow_initialized_at = datetime.now()  # ADD THIS
    self.updated_at = datetime.now()
```

### Step 2: Create EscrowBalanceResult Dataclass

**File:** `src/pourtier/application/use_cases/get_escrow_balance.py`

Add at top of file:
```python
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class EscrowBalanceResult:
    """Result of escrow balance query."""
    
    escrow_account: Optional[str]
    balance: Decimal
    token_mint: str
    is_initialized: bool
    initialized_at: Optional[datetime]
    last_synced_at: Optional[datetime]
```

### Step 3: Update GetEscrowBalance Use Case

**File:** `src/pourtier/application/use_cases/get_escrow_balance.py`

Change method signature:
```python
async def execute(
    self,
    user_id: UUID,
    sync_from_blockchain: bool = False,
) -> EscrowBalanceResult:  # Changed from -> Decimal
```

Replace the validation logic (lines 64-68):
```python
# OLD - DO NOT USE:
if not user.escrow_account:
    raise ValidationError(
        field="escrow_account",
        reason="Escrow not initialized for user",
    )

# NEW - USE THIS:
is_initialized = bool(user.escrow_account)

# Optionally sync from blockchain if initialized
last_synced = None
if is_initialized and sync_from_blockchain:
    blockchain_balance = await self.escrow_query_service.get_escrow_balance(
        user.escrow_account
    )
    
    if blockchain_balance != user.escrow_balance:
        user.update_escrow_balance(blockchain_balance)
        await self.user_repository.update(user)
    
    last_synced = datetime.utcnow()

# Return structured result
return EscrowBalanceResult(
    escrow_account=user.escrow_account,
    balance=user.escrow_balance if is_initialized else Decimal("0.00"),
    token_mint=user.escrow_token_mint if user.escrow_token_mint else "USDC",
    is_initialized=is_initialized,
    initialized_at=user.escrow_initialized_at if is_initialized else None,
    last_synced_at=last_synced if sync_from_blockchain else None,
)
```

### Step 4: Update Response Schema

**File:** `src/pourtier/presentation/schemas/escrow_schemas.py`
```python
class BalanceResponse(BaseModel):
    """Response schema for escrow balance."""

    escrow_account: Optional[str] = Field(
        None,
        description="Escrow PDA address (null if not initialized)",
    )
    balance: Decimal = Field(..., description="Current escrow balance")
    token_mint: str = Field(..., description="Token mint address")
    is_initialized: bool = Field(
        ...,
        description="Whether escrow account is initialized",
    )
    initialized_at: Optional[datetime] = Field(
        None,
        description="When escrow was initialized",
    )
    synced_from_blockchain: bool = Field(
        ...,
        description="Whether balance was synced from blockchain",
    )
    last_synced_at: Optional[datetime] = Field(
        None,
        description="When balance was last synced from blockchain",
    )

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
        }
```

### Step 5: Update API Route

**File:** `src/pourtier/presentation/api/routes/escrow.py`
```python
@router.get(
    "/balance",
    response_model=BalanceResponse,
    summary="Get escrow balance",
)
async def get_escrow_balance(
    sync: bool = False,
    current_user: User = Depends(get_current_user),
    use_case: GetEscrowBalance = Depends(get_get_escrow_balance),
):
    """Get current escrow balance."""
    try:
        result = await use_case.execute(
            user_id=current_user.id,
            sync_from_blockchain=sync,
        )

        return BalanceResponse(
            escrow_account=result.escrow_account,
            balance=result.balance,
            token_mint=result.token_mint,
            is_initialized=result.is_initialized,
            initialized_at=result.initialized_at,
            synced_from_blockchain=sync,
            last_synced_at=result.last_synced_at,
        )

    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except BlockchainError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Blockchain error: {str(e)}",
        )
```

**IMPORTANT:** Remove `ValidationError` from exception handling.

### Step 6: Update Database Model

**File:** `src/pourtier/infrastructure/persistence/models.py`

Add column:
```python
class UserModel(Base):
    __tablename__ = "users"
    
    # ... existing fields ...
    
    escrow_initialized_at = Column(DateTime, nullable=True)
```

Update `to_entity()`:
```python
def to_entity(self) -> User:
    return User(
        id=self.id,
        wallet_address=self.wallet_address,
        escrow_account=self.escrow_account,
        escrow_balance=self.escrow_balance,
        escrow_token_mint=self.escrow_token_mint,
        escrow_initialized_at=self.escrow_initialized_at,  # ADD THIS
        created_at=self.created_at,
        updated_at=self.updated_at,
    )
```

Update `from_entity()`:
```python
@classmethod
def from_entity(cls, user: User) -> "UserModel":
    return cls(
        id=user.id,
        wallet_address=user.wallet_address,
        escrow_account=user.escrow_account,
        escrow_balance=user.escrow_balance,
        escrow_token_mint=user.escrow_token_mint,
        escrow_initialized_at=user.escrow_initialized_at,  # ADD THIS
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
```

### Step 7: Create Database Migration
```bash
cd ~/lumiere/lumiere-backend/pourtier
alembic revision -m "add_escrow_initialized_at_to_users"
```

Edit the generated migration file:
```python
def upgrade():
    op.add_column(
        'users',
        sa.Column(
            'escrow_initialized_at',
            sa.DateTime(),
            nullable=True,
        )
    )
    
    # Backfill for existing users with escrow accounts
    op.execute("""
        UPDATE users 
        SET escrow_initialized_at = created_at 
        WHERE escrow_account IS NOT NULL 
        AND escrow_initialized_at IS NULL
    """)


def downgrade():
    op.drop_column('users', 'escrow_initialized_at')
```

Run migration:
```bash
alembic upgrade head
```

### Step 8: Update Unit Tests

**File:** `tests/unit/application/test_get_escrow_balance.py`

Change imports:
```python
from pourtier.application.use_cases.get_escrow_balance import (
    EscrowBalanceResult,  # ADD THIS
    GetEscrowBalance,
)
from pourtier.domain.exceptions import EntityNotFoundError  # Remove ValidationError
```

Update all test assertions from:
```python
assert result == expected_balance
```

To:
```python
assert isinstance(result, EscrowBalanceResult)
assert result.balance == expected_balance
assert result.is_initialized is True
assert result.escrow_account == escrow_account
```

**Critical test change - `test_get_balance_escrow_not_initialized`:**

OLD (throws error):
```python
try:
    await use_case.execute(user_id=user_id)
    assert False, "Should raise ValidationError"
except ValidationError as e:
    assert "Escrow not initialized" in str(e)
```

NEW (returns status):
```python
result = await use_case.execute(user_id=user_id)

assert isinstance(result, EscrowBalanceResult)
assert result.balance == Decimal("0")
assert result.is_initialized is False
assert result.escrow_account is None
```

## Testing

Run unit tests:
```bash
cd ~/lumiere/lumiere-backend
laborant test pourtier --unit
```

Expected: All tests pass (213/213)

Run integration tests:
```bash
laborant test pourtier --integration
```

## Deployment

### Development Environment
```bash
# Run migration
cd ~/lumiere/lumiere-backend/pourtier
alembic upgrade head

# Restart service
sudo systemctl restart lumiere-dev
```

### Test Environment
```bash
# Restart test stack
sudo systemctl restart lumiere-test
```

### Production Environment
```bash
# Backup database first
pg_dump lumiere_db > backup_$(date +%Y%m%d).sql

# Run migration
alembic upgrade head

# Restart service
sudo systemctl restart lumiere
```

## Frontend Impact

After this fix, the frontend `DepositModal` will receive:
```typescript
{
  escrow_account: null,  // or PDA address if initialized
  balance: "0.00",
  token_mint: "USDC",
  is_initialized: false,  // NEW - can check this!
  initialized_at: null,
  synced_from_blockchain: false,
  last_synced_at: null
}
```

Frontend can now:
```typescript
const balance = await escrowRepository.getEscrowBalance(false)

if (!balance.isInitialized) {
  // Automatically trigger initialization
  await escrowService.initializeEscrow()
}
```

## Rollback Plan

If issues occur:
```bash
# Rollback migration
alembic downgrade -1

# Revert code changes
git revert <commit-hash>

# Restart services
sudo systemctl restart lumiere-dev
```

## Success Criteria

- [ ] All unit tests pass (213/213)
- [ ] All integration tests pass
- [ ] E2E test passes
- [ ] Frontend deposit works without "escrow not initialized" error
- [ ] Existing initialized users unaffected
- [ ] New users can complete first deposit smoothly

---

**Document Version:** 1.0  
**Created:** 2024-10-26  
**Status:** Ready for Implementation
