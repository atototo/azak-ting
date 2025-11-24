"""
PyTorch/FAISS 모델 로드 시 동시성 제어

AsyncIOScheduler 환경에서 여러 작업이 동시에 PyTorch 모델을 로드하면
Segmentation Fault가 발생할 수 있습니다.

이 Lock을 사용하여 한 번에 하나의 작업만 PyTorch 모델에 접근하도록 보장합니다.
"""
import asyncio
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ModelLoadLock:
    """
    PyTorch/FAISS 모델 로드 시 동시 접근 방지 (Singleton)

    Usage:
        from backend.llm.model_lock import ModelLoadLock

        async with ModelLoadLock.get_lock():
            # PyTorch 모델 로드 또는 사용
            model.load()
    """
    _lock: Optional[asyncio.Lock] = None

    @classmethod
    def get_lock(cls) -> asyncio.Lock:
        """
        전역 Lock 반환 (Singleton)

        Returns:
            asyncio.Lock: 모든 작업이 공유하는 단일 Lock
        """
        if cls._lock is None:
            cls._lock = asyncio.Lock()
            logger.info("🔒 ModelLoadLock 초기화 완료 (PyTorch 동시성 제어)")
        return cls._lock
