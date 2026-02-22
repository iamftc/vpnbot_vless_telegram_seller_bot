"""
SQLAlchemy ORM models — PostgreSQL.
Preserves original data schema, adds indexes, FKs, new tables.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    is_dealer: Mapped[bool] = mapped_column(Boolean, default=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    referral_code: Mapped[Optional[str]] = mapped_column(String(16), unique=True, nullable=True)
    referred_by: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=True
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    notified_3days: Mapped[bool] = mapped_column(Boolean, default=False)

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user")

    __table_args__ = (
        Index("ix_users_username", "username"),
        Index("ix_users_referral_code", "referral_code"),
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=False
    )
    client_name: Mapped[str] = mapped_column(String(128))
    email: Mapped[str] = mapped_column(String(128), unique=True)
    client_id: Mapped[str] = mapped_column(String(64))
    inbound_id: Mapped[int] = mapped_column(Integer)
    inbound_name: Mapped[str] = mapped_column(String(128))
    expiry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_by_dealer_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    dealer_username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    plan_type: Mapped[str] = mapped_column(String(16))
    payment_method: Mapped[str] = mapped_column(String(16), default="free")
    notified_3days: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="subscriptions")

    __table_args__ = (
        Index("ix_subscriptions_user_id", "user_id"),
        Index("ix_subscriptions_expiry", "expiry_date"),
        Index("ix_subscriptions_email", "email"),
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=False
    )
    amount: Mapped[float] = mapped_column(Float)
    type: Mapped[str] = mapped_column(String(32))
    payment_method: Mapped[str] = mapped_column(String(16), default="cash")
    stars_count: Mapped[int] = mapped_column(Integer, default=0)
    idempotency_key: Mapped[Optional[str]] = mapped_column(
        String(128), unique=True, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="transactions")

    __table_args__ = (
        Index("ix_transactions_user_id", "user_id"),
        Index("ix_transactions_idempotency", "idempotency_key"),
    )


class CryptoInvoice(Base):
    __tablename__ = "crypto_invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    invoice_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    amount: Mapped[float] = mapped_column(Float)
    days: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_crypto_invoices_status", "status"),
    )


class RequiredChannel(Base):
    __tablename__ = "required_channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[str] = mapped_column(String(32), unique=True)
    channel_title: Mapped[str] = mapped_column(String(128))
    channel_url: Mapped[str] = mapped_column(String(256))
    type: Mapped[str] = mapped_column(String(16), default="daily")


class DailyGiveaway(Base):
    __tablename__ = "daily_giveaway"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    last_claimed: Mapped[str] = mapped_column(String(10))


class AuditLog(Base):
    """New table for security auditing."""
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    action: Mapped[str] = mapped_column(String(64))
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_audit_user_id", "user_id"),
        Index("ix_audit_action", "action"),
    )


class Referral(Base):
    """New table for referral tracking."""
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    referrer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"))
    referred_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"))
    bonus_days: Mapped[int] = mapped_column(Integer, default=3)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("referrer_id", "referred_id"),
    )


class BannedUser(Base):
    """New table for ban management."""
    __tablename__ = "banned_users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    banned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    banned_by: Mapped[int] = mapped_column(BigInteger)
