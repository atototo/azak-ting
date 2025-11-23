"""
KIS API Token 모델

Redis 대체: KIS API 토큰을 PostgreSQL에 저장합니다.
"""
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class KISToken(Base):
    """KIS API 토큰 모델"""

    __tablename__ = "kis_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    token_type = Column(String(50), nullable=False, unique=True, index=True)
    token_value = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=False), nullable=True)
    created_at = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<KISToken(token_type='{self.token_type}', expires_at='{self.expires_at}')>"
