from decimal import Decimal
from datetime import date
from typing import Optional, List
from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from source.persistence.database import Base

class CategoryGroupModel(Base):
    __tablename__ = "category_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    group_type: Mapped[str] = mapped_column(String(50), default="expense", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    categories: Mapped[List["CategoryModel"]] = relationship(back_populates="group")

class CategoryModel(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    category_type: Mapped[str] = mapped_column(String(50), nullable = False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default = False, nullable=False)
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("category_groups.id"), nullable=True)

    # Relationship to transactions
    group: Mapped[Optional["CategoryGroupModel"]] = relationship(back_populates="categories")
    transactions: Mapped[List["TransactionModel"]] = relationship(back_populates="category", cascade="all, delete-orphan")
    allocations: Mapped[List["MonthlyAllocationModel"]] = relationship(back_populates="category", cascade="all, delete-orphan")

class TransactionModel(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    trans_date: Mapped[date] = mapped_column(nullable=False)
    note: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="tracked", nullable=False)

    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"), nullable=True)
    category: Mapped[Optional["CategoryModel"]] = relationship(back_populates="transactions")

class MonthlyAllocationModel(Base):
    __tablename__ = "monthly_allocations"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    planned_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)

    # Relationship back to Category
    category: Mapped["CategoryModel"] = relationship(back_populates="allocations")

    # Prevent duplicate records for the same category in the same month
    __table_args__ = (
        UniqueConstraint("category_id", "year", "month", name="uq_category_month_year"),
    )

class MonthlyGroupStateModel(Base):
    __tablename__ = "monthly_group_states"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("category_groups.id"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("group_id", "year", "month", name="uq_group_month_state"),
    )

class PlaidItemModel(Base):
    __tablename__ = "plaid_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(String, unique=True, nullable=False)
    access_token = Column(String, nullable=False)
    institution_id = Column(String, nullable=True)
    institution_name = Column(String, nullable=True)
    status = Column(String, default="active")
    cursor = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class PlaidAccountModel(Base):
    __tablename__ = "plaid_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(String, ForeignKey("plaid_items.item_id", ondelete="CASCADE"), nullable=False)
    account_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    official_name = Column(String, nullable=True)
    mask = Column(String, nullable=True)
    type = Column(String, nullable=True)
    subtype = Column(String, nullable=True)
    current_balance = Column(Float, default=0.0)
    available_balance = Column(Float, default=0.0)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())