"""
공개 프리뷰 링크 API 엔드포인트.

관리자가 종목별 홍보용 공개 링크를 생성하고, 공개 링크로 종목 정보에 접근할 수 있습니다.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from backend.db.session import get_db
from backend.db.models.public_preview_link import PublicPreviewLink
from backend.db.models.user import User
from backend.auth.dependencies import require_admin


router = APIRouter(tags=["Preview Links"])


# Request/Response Models
class CreatePreviewLinkRequest(BaseModel):
    """공개 프리뷰 링크 생성 요청 모델."""
    stock_code: str
    expires_at: Optional[datetime] = None


class PreviewLinkResponse(BaseModel):
    """공개 프리뷰 링크 응답 모델."""
    link_id: str
    stock_code: str
    created_by: int
    created_at: datetime
    expires_at: Optional[datetime]
    public_url: str

    class Config:
        from_attributes = True


class PublicPreviewResponse(BaseModel):
    """공개 프리뷰 조회 응답 모델."""
    stock_code: str


@router.post(
    "/api/admin/preview-links",
    response_model=PreviewLinkResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_preview_link(
    request: CreatePreviewLinkRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    공개 프리뷰 링크 생성 (관리자 전용).

    Args:
        request: 종목 코드 및 만료일 (optional)
        current_user: 현재 사용자 (관리자만 가능)
        db: 데이터베이스 세션

    Returns:
        PreviewLinkResponse: 생성된 링크 정보

    Raises:
        HTTPException: 403 (권한 없음)
    """
    # UUID 기반 링크 ID 생성
    link_id = str(uuid.uuid4())

    # DB에 저장
    preview_link = PublicPreviewLink(
        link_id=link_id,
        stock_code=request.stock_code,
        created_by=current_user.id,
        created_at=datetime.now(),
        expires_at=request.expires_at
    )

    db.add(preview_link)
    db.commit()
    db.refresh(preview_link)

    # 공개 URL 생성 (프론트엔드 base URL은 환경변수로 설정 필요)
    # 여기서는 상대 경로만 반환
    public_url = f"/public/{link_id}"

    return PreviewLinkResponse(
        link_id=preview_link.link_id,
        stock_code=preview_link.stock_code,
        created_by=preview_link.created_by,
        created_at=preview_link.created_at,
        expires_at=preview_link.expires_at,
        public_url=public_url
    )


@router.get(
    "/api/public-preview/{link_id}",
    response_model=PublicPreviewResponse,
    status_code=status.HTTP_200_OK
)
async def get_preview_by_link(
    link_id: str,
    db: Session = Depends(get_db)
):
    """
    공개 프리뷰 링크로 종목 코드 조회 (인증 불필요).

    Args:
        link_id: 링크 ID
        db: 데이터베이스 세션

    Returns:
        PublicPreviewResponse: 종목 코드

    Raises:
        HTTPException: 404 (링크 없음), 410 (만료됨)
    """
    # DB에서 링크 조회
    preview_link = db.query(PublicPreviewLink).filter(
        PublicPreviewLink.link_id == link_id
    ).first()

    if not preview_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="링크를 찾을 수 없습니다"
        )

    # 만료 확인
    if preview_link.expires_at and preview_link.expires_at < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="링크가 만료되었습니다"
        )

    return PublicPreviewResponse(stock_code=preview_link.stock_code)


@router.get(
    "/api/admin/preview-links/{stock_code}",
    response_model=list[PreviewLinkResponse],
    status_code=status.HTTP_200_OK
)
async def get_preview_links_by_stock(
    stock_code: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    특정 종목의 모든 공개 프리뷰 링크 조회 (관리자 전용).

    Args:
        stock_code: 종목 코드
        current_user: 현재 사용자 (관리자만 가능)
        db: 데이터베이스 세션

    Returns:
        list[PreviewLinkResponse]: 링크 목록
    """
    preview_links = db.query(PublicPreviewLink).filter(
        PublicPreviewLink.stock_code == stock_code
    ).order_by(PublicPreviewLink.created_at.desc()).all()

    return [
        PreviewLinkResponse(
            link_id=link.link_id,
            stock_code=link.stock_code,
            created_by=link.created_by,
            created_at=link.created_at,
            expires_at=link.expires_at,
            public_url=f"/public/{link.link_id}"
        )
        for link in preview_links
    ]


@router.delete(
    "/api/admin/preview-links/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_preview_link(
    link_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    공개 프리뷰 링크 삭제 (관리자 전용).

    Args:
        link_id: 링크 ID
        current_user: 현재 사용자 (관리자만 가능)
        db: 데이터베이스 세션

    Raises:
        HTTPException: 404 (링크 없음)
    """
    preview_link = db.query(PublicPreviewLink).filter(
        PublicPreviewLink.link_id == link_id
    ).first()

    if not preview_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="링크를 찾을 수 없습니다"
        )

    db.delete(preview_link)
    db.commit()
