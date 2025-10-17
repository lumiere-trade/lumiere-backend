BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 6f6dcb3513f2

CREATE TABLE legal_documents (
    id UUID NOT NULL, 
    document_type VARCHAR(50) NOT NULL, 
    version VARCHAR(20) NOT NULL, 
    title VARCHAR(200) NOT NULL, 
    content TEXT NOT NULL, 
    status VARCHAR(20) NOT NULL, 
    effective_date TIMESTAMP WITHOUT TIME ZONE, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT valid_document_type CHECK (document_type IN ('terms_of_service', 'privacy_policy')), 
    CONSTRAINT valid_document_status CHECK (status IN ('draft', 'active', 'archived')), 
    CONSTRAINT effective_after_created CHECK (effective_date IS NULL OR effective_date >= created_at)
);

CREATE INDEX ix_legal_documents_document_type ON legal_documents (document_type);

CREATE INDEX ix_legal_documents_status ON legal_documents (status);

CREATE INDEX ix_legal_documents_type_status ON legal_documents (document_type, status);

CREATE INDEX ix_legal_documents_effective_date ON legal_documents (effective_date) WHERE effective_date IS NOT NULL;

CREATE TABLE users (
    id UUID NOT NULL, 
    wallet_address VARCHAR(44) NOT NULL, 
    escrow_account VARCHAR(44), 
    escrow_balance DECIMAL(18, 6) NOT NULL, 
    escrow_token_mint VARCHAR(44), 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT valid_wallet_length CHECK (LENGTH(wallet_address) >= 32), 
    CONSTRAINT positive_escrow_balance CHECK (escrow_balance >= 0), 
    CONSTRAINT escrow_account_length CHECK (escrow_account IS NULL OR LENGTH(escrow_account) >= 32)
);

CREATE UNIQUE INDEX ix_users_wallet_address ON users (wallet_address);

CREATE INDEX ix_users_created_at ON users (created_at DESC);

CREATE INDEX ix_users_escrow_account ON users (escrow_account) WHERE escrow_account IS NOT NULL;

CREATE TABLE subscriptions (
    id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    plan_type VARCHAR(20) NOT NULL, 
    status VARCHAR(20) NOT NULL, 
    started_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    expires_at TIMESTAMP WITHOUT TIME ZONE, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT fk_subscriptions_user_id FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT valid_plan CHECK (plan_type IN ('free', 'basic', 'pro')), 
    CONSTRAINT valid_status CHECK (status IN ('active', 'cancelled', 'expired')), 
    CONSTRAINT expires_after_start CHECK (expires_at IS NULL OR expires_at > started_at)
);

CREATE INDEX ix_subscriptions_user_id ON subscriptions (user_id);

CREATE INDEX ix_subscriptions_status ON subscriptions (status);

CREATE INDEX ix_subscriptions_user_status ON subscriptions (user_id, status);

CREATE INDEX ix_subscriptions_expires_at ON subscriptions (expires_at) WHERE expires_at IS NOT NULL;

CREATE TABLE escrow_transactions (
    id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    tx_signature VARCHAR(88) NOT NULL, 
    transaction_type VARCHAR(20) NOT NULL, 
    amount DECIMAL(18, 6) NOT NULL, 
    token_mint VARCHAR(44) NOT NULL, 
    status VARCHAR(20) NOT NULL, 
    subscription_id UUID, 
    confirmed_at TIMESTAMP WITHOUT TIME ZONE, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT fk_escrow_transactions_user_id FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT valid_transaction_type CHECK (transaction_type IN ('deposit', 'withdraw', 'initialize')), 
    CONSTRAINT valid_tx_status CHECK (status IN ('pending', 'confirmed', 'failed')), 
    CONSTRAINT confirmed_after_created CHECK (confirmed_at IS NULL OR confirmed_at >= created_at)
);

CREATE UNIQUE INDEX ix_escrow_transactions_tx_signature ON escrow_transactions (tx_signature);

CREATE INDEX ix_escrow_transactions_user_id ON escrow_transactions (user_id);

CREATE INDEX ix_escrow_transactions_type ON escrow_transactions (transaction_type);

CREATE INDEX ix_escrow_transactions_status ON escrow_transactions (status);

CREATE INDEX ix_escrow_transactions_created_at ON escrow_transactions (created_at DESC);

CREATE INDEX ix_escrow_tx_user_created ON escrow_transactions (user_id, created_at DESC);

CREATE TABLE user_legal_acceptances (
    id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    document_id UUID NOT NULL, 
    accepted_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    acceptance_method VARCHAR(30) NOT NULL, 
    ip_address VARCHAR(45), 
    user_agent VARCHAR(500), 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT fk_user_legal_acceptances_document_id FOREIGN KEY(document_id) REFERENCES legal_documents (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_user_legal_acceptances_user_id FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT unique_user_document UNIQUE (user_id, document_id), 
    CONSTRAINT valid_acceptance_method CHECK (acceptance_method IN ('web_checkbox', 'api_explicit', 'migration_implicit'))
);

CREATE INDEX ix_user_legal_acceptances_document_id ON user_legal_acceptances (document_id);

CREATE INDEX ix_user_legal_acceptances_user_id ON user_legal_acceptances (user_id);

CREATE INDEX ix_user_legal_acceptances_accepted_at ON user_legal_acceptances (accepted_at DESC);

CREATE TABLE payments (
    id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    subscription_id UUID NOT NULL, 
    amount DECIMAL(18, 6) NOT NULL, 
    currency VARCHAR(10) NOT NULL, 
    status VARCHAR(20) NOT NULL, 
    tx_signature VARCHAR(88), 
    payment_metadata TEXT, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT fk_payments_subscription_id FOREIGN KEY(subscription_id) REFERENCES subscriptions (id) ON DELETE SET NULL, 
    CONSTRAINT fk_payments_user_id FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT valid_payment_status CHECK (status IN ('pending', 'completed', 'failed')), 
    CONSTRAINT positive_amount CHECK (amount > 0)
);

CREATE UNIQUE INDEX ix_payments_tx_signature ON payments (tx_signature);

CREATE INDEX ix_payments_user_id ON payments (user_id);

CREATE INDEX ix_payments_subscription ON payments (subscription_id);

CREATE INDEX ix_payments_status ON payments (status);

CREATE INDEX ix_payments_created_at ON payments (created_at DESC);

COMMENT ON TABLE users IS 
        'Platform users with Solana wallet + escrow account';
        
        COMMENT ON TABLE subscriptions IS 
        'SaaS subscription plans and status';
        
        COMMENT ON TABLE payments IS 
        'Payment transactions for subscriptions (DEPRECATED - use escrow_transactions)';
        
        COMMENT ON TABLE escrow_transactions IS 
        'Escrow deposit/withdraw transaction history';
        
        COMMENT ON TABLE legal_documents IS 
        'Platform legal documents (Terms of Service, Privacy Policy)';
        
        COMMENT ON TABLE user_legal_acceptances IS 
        'Audit trail of user acceptances of legal documents';;

INSERT INTO alembic_version (version_num) VALUES ('6f6dcb3513f2') RETURNING alembic_version.version_num;

COMMIT;

