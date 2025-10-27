# TODO: Add Wallet Balance Endpoint

**Priority:** High  
**Component:** Pourtier API Gateway  
**Affected:** Frontend Deposit Modal  
**Created:** 2025-10-27

---

## Problem

Frontend deposit modal needs to show user's **wallet balance** (USDC in Phantom wallet), but Pourtier only has `/api/escrow/balance` endpoint which shows escrow balance.

Currently frontend tries to call `/api/wallet/balance` which returns **404**.

**Error in Production:**
```
Failed to load resource: the server responded with a status of 404
api.lumiere.trade/wallet/balance?wallet=kshy5yns5FGGXcFVfjT2fTzVsQLFnbZzL9zuh1ZKR2y
```

---

## Required Solution

Add new endpoint in Pourtier that proxies to Passeur for wallet balance:
```
GET /api/wallet/balance
```

**Flow:**
```
Frontend → Pourtier → Passeur → Solana RPC
   ↓         ↓          ↓          ↓
Request   Proxy     Query      Balance
```

---

## Implementation Steps

### 1. Create Use Case

**File:** `src/pourtier/application/use_cases/get_wallet_balance.py`
```python
"""
Get Wallet Balance use case.
Retrieves user's USDC balance from their Solana wallet (not escrow).
"""

from dataclasses import dataclass
from decimal import Decimal

from pourtier.domain.exceptions import ValidationError
from pourtier.domain.services.i_passeur_service import IPasseurService


@dataclass
class WalletBalanceResult:
    """
    Result of wallet balance query.
    
    Attributes:
        wallet_address: User's Solana wallet address
        balance: USDC balance in wallet
        token_mint: USDC token mint address
    """
    wallet_address: str
    balance: Decimal
    token_mint: str


class GetWalletBalance:
    """
    Get user's wallet USDC balance.
    
    Business rules:
    - Queries Passeur which queries Solana RPC
    - Returns actual wallet balance, not escrow balance
    - Used for deposit modal "Available" display
    """
    
    def __init__(self, passeur_service: IPasseurService):
        """
        Initialize use case with dependencies.
        
        Args:
            passeur_service: Service for querying Passeur bridge
        """
        self.passeur_service = passeur_service
    
    async def execute(self, wallet_address: str) -> WalletBalanceResult:
        """
        Execute get wallet balance.
        
        Args:
            wallet_address: Solana wallet address to query
            
        Returns:
            WalletBalanceResult with balance
            
        Raises:
            ValidationError: If wallet address invalid
        """
        if not wallet_address or len(wallet_address) < 32:
            raise ValidationError("Invalid wallet address")
        
        # Query Passeur for wallet balance
        balance = await self.passeur_service.get_wallet_balance(wallet_address)
        
        return WalletBalanceResult(
            wallet_address=wallet_address,
            balance=balance,
            token_mint="USDC",  # Hardcoded for now
        )
```

### 2. Create Passeur Service Interface (if not exists)

**File:** `src/pourtier/domain/services/i_passeur_service.py`
```python
"""
Passeur Service Interface (Port).
Defines contract for interacting with Passeur bridge.
"""

from abc import ABC, abstractmethod
from decimal import Decimal


class IPasseurService(ABC):
    """
    Interface for Passeur bridge operations.
    
    Infrastructure layer implements this to call Passeur HTTP API.
    """
    
    @abstractmethod
    async def get_wallet_balance(self, wallet_address: str) -> Decimal:
        """
        Get USDC balance for wallet address.
        
        Args:
            wallet_address: Solana wallet address
            
        Returns:
            USDC balance as Decimal
            
        Raises:
            NetworkError: If Passeur unavailable
        """
        pass
```

### 3. Implement Passeur Service

**File:** `src/pourtier/infrastructure/services/passeur_service.py`
```python
"""
Passeur Service Implementation (Adapter).
Calls Passeur HTTP API for blockchain operations.
"""

import httpx
from decimal import Decimal

from pourtier.config.settings import Settings
from pourtier.domain.exceptions import NetworkError
from pourtier.domain.services.i_passeur_service import IPasseurService


class PasseurService(IPasseurService):
    """
    Passeur service implementation using HTTP client.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize with settings.
        
        Args:
            settings: Application settings with PASSEUR_URL
        """
        self.passeur_url = settings.PASSEUR_URL
    
    async def get_wallet_balance(self, wallet_address: str) -> Decimal:
        """
        Get wallet USDC balance from Passeur.
        
        Args:
            wallet_address: Solana wallet address
            
        Returns:
            USDC balance
            
        Raises:
            NetworkError: If Passeur call fails
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.passeur_url}/wallet/balance",
                    params={"wallet": wallet_address},
                )
                response.raise_for_status()
                
                data = response.json()
                return Decimal(str(data["balance"]))
                
        except httpx.HTTPError as e:
            raise NetworkError(f"Failed to get wallet balance: {str(e)}")
```

### 4. Add API Route

**File:** `src/pourtier/presentation/api/routes/wallet.py` (NEW FILE)
```python
"""
Wallet API routes.

Provides endpoints for wallet operations:
- GET /wallet/balance - Get wallet USDC balance
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from pourtier.application.use_cases.get_wallet_balance import GetWalletBalance
from pourtier.di.dependencies import get_get_wallet_balance
from pourtier.domain.exceptions import ValidationError
from pourtier.presentation.schemas.wallet_schemas import WalletBalanceResponse

router = APIRouter(prefix="/wallet", tags=["Wallet"])


@router.get(
    "/balance",
    response_model=WalletBalanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get wallet balance",
    description="Get USDC balance in user's Solana wallet (not escrow)",
)
async def get_wallet_balance(
    wallet: str = Query(..., description="Solana wallet address"),
    use_case: GetWalletBalance = Depends(get_get_wallet_balance),
) -> WalletBalanceResponse:
    """
    Get wallet USDC balance.
    
    This returns the balance in the user's Solana wallet,
    NOT the escrow balance. Use /api/escrow/balance for escrow.
    
    Args:
        wallet: Solana wallet address to query
        use_case: GetWalletBalance use case (injected)
        
    Returns:
        Wallet balance details
        
    Raises:
        HTTPException: 400 if wallet address invalid
        HTTPException: 502 if Passeur unavailable
    """
    try:
        result = await use_case.execute(wallet_address=wallet)
        
        return WalletBalanceResponse(
            wallet_address=result.wallet_address,
            balance=str(result.balance),
            token_mint=result.token_mint,
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to get wallet balance: {str(e)}",
        )
```

### 5. Create Response Schema

**File:** `src/pourtier/presentation/schemas/wallet_schemas.py` (NEW FILE)
```python
"""
Wallet API schemas.
"""

from pydantic import BaseModel, Field


class WalletBalanceResponse(BaseModel):
    """
    Response for wallet balance query.
    
    Attributes:
        wallet_address: Solana wallet address
        balance: USDC balance (as string to preserve precision)
        token_mint: Token mint address (USDC)
    """
    
    wallet_address: str = Field(
        ...,
        description="Solana wallet address",
        example="kshy5yns5FGGXcFVfjT2fTzVsQLFnbZzL9zuh1ZKR2y",
    )
    balance: str = Field(
        ...,
        description="USDC balance",
        example="125.50",
    )
    token_mint: str = Field(
        ...,
        description="Token mint address",
        example="USDC",
    )
```

### 6. Register Route in Main App

**File:** `src/pourtier/main.py`

Add import:
```python
from pourtier.presentation.api.routes import wallet
```

Register router:
```python
app.include_router(wallet.router, prefix="/api")
```

### 7. Add DI Dependency

**File:** `src/pourtier/di/dependencies.py`
```python
def get_get_wallet_balance() -> GetWalletBalance:
    """Get GetWalletBalance use case."""
    container = get_container()
    return GetWalletBalance(
        passeur_service=container.passeur_service,
    )
```

### 8. Update DI Container

**File:** `src/pourtier/di/__init__.py`

Add PasseurService to container:
```python
@property
def passeur_service(self) -> PasseurService:
    """Get Passeur service."""
    if not self._passeur_service:
        settings = get_settings()
        self._passeur_service = PasseurService(settings)
    return self._passeur_service
```

---

## Testing

### Manual Test
```bash
# Start services
docker-compose -f docker-compose.development.yaml up -d

# Test endpoint
curl "http://localhost:9000/api/wallet/balance?wallet=kshy5yns5FGGXcFVfjT2fTzVsQLFnbZzL9zuh1ZKR2y"

# Expected response:
{
  "wallet_address": "kshy5yns5FGGXcFVfjT2fTzVsQLFnbZzL9zuh1ZKR2y",
  "balance": "125.50",
  "token_mint": "USDC"
}
```

### Unit Test
Create `tests/unit/application/test_get_wallet_balance.py`

### Integration Test
Create `tests/integration/api/test_wallet_routes.py`

---

## Frontend Changes (After Backend Complete)

Update `passeur.repository.ts` to call Pourtier instead:
```typescript
// OLD (direct to Passeur)
const balance = await fetch(`${passeurUrl}/wallet/balance?wallet=${address}`)

// NEW (through Pourtier)
const balance = await fetch(`${apiUrl}/api/wallet/balance?wallet=${address}`)
```

---

## Acceptance Criteria

- [ ] `GET /api/wallet/balance?wallet={address}` endpoint works
- [ ] Returns USDC balance from Solana wallet
- [ ] Proper error handling (400 for invalid wallet, 502 for Passeur errors)
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Frontend deposit modal shows correct wallet balance
- [ ] No more 404 errors in production console

---

## Notes

- This is **wallet balance**, not escrow balance
- Used specifically for deposit modal "Available: X USDC"
- Passeur already has `/wallet/balance` endpoint, we just proxy it
- Follow existing patterns from `/api/escrow/balance` implementation

---

**Related Files:**
- Frontend: `app/lib/infrastructure/api/passeur.repository.ts`
- Frontend: `app/lib/application/services/escrow.service.ts` (getWalletBalance method)
