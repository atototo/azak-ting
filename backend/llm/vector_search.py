"""
뉴스 벡터 검색 모듈 (AsyncIO 완전 재설계)

FAISS에서 유사한 과거 뉴스를 검색하고, 해당 뉴스의 주가 변동률을 조회합니다.

설계 원칙:
- Singleton 패턴으로 단일 인스턴스 보장
- 완전 비동기 (async/await)
- ModelLoadLock으로 PyTorch 동시성 제어
- 초기화 시 FAISS 인덱스 한 번만 로드
- CPU 집약 작업은 executor로 분리

인덱스 최적화 (Issue #19):
- IndexIVFFlat + Inner Product 사용 (10,000건 이상 최적)
- Inner Product = Cosine Similarity (L2 정규화된 벡터)
- 클러스터 기반 검색으로 O(N) → O(√N) 성능 개선
"""
import logging
import os
import pickle
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

import faiss
import numpy as np
from sqlalchemy.orm import Session

from backend.config import settings
from backend.llm.embedder import get_news_embedder
from backend.db.models.news import NewsArticle
from backend.db.models.match import NewsStockMatch
from backend.llm.model_lock import ModelLoadLock


logger = logging.getLogger(__name__)


class NewsVectorSearch:
    """
    뉴스 벡터 검색 클래스 - FAISS 기반 (Singleton + 완전 비동기)

    Features:
    - Singleton 패턴으로 전역 단일 인스턴스
    - ModelLoadLock으로 PyTorch Segmentation Fault 방지
    - 초기화 시 FAISS 인덱스 한 번만 로드
    - 모든 메서드 async/await
    - IndexIVFFlat + Inner Product (Issue #19)
    """

    _instance: Optional['NewsVectorSearch'] = None
    _initialized: bool = False

    # IVF 인덱스 설정
    IVF_NLIST = 100  # 클러스터 수 (sqrt(N) 권장, 10000건 → 100)
    IVF_NPROBE = 10  # 검색 시 탐색할 클러스터 수
    MIN_VECTORS_FOR_IVF = 1000  # IVF 학습에 필요한 최소 벡터 수

    def __new__(cls):
        """Singleton 패턴 구현"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """초기화 (최초 1회만 실행)"""
        if NewsVectorSearch._initialized:
            return

        self.embedder = get_news_embedder()
        self.index_path = settings.FAISS_INDEX_PATH
        self.metadata_path = settings.FAISS_METADATA_PATH
        self._index: Optional[faiss.Index] = None
        self._metadata: List[Dict[str, Any]] = []
        self._is_ivf: bool = False  # IVF 인덱스 여부

        NewsVectorSearch._initialized = True
        logger.info("🔍 NewsVectorSearch 초기화 완료 (Singleton)")

    def _ensure_index_dir(self):
        """인덱스 디렉토리 생성"""
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.metadata_path), exist_ok=True)

    def _create_empty_index(self) -> faiss.Index:
        """빈 IndexFlatIP 인덱스 생성 (Inner Product)"""
        return faiss.IndexFlatIP(settings.EMBEDDING_DIM)

    def _is_index_ivf(self, index: faiss.Index) -> bool:
        """인덱스가 IVF 타입인지 확인"""
        try:
            # IVF 인덱스는 nprobe 속성을 가짐
            _ = index.nprobe
            return True
        except AttributeError:
            return False

    async def load_index(self):
        """
        FAISS 인덱스 및 메타데이터 로드 (ModelLoadLock 적용)

        PyTorch Segmentation Fault 방지를 위해 Lock 사용
        기존 IndexFlatL2와 새로운 IndexIVFFlat 모두 지원
        """
        async with ModelLoadLock.get_lock():
            if self._index is not None:
                logger.debug("FAISS 인덱스 이미 로드됨 (재사용)")
                return

            if not os.path.exists(self.index_path) or not os.path.exists(self.metadata_path):
                logger.warning("FAISS 인덱스 파일 없음, 빈 인덱스 초기화")
                self._index = self._create_empty_index()
                self._metadata = []
                self._is_ivf = False
                return

            try:
                # FAISS 인덱스 로드
                self._index = faiss.read_index(self.index_path)
                self._is_ivf = self._is_index_ivf(self._index)

                # IVF 인덱스면 nprobe 설정
                if self._is_ivf:
                    self._index.nprobe = self.IVF_NPROBE
                    logger.info(f"📊 IVF 인덱스 로드됨 (nprobe={self.IVF_NPROBE})")

                # 메타데이터 로드
                with open(self.metadata_path, 'rb') as f:
                    self._metadata = pickle.load(f)

                index_type = "IVFFlat+IP" if self._is_ivf else "FlatL2(legacy)"
                logger.info(f"✅ FAISS 인덱스 로드 완료: {self._index.ntotal}개 벡터 ({index_type})")

            except Exception as e:
                logger.error(f"❌ FAISS 인덱스 로드 실패: {e}")
                self._index = self._create_empty_index()
                self._metadata = []
                self._is_ivf = False

    def save_index(self):
        """
        FAISS 인덱스 및 메타데이터 저장

        Note: 동기 함수 (파일 I/O는 CPU-bound 작업이므로 동기 처리)
        """
        try:
            self._ensure_index_dir()

            # FAISS 인덱스 저장
            faiss.write_index(self._index, self.index_path)

            # 메타데이터 저장
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self._metadata, f)

            logger.info(f"💾 FAISS 인덱스 저장 완료: {self._index.ntotal}개 벡터")

        except Exception as e:
            logger.error(f"❌ FAISS 인덱스 저장 실패: {e}")

    async def add_embeddings(
        self,
        news_ids: List[int],
        embeddings: List[List[float]],
        stock_codes: List[str],
        published_timestamps: List[int],
    ) -> int:
        """
        임베딩을 FAISS 인덱스에 추가 (비동기)

        Args:
            news_ids: 뉴스 ID 리스트
            embeddings: 임베딩 벡터 리스트
            stock_codes: 종목 코드 리스트
            published_timestamps: 발행 시각 (Unix timestamp) 리스트

        Returns:
            추가된 벡터 수
        """
        if len(news_ids) != len(embeddings) != len(stock_codes) != len(published_timestamps):
            logger.error("입력 리스트 길이 불일치")
            return 0

        try:
            await self.load_index()  # ← Lock으로 보호

            # numpy 배열로 변환
            embeddings_np = np.array(embeddings, dtype=np.float32)

            # FAISS 인덱스에 추가
            self._index.add(embeddings_np)

            # 메타데이터 추가
            for news_id, stock_code, timestamp in zip(news_ids, stock_codes, published_timestamps):
                self._metadata.append({
                    "news_article_id": news_id,
                    "stock_code": stock_code,
                    "published_at": timestamp,
                })

            # 저장
            self.save_index()

            logger.info(f"✅ FAISS 인덱스에 {len(news_ids)}개 벡터 추가")
            return len(news_ids)

        except Exception as e:
            logger.error(f"❌ 임베딩 추가 실패: {e}")
            return 0

    async def get_indexed_news_ids(self) -> set:
        """
        FAISS에 이미 인덱싱된 뉴스 ID 목록 반환 (비동기)

        Returns:
            인덱싱된 뉴스 ID 집합
        """
        try:
            await self.load_index()  # ← Lock으로 보호

            if not self._metadata:
                return set()

            return set(meta["news_article_id"] for meta in self._metadata)

        except Exception as e:
            logger.error(f"❌ 인덱싱된 뉴스 ID 조회 실패: {e}")
            return set()

    async def search_similar_news(
        self,
        news_text: str,
        stock_code: Optional[str] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """
        유사한 과거 뉴스 검색 (비동기)

        Args:
            news_text: 검색할 뉴스 텍스트
            stock_code: 종목 코드 필터 (None이면 전체 검색)
            top_k: 반환할 최대 결과 수
            similarity_threshold: 유사도 임계값 (0.0 ~ 1.0)

        Returns:
            유사 뉴스 리스트 [
                {
                    "news_id": int,
                    "similarity": float,
                    "stock_code": str,
                    "published_at": int
                },
                ...
            ]
        """
        try:
            await self.load_index()  # ← Lock으로 보호

            if self._index.ntotal == 0:
                logger.warning("FAISS 인덱스 비어있음")
                return []

            # 임베딩 생성 (CPU 집약적 작업이므로 executor에서 실행)
            loop = asyncio.get_event_loop()
            query_embedding = await loop.run_in_executor(
                None, self.embedder.embed_text, news_text
            )
            query_vector = np.array([query_embedding], dtype=np.float32)

            # FAISS 검색
            search_k = top_k * 10 if stock_code else top_k
            logger.debug(f"FAISS 검색 시작: query_vector shape={query_vector.shape}, k={search_k}")
            distances, indices = self._index.search(query_vector, search_k)
            logger.debug(f"FAISS 검색 완료: found {len(indices[0])} items")

            # 결과 필터링 및 변환
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx < 0 or idx >= len(self._metadata):
                    continue

                meta = self._metadata[idx]

                # 종목 코드 필터
                if stock_code and meta["stock_code"] != stock_code:
                    continue

                # 유사도 계산
                # - Inner Product (IVF): 정규화된 벡터는 IP = cosine similarity
                # - L2 distance (legacy): 근사 변환
                if self._is_ivf:
                    similarity = float(dist)  # IP는 바로 similarity
                else:
                    similarity = 1 / (1 + dist)  # L2 → similarity 근사

                if similarity < similarity_threshold:
                    continue

                results.append({
                    "news_id": meta["news_article_id"],
                    "similarity": round(similarity, 4),
                    "stock_code": meta["stock_code"],
                    "published_at": meta.get("published_at"),  # 기존 인덱스 호환성 (None 허용)
                })

                if len(results) >= top_k:
                    break

            logger.debug(f"🔍 유사 뉴스 검색 완료: {len(results)}건")
            return results

        except Exception as e:
            logger.error(f"❌ 유사 뉴스 검색 실패: {e}")
            return []

    async def get_news_with_price_changes(
        self,
        news_text: str,
        stock_code: Optional[str] = None,
        db: Optional[Session] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """
        유사 뉴스와 해당 뉴스의 주가 변동률 함께 조회 (비동기)

        Args:
            news_text: 검색할 뉴스 텍스트
            stock_code: 종목 코드 필터
            db: DB 세션
            top_k: 반환할 최대 결과 수
            similarity_threshold: 유사도 임계값

        Returns:
            유사 뉴스 및 주가 변동률 리스트 [
                {
                    "news_id": int,
                    "similarity": float,
                    "news_title": str,
                    "news_content": str,
                    "stock_code": str,
                    "published_at": datetime,
                    "price_changes": {
                        "1d": float or None,
                        "2d": float or None,
                        "3d": float or None,
                        "5d": float or None,
                        "10d": float or None,
                        "20d": float or None
                    }
                },
                ...
            ]
        """
        try:
            # 유사 뉴스 검색
            similar_news = await self.search_similar_news(
                news_text=news_text,
                stock_code=stock_code,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
            )

            if not similar_news or not db:
                return similar_news

            # DB에서 상세 정보 및 주가 변동률 조회
            result = []
            for news in similar_news:
                news_id = news["news_id"]

                # 뉴스 상세 정보
                news_article = db.query(NewsArticle).filter(NewsArticle.id == news_id).first()
                if not news_article:
                    continue

                # 주가 변동률 조회
                match = (
                    db.query(NewsStockMatch)
                    .filter(NewsStockMatch.news_id == news_id)
                    .first()
                )

                price_changes = {}
                if match:
                    price_changes = {
                        "1d": match.price_change_1d,
                        "2d": match.price_change_2d,
                        "3d": match.price_change_3d,
                        "5d": match.price_change_5d,
                        "10d": match.price_change_10d,
                        "20d": match.price_change_20d,
                    }
                else:
                    price_changes = {
                        "1d": None,
                        "2d": None,
                        "3d": None,
                        "5d": None,
                        "10d": None,
                        "20d": None,
                    }

                result.append({
                    "news_id": news_id,
                    "similarity": news["similarity"],
                    "news_title": news_article.title,
                    "news_content": news_article.content,
                    "stock_code": news_article.stock_code,
                    "published_at": news_article.published_at,
                    "price_changes": price_changes,
                })

            logger.debug(f"📊 주가 변동률 포함 검색 완료: {len(result)}건")
            return result

        except Exception as e:
            logger.error(f"❌ 주가 변동률 조회 실패: {e}")
            return []


# Singleton 인스턴스
_vector_search_instance: Optional[NewsVectorSearch] = None


async def get_vector_search() -> NewsVectorSearch:
    """
    NewsVectorSearch Singleton 인스턴스 반환 (비동기)

    최초 호출 시 FAISS 인덱스를 로드합니다.

    Returns:
        NewsVectorSearch 인스턴스
    """
    global _vector_search_instance

    if _vector_search_instance is None:
        _vector_search_instance = NewsVectorSearch()
        await _vector_search_instance.load_index()  # 초기 로드

    return _vector_search_instance
