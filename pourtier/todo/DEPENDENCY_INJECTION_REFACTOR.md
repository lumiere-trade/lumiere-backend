# Dependency Injection Refactor - Pourtier

## Problem

**Current State:**
Use case dependency functions in `src/pourtier/di/dependencies.py` get services directly from container instead of using `Depends()`:
```python
def get_initialize_escrow(session: AsyncSession = Depends(get_db_session)):
    container = get_container()
    passeur_bridge = container.passeur_bridge  # ❌ Direct from container
    escrow_query_service = container.escrow_query_service  # ❌ Direct from container
```

**Why This is Wrong:**
1. Bypasses FastAPI's dependency injection system
2. Cannot be overridden in tests via `app.dependency_overrides`
3. Creates tight coupling to container implementation
4. Breaks Clean Architecture principles

**Test Impact:**
Integration tests fail with DNS errors trying to connect to real `passeur:7766` because mock cannot be injected:
- `test_deposit_success` - DNS error
- `test_initialize_escrow_success` - DNS error  
- `test_withdraw_success` - DNS error
- `test_get_balance_with_sync` - Assertion failed (mock not applied)

**Result:** Only 7/11 integration tests pass

---

## Solution

Refactor all use case dependency functions to inject services via `Depends()`:
```python
def get_initialize_escrow(
    session: AsyncSession = Depends(get_db_session),
    passeur_bridge = Depends(get_passeur_bridge),  # ✅ Inject via Depends
    escrow_query_service = Depends(get_escrow_query_service),  # ✅ Inject via Depends
):
    container = get_container()
    user_repo = container.get_user_repository(session)
    escrow_tx_repo = container.get_escrow_transaction_repository(session)
    
    return InitializeEscrow(
        user_repository=user_repo,
        escrow_transaction_repository=escrow_tx_repo,
        passeur_bridge=passeur_bridge,  # Injected dependency
    )
```

---

## Affected Functions

All functions in `src/pourtier/di/dependencies.py` that use external services:

### 1. Functions using `passeur_bridge`:
- `get_initialize_escrow()`
- `get_deposit_to_escrow()`
- `get_withdraw_from_escrow()`
- `get_get_wallet_balance()`
- `get_prepare_initialize_escrow()`
- `get_prepare_deposit_to_escrow()`

### 2. Functions using `escrow_query_service`:
- `get_get_escrow_balance()`

### 3. Functions using `wallet_authenticator`:
- `get_login_user()`
- `get_verify_wallet_signature()`

---

## Refactor Steps

1. **Add `Depends()` parameters to use case functions:**
   - Add `passeur_bridge = Depends(get_passeur_bridge)` where needed
   - Add `escrow_query_service = Depends(get_escrow_query_service)` where needed
   - Add `wallet_auth = Depends(get_wallet_authenticator)` where needed

2. **Remove direct container access:**
   - Replace `container.passeur_bridge` with injected parameter
   - Replace `container.escrow_query_service` with injected parameter
   - Replace `container.get_wallet_authenticator()` with injected parameter

3. **Update tests:**
   - Verify `app.dependency_overrides` now works correctly
   - All 11 integration tests should pass

4. **Verify production code:**
   - No changes needed in routes (they already use `Depends()`)
   - Container still provides services for production
   - Only test mocking is improved

---

## Files to Change

### Primary:
- `src/pourtier/di/dependencies.py` - Add `Depends()` to 9 functions

### Verify (should not need changes):
- `src/pourtier/presentation/api/routes/escrow.py`
- `tests/integration/api/test_escrow_routes.py`

---

## Expected Outcome

After refactor:
- ✅ All 11/11 integration tests pass
- ✅ Mocks work correctly in tests
- ✅ No DNS errors
- ✅ Clean dependency injection architecture
- ✅ Production code unchanged (still uses container)

---

## Architecture Benefits

1. **Testability:** Easy to mock any service via `app.dependency_overrides`
2. **Flexibility:** Can swap implementations without changing use cases
3. **Clean Architecture:** Use cases don't know about container
4. **FastAPI Best Practice:** Follows framework conventions

---

## Priority: HIGH

This blocks proper integration testing and violates Clean Architecture principles.

**Estimated Time:** 30-45 minutes
**Risk:** LOW (only changes dependency injection, no business logic changes)

---

Date: 2025-10-29
Status: TODO
Created by: Vladimir
