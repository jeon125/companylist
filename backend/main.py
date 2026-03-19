from fastapi import FastAPI, HTTPException
from sqlmodel import Session, select
from db.database import engine
from db.models import Company, Category
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# -----------------------------
# 요청 모델
# -----------------------------
class CompanyCreate(BaseModel):
    name: str
    category_id: int
    address: Optional[str] = None
    tel: Optional[str] = None
    homepage: Optional[str] = None


class CompanyUpdate(BaseModel):
    name: str
    category_id: int
    address: Optional[str] = None
    tel: Optional[str] = None
    homepage: Optional[str] = None


# -----------------------------
# 전체 조회 (ORM 사용)
# -----------------------------
@app.get("/companies")
def get_companies():
    with Session(engine) as session:
        companies = session.exec(select(Company)).all()

        return [
            {
                "id": c.id,
                "name": c.name,
                "address": c.address,
                "tel": c.tel,
                "homepage": c.homepage,
                "category": c.category.name if c.category else ""
            }
            for c in companies
        ]


# -----------------------------
# 카테고리 조회
# -----------------------------
@app.get("/companies/{category_name}")
def get_companies_by_category(category_name: str):
    with Session(engine) as session:
        category = session.exec(
            select(Category).where(Category.name == category_name)
        ).first()

        if not category:
            return []

        companies = category.companies  # 🔥 ORM 관계 사용

        return [
            {
                "id": c.id,
                "name": c.name,
                "address": c.address,
                "tel": c.tel,
                "homepage": c.homepage,
                "category": category.name
            }
            for c in companies
        ]


# -----------------------------
# 등록
# -----------------------------
@app.post("/companies")
def create_company(company: CompanyCreate):

    if not company.name.strip():
        raise HTTPException(400, "업체명은 필수입니다.")

    with Session(engine) as session:

        existing = session.exec(
            select(Company).where(
                (Company.name == company.name.strip()) &
                (Company.address == (company.address or "").strip())
            )
        ).first()

        if existing:
            raise HTTPException(400, "같은 업체명과 주소가 존재합니다.")

        new_company = Company(
            name=company.name.strip(),
            address=(company.address or "").strip(),
            tel=company.tel or "",
            homepage=company.homepage or "",
            category_id=company.category_id
        )

        session.add(new_company)
        session.commit()
        session.refresh(new_company)

        return {"message": "등록 완료"}


# -----------------------------
# 수정
# -----------------------------
@app.put("/companies/{company_id}")
def update_company(company_id: int, company: CompanyUpdate):

    with Session(engine) as session:
        db_company = session.get(Company, company_id)

        if not db_company:
            raise HTTPException(404, "업체 없음")

        db_company.name = company.name.strip()
        db_company.address = (company.address or "").strip()
        db_company.tel = company.tel or ""
        db_company.homepage = company.homepage or ""
        db_company.category_id = company.category_id

        session.add(db_company)
        session.commit()

        return {"message": "수정 완료"}


# -----------------------------
# 삭제
# -----------------------------
@app.delete("/companies/{company_id}")
def delete_company(company_id: int):

    with Session(engine) as session:
        db_company = session.get(Company, company_id)

        if not db_company:
            raise HTTPException(404, "업체 없음")

        session.delete(db_company)
        session.commit()

        return {"message": "삭제 완료"}