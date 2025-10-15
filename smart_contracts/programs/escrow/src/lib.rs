use anchor_lang::prelude::*;
use anchor_spl::associated_token::AssociatedToken;
use anchor_spl::token::{self, CloseAccount, Mint, Token, TokenAccount, Transfer};

declare_id!("9gvUtaF99sQ287PNzRfCbhFTC4PUnnd7jdAjnY5GUVhS");

pub mod constants;
pub mod errors;
pub mod events;
pub mod state;

use constants::*;
use errors::*;
use events::*;
use state::*;

#[program]
pub mod escrow {
    use super::*;

    /// Initialize user escrow (one per user)
    ///
    /// Security:
    /// - User-only PDA derivation (no strategy_id)
    /// - Token decimals validation
    /// - Max balance enforcement
    pub fn initialize_escrow(
        ctx: Context<InitializeEscrow>,
        bump: u8,
        max_balance: u64,
    ) -> Result<()> {
        let escrow_key = ctx.accounts.escrow.key();
        let escrow = &mut ctx.accounts.escrow;
        let clock = Clock::get()?;
        let mint = &ctx.accounts.token_mint;

        // Validate max balance
        if max_balance > 0 {
            require!(
                max_balance <= MAX_ALLOWED_BALANCE,
                EscrowError::MaxBalanceExceeded
            );
        }

        // Validate token decimals
        require!(
            mint.decimals >= MIN_TOKEN_DECIMALS
                && mint.decimals <= MAX_TOKEN_DECIMALS,
            EscrowError::InvalidTokenDecimals
        );

        // Initialize state
        escrow.user = ctx.accounts.user.key();
        escrow.platform_authority = Pubkey::default();
        escrow.trading_authority = Pubkey::default();
        escrow.token_mint = mint.key();
        escrow.bump = bump;
        escrow.flags = 0;
        escrow.created_at = clock.unix_timestamp;
        escrow.platform_activated_at = 0;
        escrow.trading_activated_at = 0;
        escrow.last_paused_at = 0;
        escrow.action_nonce = 0;
        escrow.total_deposited = 0;
        escrow.total_withdrawn = 0;
        escrow.total_fees_paid = 0;
        escrow.total_traded = 0;
        escrow.max_balance = if max_balance == 0 {
            DEFAULT_MAX_BALANCE
        } else {
            max_balance
        };
        escrow.max_lifetime = 0;
        escrow.reserved = [0; 176];

        // Save values for event
        let user_key = escrow.user;
        let token_mint_key = escrow.token_mint;
        let timestamp = clock.unix_timestamp;

        emit!(EscrowInitialized {
            escrow: escrow_key,
            user: user_key,
            token_mint: token_mint_key,
            timestamp,
        });

        msg!("Escrow initialized for user");
        Ok(())
    }

    /// Deposit tokens to escrow
    ///
    /// Security:
    /// - Owner-only operation
    /// - Max balance check
    /// - Overflow protection
    /// - Expiration check
    pub fn deposit_token(
        ctx: Context<DepositToken>,
        amount: u64,
    ) -> Result<()> {
        let escrow_key = ctx.accounts.escrow.key();
        let escrow = &mut ctx.accounts.escrow;
        let clock = Clock::get()?;

        // CHECKS
        require!(!escrow.is_paused(), EscrowError::EscrowPaused);
        require!(amount > 0, EscrowError::InvalidAmount);
        require!(
            !escrow.is_expired(clock.unix_timestamp),
            EscrowError::EscrowExpired
        );

        let current_balance = ctx.accounts.escrow_token_account.amount;
        let new_balance = current_balance
            .checked_add(amount)
            .ok_or(EscrowError::MathOverflow)?;

        if escrow.max_balance > 0 {
            require!(
                new_balance <= escrow.max_balance,
                EscrowError::MaxBalanceExceeded
            );
        }

        // EFFECTS
        escrow.total_deposited = escrow
            .total_deposited
            .checked_add(amount)
            .ok_or(EscrowError::MathOverflow)?;
        escrow.action_nonce = escrow.action_nonce.wrapping_add(1);

        let timestamp = clock.unix_timestamp;

        // INTERACTIONS
        let cpi_accounts = Transfer {
            from: ctx.accounts.user_token_account.to_account_info(),
            to: ctx.accounts.escrow_token_account.to_account_info(),
            authority: ctx.accounts.user.to_account_info(),
        };
        token::transfer(
            CpiContext::new(
                ctx.accounts.token_program.to_account_info(),
                cpi_accounts,
            ),
            amount,
        )?;

        emit!(TokenDeposit {
            escrow: escrow_key,
            amount,
            new_balance,
            timestamp,
        });

        Ok(())
    }

    /// Delegate platform authority (Pourtier)
    ///
    /// Security:
    /// - Owner-only operation
    /// - Can only be set once
    /// - Cannot be default pubkey
    /// - 5-minute time-lock before use
    pub fn delegate_platform_authority(
        ctx: Context<DelegatePlatformAuthority>,
        platform_authority: Pubkey,
    ) -> Result<()> {
        let escrow_key = ctx.accounts.escrow.key();
        let escrow = &mut ctx.accounts.escrow;
        let clock = Clock::get()?;

        // CHECKS
        require!(!escrow.is_paused(), EscrowError::EscrowPaused);
        require!(
            platform_authority != Pubkey::default(),
            EscrowError::InvalidAuthority
        );
        require!(
            escrow.platform_authority == Pubkey::default(),
            EscrowError::PlatformAuthorityAlreadySet
        );
        require!(
            !escrow.is_expired(clock.unix_timestamp),
            EscrowError::EscrowExpired
        );

        // EFFECTS
        escrow.platform_authority = platform_authority;
        escrow.set_platform_active(true);
        escrow.platform_activated_at = clock.unix_timestamp;
        escrow.action_nonce = escrow.action_nonce.wrapping_add(1);

        let timestamp = clock.unix_timestamp;

        emit!(PlatformAuthorityDelegated {
            escrow: escrow_key,
            authority: platform_authority,
            timestamp,
        });

        msg!("Platform authority delegated");
        Ok(())
    }

    /// Delegate trading authority (Chevalier)
    ///
    /// Security:
    /// - Owner-only operation
    /// - Can only be set once
    /// - Cannot be default pubkey
    /// - 5-minute time-lock before use
    pub fn delegate_trading_authority(
        ctx: Context<DelegateTradingAuthority>,
        trading_authority: Pubkey,
    ) -> Result<()> {
        let escrow_key = ctx.accounts.escrow.key();
        let escrow = &mut ctx.accounts.escrow;
        let clock = Clock::get()?;

        // CHECKS
        require!(!escrow.is_paused(), EscrowError::EscrowPaused);
        require!(
            trading_authority != Pubkey::default(),
            EscrowError::InvalidAuthority
        );
        require!(
            escrow.trading_authority == Pubkey::default(),
            EscrowError::TradingAuthorityAlreadySet
        );
        require!(
            !escrow.is_expired(clock.unix_timestamp),
            EscrowError::EscrowExpired
        );

        // EFFECTS
        escrow.trading_authority = trading_authority;
        escrow.set_trading_active(true);
        escrow.trading_activated_at = clock.unix_timestamp;
        escrow.action_nonce = escrow.action_nonce.wrapping_add(1);

        let timestamp = clock.unix_timestamp;

        emit!(TradingAuthorityDelegated {
            escrow: escrow_key,
            authority: trading_authority,
            timestamp,
        });

        msg!("Trading authority delegated");
        Ok(())
    }

    /// Revoke platform authority
    ///
    /// Security:
    /// - Owner-only operation
    pub fn revoke_platform_authority(
        ctx: Context<RevokePlatformAuthority>,
    ) -> Result<()> {
        let escrow_key = ctx.accounts.escrow.key();
        let escrow = &mut ctx.accounts.escrow;
        let clock = Clock::get()?;

        // CHECKS
        require!(!escrow.is_paused(), EscrowError::EscrowPaused);

        // EFFECTS
        escrow.platform_authority = Pubkey::default();
        escrow.set_platform_active(false);
        escrow.platform_activated_at = 0;
        escrow.action_nonce = escrow.action_nonce.wrapping_add(1);

        let timestamp = clock.unix_timestamp;

        emit!(PlatformAuthorityRevoked {
            escrow: escrow_key,
            timestamp,
        });

        msg!("Platform authority revoked");
        Ok(())
    }

    /// Revoke trading authority
    ///
    /// Security:
    /// - Owner-only operation
    pub fn revoke_trading_authority(
        ctx: Context<RevokeTradingAuthority>,
    ) -> Result<()> {
        let escrow_key = ctx.accounts.escrow.key();
        let escrow = &mut ctx.accounts.escrow;
        let clock = Clock::get()?;

        // CHECKS
        require!(!escrow.is_paused(), EscrowError::EscrowPaused);

        // EFFECTS
        escrow.trading_authority = Pubkey::default();
        escrow.set_trading_active(false);
        escrow.trading_activated_at = 0;
        escrow.action_nonce = escrow.action_nonce.wrapping_add(1);

        let timestamp = clock.unix_timestamp;

        emit!(TradingAuthorityRevoked {
            escrow: escrow_key,
            timestamp,
        });

        msg!("Trading authority revoked");
        Ok(())
    }

    /// Withdraw subscription fee (platform only)
    ///
    /// Security:
    /// - Platform authority ONLY
    /// - 5-minute time-lock enforced
    /// - Max subscription fee limit
    /// - Separate accounting (total_fees_paid)
    pub fn withdraw_subscription_fee(
        ctx: Context<WithdrawSubscriptionFee>,
        amount: u64,
    ) -> Result<()> {
        let escrow_key = ctx.accounts.escrow.key();
        let escrow = &mut ctx.accounts.escrow;
        let clock = Clock::get()?;

        // CHECKS
        require!(!escrow.is_paused(), EscrowError::EscrowPaused);
        require!(amount > 0, EscrowError::InvalidAmount);
        require!(
            amount <= MAX_SUBSCRIPTION_FEE,
            EscrowError::AmountTooLarge
        );
        require!(
            ctx.accounts.platform_authority.key()
                == escrow.platform_authority,
            EscrowError::UnauthorizedPlatform
        );
        require!(
            escrow.is_platform_authority_mature(clock.unix_timestamp),
            EscrowError::PlatformAuthorityTooNew
        );

        let current_balance = ctx.accounts.escrow_token_account.amount;
        require!(
            amount <= current_balance,
            EscrowError::InsufficientBalance
        );

        // EFFECTS
        escrow.total_fees_paid = escrow
            .total_fees_paid
            .checked_add(amount)
            .ok_or(EscrowError::MathOverflow)?;
        escrow.action_nonce = escrow.action_nonce.wrapping_add(1);

        let remaining = current_balance.saturating_sub(amount);
        let user_ref = escrow.user;
        let bump_val = escrow.bump;
        let timestamp = clock.unix_timestamp;

        emit!(SubscriptionFeeWithdraw {
            escrow: escrow_key,
            amount,
            remaining_balance: remaining,
            timestamp,
        });

        // INTERACTIONS
        let seeds = &[b"escrow", user_ref.as_ref(), &[bump_val]];
        let signer = &[&seeds[..]];

        let cpi_accounts = Transfer {
            from: ctx.accounts.escrow_token_account.to_account_info(),
            to: ctx.accounts.platform_token_account.to_account_info(),
            authority: ctx.accounts.escrow.to_account_info(),
        };
        token::transfer(
            CpiContext::new_with_signer(
                ctx.accounts.token_program.to_account_info(),
                cpi_accounts,
                signer,
            ),
            amount,
        )?;

        msg!("Subscription fee withdrawn: {} tokens", amount);
        Ok(())
    }

    /// Withdraw for trade execution (trading bot only)
    ///
    /// Security:
    /// - Trading authority ONLY
    /// - 5-minute time-lock enforced
    /// - Max transaction amount limit
    /// - Separate accounting (total_traded)
    pub fn withdraw_for_trade(
        ctx: Context<WithdrawForTrade>,
        amount: u64,
    ) -> Result<()> {
        let escrow_key = ctx.accounts.escrow.key();
        let escrow = &mut ctx.accounts.escrow;
        let clock = Clock::get()?;

        // CHECKS
        require!(!escrow.is_paused(), EscrowError::EscrowPaused);
        require!(amount > 0, EscrowError::InvalidAmount);
        require!(
            amount <= MAX_TRANSACTION_AMOUNT,
            EscrowError::AmountTooLarge
        );
        require!(
            ctx.accounts.trading_authority.key()
                == escrow.trading_authority,
            EscrowError::UnauthorizedTrading
        );
        require!(
            escrow.is_trading_authority_mature(clock.unix_timestamp),
            EscrowError::TradingAuthorityTooNew
        );

        let current_balance = ctx.accounts.escrow_token_account.amount;
        require!(
            amount <= current_balance,
            EscrowError::InsufficientBalance
        );

        // EFFECTS
        escrow.total_traded = escrow
            .total_traded
            .checked_add(amount)
            .ok_or(EscrowError::MathOverflow)?;
        escrow.action_nonce = escrow.action_nonce.wrapping_add(1);

        let remaining = current_balance.saturating_sub(amount);
        let user_ref = escrow.user;
        let bump_val = escrow.bump;
        let timestamp = clock.unix_timestamp;

        emit!(TradeWithdraw {
            escrow: escrow_key,
            amount,
            remaining_balance: remaining,
            timestamp,
        });

        // INTERACTIONS
        let seeds = &[b"escrow", user_ref.as_ref(), &[bump_val]];
        let signer = &[&seeds[..]];

        let cpi_accounts = Transfer {
            from: ctx.accounts.escrow_token_account.to_account_info(),
            to: ctx.accounts.trading_token_account.to_account_info(),
            authority: ctx.accounts.escrow.to_account_info(),
        };
        token::transfer(
            CpiContext::new_with_signer(
                ctx.accounts.token_program.to_account_info(),
                cpi_accounts,
                signer,
            ),
            amount,
        )?;

        msg!("Trade withdrawal: {} tokens", amount);
        Ok(())
    }

    /// User withdrawal (when no authorities active)
    ///
    /// Security:
    /// - Owner-only operation
    /// - Cannot withdraw if ANY authority active
    /// - Must revoke authorities first
    pub fn withdraw_token(
        ctx: Context<WithdrawToken>,
        amount: u64,
    ) -> Result<()> {
        let escrow_key = ctx.accounts.escrow.key();
        let escrow = &mut ctx.accounts.escrow;
        let clock = Clock::get()?;

        // CHECKS
        require!(!escrow.is_paused(), EscrowError::EscrowPaused);
        require!(
            !escrow.has_active_authority(),
            EscrowError::EscrowStillActive
        );
        require!(amount > 0, EscrowError::InvalidAmount);

        let current_balance = ctx.accounts.escrow_token_account.amount;
        require!(
            amount <= current_balance,
            EscrowError::InsufficientBalance
        );

        // EFFECTS
        escrow.total_withdrawn = escrow
            .total_withdrawn
            .checked_add(amount)
            .ok_or(EscrowError::MathOverflow)?;
        escrow.action_nonce = escrow.action_nonce.wrapping_add(1);

        let remaining = current_balance.saturating_sub(amount);
        let user_ref = escrow.user;
        let bump_val = escrow.bump;
        let timestamp = clock.unix_timestamp;

        emit!(TokenWithdraw {
            escrow: escrow_key,
            amount,
            remaining_balance: remaining,
            timestamp,
        });

        // INTERACTIONS
        let seeds = &[b"escrow", user_ref.as_ref(), &[bump_val]];
        let signer = &[&seeds[..]];

        let cpi_accounts = Transfer {
            from: ctx.accounts.escrow_token_account.to_account_info(),
            to: ctx.accounts.user_token_account.to_account_info(),
            authority: ctx.accounts.escrow.to_account_info(),
        };
        token::transfer(
            CpiContext::new_with_signer(
                ctx.accounts.token_program.to_account_info(),
                cpi_accounts,
                signer,
            ),
            amount,
        )?;

        msg!("User withdrawal: {} tokens", amount);
        Ok(())
    }

    /// Emergency withdrawal (paused state only)
    ///
    /// Security:
    /// - Owner-only operation
    /// - Requires paused state
    /// - No active authorities allowed
    pub fn emergency_withdraw(
        ctx: Context<EmergencyWithdraw>,
        amount: u64,
    ) -> Result<()> {
        let escrow = &mut ctx.accounts.escrow;

        // CHECKS
        require!(escrow.is_paused(), EscrowError::EscrowNotPaused);
        require!(
            !escrow.has_active_authority(),
            EscrowError::EscrowStillActive
        );
        require!(amount > 0, EscrowError::InvalidAmount);

        let current_balance = ctx.accounts.escrow_token_account.amount;
        require!(
            amount <= current_balance,
            EscrowError::InsufficientBalance
        );

        // EFFECTS
        escrow.total_withdrawn = escrow
            .total_withdrawn
            .checked_add(amount)
            .ok_or(EscrowError::MathOverflow)?;
        escrow.action_nonce = escrow.action_nonce.wrapping_add(1);

        let user_ref = escrow.user;
        let bump_val = escrow.bump;

        // INTERACTIONS
        let seeds = &[b"escrow", user_ref.as_ref(), &[bump_val]];
        let signer = &[&seeds[..]];

        let cpi_accounts = Transfer {
            from: ctx.accounts.escrow_token_account.to_account_info(),
            to: ctx.accounts.user_token_account.to_account_info(),
            authority: ctx.accounts.escrow.to_account_info(),
        };
        token::transfer(
            CpiContext::new_with_signer(
                ctx.accounts.token_program.to_account_info(),
                cpi_accounts,
                signer,
            ),
            amount,
        )?;

        msg!("Emergency withdrawal: {} tokens", amount);
        Ok(())
    }

    /// Pause escrow (owner only)
    pub fn pause_escrow(ctx: Context<PauseEscrow>) -> Result<()> {
        let escrow_key = ctx.accounts.escrow.key();
        let escrow = &mut ctx.accounts.escrow;
        let clock = Clock::get()?;

        escrow.set_paused(true, clock.unix_timestamp);
        escrow.action_nonce = escrow.action_nonce.wrapping_add(1);

        let timestamp = clock.unix_timestamp;

        emit!(EscrowPaused {
            escrow: escrow_key,
            timestamp,
        });

        msg!("Escrow paused");
        Ok(())
    }

    /// Unpause escrow (owner only)
    ///
    /// Security:
    /// - 5-minute cooldown after pause
    pub fn unpause_escrow(ctx: Context<UnpauseEscrow>) -> Result<()> {
        let escrow_key = ctx.accounts.escrow.key();
        let escrow = &mut ctx.accounts.escrow;
        let clock = Clock::get()?;

        // CHECKS
        require!(
            escrow.can_unpause(clock.unix_timestamp),
            EscrowError::CooldownNotElapsed
        );

        // EFFECTS
        escrow.set_paused(false, clock.unix_timestamp);
        escrow.action_nonce = escrow.action_nonce.wrapping_add(1);

        let timestamp = clock.unix_timestamp;

        emit!(EscrowUnpaused {
            escrow: escrow_key,
            timestamp,
        });

        msg!("Escrow unpaused");
        Ok(())
    }

    /// Set max lifetime (owner only)
    pub fn set_max_lifetime(
        ctx: Context<SetMaxLifetime>,
        max_lifetime_seconds: i64,
    ) -> Result<()> {
        let escrow = &mut ctx.accounts.escrow;

        require!(
            max_lifetime_seconds >= 0,
            EscrowError::InvalidLifetime
        );

        escrow.max_lifetime = max_lifetime_seconds;
        escrow.action_nonce = escrow.action_nonce.wrapping_add(1);

        msg!("Max lifetime set: {} seconds", max_lifetime_seconds);
        Ok(())
    }

    /// Close escrow (owner only)
    ///
    /// Security:
    /// - No active authorities
    /// - Balance below dust threshold
    /// - Rent recovery validation
    pub fn close_escrow(ctx: Context<CloseEscrow>) -> Result<()> {
        let escrow_key = ctx.accounts.escrow.key();
        let escrow = &ctx.accounts.escrow;
        let clock = Clock::get()?;

        // CHECKS
        require!(!escrow.is_paused(), EscrowError::EscrowPaused);
        require!(
            !escrow.has_active_authority(),
            EscrowError::EscrowStillActive
        );

        let balance = ctx.accounts.escrow_token_account.amount;
        require!(balance <= DUST_THRESHOLD, EscrowError::EscrowNotEmpty);

        let token_account_lamports = ctx
            .accounts
            .escrow_token_account
            .to_account_info()
            .lamports();
        require!(
            token_account_lamports >= MIN_RENT_EXEMPT_LAMPORTS,
            EscrowError::RentNotRecovered
        );

        let user_ref = escrow.user;
        let bump_val = escrow.bump;
        let timestamp = clock.unix_timestamp;

        emit!(EscrowClosed {
            escrow: escrow_key,
            timestamp,
        });

        // INTERACTIONS
        let seeds = &[b"escrow", user_ref.as_ref(), &[bump_val]];
        let signer = &[&seeds[..]];

        let cpi_accounts = CloseAccount {
            account: ctx.accounts.escrow_token_account.to_account_info(),
            destination: ctx.accounts.user.to_account_info(),
            authority: ctx.accounts.escrow.to_account_info(),
        };
        token::close_account(CpiContext::new_with_signer(
            ctx.accounts.token_program.to_account_info(),
            cpi_accounts,
            signer,
        ))?;

        msg!("Escrow closed - rent recovered");
        Ok(())
    }
}

// ============================================================
// ACCOUNT VALIDATION STRUCTS
// ============================================================

#[derive(Accounts)]
#[instruction(bump: u8, max_balance: u64)]
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

#[derive(Accounts)]
pub struct DepositToken<'info> {
    #[account(
        mut,
        seeds = [b"escrow", user.key().as_ref()],
        bump = escrow.bump,
        has_one = user @ EscrowError::Unauthorized,
        has_one = token_mint @ EscrowError::InvalidTokenMint
    )]
    pub escrow: Account<'info, EscrowAccount>,

    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = escrow
    )]
    pub escrow_token_account: Account<'info, TokenAccount>,

    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = user
    )]
    pub user_token_account: Account<'info, TokenAccount>,

    pub token_mint: Account<'info, Mint>,

    #[account(mut)]
    pub user: Signer<'info>,

    pub token_program: Program<'info, Token>,
}

#[derive(Accounts)]
pub struct DelegatePlatformAuthority<'info> {
    #[account(
        mut,
        seeds = [b"escrow", user.key().as_ref()],
        bump = escrow.bump,
        has_one = user @ EscrowError::Unauthorized
    )]
    pub escrow: Account<'info, EscrowAccount>,

    pub user: Signer<'info>,
}

#[derive(Accounts)]
pub struct DelegateTradingAuthority<'info> {
    #[account(
        mut,
        seeds = [b"escrow", user.key().as_ref()],
        bump = escrow.bump,
        has_one = user @ EscrowError::Unauthorized
    )]
    pub escrow: Account<'info, EscrowAccount>,

    pub user: Signer<'info>,
}

#[derive(Accounts)]
pub struct RevokePlatformAuthority<'info> {
    #[account(
        mut,
        seeds = [b"escrow", user.key().as_ref()],
        bump = escrow.bump,
        has_one = user @ EscrowError::Unauthorized
    )]
    pub escrow: Account<'info, EscrowAccount>,

    pub user: Signer<'info>,
}

#[derive(Accounts)]
pub struct RevokeTradingAuthority<'info> {
    #[account(
        mut,
        seeds = [b"escrow", user.key().as_ref()],
        bump = escrow.bump,
        has_one = user @ EscrowError::Unauthorized
    )]
    pub escrow: Account<'info, EscrowAccount>,

    pub user: Signer<'info>,
}

#[derive(Accounts)]
pub struct WithdrawSubscriptionFee<'info> {
    #[account(
        mut,
        seeds = [b"escrow", escrow.user.as_ref()],
        bump = escrow.bump,
        has_one = token_mint @ EscrowError::InvalidTokenMint
    )]
    pub escrow: Account<'info, EscrowAccount>,

    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = escrow
    )]
    pub escrow_token_account: Account<'info, TokenAccount>,

    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = platform_authority
    )]
    pub platform_token_account: Account<'info, TokenAccount>,

    pub token_mint: Account<'info, Mint>,

    pub platform_authority: Signer<'info>,

    pub token_program: Program<'info, Token>,
}

#[derive(Accounts)]
pub struct WithdrawForTrade<'info> {
    #[account(
        mut,
        seeds = [b"escrow", escrow.user.as_ref()],
        bump = escrow.bump,
        has_one = token_mint @ EscrowError::InvalidTokenMint
    )]
    pub escrow: Account<'info, EscrowAccount>,

    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = escrow
    )]
    pub escrow_token_account: Account<'info, TokenAccount>,

    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = trading_authority
    )]
    pub trading_token_account: Account<'info, TokenAccount>,

    pub token_mint: Account<'info, Mint>,

    pub trading_authority: Signer<'info>,

    pub token_program: Program<'info, Token>,
}

#[derive(Accounts)]
pub struct WithdrawToken<'info> {
    #[account(
        mut,
        seeds = [b"escrow", user.key().as_ref()],
        bump = escrow.bump,
        has_one = user @ EscrowError::Unauthorized,
        has_one = token_mint @ EscrowError::InvalidTokenMint
    )]
    pub escrow: Account<'info, EscrowAccount>,

    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = escrow
    )]
    pub escrow_token_account: Account<'info, TokenAccount>,

    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = user
    )]
    pub user_token_account: Account<'info, TokenAccount>,

    pub token_mint: Account<'info, Mint>,

    #[account(mut)]
    pub user: Signer<'info>,

    pub token_program: Program<'info, Token>,
}

#[derive(Accounts)]
pub struct EmergencyWithdraw<'info> {
    #[account(
        mut,
        seeds = [b"escrow", user.key().as_ref()],
        bump = escrow.bump,
        has_one = user @ EscrowError::Unauthorized,
        has_one = token_mint @ EscrowError::InvalidTokenMint
    )]
    pub escrow: Account<'info, EscrowAccount>,

    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = escrow
    )]
    pub escrow_token_account: Account<'info, TokenAccount>,

    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = user
    )]
    pub user_token_account: Account<'info, TokenAccount>,

    pub token_mint: Account<'info, Mint>,

    #[account(mut)]
    pub user: Signer<'info>,

    pub token_program: Program<'info, Token>,
}

#[derive(Accounts)]
pub struct PauseEscrow<'info> {
    #[account(
        mut,
        seeds = [b"escrow", user.key().as_ref()],
        bump = escrow.bump,
        has_one = user @ EscrowError::Unauthorized
    )]
    pub escrow: Account<'info, EscrowAccount>,

    pub user: Signer<'info>,
}

#[derive(Accounts)]
pub struct UnpauseEscrow<'info> {
    #[account(
        mut,
        seeds = [b"escrow", user.key().as_ref()],
        bump = escrow.bump,
        has_one = user @ EscrowError::Unauthorized
    )]
    pub escrow: Account<'info, EscrowAccount>,

    pub user: Signer<'info>,
}

#[derive(Accounts)]
pub struct SetMaxLifetime<'info> {
    #[account(
        mut,
        seeds = [b"escrow", user.key().as_ref()],
        bump = escrow.bump,
        has_one = user @ EscrowError::Unauthorized
    )]
    pub escrow: Account<'info, EscrowAccount>,

    pub user: Signer<'info>,
}

#[derive(Accounts)]
pub struct CloseEscrow<'info> {
    #[account(
        mut,
        seeds = [b"escrow", user.key().as_ref()],
        bump = escrow.bump,
        has_one = user @ EscrowError::Unauthorized,
        close = user
    )]
    pub escrow: Account<'info, EscrowAccount>,

    #[account(
        mut,
        associated_token::mint = escrow.token_mint,
        associated_token::authority = escrow
    )]
    pub escrow_token_account: Account<'info, TokenAccount>,

    #[account(mut)]
    pub user: Signer<'info>,

    pub token_program: Program<'info, Token>,
}
