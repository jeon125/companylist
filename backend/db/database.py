from sqlmodel import SQLModel, create_engine

# SQLite 파일 위치
DATABASE_URL = "sqlite:///./db/company.db"

# 엔진 생성
engine = create_engine(
    DATABASE_URL,
    echo=True  # SQL 로그 출력 (디버깅용)
)