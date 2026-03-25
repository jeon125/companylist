from fastapi import FastAPI, HTTPException
from sqlmodel import Session, select
from db.database import engine
from db.models import Company, Category
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy.exc import IntegrityError  # ✅ 추가

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
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None


class CompanyUpdate(BaseModel):
    name: str
    category_id: int
    address: Optional[str] = None
    tel: Optional[str] = None
    homepage: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None


# -----------------------------
# 전체 조회
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
                "contact_person": c.contact_person,
                "email": c.email,
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

        companies = category.companies

        return [
            {
                "id": c.id,
                "name": c.name,
                "address": c.address,
                "tel": c.tel,
                "homepage": c.homepage,
                "contact_person": c.contact_person,
                "email": c.email,
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

    if not (company.address and company.address.strip()):
        raise HTTPException(400, "주소는 필수입니다.")

    with Session(engine) as session:

        existing = session.exec(
            select(Company).where(
                (Company.name == company.name.strip()) &
                (Company.address == company.address.strip())
            )
        ).first()

        if existing:
            raise HTTPException(400, "같은 업체명과 주소가 존재합니다.")

        if company.email:
            existing_email = session.exec(
                select(Company).where(Company.email == company.email)
            ).first()

            if existing_email:
                raise HTTPException(400, "이미 사용 중인 이메일입니다.")

        new_company = Company(
            name=company.name.strip(),
            address=company.address.strip(),
            tel=company.tel or "",
            homepage=company.homepage or "",
            contact_person=company.contact_person or "",
            email=company.email,
            category_id=company.category_id
        )

        try:
            session.add(new_company)
            session.commit()
            session.refresh(new_company)

        except IntegrityError:
            session.rollback()
            raise HTTPException(400, "이메일 중복 또는 데이터 오류")

        except Exception:
            session.rollback()
            raise HTTPException(500, "서버 오류 발생")

        return {"message": "등록 완료"}


# -----------------------------
# 수정
# -----------------------------
@app.put("/companies/{company_id}")
def update_company(company_id: int, company: CompanyUpdate):

    if not company.name.strip():
        raise HTTPException(400, "업체명은 필수입니다.")

    if not (company.address and company.address.strip()):
        raise HTTPException(400, "주소는 필수입니다.")

    with Session(engine) as session:
        db_company = session.get(Company, company_id)

        if not db_company:
            raise HTTPException(404, "업체 없음")

        if company.email:
            existing_email = session.exec(
                select(Company).where(
                    (Company.email == company.email) &
                    (Company.id != company_id)
                )
            ).first()

            if existing_email:
                raise HTTPException(400, "이미 사용 중인 이메일입니다.")

        db_company.name = company.name.strip()
        db_company.address = company.address.strip()
        db_company.tel = company.tel or ""
        db_company.homepage = company.homepage or ""
        db_company.contact_person = company.contact_person or ""
        db_company.email = company.email
        db_company.category_id = company.category_id

        try:
            session.add(db_company)
            session.commit()

        except IntegrityError:
            session.rollback()
            raise HTTPException(400, "이메일 중복 또는 데이터 오류")

        except Exception:
            session.rollback()
            raise HTTPException(500, "서버 오류 발생")

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

        try:
            session.delete(db_company)
            session.commit()

        except Exception:
            session.rollback()
            raise HTTPException(500, "서버 오류 발생")

        return {"message": "삭제 완료"}