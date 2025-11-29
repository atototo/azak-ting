"""
Azak FastAPI 애플리케이션 진입점 (API 서버)

역할:
- 데이터 조회 API 제공 (읽기 위주)
- 간단한 데이터 생성
- 무거운 작업은 스케줄러 서버로 위임

주의: ML 모델 로드 및 스케줄러는 scheduler_main.py에서 실행됨
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings


# 로깅 설정
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# 불필요한 INFO 로그 제거
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("watchfiles").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="Azak API",
    version="1.0.0",
    description="증권 뉴스 예측 및 텔레그램 알림 시스템",
    debug=settings.DEBUG,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
from backend.api import health, prediction, dashboard, news, stocks, stock_management, ab_test, models, evaluations, auth, users, preview_links
app.include_router(auth.router)  # 인증은 tags가 router에 이미 정의됨
app.include_router(users.router)  # 사용자 관리는 tags가 router에 이미 정의됨
app.include_router(health.router, tags=["Health"])
app.include_router(prediction.router, tags=["Prediction"])
app.include_router(dashboard.router, tags=["Dashboard"])
app.include_router(news.router, tags=["News"])
app.include_router(stocks.router, tags=["Stocks"])
app.include_router(stock_management.router, tags=["Stock Management"])
app.include_router(ab_test.router, tags=["A/B Test"])
app.include_router(models.router, tags=["Models"])
app.include_router(evaluations.router, tags=["Evaluations"])
app.include_router(preview_links.router)  # 공개 프리뷰 링크 (tags는 router에 정의됨)


@app.on_event("startup")
async def startup_event():
    """API 서버 시작 이벤트"""
    logger.info(f"🚀 {settings.APP_NAME} API 서버 시작 (가벼운 모드)")
    logger.info("📝 ML 모델 및 스케줄러는 스케줄러 서버에서 실행됩니다")


@app.on_event("shutdown")
async def shutdown_event():
    """API 서버 종료 이벤트"""
    logger.info(f"🛑 {settings.APP_NAME} API 서버 종료")


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": f"{settings.APP_NAME} API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "stats": "/stats",
    }


def main():
    """메인 진입점 - uvicorn으로 서버 실행"""
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
