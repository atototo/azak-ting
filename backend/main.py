"""
Azak FastAPI 애플리케이션 진입점
"""
import os

# 0. 환경 변수 설정 (가장 먼저 실행)
# PM2/Multiprocessing 환경에서 PyTorch/FAISS 충돌 방지
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.scheduler.crawler_scheduler import get_crawler_scheduler


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
    """애플리케이션 시작 이벤트"""
    logger.info(f"🚀 {settings.APP_NAME} 애플리케이션 시작")

    # 1️⃣ ML 모델 사전 로드 (Eager Loading) - Segmentation Fault 방지
    # 메인 스레드에서 안전하게 모델을 로드한 후 스케줄러 시작
    try:
        logger.info("📦 ML 모델 로드 시작...")

        from backend.llm.embedder import get_news_embedder
        from backend.llm.predictor import get_predictor

        embedder = get_news_embedder()
        # Lazy loading 트리거 - 실제로 모델을 메모리에 로드
        _ = embedder.tokenizer
        _ = embedder.model
        logger.info("✅ 임베딩 모델 로드 완료 (메인 스레드)")

        predictor = get_predictor()
        logger.info("✅ 예측 모델 로드 완료 (메인 스레드)")

    except Exception as e:
        logger.error(f"❌ ML 모델 로드 실패: {e}", exc_info=True)
        # 모델 로드 실패 시에도 앱은 계속 실행 (예측 기능만 비활성화)

    # 2️⃣ APScheduler 시작 (뉴스: 10분, 주가: 1분)
    scheduler = get_crawler_scheduler(news_interval_minutes=10, stock_interval_minutes=1)
    scheduler.start()
    logger.info("✅ 크롤러 스케줄러 시작 (뉴스 + 주가)")


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 이벤트"""
    logger.info(f"🛑 {settings.APP_NAME} 애플리케이션 종료")

    # APScheduler 종료
    scheduler = get_crawler_scheduler()
    scheduler.shutdown()
    logger.info("✅ 크롤러 스케줄러 종료 (뉴스 + 주가)")


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
