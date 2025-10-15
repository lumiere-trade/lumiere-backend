use anchor_lang::prelude::*;

/// Escrow initialized event
#[event]
pub struct EscrowInitialized {
    pub escrow: Pubkey,
    pub user: Pubkey,
    pub token_mint: Pubkey,
    pub timestamp: i64,
}

/// Token deposit event
#[event]
pub struct TokenDeposit {
    pub escrow: Pubkey,
    pub amount: u64,
    pub new_balance: u64,
    pub timestamp: i64,
}

/// Platform authority delegated event
#[event]
pub struct PlatformAuthorityDelegated {
    pub escrow: Pubkey,
    pub authority: Pubkey,
    pub timestamp: i64,
}

/// Trading authority delegated event
#[event]
pub struct TradingAuthorityDelegated {
    pub escrow: Pubkey,
    pub authority: Pubkey,
    pub timestamp: i64,
}

/// Platform authority revoked event
#[event]
pub struct PlatformAuthorityRevoked {
    pub escrow: Pubkey,
    pub timestamp: i64,
}

/// Trading authority revoked event
#[event]
pub struct TradingAuthorityRevoked {
    pub escrow: Pubkey,
    pub timestamp: i64,
}

/// User withdrawal event
#[event]
pub struct TokenWithdraw {
    pub escrow: Pubkey,
    pub amount: u64,
    pub remaining_balance: u64,
    pub timestamp: i64,
}

/// Subscription fee withdrawal event
#[event]
pub struct SubscriptionFeeWithdraw {
    pub escrow: Pubkey,
    pub amount: u64,
    pub remaining_balance: u64,
    pub timestamp: i64,
}

/// Trade withdrawal event
#[event]
pub struct TradeWithdraw {
    pub escrow: Pubkey,
    pub amount: u64,
    pub remaining_balance: u64,
    pub timestamp: i64,
}

/// Emergency withdrawal event
#[event]
pub struct EmergencyWithdrawal {
    pub escrow: Pubkey,
    pub amount: u64,
    pub timestamp: i64,
}

/// Escrow paused event
#[event]
pub struct EscrowPaused {
    pub escrow: Pubkey,
    pub timestamp: i64,
}

/// Escrow unpaused event
#[event]
pub struct EscrowUnpaused {
    pub escrow: Pubkey,
    pub timestamp: i64,
}

/// Escrow closed event
#[event]
pub struct EscrowClosed {
    pub escrow: Pubkey,
    pub timestamp: i64,
}
