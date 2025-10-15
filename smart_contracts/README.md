# Smart Contracts - Solana Escrow Programs

**Non-custodial escrow smart contracts for secure fund management on Solana.**

---

## Overview

Lumiere's escrow smart contracts provide non-custodial fund management on Solana blockchain. Users maintain full ownership of their funds while delegating specific authorities for trading and subscription payments.

**Framework:** Anchor (Solana's framework for building secure programs)

**Language:** Rust

**Network:** Solana (Devnet for testing, Mainnet for production)

---

## Architecture

### Dual Authority Model
```
User Wallet (Owner)
    │
    ├──► Platform Authority (Pourtier)
    │    └── Subscription fees only
    │        Max: 1,000 USDC/month
    │
    └──► Trading Authority (Chevalier)
         └── Trade execution only
             Max: 100,000 USDC/transaction
```

**Key Principle:** User retains ownership, delegates limited permissions.

---

## Escrow Account Structure

### PDA Derivation
```
seeds: ["escrow", user_pubkey]
```

One escrow per user (no strategy_id in PDA).

### State Fields
```rust
pub struct EscrowAccount {
    // Ownership
    pub user: Pubkey,                    // Escrow owner
    pub platform_authority: Pubkey,      // Pourtier (subscriptions)
    pub trading_authority: Pubkey,       // Chevalier (trading)
    
    // Configuration
    pub token_mint: Pubkey,              // USDC mint
    pub bump: u8,                        // PDA bump seed
    pub flags: u8,                       // Status flags
    
    // Timestamps
    pub created_at: i64,
    pub platform_activated_at: i64,
    pub trading_activated_at: i64,
    pub last_paused_at: i64,
    
    // Security
    pub action_nonce: u64,               // Replay protection
    
    // Analytics
    pub total_deposited: u64,
    pub total_withdrawn: u64,
    pub total_fees_paid: u64,            // Subscription payments
    pub total_traded: u64,               // Trading volume
    
    // Limits
    pub max_balance: u64,
    pub max_lifetime: i64,
}
```

---

## Instructions

### User Operations (Owner Only)

**Initialize Escrow**
```rust
initialize_escrow(bump, max_balance)
```
- Creates escrow PDA
- Creates associated token account
- Sets max balance limit

**Deposit Tokens**
```rust
deposit_token(amount)
```
- Transfer USDC to escrow
- Updates total_deposited
- Checks max_balance limit

**Withdraw Tokens**
```rust
withdraw_token(amount)
```
- Owner-only withdrawal
- Requires NO active authorities
- Must revoke authorities first

**Emergency Withdraw**
```rust
emergency_withdraw(amount)
```
- Works in paused state
- Requires NO active authorities
- Emergency exit mechanism

**Delegate Platform Authority**
```rust
delegate_platform_authority(authority_pubkey)
```
- Grants Pourtier subscription rights
- Can only be set once
- 5-minute time-lock before use

**Delegate Trading Authority**
```rust
delegate_trading_authority(authority_pubkey)
```
- Grants Chevalier trading rights
- Can only be set once
- 5-minute time-lock before use

**Revoke Platform Authority**
```rust
revoke_platform_authority()
```
- Removes subscription permissions
- Immediate effect

**Revoke Trading Authority**
```rust
revoke_trading_authority()
```
- Removes trading permissions
- Immediate effect

**Pause/Unpause Escrow**
```rust
pause_escrow()
unpause_escrow()
```
- Disables all operations
- 5-minute cooldown before unpause

**Close Escrow**
```rust
close_escrow()
```
- Recovers rent
- Requires balance ≤ 10 (dust threshold)
- Requires NO active authorities

---

### Platform Operations (Pourtier Only)

**Withdraw Subscription Fee**
```rust
withdraw_subscription_fee(amount)
```
- Platform authority only
- Max: 1,000 USDC per call
- 5-minute time-lock enforced
- Updates total_fees_paid

---

### Trading Operations (Chevalier Only)

**Withdraw for Trade**
```rust
withdraw_for_trade(amount)
```
- Trading authority only
- Max: 100,000 USDC per call
- 5-minute time-lock enforced
- Updates total_traded

---

## Security Features

### Time-Locks

**Authority Delegation:** 5-minute delay before use
```rust
const MIN_AUTHORITY_AGE: i64 = 300; // seconds
```

**Purpose:** Prevents instant authority abuse after delegation.

**Unpause Cooldown:** 5-minute wait after pause
```rust
const UNPAUSE_COOLDOWN: i64 = 300; // seconds
```

**Purpose:** Prevents rapid pause/unpause attacks.

### Transaction Limits

**Subscription Fee:** 1,000 USDC max
```rust
const MAX_SUBSCRIPTION_FEE: u64 = 1_000_000_000; // 6 decimals
```

**Trade Amount:** 100,000 USDC max
```rust
const MAX_TRANSACTION_AMOUNT: u64 = 100_000_000_000;
```

**Escrow Balance:** 10M USDC max
```rust
const MAX_ALLOWED_BALANCE: u64 = 10_000_000_000_000;
```

### Replay Protection

**Action Nonce:** Increments on every state change
```rust
pub action_nonce: u64
```

Prevents transaction replay attacks.

### CEI Pattern

All instructions follow **Checks-Effects-Interactions** pattern:
1. Validate inputs and permissions
2. Update state
3. Execute token transfers

Prevents reentrancy attacks.

---

## Events

All state changes emit events for off-chain monitoring:
```rust
EscrowInitialized
TokenDeposit
TokenWithdraw
PlatformAuthorityDelegated
TradingAuthorityDelegated
PlatformAuthorityRevoked
TradingAuthorityRevoked
SubscriptionFeeWithdraw
TradeWithdraw
EscrowPaused
EscrowUnpaused
EscrowClosed
```

---

## Installation

### Prerequisites
```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install Solana CLI
sh -c "$(curl -sSfL https://release.solana.com/stable/install)"

# Install Anchor
cargo install --git https://github.com/coral-xyz/anchor avm --locked
avm install latest
avm use latest
```

### Build
```bash
cd smart_contracts

# Build program
anchor build

# Run tests
anchor test
```

---

## Deployment

### Devnet
```bash
# Set network
solana config set --url devnet

# Get devnet SOL
solana airdrop 2

# Deploy
anchor deploy
```

### Mainnet
```bash
# Set network
solana config set --url mainnet-beta

# Deploy (requires SOL for rent)
anchor deploy
```

---

## Program ID

**Current Program ID:**
```
9gvUtaF99sQ287PNzRfCbhFTC4PUnnd7jdAjnY5GUVhS
```

Update in `lib.rs` after deployment:
```rust
declare_id!("YourNewProgramID");
```

---

## Testing

### Unit Tests
```bash
# Run Rust tests
cargo test

# With output
cargo test -- --nocapture
```

### Integration Tests
```bash
# Run Anchor tests
anchor test

# Skip deployment (use existing)
anchor test --skip-deploy
```

---

## Project Structure
```
smart_contracts/
├── programs/
│   └── escrow/
│       ├── src/
│       │   ├── lib.rs          # Main program logic
│       │   ├── state.rs        # Account structures
│       │   ├── errors.rs       # Error definitions
│       │   ├── events.rs       # Event definitions
│       │   └── constants.rs    # Constants and limits
│       └── Cargo.toml
├── tests/
│   └── escrow.ts              # TypeScript integration tests
├── migrations/
│   └── deploy.ts              # Deployment script
├── Anchor.toml                # Anchor config
└── package.json               # Node dependencies
```

---

## Security Considerations

### Audits

- **Status:** Not yet audited
- **Focus areas:** Authority delegation, time-locks, limits

### Known Limitations

- Authority can only be delegated once (cannot change)
- 5-minute time-lock applies to all authority operations
- Max balance enforced at contract level

### Best Practices

- Always test on devnet first
- Start with low max_balance limits
- Monitor events for suspicious activity
- Revoke authorities when not needed

---

## API Integration

See [Passeur](../passeur) for Python integration with escrow contracts.

Example:
```python
from passeur.bridge import PasseurBridgeClient

client = PasseurBridgeClient(url="http://localhost:8767")

# Initialize escrow
result = await client.initialize_escrow(
    user_wallet="user_pubkey",
    token_mint="USDC_mint"
)

# Deposit funds
await client.deposit(
    escrow_account="escrow_pda",
    amount=1000_000000  # 1000 USDC
)
```

---

## Constants Reference
```rust
// Balance limits
DEFAULT_MAX_BALANCE: 1M USDC
MAX_ALLOWED_BALANCE: 10M USDC
MAX_TRANSACTION_AMOUNT: 100K USDC
DUST_THRESHOLD: 10 (0.00001 USDC)

// Security
MIN_AUTHORITY_AGE: 300 seconds (5 min)
UNPAUSE_COOLDOWN: 300 seconds (5 min)
TIMESTAMP_TOLERANCE: 30 seconds

// Token validation
MIN_TOKEN_DECIMALS: 6
MAX_TOKEN_DECIMALS: 9

// Subscription
MAX_SUBSCRIPTION_FEE: 1,000 USDC
```

---

## Related Components

- [Passeur](../passeur) - Blockchain bridge
- [Pourtier](../pourtier) - Platform authority
- [Shared](../shared) - Transaction utilities

---

## License

Apache License 2.0 - See [LICENSE](../LICENSE)

---

**Questions?** Open an issue or contact: dev@lumiere.trade

**Security Issues:** security@lumiere.trade
