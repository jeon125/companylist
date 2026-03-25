from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List


class Category(SQLModel, table=True):
    __tablename__ = "category"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)

    # Company와의 관계 (역방향)
    companies: List["Company"] = Relationship(back_populates="category")


class Company(SQLModel, table=True):
    __tablename__ = "company"

    id: Optional[int] = Field(default=None, primary_key=True)

    name: str = Field(index=True)
    category_id: int = Field(foreign_key="category.id")

    address: Optional[str] = None
    tel: Optional[str] = None
    homepage: Optional[str] = None
    contact_person: Optional[str] = Field(default=None, max_length=50, description="담당자 이름")
    email: Optional[str] = Field(default=None, index=True, unique=True, description="담당자 이메일")

    # Category와의 관계
    category: Optional[Category] = Relationship(back_populates="companies")