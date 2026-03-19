import pandas as pd
from sqlmodel import Session
from db.database import engine
from db.models import Company

# 엑셀 읽기
df = pd.read_excel("../data/company.xlsx")

# 카테고리 매핑
category_map = {
    "관공서": 1,
    "기업": 2,
    "학교": 3
}

with Session(engine) as session:
    for _, row in df.iterrows():
        company = Company(
            name=row["업체명"],
            address=row["주소"],
            tel=row["전화번호"],
            homepage=row["홈페이지"],
            category_id=category_map[row["분류"]]
        )
        session.add(company)

    session.commit()

print("데이터 삽입 완료")