-- ============================================================
-- POURTIER DATABASE SCHEMA (REFACTORED)
-- ============================================================
-- Purpose: User management, subscriptions, escrow management
-- Owner: Pourtier component
-- Database: pourtier_db
-- ============================================================

-- ============================================================
-- USERS (Wallet-based authentication + Escrow)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    wallet_address VARCHAR(44) UNIQUE NOT NULL,
    email VARCHAR(255),
    display_name VARCHAR(100),

    -- Escrow fields (ONE per user)
    escrow_account VARCHAR(44) UNIQUE,
    escrow_balance DECIMAL(20, 8) DEFAULT 0 NOT NULL,
    escrow_token_mint VARCHAR(44) DEFAULT 'USDC',
    escrow_initialized_at TIMESTAMP,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_wallet_length CHECK (
        LENGTH(wallet_address) >= 32
    ),
    CONSTRAINT positive_escrow_balance CHECK (
        escrow_balance >= 0
    ),
    CONSTRAINT escrow_account_length CHECK (
        escrow_account IS NULL OR LENGTH(escrow_account) >= 32
    )
);

-- ============================================================
-- SUBSCRIPTIONS (SaaS subscription management)
-- ============================================================
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_plan CHECK (
        plan_type IN ('free', 'basic', 'pro')
    ),
    CONSTRAINT valid_status CHECK (
        status IN ('active', 'cancelled', 'expired')
    ),
    CONSTRAINT expires_after_start CHECK (
        expires_at IS NULL OR expires_at > started_at
    )
);

-- ============================================================
-- PAYMENTS (Subscription payments)
-- ============================================================
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id UUID REFERENCES subscriptions(id)
        ON DELETE SET NULL,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(10) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    tx_signature VARCHAR(88),
    status VARCHAR(50) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_payment_method CHECK (
        payment_method IN ('solana_pay')
    ),
    CONSTRAINT valid_payment_status CHECK (
        status IN ('pending', 'completed', 'failed')
    ),
    CONSTRAINT positive_amount CHECK (amount > 0)
);

-- ============================================================
-- ESCROW_TRANSACTIONS (Transaction history)
-- ============================================================
CREATE TABLE IF NOT EXISTS escrow_transactions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tx_signature VARCHAR(88) UNIQUE NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    amount DECIMAL(20, 8) NOT NULL,
    token_mint VARCHAR(44) NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    confirmed_at TIMESTAMP,

    CONSTRAINT valid_transaction_type CHECK (
        transaction_type IN ('deposit', 'withdraw', 'initialize')
    ),
    CONSTRAINT valid_tx_status CHECK (
        status IN ('pending', 'confirmed', 'failed')
    ),
    CONSTRAINT confirmed_after_created CHECK (
        confirmed_at IS NULL OR confirmed_at >= created_at
    )
);

-- ============================================================
-- LEGAL_DOCUMENTS (Platform legal documents)
-- ============================================================
CREATE TABLE IF NOT EXISTS legal_documents (
    id UUID PRIMARY KEY,
    document_type VARCHAR(50) NOT NULL,
    version VARCHAR(20) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    status VARCHAR(20) NOT NULL,
    effective_date TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_document_type CHECK (
        document_type IN ('terms_of_service', 'privacy_policy')
    ),
    CONSTRAINT valid_document_status CHECK (
        status IN ('draft', 'active', 'archived')
    ),
    CONSTRAINT effective_after_created CHECK (
        effective_date IS NULL OR effective_date >= created_at
    )
);

-- ============================================================
-- USER_LEGAL_ACCEPTANCES (User acceptance tracking)
-- ============================================================
CREATE TABLE IF NOT EXISTS user_legal_acceptances (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_id UUID NOT NULL
        REFERENCES legal_documents(id) ON DELETE RESTRICT,
    accepted_at TIMESTAMP NOT NULL DEFAULT NOW(),
    acceptance_method VARCHAR(30) NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_acceptance_method CHECK (
        acceptance_method IN (
            'web_checkbox',
            'api_explicit',
            'migration_implicit'
        )
    ),
    CONSTRAINT unique_user_document UNIQUE (user_id, document_id)
);

-- ============================================================
-- INDEXES (Performance optimization)
-- ============================================================

-- Users indexes
CREATE INDEX IF NOT EXISTS idx_users_wallet
    ON users(wallet_address);
CREATE INDEX IF NOT EXISTS idx_users_created_at
    ON users(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_escrow_account
    ON users(escrow_account) WHERE escrow_account IS NOT NULL;

-- Subscriptions indexes
CREATE INDEX IF NOT EXISTS idx_subscriptions_user
    ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status
    ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_expires_at
    ON subscriptions(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_status
    ON subscriptions(user_id, status);

-- Payments indexes
CREATE INDEX IF NOT EXISTS idx_payments_user
    ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_subscription
    ON payments(subscription_id);
CREATE INDEX IF NOT EXISTS idx_payments_status
    ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_created_at
    ON payments(created_at DESC);

-- Escrow transactions indexes
CREATE INDEX IF NOT EXISTS idx_escrow_transactions_user
    ON escrow_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_escrow_transactions_type
    ON escrow_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_escrow_transactions_status
    ON escrow_transactions(status);
CREATE INDEX IF NOT EXISTS idx_escrow_transactions_created_at
    ON escrow_transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_escrow_tx_user_created
    ON escrow_transactions(user_id, created_at DESC);

-- Legal documents indexes
CREATE INDEX IF NOT EXISTS idx_legal_documents_type
    ON legal_documents(document_type);
CREATE INDEX IF NOT EXISTS idx_legal_documents_status
    ON legal_documents(status);
CREATE INDEX IF NOT EXISTS idx_legal_documents_type_status
    ON legal_documents(document_type, status);
CREATE INDEX IF NOT EXISTS idx_legal_documents_effective_date
    ON legal_documents(effective_date) WHERE effective_date IS NOT NULL;

-- User legal acceptances indexes
CREATE INDEX IF NOT EXISTS idx_user_legal_acceptances_user
    ON user_legal_acceptances(user_id);
CREATE INDEX IF NOT EXISTS idx_user_legal_acceptances_document
    ON user_legal_acceptances(document_id);
CREATE INDEX IF NOT EXISTS idx_user_legal_acceptances_accepted_at
    ON user_legal_acceptances(accepted_at DESC);

-- ============================================================
-- FUNCTIONS (Helper functions)
-- ============================================================

-- Function to update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ============================================================
-- TRIGGERS (Automatic timestamp updates)
-- ============================================================

-- Users trigger
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Subscriptions trigger
DROP TRIGGER IF EXISTS update_subscriptions_updated_at
    ON subscriptions;
CREATE TRIGGER update_subscriptions_updated_at
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Payments trigger
DROP TRIGGER IF EXISTS update_payments_updated_at ON payments;
CREATE TRIGGER update_payments_updated_at
    BEFORE UPDATE ON payments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Legal documents trigger
DROP TRIGGER IF EXISTS update_legal_documents_updated_at
    ON legal_documents;
CREATE TRIGGER update_legal_documents_updated_at
    BEFORE UPDATE ON legal_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- COMMENTS (Documentation)
-- ============================================================

COMMENT ON TABLE users IS
    'Platform users with Solana wallet + escrow account';
COMMENT ON TABLE subscriptions IS
    'SaaS subscription plans and status';
COMMENT ON TABLE payments IS
    'Payment transactions for subscriptions (Solana Pay only)';
COMMENT ON TABLE escrow_transactions IS
    'Escrow deposit/withdraw transaction history';
COMMENT ON TABLE legal_documents IS
    'Platform legal documents (Terms of Service, Privacy Policy)';
COMMENT ON TABLE user_legal_acceptances IS
    'Audit trail of user acceptances of legal documents';

COMMENT ON COLUMN users.wallet_address IS
    'Solana wallet address (32-44 chars base58)';
COMMENT ON COLUMN users.escrow_account IS
    'User escrow PDA (ONE per user, shared by all strategies)';
COMMENT ON COLUMN users.escrow_balance IS
    'Current escrow balance (updated after confirmed tx)';
COMMENT ON COLUMN users.escrow_token_mint IS
    'Token mint address (USDC, SOL, etc.)';
COMMENT ON COLUMN subscriptions.plan_type IS
    'Subscription tier: free, basic, pro';
COMMENT ON COLUMN escrow_transactions.tx_signature IS
    'Solana transaction signature';
COMMENT ON COLUMN legal_documents.document_type IS
    'Type of legal document: terms_of_service, privacy_policy';
COMMENT ON COLUMN legal_documents.status IS
    'Document lifecycle: draft, active, archived';
COMMENT ON COLUMN user_legal_acceptances.acceptance_method IS
    'How user accepted: web_checkbox, api_explicit, migration';
COMMENT ON COLUMN user_legal_acceptances.ip_address IS
    'User IP address at time of acceptance (audit trail)';
