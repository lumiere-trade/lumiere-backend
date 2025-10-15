use anchor_lang::prelude::*;

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

    #[msg("Platform authority not set")]
    PlatformAuthorityNotSet,

    #[msg("Trading authority not set")]
    TradingAuthorityNotSet,

    #[msg("Amount too large: Exceeds per-transaction limit")]
    AmountTooLarge,

    #[msg("Invalid token mint")]
    InvalidTokenMint,

    #[msg("Invalid destination account")]
    InvalidDestination,

    #[msg("Deadline exceeded: Transaction expired")]
    DeadlineExceeded,

    #[msg("Escrow expired: Maximum lifetime exceeded")]
    EscrowExpired,

    #[msg("Invalid lifetime: Must be non-negative")]
    InvalidLifetime,

    #[msg("Platform authority too new: Must wait 5 minutes")]
    PlatformAuthorityTooNew,

    #[msg("Trading authority too new: Must wait 5 minutes")]
    TradingAuthorityTooNew,

    #[msg("Stale transaction: Nonce mismatch")]
    StaleTransaction,

    #[msg("Cooldown not elapsed: Must wait 5 minutes after pause")]
    CooldownNotElapsed,

    #[msg("Invalid token decimals: Must be between 6 and 9")]
    InvalidTokenDecimals,

    #[msg("Rent not recovered: Token account still has lamports")]
    RentNotRecovered,

    #[msg("Unauthorized platform: Only platform authority can call")]
    UnauthorizedPlatform,

    #[msg("Unauthorized trading: Only trading authority can call")]
    UnauthorizedTrading,

    #[msg("Platform authority already set")]
    PlatformAuthorityAlreadySet,

    #[msg("Trading authority already set")]
    TradingAuthorityAlreadySet,
}
