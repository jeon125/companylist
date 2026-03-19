from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List


class Category(SQLModel, table=True):
    __tablename__ = "category"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)

    # 🔥 Company와의 관계 (역방향)
    companies: List["Company"] = Relationship(back_populates="category")


class Company(SQLModel, table=True):
    __tablename__ = "company"

    id: Optional[int] = Field(default=None, primary_key=True)

    name: str = Field(index=True)
    category_id: int = Field(foreign_key="category.id")

    address: Optional[str] = None
    tel: Optional[str] = None
    homepage: Optional[str] = None

    # 🔥 Category와의 관계 (핵심)
    category: Optional[Category] = Relationship(back_populates="companies")