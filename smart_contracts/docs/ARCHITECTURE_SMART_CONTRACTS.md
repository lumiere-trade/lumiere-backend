# Smart Contracts - Solana Escrow Programs

**Version:** 0.1.0
**Last Updated:** January 20, 2026
**Component Type:** Blockchain Smart Contracts (Solana/Anchor)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Core Components](#3-core-components)
4. [Security Model](#4-security-model)
5. [Instruction Reference](#5-instruction-reference)
6. [State Management](#6-state-management)
7. [Events & Monitoring](#7-events--monitoring)
8. [Deployment Guide](#8-deployment-guide)
9. [Integration Points](#9-integration-points)
10. [Testing Strategy](#10-testing-strategy)
11. [Troubleshooting Guide](#11-troubleshooting-guide)

---

## 1. Executive Summary

### 1.1 Purpose

Smart Contracts component provides **non-custodial escrow programs** on Solana blockchain, enabling secure fund management with dual authority delegation for trading and subscription payments while maintaining user ownership.

### 1.2 Key Capabilities

- **Non-Custodial Design**: Users retain full ownership, delegate limited permissions
- **Dual Authority Model**: Separate authorities for platform (subscriptions) and trading
- **Time-Lock Security**: 5-minute activation delay for delegated authorities
- **Transaction Limits**: Per-operation caps to prevent abuse
- **Emergency Controls**: Pause/unpause with cooldown, emergency withdrawal
- **Replay Protection**: Nonce-based transaction ordering
- **Event Emission**: Complete audit trail via on-chain events
- **Rent Recovery**: Close accounts and recover SOL rent

### 1.3 Security Features

| Feature | Implementation | Purpose |
|---------|---------------|---------|
| Time-Locks | 5-minute delay | Prevent instant authority abuse |
| Transaction Limits | Max 100K USDC/trade | Limit exposure per operation |
| Nonce Protection | Incrementing counter | Prevent replay attacks |
| CEI Pattern | Checks-Effects-Interactions | Prevent reentrancy |
| Pause Mechanism | Owner-controlled | Emergency shutdown |
| Dual Authority | Separate roles | Principle of least privilege |

### 1.4 Technology Stack

- **Framework**: Anchor 0.31.1 (Solana development framework)
- **Language**: Rust (smart contract logic)
- **Testing**: TypeScript + Mocha + Chai
- **Network**: Solana (Devnet/Mainnet-Beta)
- **Token Standard**: SPL Token (USDC, SOL)
- **Build Tool**: Cargo + Anchor CLI

---

## 2. System Architecture

### 2.1 High-Level Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                    Solana Blockchain Network                    │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │         Escrow Program (Deployed Smart Contract)          │ │
│  │         Program ID: 9gvUtaF99sQ287PNzRfCbhFTC4PUnnd7...   │ │
│  └───────────────────────────────────────────────────────────┘ │
│                          │                                      │
│                          │ Instructions                         │
│                          │                                      │
│         ┌────────────────┴────────────────┐                    │
│         │                                  │                    │
│    ┌────▼─────┐                      ┌────▼─────┐             │
│    │  User    │                      │ Platform │             │
│    │  Wallet  │                      │Authority │             │
│    │ (Owner)  │                      │(Pourtier)│             │
│    └────┬─────┘                      └────┬─────┘             │
│         │                                  │                    │
│         │ Owner Instructions:              │ Platform:          │
│         │ - initialize_escrow             │ - withdraw_        │
│         │ - deposit_token                 │   subscription_fee │
│         │ - delegate_authorities          │                    │
│         │ - revoke_authorities            │                    │
│         │ - pause/unpause                 │                    │
│         │ - withdraw_token                │                    │
│         │ - emergency_withdraw            │                    │
│         │ - close_escrow                  │                    │
│         │                                  │                    │
│         │                            ┌────▼─────┐             │
│         │                            │ Trading  │             │
│         │                            │Authority │             │
│         │                            │(Chevalier│             │
│         │                            └────┬─────┘             │
│         │                                  │                    │
│         │                                  │ Trading:           │
│         │                                  │ - withdraw_for_    │
│         │                                  │   trade            │
│         │                                  │                    │
│  ┌──────▼──────────────────────────────────▼─────────────────┐ │
│  │                 Escrow Account (PDA)                      │ │
│  │  Seeds: ["escrow", user_pubkey]                          │ │
│  │                                                           │ │
│  │  State:                                                   │ │
│  │  - user: Pubkey                    (owner)               │ │
│  │  - platform_authority: Pubkey      (Pourtier)            │ │
│  │  - trading_authority: Pubkey       (Chevalier)           │ │
│  │  - token_mint: Pubkey              (USDC)                │ │
│  │  - flags: u8                       (status bits)          │ │
│  │  - timestamps: i64                 (activation times)     │ │
│  │  - action_nonce: u64               (replay protection)    │ │
│  │  - analytics: u64                  (deposits/withdrawals) │ │
│  │  - limits: u64                     (max_balance)          │ │
│  └───────────────────────────────────────────────────────────┘ │
│                          │                                      │
│                          │ Owns                                 │
│                          │                                      │
│  ┌───────────────────────▼───────────────────────────────────┐ │
│  │        Associated Token Account (ATA)                     │ │
│  │        Authority: Escrow PDA                              │ │
│  │        Mint: USDC                                         │ │
│  │        Balance: User's deposited funds                    │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                          │
                          │ Events
                          │
                ┌─────────▼──────────┐
                │  Transaction Logs  │
                │  (Indexable Events)│
                │                    │
                │  - EscrowInitialized│
                │  - TokenDeposit    │
                │  - AuthorityDelegated│
                │  - TradeWithdraw   │
                │  - EscrowPaused    │
                │  ... etc           │
                └────────────────────┘
                          │
                          │ Consumed by
                          │
                ┌─────────▼──────────┐
                │     Passeur        │
                │  (Event Indexer)   │
                │  Bridge to Backend │
                └────────────────────┘
```

### 2.2 PDA Architecture

**Program Derived Address (PDA) Strategy:**
```rust
// One escrow per user (no strategy_id)
seeds = ["escrow", user_pubkey]

// Example:
User: 8c53d17b-da2e-4284-8a3b-25e5cd510c83
PDA:  Esc7RowPDA1User8c53d17bda2e42848a3b...
```

**Key Decision:** Single escrow per user simplifies architecture and reduces rent costs.

### 2.3 Authority Model
```
┌────────────────────────────────────────────────────────────┐
│                    User (Owner)                            │
│              Full Control at All Times                     │
└─────┬──────────────────────────────────────────────────────┘
      │
      │ Delegates (optional)
      │
      ├─────────────────────────┬──────────────────────────────┐
      │                         │                              │
┌─────▼─────────────┐  ┌────────▼────────────┐  ┌───────────▼──────────┐
│ Platform Authority│  │ Trading Authority   │  │  No Authority        │
│   (Pourtier)      │  │   (Chevalier)       │  │  (User-only mode)    │
└───────────────────┘  └─────────────────────┘  └──────────────────────┘
│                      │                         │
│ Permissions:         │ Permissions:            │ Permissions:
│ - Subscription fees  │ - Execute trades        │ - Deposit
│   (max 1K USDC)     │   (max 100K USDC)       │ - Withdraw
│ - Monthly billing   │ - Trade execution       │ - Close escrow
│                      │   only                  │
│ Time-lock: 5 min    │ Time-lock: 5 min        │ Time-lock: None
│ Can revoke: Yes     │ Can revoke: Yes         │ Can delegate: Yes
└─────────────────────┴─────────────────────────┴──────────────────────┘
```

---

## 3. Core Components

### 3.1 State Structure (state.rs)

#### 3.1.1 EscrowAccount

**Purpose**: Main account storing escrow state and permissions.
```rust
#[account]
pub struct EscrowAccount {
    // === OWNERSHIP (96 bytes) ===
    pub user: Pubkey,                    // 32 bytes - Escrow owner
    pub platform_authority: Pubkey,      // 32 bytes - Pourtier
    pub trading_authority: Pubkey,       // 32 bytes - Chevalier
    
    // === CONFIGURATION (34 bytes) ===
    pub token_mint: Pubkey,              // 32 bytes - USDC mint
    pub bump: u8,                        // 1 byte - PDA bump
    pub flags: u8,                       // 1 byte - Status flags
    
    // === TIMESTAMPS (40 bytes) ===
    pub created_at: i64,                 // 8 bytes - Creation time
    pub platform_activated_at: i64,      // 8 bytes - Platform delegation time
    pub trading_activated_at: i64,       // 8 bytes - Trading delegation time
    pub last_paused_at: i64,             // 8 bytes - Last pause time
    
    // === SECURITY (8 bytes) ===
    pub action_nonce: u64,               // 8 bytes - Replay protection
    
    // === ANALYTICS (32 bytes) ===
    pub total_deposited: u64,            // 8 bytes - Lifetime deposits
    pub total_withdrawn: u64,            // 8 bytes - Lifetime withdrawals
    pub total_fees_paid: u64,            // 8 bytes - Subscription fees paid
    pub total_traded: u64,               // 8 bytes - Trading volume
    
    // === LIMITS (16 bytes) ===
    pub max_balance: u64,                // 8 bytes - Max allowed balance
    pub max_lifetime: i64,               // 8 bytes - Expiration time (0 = never)
    
    // === RESERVED (176 bytes) ===
    pub reserved: [u8; 176],             // Future upgrades
}

// Total: 8 (discriminator) + 402 (data) = 410 bytes
```

**Space Calculation:**
```rust
pub const INIT_SPACE: usize = 
    32 +    // user
    32 +    // platform_authority
    32 +    // trading_authority
    32 +    // token_mint
    1 +     // bump
    1 +     // flags
    8 +     // created_at
    8 +     // platform_activated_at
    8 +     // trading_activated_at
    8 +     // last_paused_at
    8 +     // action_nonce
    8 +     // total_deposited
    8 +     // total_withdrawn
    8 +     // total_fees_paid
    8 +     // total_traded
    8 +     // max_balance
    8 +     // max_lifetime
    176;    // reserved
```

#### 3.1.2 Flags System

**Bitwise Flags for State Management:**
```rust
const FLAG_PLATFORM_ACTIVE: u8 = 0b0001;  // Bit 0: Platform authority active
const FLAG_TRADING_ACTIVE: u8  = 0b0010;  // Bit 1: Trading authority active
const FLAG_PAUSED: u8          = 0b0100;  // Bit 2: Escrow paused
// Bits 3-7: Reserved for future features
```

**Helper Methods:**
```rust
// Check flags
pub fn is_platform_active(&self) -> bool {
    self.flags & FLAG_PLATFORM_ACTIVE != 0
}

pub fn is_trading_active(&self) -> bool {
    self.flags & FLAG_TRADING_ACTIVE != 0
}

pub fn is_paused(&self) -> bool {
    self.flags & FLAG_PAUSED != 0
}

// Set flags
pub fn set_platform_active(&mut self, active: bool) {
    if active {
        self.flags |= FLAG_PLATFORM_ACTIVE;
    } else {
        self.flags &= !FLAG_PLATFORM_ACTIVE;
    }
}
```

**Benefits:**
- Space efficient (1 byte for 8 boolean states)
- Fast bitwise operations
- Easy to extend with reserved bits

### 3.2 Constants (constants.rs)

#### 3.2.1 Balance Limits
```rust
// Default max balance per escrow
pub const DEFAULT_MAX_BALANCE: u64 = 1_000_000_000_000; // 1M USDC (6 decimals)

// Absolute maximum (safety cap)
pub const MAX_ALLOWED_BALANCE: u64 = 10_000_000_000_000; // 10M USDC

// Max per trade transaction
pub const MAX_TRANSACTION_AMOUNT: u64 = 100_000_000_000; // 100K USDC

// Min balance to allow closure (dust)
pub const DUST_THRESHOLD: u64 = 10; // 0.00001 USDC
```

#### 3.2.2 Security Parameters
```rust
// Time-lock for authority delegation
pub const MIN_AUTHORITY_AGE: i64 = 300; // 5 minutes in seconds

// Cooldown after pause before unpause
pub const UNPAUSE_COOLDOWN: i64 = 300; // 5 minutes

// Clock drift tolerance
pub const TIMESTAMP_TOLERANCE: i64 = 30; // 30 seconds
```

#### 3.2.3 Token Validation
```rust
// USDC has 6 decimals
pub const MIN_TOKEN_DECIMALS: u8 = 6;
pub const MAX_TOKEN_DECIMALS: u8 = 9;
```

#### 3.2.4 Subscription Limits
```rust
// Max monthly subscription fee
pub const MAX_SUBSCRIPTION_FEE: u64 = 1_000_000_000; // 1,000 USDC
```

#### 3.2.5 Rent Calculation
```rust
// Typical rent for token account
pub const MIN_RENT_EXEMPT_LAMPORTS: u64 = 2_039_280; // ~0.002 SOL
```

### 3.3 Error Definitions (errors.rs)
```rust
#[error_code]
pub enum EscrowError {
    #[msg("Unauthorized: Only escrow owner can perform this action")]
    Unauthorized,
    
    #[msg("Invalid amount: Must be greater than 0")]
    InvalidAmount,
    
    #[msg("Insufficient balance in escrow")]
    InsufficientBalance,
    
    #[msg("Escrow has active authorities: Revoke before withdrawing")]
    EscrowStillActive,
    
    #[msg("Escrow not empty: Balance must be below dust threshold")]
    EscrowNotEmpty,
    
    #[msg("Math overflow: Amount too large")]
    MathOverflow,
    
    #[msg("Invalid authority: Cannot be default pubkey")]
    InvalidAuthority,
    
    #[msg("Escrow paused: Operations disabled")]
    EscrowPaused,
    
    #[msg("Escrow not paused: Emergency withdrawal requires paused state")]
    EscrowNotPaused,
    
    #[msg("Max balance exceeded")]
    MaxBalanceExceeded,
    
    #[msg("Amount too large: Exceeds per-transaction limit")]
    AmountTooLarge,
    
    #[msg("Invalid token mint")]
    InvalidTokenMint,
    
    #[msg("Platform authority too new: Must wait 5 minutes")]
    PlatformAuthorityTooNew,
    
    #[msg("Trading authority too new: Must wait 5 minutes")]
    TradingAuthorityTooNew,
    
    #[msg("Cooldown not elapsed: Must wait 5 minutes after pause")]
    CooldownNotElapsed,
    
    #[msg("Invalid token decimals: Must be between 6 and 9")]
    InvalidTokenDecimals,
    
    #[msg("Unauthorized platform: Only platform authority can call")]
    UnauthorizedPlatform,
    
    #[msg("Unauthorized trading: Only trading authority can call")]
    UnauthorizedTrading,
    
    #[msg("Platform authority already set")]
    PlatformAuthorityAlreadySet,
    
    #[msg("Trading authority already set")]
    TradingAuthorityAlreadySet,
    
    #[msg("Escrow expired: Maximum lifetime exceeded")]
    EscrowExpired,
    
    #[msg("Rent not recovered: Token account still has lamports")]
    RentNotRecovered,
}
```

### 3.4 Events (events.rs)

**All state changes emit events for off-chain indexing:**
```rust
#[event]
pub struct EscrowInitialized {
    pub escrow: Pubkey,
    pub user: Pubkey,
    pub token_mint: Pubkey,
    pub timestamp: i64,
}

#[event]
pub struct TokenDeposit {
    pub escrow: Pubkey,
    pub amount: u64,
    pub new_balance: u64,
    pub timestamp: i64,
}

#[event]
pub struct PlatformAuthorityDelegated {
    pub escrow: Pubkey,
    pub authority: Pubkey,
    pub timestamp: i64,
}

#[event]
pub struct TradingAuthorityDelegated {
    pub escrow: Pubkey,
    pub authority: Pubkey,
    pub timestamp: i64,
}

#[event]
pub struct PlatformAuthorityRevoked {
    pub escrow: Pubkey,
    pub timestamp: i64,
}

#[event]
pub struct TradingAuthorityRevoked {
    pub escrow: Pubkey,
    pub timestamp: i64,
}

#[event]
pub struct TokenWithdraw {
    pub escrow: Pubkey,
    pub amount: u64,
    pub remaining_balance: u64,
    pub timestamp: i64,
}

#[event]
pub struct SubscriptionFeeWithdraw {
    pub escrow: Pubkey,
    pub amount: u64,
    pub remaining_balance: u64,
    pub timestamp: i64,
}

#[event]
pub struct TradeWithdraw {
    pub escrow: Pubkey,
    pub amount: u64,
    pub remaining_balance: u64,
    pub timestamp: i64,
}

#[event]
pub struct EscrowPaused {
    pub escrow: Pubkey,
    pub timestamp: i64,
}

#[event]
pub struct EscrowUnpaused {
    pub escrow: Pubkey,
    pub timestamp: i64,
}

#[event]
pub struct EscrowClosed {
    pub escrow: Pubkey,
    pub timestamp: i64,
}
```

---

## 4. Security Model

### 4.1 CEI Pattern (Checks-Effects-Interactions)

**All instructions follow strict CEI pattern to prevent reentrancy:**
```rust
pub fn withdraw_for_trade(ctx: Context<WithdrawForTrade>, amount: u64) -> Result<()> {
    let escrow = &mut ctx.accounts.escrow;
    
    // ========== CHECKS ==========
    require!(!escrow.is_paused(), EscrowError::EscrowPaused);
    require!(amount > 0, EscrowError::InvalidAmount);
    require!(amount <= MAX_TRANSACTION_AMOUNT, EscrowError::AmountTooLarge);
    require!(
        ctx.accounts.trading_authority.key() == escrow.trading_authority,
        EscrowError::UnauthorizedTrading
    );
    require!(
        escrow.is_trading_authority_mature(clock.unix_timestamp),
        EscrowError::TradingAuthorityTooNew
    );
    
    let current_balance = ctx.accounts.escrow_token_account.amount;
    require!(amount <= current_balance, EscrowError::InsufficientBalance);
    
    // ========== EFFECTS ==========
    escrow.total_traded = escrow.total_traded
        .checked_add(amount)
        .ok_or(EscrowError::MathOverflow)?;
    escrow.action_nonce = escrow.action_nonce.wrapping_add(1);
    
    emit!(TradeWithdraw { ... });
    
    // ========== INTERACTIONS ==========
    let seeds = &[b"escrow", user_ref.as_ref(), &[bump_val]];
    let signer = &[&seeds[..]];
    
    token::transfer(
        CpiContext::new_with_signer(...),
        amount
    )?;
    
    Ok(())
}
```

**Benefits:**
- Prevents reentrancy attacks
- Clear separation of concerns
- Easy to audit
- Consistent pattern across all instructions

### 4.2 Time-Lock Mechanism

**Authority Delegation Security:**
```rust
// When delegating authority
pub fn delegate_trading_authority(ctx, trading_authority) -> Result<()> {
    let escrow = &mut ctx.accounts.escrow;
    let clock = Clock::get()?;
    
    escrow.trading_authority = trading_authority;
    escrow.trading_activated_at = clock.unix_timestamp;  // Record activation time
    escrow.set_trading_active(true);
    
    Ok(())
}

// When using authority (5 minutes later)
pub fn withdraw_for_trade(ctx, amount) -> Result<()> {
    let escrow = &ctx.accounts.escrow;
    let clock = Clock::get()?;
    
    // CRITICAL CHECK: 5-minute time-lock
    require!(
        escrow.is_trading_authority_mature(clock.unix_timestamp),
        EscrowError::TradingAuthorityTooNew
    );
    
    // Implementation
    pub fn is_trading_authority_mature(&self, current_timestamp: i64) -> bool {
        if self.trading_activated_at == 0 {
            return false;  // Not delegated
        }
        current_timestamp - self.trading_activated_at >= MIN_AUTHORITY_AGE  // 300s
    }
    
    // ... proceed with withdrawal
}
```

**Purpose:**
- Gives user 5 minutes to revoke if delegation was malicious
- Prevents instant abuse after authority compromise
- Similar to blockchain transaction finality

### 4.3 Pause Mechanism with Cooldown
```rust
// User pauses escrow immediately
pub fn pause_escrow(ctx: Context<PauseEscrow>) -> Result<()> {
    let escrow = &mut ctx.accounts.escrow;
    let clock = Clock::get()?;
    
    escrow.set_paused(true, clock.unix_timestamp);  // Record pause time
    escrow.action_nonce = escrow.action_nonce.wrapping_add(1);
    
    emit!(EscrowPaused { ... });
    Ok(())
}

// User must wait 5 minutes before unpause
pub fn unpause_escrow(ctx: Context<UnpauseEscrow>) -> Result<()> {
    let escrow = &mut ctx.accounts.escrow;
    let clock = Clock::get()?;
    
    // CRITICAL CHECK: 5-minute cooldown
    require!(
        escrow.can_unpause(clock.unix_timestamp),
        EscrowError::CooldownNotElapsed
    );
    
    // Implementation
    pub fn can_unpause(&self, current_timestamp: i64) -> bool {
        if self.last_paused_at == 0 {
            return true;  // Never paused
        }
        current_timestamp - self.last_paused_at >= UNPAUSE_COOLDOWN  // 300s
    }
    
    escrow.set_paused(false, clock.unix_timestamp);
    emit!(EscrowUnpaused { ... });
    Ok(())
}
```

**Purpose:**
- Prevents rapid pause/unpause attacks
- Gives time for investigation during pause
- Prevents DoS via constant state changes

### 4.4 Replay Protection

**Nonce-based ordering:**
```rust
pub struct EscrowAccount {
    pub action_nonce: u64,  // Increments on every state change
    // ...
}

// Every instruction that modifies state
pub fn some_instruction(ctx: Context<...>) -> Result<()> {
    let escrow = &mut ctx.accounts.escrow;
    
    // ... perform action ...
    
    // CRITICAL: Increment nonce
    escrow.action_nonce = escrow.action_nonce.wrapping_add(1);
    
    Ok(())
}
```

**Benefits:**
- Prevents transaction replay
- Provides ordering guarantee
- Enables off-chain nonce tracking
- Wrapping prevents overflow

### 4.5 Transaction Limits

**Multi-layer protection:**
```rust
// Layer 1: Per-transaction limits
pub fn withdraw_for_trade(ctx, amount: u64) -> Result<()> {
    require!(
        amount <= MAX_TRANSACTION_AMOUNT,  // 100K USDC max
        EscrowError::AmountTooLarge
    );
    // ...
}

pub fn withdraw_subscription_fee(ctx, amount: u64) -> Result<()> {
    require!(
        amount <= MAX_SUBSCRIPTION_FEE,  // 1K USDC max
        EscrowError::AmountTooLarge
    );
    // ...
}

// Layer 2: Max escrow balance
pub fn deposit_token(ctx, amount: u64) -> Result<()> {
    let new_balance = current_balance.checked_add(amount)?;
    
    if escrow.max_balance > 0 {
        require!(
            new_balance <= escrow.max_balance,
            EscrowError::MaxBalanceExceeded
        );
    }
    // ...
}

// Layer 3: Absolute safety cap
pub fn initialize_escrow(ctx, max_balance: u64) -> Result<()> {
    if max_balance > 0 {
        require!(
            max_balance <= MAX_ALLOWED_BALANCE,  // 10M USDC absolute max
            EscrowError::MaxBalanceExceeded
        );
    }
    // ...
}
```

**Defense in Depth:**
- Per-transaction limits prevent single large drain
- Per-escrow limits prevent accumulation
- Absolute caps provide safety net

---

## 5. Instruction Reference

### 5.1 User Operations

#### 5.1.1 initialize_escrow

**Purpose**: Create new escrow account for user.

**Authority**: User (owner)

**Signature:**
```rust
pub fn initialize_escrow(
    ctx: Context<InitializeEscrow>,
    bump: u8,
    max_balance: u64,
) -> Result<()>
```

**Accounts:**
```rust
#[derive(Accounts)]
pub struct InitializeEscrow<'info> {
    #[account(
        init,
        payer = user,
        space = 8 + EscrowAccount::INIT_SPACE,
        seeds = [b"escrow", user.key().as_ref()],
        bump
    )]
    pub escrow: Account<'info, EscrowAccount>,
    
    #[account(
        init,
        payer = user,
        associated_token::mint = token_mint,
        associated_token::authority = escrow
    )]
    pub escrow_token_account: Account<'info, TokenAccount>,
    
    pub token_mint: Account<'info, Mint>,
    
    #[account(mut)]
    pub user: Signer<'info>,
    
    pub system_program: Program<'info, System>,
    pub token_program: Program<'info, Token>,
    pub associated_token_program: Program<'info, AssociatedToken>,
}
```

**Checks:**
- Token decimals between 6-9
- Max balance ≤ MAX_ALLOWED_BALANCE (if specified)

**Effects:**
- Creates escrow PDA
- Creates associated token account
- Initializes all fields
- Sets max_balance (or DEFAULT_MAX_BALANCE)

**Events:**
- `EscrowInitialized`

**Example:**
```typescript
await program.methods
  .initializeEscrow(bump, new BN(1_000_000_000_000)) // 1M USDC max
  .accounts({
    escrow: escrowPda,
    escrowTokenAccount: ata,
    tokenMint: usdcMint,
    user: userWallet.publicKey,
    systemProgram: SystemProgram.programId,
    tokenProgram: TOKEN_PROGRAM_ID,
    associatedTokenProgram: ASSOCIATED_TOKEN_PROGRAM_ID,
  })
  .signers([userWallet])
  .rpc();
```

#### 5.1.2 deposit_token

**Purpose**: Deposit tokens into escrow.

**Authority**: User (owner)

**Signature:**
```rust
pub fn deposit_token(
    ctx: Context<DepositToken>,
    amount: u64,
) -> Result<()>
```

**Checks:**
- Not paused
- Amount > 0
- Not expired
- New balance ≤ max_balance

**Effects:**
- Transfers tokens from user to escrow
- Increments total_deposited
- Increments nonce

**Events:**
- `TokenDeposit`

#### 5.1.3 delegate_platform_authority

**Purpose**: Grant subscription fee permissions to Pourtier.

**Authority**: User (owner)

**Signature:**
```rust
pub fn delegate_platform_authority(
    ctx: Context<DelegatePlatformAuthority>,
    platform_authority: Pubkey,
) -> Result<()>
```

**Checks:**
- Not paused
- Authority != default pubkey
- Not already delegated
- Not expired

**Effects:**
- Sets platform_authority
- Records platform_activated_at (starts 5min timer)
- Sets PLATFORM_ACTIVE flag
- Increments nonce

**Events:**
- `PlatformAuthorityDelegated`

**Time-Lock:** 5 minutes before authority can withdraw fees

#### 5.1.4 delegate_trading_authority

**Purpose**: Grant trading permissions to Chevalier.

**Authority**: User (owner)

**Signature:**
```rust
pub fn delegate_trading_authority(
    ctx: Context<DelegateTradingAuthority>,
    trading_authority: Pubkey,
) -> Result<()>
```

**Checks:**
- Not paused
- Authority != default pubkey
- Not already delegated
- Not expired

**Effects:**
- Sets trading_authority
- Records trading_activated_at (starts 5min timer)
- Sets TRADING_ACTIVE flag
- Increments nonce

**Events:**
- `TradingAuthorityDelegated`

**Time-Lock:** 5 minutes before authority can execute trades

#### 5.1.5 revoke_platform_authority

**Purpose**: Remove Pourtier's subscription permissions.

**Authority**: User (owner)

**Effects:**
- Clears platform_authority
- Clears PLATFORM_ACTIVE flag
- Resets platform_activated_at
- Increments nonce

**Events:**
- `PlatformAuthorityRevoked`

**Immediate Effect:** No cooldown

#### 5.1.6 revoke_trading_authority

**Purpose**: Remove Chevalier's trading permissions.

**Authority**: User (owner)

**Effects:**
- Clears trading_authority
- Clears TRADING_ACTIVE flag
- Resets trading_activated_at
- Increments nonce

**Events:**
- `TradingAuthorityRevoked`

**Immediate Effect:** No cooldown

#### 5.1.7 withdraw_token

**Purpose**: User withdraws funds (when no authorities active).

**Authority**: User (owner)

**Checks:**
- Not paused
- No active authorities (must revoke first)
- Amount > 0
- Sufficient balance

**Effects:**
- Transfers tokens from escrow to user
- Increments total_withdrawn
- Increments nonce

**Events:**
- `TokenWithdraw`

#### 5.1.8 emergency_withdraw

**Purpose**: Withdraw funds while paused (emergency exit).

**Authority**: User (owner)

**Checks:**
- MUST be paused
- No active authorities
- Amount > 0
- Sufficient balance

**Effects:**
- Transfers tokens from escrow to user
- Increments total_withdrawn
- Increments nonce

**Use Case:** Emergency recovery when escrow is paused

#### 5.1.9 pause_escrow

**Purpose**: Immediately disable all operations.

**Authority**: User (owner)

**Effects:**
- Sets PAUSED flag
- Records last_paused_at (starts cooldown)
- Increments nonce

**Events:**
- `EscrowPaused`

**Immediate Effect:** All operations blocked except emergency_withdraw

#### 5.1.10 unpause_escrow

**Purpose**: Resume operations after pause.

**Authority**: User (owner)

**Checks:**
- 5-minute cooldown elapsed since pause

**Effects:**
- Clears PAUSED flag
- Increments nonce

**Events:**
- `EscrowUnpaused`

**Time-Lock:** 5 minutes after pause

#### 5.1.11 close_escrow

**Purpose**: Close escrow and recover rent.

**Authority**: User (owner)

**Checks:**
- Not paused
- No active authorities
- Balance ≤ DUST_THRESHOLD (10 = 0.00001 USDC)
- Token account has rent lamports

**Effects:**
- Closes token account
- Transfers rent to user
- Closes escrow account

**Events:**
- `EscrowClosed`

**Rent Recovery:** ~0.002 SOL returned to user

### 5.2 Platform Operations

#### 5.2.1 withdraw_subscription_fee

**Purpose**: Pourtier withdraws monthly subscription fee.

**Authority**: Platform authority (Pourtier)

**Signature:**
```rust
pub fn withdraw_subscription_fee(
    ctx: Context<WithdrawSubscriptionFee>,
    amount: u64,
) -> Result<()>
```

**Checks:**
- Not paused
- Amount > 0
- Amount ≤ MAX_SUBSCRIPTION_FEE (1,000 USDC)
- Caller is platform_authority
- 5-minute time-lock elapsed
- Sufficient balance

**Effects:**
- Transfers tokens to platform
- Increments total_fees_paid
- Increments nonce

**Events:**
- `SubscriptionFeeWithdraw`

**Limit:** 1,000 USDC per call

### 5.3 Trading Operations

#### 5.3.1 withdraw_for_trade

**Purpose**: Chevalier withdraws funds to execute trade.

**Authority**: Trading authority (Chevalier)

**Signature:**
```rust
pub fn withdraw_for_trade(
    ctx: Context<WithdrawForTrade>,
    amount: u64,
) -> Result<()>
```

**Checks:**
- Not paused
- Amount > 0
- Amount ≤ MAX_TRANSACTION_AMOUNT (100,000 USDC)
- Caller is trading_authority
- 5-minute time-lock elapsed
- Sufficient balance

**Effects:**
- Transfers tokens to trading authority
- Increments total_traded
- Increments nonce

**Events:**
- `TradeWithdraw`

**Limit:** 100,000 USDC per call

---

## 6. State Management

### 6.1 State Lifecycle
```
┌──────────────────────────────────────────────────────────────┐
│                   Escrow Lifecycle                           │
└──────────────────────────────────────────────────────────────┘

1. INITIALIZATION
   ↓
   initialize_escrow()
   ↓
   State: CREATED (no authorities)
   Flags: 0b0000
   
2. DEPOSIT FUNDS
   ↓
   deposit_token(amount)
   ↓
   State: FUNDED
   
3. DELEGATE AUTHORITIES (optional)
   ↓
   delegate_platform_authority(pourtier_pubkey)
   delegate_trading_authority(chevalier_pubkey)
   ↓
   State: DELEGATED
   Flags: 0b0011 (PLATFORM_ACTIVE | TRADING_ACTIVE)
   
   TIME-LOCK: Wait 5 minutes
   
4. ACTIVE TRADING
   ↓
   Chevalier: withdraw_for_trade(amount)
   Pourtier: withdraw_subscription_fee(amount)
   ↓
   State: ACTIVE
   
5. PAUSE (if needed)
   ↓
   pause_escrow()
   ↓
   State: PAUSED
   Flags: 0b0111 (PAUSED | PLATFORM_ACTIVE | TRADING_ACTIVE)
   
   Operations blocked except emergency_withdraw
   
   TIME-LOCK: Wait 5 minutes
   
   ↓
   unpause_escrow()
   ↓
   State: ACTIVE (resumed)
   
6. REVOKE AUTHORITIES
   ↓
   revoke_platform_authority()
   revoke_trading_authority()
   ↓
   State: REVOKED (back to user-only mode)
   Flags: 0b0000
   
7. WITHDRAWAL
   ↓
   withdraw_token(all_balance)
   ↓
   State: EMPTY (balance ≤ DUST_THRESHOLD)
   
8. CLOSURE
   ↓
   close_escrow()
   ↓
   State: CLOSED (account deleted, rent recovered)
```

### 6.2 Flag State Diagram
```
Initial State: 0b0000
│
├─► delegate_platform_authority() ─► 0b0001 (PLATFORM_ACTIVE)
│
├─► delegate_trading_authority()  ─► 0b0010 (TRADING_ACTIVE)
│
├─► Both authorities ──────────────► 0b0011 (PLATFORM_ACTIVE | TRADING_ACTIVE)
│
├─► pause_escrow() ────────────────► 0b0100 (PAUSED)
│                                    0b0101 (PAUSED | PLATFORM_ACTIVE)
│                                    0b0110 (PAUSED | TRADING_ACTIVE)
│                                    0b0111 (PAUSED | PLATFORM_ACTIVE | TRADING_ACTIVE)
│
├─► unpause_escrow() ──────────────► Clears PAUSED bit
│
├─► revoke_platform_authority() ───► Clears PLATFORM_ACTIVE bit
│
└─► revoke_trading_authority() ────► Clears TRADING_ACTIVE bit
```

### 6.3 Nonce Progression

**Every state change increments nonce:**
```
Action                          Nonce
─────────────────────────────────────
initialize_escrow()              0 → 0 (initial)
deposit_token(100)               0 → 1
delegate_platform_authority()    1 → 2
delegate_trading_authority()     2 → 3
withdraw_subscription_fee(10)    3 → 4
withdraw_for_trade(50)           4 → 5
pause_escrow()                   5 → 6
unpause_escrow()                 6 → 7
revoke_trading_authority()       7 → 8
withdraw_token(40)               8 → 9
```

**Benefits:**
- Event ordering
- Replay protection
- Audit trail

---

## 7. Events & Monitoring

### 7.1 Event Emission Pattern

**All instructions emit events:**
```rust
pub fn some_instruction(ctx: Context<...>) -> Result<()> {
    // ... perform action ...
    
    // Capture values BEFORE interactions
    let escrow_key = ctx.accounts.escrow.key();
    let timestamp = Clock::get()?.unix_timestamp;
    
    // Emit event
    emit!(SomeEvent {
        escrow: escrow_key,
        timestamp,
        // ... other fields
    });
    
    Ok(())
}
```

### 7.2 Event Indexing

**Passeur consumes events for backend integration:**
```
Solana Transaction Logs
    ↓
Event: PlatformAuthorityDelegated {
    escrow: Esc7Row...,
    authority: Pout1er...,
    timestamp: 1737388800
}
    ↓
Passeur Event Indexer
    ↓
Parse event → Extract fields
    ↓
Webhook to Backend:
POST /api/blockchain/events
{
    "event_type": "platform_authority_delegated",
    "escrow": "Esc7Row...",
    "authority": "Pout1er...",
    "timestamp": 1737388800
}
    ↓
Backend updates database
```

### 7.3 Critical Events

**Monitor these for security:**

- **EscrowPaused**: Investigate why user paused
- **PlatformAuthorityDelegated**: Track authority changes
- **TradingAuthorityDelegated**: Track authority changes
- **SubscriptionFeeWithdraw**: Monitor fee amounts
- **TradeWithdraw**: Monitor trade volumes

---

## 8. Deployment Guide

### 8.1 Prerequisites
```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install Solana CLI
sh -c "$(curl -sSfL https://release.solana.com/stable/install)"

# Install Anchor
cargo install --git https://github.com/coral-xyz/anchor avm --locked
avm install latest
avm use latest

# Verify installations
anchor --version  # Should be 0.31.1
solana --version
cargo --version
```

### 8.2 Build Process
```bash
cd ~/lumiere/lumiere-backend/smart_contracts

# Build program
anchor build

# Output:
# target/deploy/escrow.so              (compiled program)
# target/deploy/escrow-keypair.json    (program keypair)
# target/idl/escrow.json               (IDL for clients)
```

### 8.3 Deployment Script

**Using deploy_escrow.sh:**
```bash
# Deploy to Devnet
./deploy_escrow.sh --environment dev

# Deploy to Mainnet
./deploy_escrow.sh --environment prod

# Upgrade existing program
./deploy_escrow.sh --environment prod --upgrade
```

**Script Flow:**
```
1. Check dependencies (anchor, solana)
2. Setup keypair (~/.config/solana/id.json)
3. Configure network (devnet/mainnet)
4. Check balance (airdrop if devnet)
5. Build program (anchor build)
6. Deploy/Upgrade
7. Verify deployment
8. Generate summary
```

**Output:**
```
================================================================================
ESCROW SMART CONTRACT DEPLOYMENT SUMMARY
================================================================================

Timestamp:      20260120_145030
Environment:    dev
Mode:           NEW
Program ID:     9gvUtaF99sQ287PNzRfCbhFTC4PUnnd7jdAjnY5GUVhS
Cluster:        https://api.devnet.solana.com
Deployer:       8c53d17bDa2e42848a3b25e5cd510c83...

Build Artifacts:
    build/escrow.so
    build/escrow-keypair.json
    build/program_id.txt

Solana Explorer:
    https://explorer.solana.com/address/9gvUtaF99s.../devnet

Next Steps:
    1. Update declare_id! in lib.rs
    2. Rebuild program
    3. Upload IDL
    4. Run tests
    5. Update frontend config

================================================================================
```

### 8.4 Post-Deployment

**1. Update Program ID:**
```rust
// programs/escrow/src/lib.rs
declare_id!("9gvUtaF99sQ287PNzRfCbhFTC4PUnnd7jdAjnY5GUVhS");
```

**2. Rebuild:**
```bash
anchor build
```

**3. Upload IDL:**
```bash
anchor idl init 9gvUtaF99sQ287PNzRfCbhFTC4PUnnd7jdAjnY5GUVhS \
  --filepath target/idl/escrow.json
```

**4. Verify:**
```bash
solana program show 9gvUtaF99sQ287PNzRfCbhFTC4PUnnd7jdAjnY5GUVhS
```

**5. Run Tests:**
```bash
anchor test --skip-local-validator
```

---

## 9. Integration Points

### 9.1 Passeur Integration

**Passeur bridges blockchain to backend:**
```python
# passeur/bridge.py
class PasseurBridgeClient:
    
    async def initialize_escrow(
        self,
        user_wallet: str,
        token_mint: str,
        max_balance: int = DEFAULT_MAX_BALANCE
    ) -> Dict:
        """Initialize user escrow on-chain."""
        
        # Derive PDA
        escrow_pda = self._derive_escrow_pda(user_wallet)
        
        # Build transaction
        tx = await self.program.methods.initialize_escrow(
            bump=escrow_pda.bump,
            max_balance=max_balance
        ).accounts({
            "escrow": escrow_pda.address,
            "user": user_wallet,
            "tokenMint": token_mint,
            # ...
        }).rpc()
        
        return {
            "signature": tx,
            "escrow": str(escrow_pda.address)
        }
    
    async def delegate_trading_authority(
        self,
        escrow: str,
        chevalier_pubkey: str
    ) -> str:
        """Delegate trading authority to Chevalier."""
        
        tx = await self.program.methods.delegate_trading_authority(
            trading_authority=chevalier_pubkey
        ).accounts({
            "escrow": escrow,
            "user": self.user_wallet,
        }).rpc()
        
        return tx
```

### 9.2 Frontend Integration

**TypeScript client example:**
```typescript
import { Program, AnchorProvider } from "@coral-xyz/anchor";
import { Escrow } from "./idl/escrow";

const provider = new AnchorProvider(connection, wallet, {});
const program = new Program<Escrow>(IDL, PROGRAM_ID, provider);

// Initialize escrow
const [escrowPda] = PublicKey.findProgramAddressSync(
  [Buffer.from("escrow"), wallet.publicKey.toBuffer()],
  program.programId
);

await program.methods
  .initializeEscrow(bump, new BN(1_000_000_000_000))
  .accounts({
    escrow: escrowPda,
    user: wallet.publicKey,
    tokenMint: USDC_MINT,
    // ...
  })
  .rpc();

// Subscribe to events
program.addEventListener("EscrowInitialized", (event) => {
  console.log("Escrow created:", event.escrow.toString());
});
```

### 9.3 Chevalier Integration

**Trading bot withdraws funds:**
```python
# chevalier/blockchain/escrow_client.py
class EscrowClient:
    
    async def withdraw_for_trade(
        self,
        escrow: str,
        amount: int,
        trading_authority_keypair: Keypair
    ) -> str:
        """Execute trade withdrawal as trading authority."""
        
        # Verify time-lock elapsed
        escrow_account = await self.program.account.escrow_account.fetch(escrow)
        
        current_time = int(time.time())
        activation_time = escrow_account.trading_activated_at
        
        if current_time - activation_time < 300:  # 5 minutes
            raise TimeoutError("Trading authority not mature yet")
        
        # Execute withdrawal
        tx = await self.program.methods.withdraw_for_trade(amount).accounts({
            "escrow": escrow,
            "tradingAuthority": trading_authority_keypair.pubkey(),
            # ...
        }).signers([trading_authority_keypair]).rpc()
        
        return tx
```

---

## 10. Testing Strategy

### 10.1 Unit Tests (Rust)

**State logic tests:**
```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_dual_authority_flags() {
        let mut escrow = create_test_escrow();
        
        // Test platform authority
        assert!(!escrow.is_platform_active());
        escrow.set_platform_active(true);
        assert!(escrow.is_platform_active());
        assert!(!escrow.is_trading_active());
        
        // Test trading authority
        escrow.set_trading_active(true);
        assert!(escrow.is_trading_active());
        assert!(escrow.is_platform_active());
        
        // Test has_active_authority
        assert!(escrow.has_active_authority());
    }
    
    #[test]
    fn test_authority_maturity() {
        let mut escrow = create_test_escrow();
        
        assert!(!escrow.is_platform_authority_mature(1300));
        escrow.platform_activated_at = 1000;
        assert!(!escrow.is_platform_authority_mature(1299));
        assert!(escrow.is_platform_authority_mature(1300));
    }
}
```

**Run:**
```bash
cargo test -- --nocapture
```

### 10.2 Integration Tests (TypeScript)

**Full flow tests:**
```typescript
describe("escrow", () => {
  it("Initializes escrow", async () => {
    const tx = await program.methods
      .initializeEscrow(bump, maxBalance)
      .accounts({ /* ... */ })
      .signers([user])
      .rpc();
    
    const escrowAccount = await program.account.escrowAccount.fetch(escrowPda);
    expect(escrowAccount.user.toString()).to.equal(user.publicKey.toString());
  });
  
  it("Enforces 5-minute time-lock", async () => {
    await program.methods
      .delegateTradingAuthority(authority.publicKey)
      .accounts({ /* ... */ })
      .signers([user])
      .rpc();
    
    // Try immediate withdrawal (should fail)
    try {
      await program.methods
        .withdrawForTrade(new BN(1000))
        .accounts({ /* ... */ })
        .signers([authority])
        .rpc();
      expect.fail("Should have failed");
    } catch (err) {
      expect(err.message).to.include("TradingAuthorityTooNew");
    }
    
    // Wait 5 minutes
    await sleep(5000);
    
    // Try again (should succeed)
    const tx = await program.methods
      .withdrawForTrade(new BN(1000))
      .accounts({ /* ... */ })
      .signers([authority])
      .rpc();
    
    expect(tx).to.exist;
  });
});
```

**Run:**
```bash
anchor test
```

### 10.3 Security Tests

**Attack vector tests:**
```typescript
it("Prevents reentrancy via CEI pattern", async () => {
  // Attempt double withdrawal
  // Should fail due to balance check in CHECKS phase
});

it("Prevents replay via nonce", async () => {
  // Get nonce before transaction
  const nonceBefore = escrow.action_nonce;
  
  // Execute transaction
  await withdraw();
  
  // Nonce should have incremented
  const nonceAfter = (await fetchEscrow()).action_nonce;
  expect(nonceAfter).to.equal(nonceBefore + 1);
});

it("Enforces transaction limits", async () => {
  try {
    await program.methods
      .withdrawForTrade(new BN(200_000_000_000)) // 200K > 100K limit
      .rpc();
    expect.fail();
  } catch (err) {
    expect(err.message).to.include("AmountTooLarge");
  }
});
```

---

## 11. Troubleshooting Guide

### 11.1 Common Issues

#### Issue: "Insufficient funds for transaction"

**Symptoms:**
```
Error: Attempt to debit an account but found no record of a prior credit
```

**Cause:** Wallet has no SOL for transaction fees.

**Solution:**
```bash
# Devnet: Request airdrop
solana airdrop 2

# Mainnet: Fund wallet
solana balance
# Transfer SOL to wallet address
```

#### Issue: "TradingAuthorityTooNew"

**Symptoms:**
```
Error: AnchorError caused by account: escrow. Error Code: TradingAuthorityTooNew
```

**Cause:** Trying to use authority before 5-minute time-lock.

**Solution:**
```bash
# Check activation time
solana account <escrow_address>

# Wait 5 minutes after delegation
sleep 300

# Retry transaction
```

#### Issue: "EscrowStillActive"

**Symptoms:**
```
Error: Escrow has active authorities: Revoke before withdrawing
```

**Cause:** User trying to withdraw while authorities delegated.

**Solution:**
```bash
# Revoke authorities first
anchor run revoke-platform
anchor run revoke-trading

# Then withdraw
anchor run withdraw
```

#### Issue: "Program deployment failed"

**Symptoms:**
```
Error: Account allocation failed: unable to confirm transaction
```

**Cause:** Insufficient SOL for program deployment.

**Solution:**
```bash
# Check deployer balance
solana balance

# Deployment requires ~5-10 SOL on devnet
solana airdrop 10

# Retry deployment
./deploy_escrow.sh --environment dev
```

### 11.2 Debugging Tools

**1. View Account Data:**
```bash
# View escrow account
solana account <escrow_pda>

# Decode with Anchor
anchor account escrow.EscrowAccount <escrow_pda>
```

**2. View Transaction Logs:**
```bash
# Get transaction details
solana confirm -v <signature>

# View program logs
solana logs | grep "Program log"
```

**3. IDL Inspection:**
```bash
# View program IDL
anchor idl fetch 9gvUtaF99sQ287PNzRfCbhFTC4PUnnd7jdAjnY5GUVhS

# Update IDL
anchor idl upgrade 9gvUtaF99sQ287PNzRfCbhFTC4PUnnd7jdAjnY5GUVhS \
  --filepath target/idl/escrow.json
```

**4. Event Monitoring:**
```typescript
// Subscribe to all events
program.addEventListener("EscrowInitialized", console.log);
program.addEventListener("TokenDeposit", console.log);
program.addEventListener("TradeWithdraw", console.log);
// ... etc
```

### 11.3 Security Checklist

**Before mainnet deployment:**

- [ ] All tests passing (unit + integration)
- [ ] Constants verified (limits, time-locks)
- [ ] CEI pattern enforced in all instructions
- [ ] Error messages clear and actionable
- [ ] Events emitted for all state changes
- [ ] Nonce incremented in all mutations
- [ ] PDA seeds correct and documented
- [ ] Account validations comprehensive
- [ ] Overflow checks on all math operations
- [ ] Authority checks on privileged instructions
- [ ] Time-locks enforced correctly
- [ ] Pause mechanism tested
- [ ] Emergency withdrawal tested
- [ ] Rent recovery tested
- [ ] External audit completed (if budget allows)

---

## Appendix A: Constants Reference
```rust
// Balance Limits
DEFAULT_MAX_BALANCE: 1_000_000_000_000      // 1M USDC
MAX_ALLOWED_BALANCE: 10_000_000_000_000     // 10M USDC
MAX_TRANSACTION_AMOUNT: 100_000_000_000     // 100K USDC per trade
DUST_THRESHOLD: 10                          // 0.00001 USDC

// Security
MIN_AUTHORITY_AGE: 300                      // 5 minutes
UNPAUSE_COOLDOWN: 300                       // 5 minutes
TIMESTAMP_TOLERANCE: 30                     // 30 seconds

// Token
MIN_TOKEN_DECIMALS: 6
MAX_TOKEN_DECIMALS: 9

// Subscription
MAX_SUBSCRIPTION_FEE: 1_000_000_000         // 1,000 USDC

// Rent
MIN_RENT_EXEMPT_LAMPORTS: 2_039_280         // ~0.002 SOL
```

---

## Appendix B: Event Reference

| Event | Fields | Trigger |
|-------|--------|---------|
| EscrowInitialized | escrow, user, token_mint, timestamp | initialize_escrow() |
| TokenDeposit | escrow, amount, new_balance, timestamp | deposit_token() |
| PlatformAuthorityDelegated | escrow, authority, timestamp | delegate_platform_authority() |
| TradingAuthorityDelegated | escrow, authority, timestamp | delegate_trading_authority() |
| PlatformAuthorityRevoked | escrow, timestamp | revoke_platform_authority() |
| TradingAuthorityRevoked | escrow, timestamp | revoke_trading_authority() |
| TokenWithdraw | escrow, amount, remaining_balance, timestamp | withdraw_token() |
| SubscriptionFeeWithdraw | escrow, amount, remaining_balance, timestamp | withdraw_subscription_fee() |
| TradeWithdraw | escrow, amount, remaining_balance, timestamp | withdraw_for_trade() |
| EscrowPaused | escrow, timestamp | pause_escrow() |
| EscrowUnpaused | escrow, timestamp | unpause_escrow() |
| EscrowClosed | escrow, timestamp | close_escrow() |

---

## Appendix C: Account Sizes
```
EscrowAccount:
  - Discriminator: 8 bytes
  - Data: 402 bytes
  - Total: 410 bytes
  - Rent: ~0.003 SOL

Associated Token Account:
  - Fixed: 165 bytes
  - Rent: ~0.002 SOL

Total per user:
  - Accounts: 2
  - Space: 575 bytes
  - Rent: ~0.005 SOL (~$1 at $200/SOL)
```

---

**END OF DOCUMENT**
