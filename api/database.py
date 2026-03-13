from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
import datetime
import os

# Tenta usar o Postgres do Docker, mas se falhar (como no GitHub Actions), usa um SQLite em memória
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fiap_user:fiap_password@postgres:5432/video_processing_db")

try:
    engine = create_engine(DATABASE_URL)
    # Tenta conectar para ver se o banco está vivo
    engine.connect()
except Exception:
    # Se falhar, usa banco de mentira em memória para os testes do GitHub
    engine = create_engine("sqlite:///:memory:")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class VideoStatus(Base):
    __tablename__ = "videos"
    id = Column(String, primary_key=True, index=True)
    filename = Column(String)
    status = Column(String) # PENDENTE, PROCESSANDO, CONCLUIDO, ERRO
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)
