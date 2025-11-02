"""
SQLAlchemy models for Pourtier persistence.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DECIMAL,
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""


class UserModel(Base):
    """User database model - Web3 wallet-based identity."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    wallet_address: Mapped[str] = mapped_column(
        String(44), unique=True, index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Relationships
    subscriptions: Mapped[list["SubscriptionModel"]] = relationship(
        "SubscriptionModel",
        back_populates="user",
        lazy="select",
        cascade="all, delete-orphan",
    )
    payments: Mapped[list["PaymentModel"]] = relationship(
        "PaymentModel",
        back_populates="user",
        lazy="select",
        cascade="all, delete-orphan",
    )
    escrow_transactions: Mapped[list["EscrowTransactionModel"]] = relationship(
        "EscrowTransactionModel",
        back_populates="user",
        lazy="select",
        cascade="all, delete-orphan",
    )
    legal_acceptances: Mapped[list["UserLegalAcceptanceModel"]] = relationship(
        "UserLegalAcceptanceModel",
        back_populates="user",
        lazy="select",
        cascade="all, delete-orphan",
    )


class SubscriptionModel(Base):
    """Subscription database model."""

    __tablename__ = "subscriptions"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False
    )
    plan_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    user: Mapped["UserModel"] = relationship(
        "UserModel", back_populates="subscriptions", lazy="select"
    )
    payments: Mapped[list["PaymentModel"]] = relationship(
        "PaymentModel",
        back_populates="subscription",
        lazy="select",
        cascade="all, delete-orphan",
    )


class PaymentModel(Base):
    """Payment database model - DEPRECATED, use EscrowTransaction."""

    __tablename__ = "payments"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False
    )
    subscription_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=18, scale=6), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    tx_signature: Mapped[str | None] = mapped_column(
        String(88), unique=True, index=True
    )
    payment_metadata: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    user: Mapped["UserModel"] = relationship(
        "UserModel", back_populates="payments", lazy="select"
    )
    subscription: Mapped["SubscriptionModel"] = relationship(
        "SubscriptionModel", back_populates="payments", lazy="select"
    )


class EscrowTransactionModel(Base):
    """Escrow transaction database model."""

    __tablename__ = "escrow_transactions"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False
    )
    tx_signature: Mapped[str] = mapped_column(
        String(88), unique=True, index=True, nullable=False
    )
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=18, scale=6), nullable=False
    )
    token_mint: Mapped[str] = mapped_column(String(44), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    subscription_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    user: Mapped["UserModel"] = relationship(
        "UserModel", back_populates="escrow_transactions", lazy="select"
    )


class LegalDocumentModel(Base):
    """Legal document database model."""

    __tablename__ = "legal_documents"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    effective_date: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    user_acceptances: Mapped[list["UserLegalAcceptanceModel"]] = relationship(
        "UserLegalAcceptanceModel",
        back_populates="legal_document",
        lazy="select",
        cascade="all, delete-orphan",
    )


class UserLegalAcceptanceModel(Base):
    """User legal acceptance database model."""

    __tablename__ = "user_legal_acceptances"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False
    )
    document_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("legal_documents.id"),
        index=True,
        nullable=False,
    )
    accepted_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    acceptance_method: Mapped[str] = mapped_column(String(30), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Relationships
    user: Mapped["UserModel"] = relationship(
        "UserModel", back_populates="legal_acceptances", lazy="select"
    )
    legal_document: Mapped["LegalDocumentModel"] = relationship(
        "LegalDocumentModel", back_populates="user_acceptances", lazy="select"
    )
