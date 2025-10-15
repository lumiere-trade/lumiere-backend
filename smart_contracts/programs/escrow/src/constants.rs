/// Constants for dual authority user-based escrow

// Balance limits
pub const DEFAULT_MAX_BALANCE: u64 = 1_000_000_000_000; // 1M USDC (6 decimals)
pub const MAX_ALLOWED_BALANCE: u64 = 10_000_000_000_000; // 10M USDC
pub const MAX_TRANSACTION_AMOUNT: u64 = 100_000_000_000; // 100k USDC per trade
pub const DUST_THRESHOLD: u64 = 10; // Min balance for closure

// Security timeouts
pub const TIMESTAMP_TOLERANCE: i64 = 30; // 30s clock tolerance
pub const MIN_AUTHORITY_AGE: i64 = 300; // 5 minutes time-lock
pub const UNPAUSE_COOLDOWN: i64 = 300; // 5 minutes cooldown

// Token validation
pub const MIN_TOKEN_DECIMALS: u8 = 6;
pub const MAX_TOKEN_DECIMALS: u8 = 9;

// Rent exemption (typical token account rent)
pub const MIN_RENT_EXEMPT_LAMPORTS: u64 = 2_039_280; // ~0.00203928 SOL

// Subscription fee limits (per month)
pub const MAX_SUBSCRIPTION_FEE: u64 = 1_000_000_000; // 1000 USDC max monthly

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_constants_sanity() {
        assert!(DEFAULT_MAX_BALANCE < MAX_ALLOWED_BALANCE);
        assert!(MAX_TRANSACTION_AMOUNT < DEFAULT_MAX_BALANCE);
        assert!(MIN_AUTHORITY_AGE >= TIMESTAMP_TOLERANCE);
        assert!(MAX_SUBSCRIPTION_FEE < MAX_TRANSACTION_AMOUNT);
    }
}
