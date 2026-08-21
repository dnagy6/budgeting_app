from decimal import Decimal
from datetime import date
from typing import Optional, List
from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from source.persistence.database import Base

class CategoryModel(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    category_type: Mapped[str] = mapped_column(String(50), nullable = False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default = False, nullable=False)

    # Relationship to transactions
    transactions: Mapped[List["TransactionModel"]] = relationship(back_populates="category", cascade="all, delete-orphan")
    allocations: Mapped[List["MonthlyAllocationModel"]] = relationship(back_populates="category", cascade="all, delete-orphan")


class TransactionModel(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    trans_date: Mapped[date] = mapped_column(nullable=False)
    note: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))
    category: Mapped[Optional[CategoryModel]] = relationship(back_populates="transactions")

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