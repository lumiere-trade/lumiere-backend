use anchor_lang::prelude::*;
use crate::constants::*;

/// User-based escrow with dual authority model
///
/// Architecture:
/// - One escrow per user (no strategy_id in PDA)
/// - Platform authority: Monthly subscription fees
/// - Trading authority: Execute trades via Chevalier bot
///
/// Security features:
/// - Nonce-based replay protection
/// - Separate authority roles
/// - Time-lock delegation (5 minutes)
/// - Pause mechanism
/// - Owner-only controls
/// - Rent exemption checks
/// - Strict CEI pattern
///
/// Seeds: ["escrow", user_pubkey]
#[account]
pub struct EscrowAccount {
    /// Owner of the escrow
    pub user: Pubkey,

    /// Platform authority (Pourtier) - subscription fees only
    pub platform_authority: Pubkey,

    /// Trading authority (Chevalier) - execute trades only
    pub trading_authority: Pubkey,

    /// Token mint (USDC, etc)
    pub token_mint: Pubkey,

    /// PDA bump seed
    pub bump: u8,

    /// Flags: [platform_active, trading_active, is_paused, reserved...]
    pub flags: u8,

    /// Creation timestamp
    pub created_at: i64,

    /// Platform authority activation timestamp
    pub platform_activated_at: i64,

    /// Trading authority activation timestamp
    pub trading_activated_at: i64,

    /// Last pause timestamp (for cooldown)
    pub last_paused_at: i64,

    /// Action nonce (replay protection)
    pub action_nonce: u64,

    /// Analytics
    pub total_deposited: u64,
    pub total_withdrawn: u64,
    pub total_fees_paid: u64,
    pub total_traded: u64,

    /// Limits
    pub max_balance: u64,
    pub max_lifetime: i64,

    /// Reserved for future upgrades
    pub reserved: [u8; 176],
}

impl EscrowAccount {
    /// Account space calculation for rent exemption
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

    // ========== Flag Bit Positions ==========
    const FLAG_PLATFORM_ACTIVE: u8 = 0b0001;
    const FLAG_TRADING_ACTIVE: u8 = 0b0010;
    const FLAG_PAUSED: u8 = 0b0100;

    // ========== Platform Authority Checks ==========

    /// Check if platform authority is active
    #[inline]
    pub fn is_platform_active(&self) -> bool {
        self.flags & Self::FLAG_PLATFORM_ACTIVE != 0
    }

    /// Set platform active flag
    pub fn set_platform_active(&mut self, active: bool) {
        if active {
            self.flags |= Self::FLAG_PLATFORM_ACTIVE;
        } else {
            self.flags &= !Self::FLAG_PLATFORM_ACTIVE;
        }
    }

    // ========== Trading Authority Checks ==========

    /// Check if trading authority is active
    #[inline]
    pub fn is_trading_active(&self) -> bool {
        self.flags & Self::FLAG_TRADING_ACTIVE != 0
    }

    /// Set trading active flag
    pub fn set_trading_active(&mut self, active: bool) {
        if active {
            self.flags |= Self::FLAG_TRADING_ACTIVE;
        } else {
            self.flags &= !Self::FLAG_TRADING_ACTIVE;
        }
    }

    // ========== Pause Checks ==========

    /// Check if escrow is paused
    #[inline]
    pub fn is_paused(&self) -> bool {
        self.flags & Self::FLAG_PAUSED != 0
    }

    /// Set paused flag and update timestamp
    pub fn set_paused(&mut self, paused: bool, timestamp: i64) {
        if paused {
            self.flags |= Self::FLAG_PAUSED;
            self.last_paused_at = timestamp;
        } else {
            self.flags &= !Self::FLAG_PAUSED;
        }
    }

    // ========== General Checks ==========

    /// Check if ANY authority is active (user can't withdraw)
    #[inline]
    pub fn has_active_authority(&self) -> bool {
        self.is_platform_active() || self.is_trading_active()
    }

    /// Check if escrow has expired based on max_lifetime
    #[inline]
    pub fn is_expired(&self, current_timestamp: i64) -> bool {
        if self.max_lifetime == 0 {
            return false;
        }
        current_timestamp - self.created_at > self.max_lifetime
    }

    /// Check if enough time passed since pause (cooldown)
    #[inline]
    pub fn can_unpause(&self, current_timestamp: i64) -> bool {
        if self.last_paused_at == 0 {
            return true;
        }
        current_timestamp - self.last_paused_at >= UNPAUSE_COOLDOWN
    }

    /// Check if platform authority is old enough (time-lock)
    #[inline]
    pub fn is_platform_authority_mature(
        &self,
        current_timestamp: i64,
    ) -> bool {
        if self.platform_activated_at == 0 {
            return false;
        }
        current_timestamp - self.platform_activated_at >= MIN_AUTHORITY_AGE
    }

    /// Check if trading authority is old enough (time-lock)
    #[inline]
    pub fn is_trading_authority_mature(
        &self,
        current_timestamp: i64,
    ) -> bool {
        if self.trading_activated_at == 0 {
            return false;
        }
        current_timestamp - self.trading_activated_at >= MIN_AUTHORITY_AGE
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_escrow() -> EscrowAccount {
        EscrowAccount {
            user: Pubkey::default(),
            platform_authority: Pubkey::default(),
            trading_authority: Pubkey::default(),
            token_mint: Pubkey::default(),
            bump: 255,
            flags: 0,
            created_at: 1000,
            platform_activated_at: 0,
            trading_activated_at: 0,
            last_paused_at: 0,
            action_nonce: 0,
            total_deposited: 0,
            total_withdrawn: 0,
            total_fees_paid: 0,
            total_traded: 0,
            max_balance: 0,
            max_lifetime: 0,
            reserved: [0; 176],
        }
    }

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

        escrow.set_platform_active(false);
        assert!(escrow.has_active_authority()); // Still trading active

        escrow.set_trading_active(false);
        assert!(!escrow.has_active_authority());
    }

    #[test]
    fn test_pause() {
        let mut escrow = create_test_escrow();

        assert!(!escrow.is_paused());
        escrow.set_paused(true, 100);
        assert!(escrow.is_paused());
        assert_eq!(escrow.last_paused_at, 100);
    }

    #[test]
    fn test_authority_maturity() {
        let mut escrow = create_test_escrow();

        // Platform authority
        assert!(!escrow.is_platform_authority_mature(1300));
        escrow.platform_activated_at = 1000;
        assert!(!escrow.is_platform_authority_mature(1299));
        assert!(escrow.is_platform_authority_mature(1300));

        // Trading authority
        assert!(!escrow.is_trading_authority_mature(1300));
        escrow.trading_activated_at = 1000;
        assert!(!escrow.is_trading_authority_mature(1299));
        assert!(escrow.is_trading_authority_mature(1300));
    }

    #[test]
    fn test_expiration() {
        let mut escrow = create_test_escrow();

        assert!(!escrow.is_expired(5000));

        escrow.max_lifetime = 100;
        assert!(!escrow.is_expired(1050));
        assert!(!escrow.is_expired(1100));
        assert!(escrow.is_expired(1101));
    }

    #[test]
    fn test_cooldown() {
        let mut escrow = create_test_escrow();

        assert!(escrow.can_unpause(5000));

        escrow.set_paused(true, 1000);
        assert!(!escrow.can_unpause(1000));
        assert!(!escrow.can_unpause(1299));
        assert!(escrow.can_unpause(1300));
    }
}
