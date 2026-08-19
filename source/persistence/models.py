from decimal import Decimal
from datetime import date
from typing import Optional, List
from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from source.persistence.database import Base

class CategoryModel(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    category_type: Mapped[str] = mapped_column(String(50), nullable = False)
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))

    # Relationship to transactions
    transactions: Mapped[List["TransactionModel"]] = relationship(back_populates="category")


class TransactionModel(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    trans_date: Mapped[date] = mapped_column(nullable=False)
    note: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))
    category: Mapped[Optional[CategoryModel]] = relationship(back_populates="transactions")