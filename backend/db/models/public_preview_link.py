"""
Public Preview Link model for sharing stock details publicly.
"""
from sqlalchemy import Column, String, Integer, DateTime
from datetime import datetime
from backend.db.base import Base


class PublicPreviewLink(Base):
    """
    공개 프리뷰 링크 테이블.

    블로그/홍보 목적으로 특정 종목 상세 화면을 공개 링크로 공유하기 위한 테이블.

    Attributes:
        link_id: 링크 ID (UUID, Primary Key)
        stock_code: 종목 코드 (예: '005930')
        created_by: 생성한 관리자 user_id
        created_at: 생성일시
        expires_at: 만료일시 (NULL일 경우 무제한)
    """

    __tablename__ = "public_preview_links"

    link_id = Column(String(255), primary_key=True)
    stock_code = Column(String(20), nullable=False, index=True)
    created_by = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<PublicPreviewLink(link_id='{self.link_id}', stock_code='{self.stock_code}', "
            f"created_by={self.created_by})>"
        )
