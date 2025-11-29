"""
Azak 스케줄러 서버 진입점

역할:
1. 정기 스케줄 작업 (크롤링, 임베딩, 평가 등)
2. 무거운 작업 처리 (리포트 생성, 대량 예측 등)
3. 내부 관리 API (API 서버의 요청 처리)
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

# FastAPI 앱 생성 (스케줄러 서버)
app = FastAPI(
    title="Azak Scheduler Server",
    version="1.0.0",
    description="백그라운드 작업 전용 서버 (크롤링, 임베딩, 평가, 리포트 생성)",
    debug=settings.DEBUG,
)

# CORS 설정 (API 서버에서의 요청 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"] + settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """스케줄러 서버 시작 이벤트"""
    logger.info(f"🤖 Azak 스케줄러 서버 시작")

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
    """스케줄러 서버 종료 이벤트"""
    logger.info(f"🛑 Azak 스케줄러 서버 종료")

    # APScheduler 종료
    scheduler = get_crawler_scheduler()
    scheduler.shutdown()
    logger.info("✅ 크롤러 스케줄러 종료 (뉴스 + 주가)")


# ==================== 내부 관리 API ====================

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Azak Scheduler Server",
        "version": "1.0.0",
        "description": "백그라운드 작업 전용 서버",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    scheduler = get_crawler_scheduler()

    return {
        "status": "healthy",
        "scheduler_running": scheduler.is_running if scheduler else False,
        "active_jobs": len(scheduler.scheduler.get_jobs()) if scheduler and scheduler.scheduler else 0,
    }


# ==================== 내부 관리 API (API 서버 요청용) ====================
# 향후 추가 예정:
# - POST /internal/generate-report (리포트 강제 생성)
# - POST /internal/generate-predictions (예측 생성)
# - POST /internal/initial-analysis (신규 종목 초기 분석)


def main():
    """메인 진입점 - uvicorn으로 서버 실행"""
    import uvicorn

    uvicorn.run(
        "backend.scheduler_main:app",
        host="0.0.0.0",
        port=8001,  # 스케줄러 서버는 8001 포트 사용
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
