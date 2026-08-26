from decimal import Decimal
from datetime import date
from typing import Optional, List
from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
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