"""Create initial database schema with full constraints and indexes

Revision ID: 6f6dcb3513f2
Revises:
Create Date: 2025-10-17 17:47:15.600395+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f6dcb3513f2'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with full constraints, indexes, and triggers."""
    
    # =================================================================
    # TABLE: legal_documents
    # =================================================================
    op.create_table(
        'legal_documents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('effective_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "document_type IN ('terms_of_service', 'privacy_policy')",
            name='valid_document_type'
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'active', 'archived')",
            name='valid_document_status'
        ),
        sa.CheckConstraint(
            'effective_date IS NULL OR effective_date >= created_at',
            name='effective_after_created'
        )
    )
    op.create_index(
        op.f('ix_legal_documents_document_type'),
        'legal_documents',
        ['document_type'],
        unique=False
    )
    op.create_index(
        op.f('ix_legal_documents_status'),
        'legal_documents',
        ['status'],
        unique=False
    )
    # Composite index for common query pattern
    op.create_index(
        'ix_legal_documents_type_status',
        'legal_documents',
        ['document_type', 'status'],
        unique=False
    )
    # Partial index for active documents
    op.create_index(
        'ix_legal_documents_effective_date',
        'legal_documents',
        ['effective_date'],
        unique=False,
        postgresql_where=sa.text('effective_date IS NOT NULL')
    )

    # =================================================================
    # TABLE: users
    # =================================================================
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('wallet_address', sa.String(length=44), nullable=False),
        sa.Column('escrow_account', sa.String(length=44), nullable=True),
        sa.Column('escrow_balance', sa.DECIMAL(precision=18, scale=6), nullable=False),
        sa.Column('escrow_token_mint', sa.String(length=44), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            'LENGTH(wallet_address) >= 32',
            name='valid_wallet_length'
        ),
        sa.CheckConstraint(
            'escrow_balance >= 0',
            name='positive_escrow_balance'
        ),
        sa.CheckConstraint(
            'escrow_account IS NULL OR LENGTH(escrow_account) >= 32',
            name='escrow_account_length'
        )
    )
    op.create_index(
        op.f('ix_users_wallet_address'),
        'users',
        ['wallet_address'],
        unique=True
    )
    op.create_index(
        'ix_users_created_at',
        'users',
        ['created_at'],
        unique=False,
        postgresql_ops={'created_at': 'DESC'}
    )
    # Partial index for users with escrow accounts
    op.create_index(
        'ix_users_escrow_account',
        'users',
        ['escrow_account'],
        unique=False,
        postgresql_where=sa.text('escrow_account IS NOT NULL')
    )

    # =================================================================
    # TABLE: subscriptions
    # =================================================================
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('plan_type', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            name='fk_subscriptions_user_id',
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "plan_type IN ('free', 'basic', 'pro')",
            name='valid_plan'
        ),
        sa.CheckConstraint(
            "status IN ('active', 'cancelled', 'expired')",
            name='valid_status'
        ),
        sa.CheckConstraint(
            'expires_at IS NULL OR expires_at > started_at',
            name='expires_after_start'
        )
    )
    op.create_index(
        op.f('ix_subscriptions_user_id'),
        'subscriptions',
        ['user_id'],
        unique=False
    )
    op.create_index(
        'ix_subscriptions_status',
        'subscriptions',
        ['status'],
        unique=False
    )
    # Composite index for common query: find user's active subscription
    op.create_index(
        'ix_subscriptions_user_status',
        'subscriptions',
        ['user_id', 'status'],
        unique=False
    )
    # Partial index for subscriptions with expiration
    op.create_index(
        'ix_subscriptions_expires_at',
        'subscriptions',
        ['expires_at'],
        unique=False,
        postgresql_where=sa.text('expires_at IS NOT NULL')
    )

    # =================================================================
    # TABLE: escrow_transactions
    # =================================================================
    op.create_table(
        'escrow_transactions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('tx_signature', sa.String(length=88), nullable=False),
        sa.Column('transaction_type', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.DECIMAL(precision=18, scale=6), nullable=False),
        sa.Column('token_mint', sa.String(length=44), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('subscription_id', sa.UUID(), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            name='fk_escrow_transactions_user_id',
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "transaction_type IN ('deposit', 'withdraw', 'initialize')",
            name='valid_transaction_type'
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'confirmed', 'failed')",
            name='valid_tx_status'
        ),
        sa.CheckConstraint(
            'confirmed_at IS NULL OR confirmed_at >= created_at',
            name='confirmed_after_created'
        )
    )
    op.create_index(
        op.f('ix_escrow_transactions_tx_signature'),
        'escrow_transactions',
        ['tx_signature'],
        unique=True
    )
    op.create_index(
        op.f('ix_escrow_transactions_user_id'),
        'escrow_transactions',
        ['user_id'],
        unique=False
    )
    op.create_index(
        'ix_escrow_transactions_type',
        'escrow_transactions',
        ['transaction_type'],
        unique=False
    )
    op.create_index(
        'ix_escrow_transactions_status',
        'escrow_transactions',
        ['status'],
        unique=False
    )
    op.create_index(
        'ix_escrow_transactions_created_at',
        'escrow_transactions',
        ['created_at'],
        unique=False,
        postgresql_ops={'created_at': 'DESC'}
    )
    # Composite index for common query: user's transaction history
    op.create_index(
        'ix_escrow_tx_user_created',
        'escrow_transactions',
        ['user_id', 'created_at'],
        unique=False,
        postgresql_ops={'created_at': 'DESC'}
    )

    # =================================================================
    # TABLE: user_legal_acceptances
    # =================================================================
    op.create_table(
        'user_legal_acceptances',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('accepted_at', sa.DateTime(), nullable=False),
        sa.Column('acceptance_method', sa.String(length=30), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['document_id'],
            ['legal_documents.id'],
            name='fk_user_legal_acceptances_document_id',
            ondelete='RESTRICT'
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            name='fk_user_legal_acceptances_user_id',
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'user_id',
            'document_id',
            name='unique_user_document'
        ),
        sa.CheckConstraint(
            "acceptance_method IN ('web_checkbox', 'api_explicit', 'migration_implicit')",
            name='valid_acceptance_method'
        )
    )
    op.create_index(
        op.f('ix_user_legal_acceptances_document_id'),
        'user_legal_acceptances',
        ['document_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_user_legal_acceptances_user_id'),
        'user_legal_acceptances',
        ['user_id'],
        unique=False
    )
    op.create_index(
        'ix_user_legal_acceptances_accepted_at',
        'user_legal_acceptances',
        ['accepted_at'],
        unique=False,
        postgresql_ops={'accepted_at': 'DESC'}
    )

    # =================================================================
    # TABLE: payments (DEPRECATED - kept for backward compatibility)
    # =================================================================
    op.create_table(
        'payments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('subscription_id', sa.UUID(), nullable=False),
        sa.Column('amount', sa.DECIMAL(precision=18, scale=6), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('tx_signature', sa.String(length=88), nullable=True),
        sa.Column('payment_metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['subscription_id'],
            ['subscriptions.id'],
            name='fk_payments_subscription_id',
            ondelete='SET NULL'
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            name='fk_payments_user_id',
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "status IN ('pending', 'completed', 'failed')",
            name='valid_payment_status'
        ),
        sa.CheckConstraint(
            'amount > 0',
            name='positive_amount'
        )
    )
    op.create_index(
        op.f('ix_payments_tx_signature'),
        'payments',
        ['tx_signature'],
        unique=True
    )
    op.create_index(
        op.f('ix_payments_user_id'),
        'payments',
        ['user_id'],
        unique=False
    )
    op.create_index(
        'ix_payments_subscription',
        'payments',
        ['subscription_id'],
        unique=False
    )
    op.create_index(
        'ix_payments_status',
        'payments',
        ['status'],
        unique=False
    )
    op.create_index(
        'ix_payments_created_at',
        'payments',
        ['created_at'],
        unique=False,
        postgresql_ops={'created_at': 'DESC'}
    )

    # =================================================================
    # TRIGGERS & FUNCTIONS (Optional - SQLAlchemy handles this)
    # =================================================================
    # NOTE: We DON'T add update_updated_at triggers because
    # SQLAlchemy models already have onupdate=datetime.now
    # which handles this at the application level.
    # Database-level triggers would be redundant and could conflict.

    # =================================================================
    # TABLE COMMENTS (Documentation)
    # =================================================================
    op.execute("""
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
        'Audit trail of user acceptances of legal documents';
    """)


def downgrade() -> None:
    """Downgrade schema - drop all tables and indexes."""
    
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('payments')
    op.drop_table('user_legal_acceptances')
    op.drop_table('subscriptions')
    op.drop_table('escrow_transactions')
    op.drop_table('users')
    op.drop_table('legal_documents')
    
    # Indexes are automatically dropped with tables
