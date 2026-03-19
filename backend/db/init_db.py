from sqlmodel import SQLModel, Session, select
from db.database import engine
from db.models import Category


def init_db():
    # 테이블 생성
    SQLModel.metadata.create_all(engine)

    # category 초기 데이터 삽입
    with Session(engine) as session:
        categories = ["관공서", "기업", "학교"]

        for name in categories:
            existing = session.exec(
                select(Category).where(Category.name == name)
            ).first()

            if not existing:
                session.add(Category(name=name))

        session.commit()


if __name__ == "__main__":
    init_db()
    print("DB 생성 및 초기 데이터 입력 완료")