"""
뉴스 임베딩 모듈

HuggingFace Transformers (BM-K/KoSimCSE-roberta)를 사용하여 뉴스를 벡터화합니다.
로컬 한글 임베딩 모델로 OpenAI API 비용 절감 및 성능 개선
"""
import logging
from typing import List, Optional, Dict, Tuple
from datetime import datetime
import time
import os

import torch
from transformers import AutoTokenizer, AutoModel
import numpy as np
from sqlalchemy.orm import Session

from backend.config import settings
from backend.db.models.news import NewsArticle
from backend.db.session import SessionLocal


logger = logging.getLogger(__name__)


class NewsEmbedder:
    """뉴스 임베딩 클래스 - 로컬 한글 임베딩 모델 사용"""

    def __init__(self):
        """임베더 초기화 - 모델은 싱글톤 패턴으로 한 번만 로드"""
        self.model_name = settings.EMBEDDING_MODEL_NAME
        self.embedding_dim = 768  # KoSimCSE-roberta의 차원
        self._tokenizer = None
        self._model = None

    @property
    def tokenizer(self):
        """토크나이저 lazy loading"""
        if self._tokenizer is None:
            logger.info(f"토크나이저 로드 중: {self.model_name}")
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            logger.info("토크나이저 로드 완료")
        return self._tokenizer

    @property
    def model(self):
        """모델 lazy loading"""
        if self._model is None:
            logger.info(f"임베딩 모델 로드 중: {self.model_name}")
            start = time.time()
            self._model = AutoModel.from_pretrained(self.model_name)
            self._model.eval()  # 평가 모드로 설정
            load_time = time.time() - start
            logger.info(f"임베딩 모델 로드 완료 ({load_time:.2f}초)")
        return self._model

    def _mean_pooling(self, model_output, attention_mask):
        """Mean Pooling - 모든 토큰의 임베딩 평균"""
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
            input_mask_expanded.sum(1), min=1e-9
        )

    def embed_text(self, text: str) -> Optional[List[float]]:
        """
        텍스트를 로컬 임베딩 모델로 벡터화합니다.

        Args:
            text: 임베딩할 텍스트

        Returns:
            768차원 임베딩 벡터 또는 None (실패 시)
        """
        try:
            # 토크나이징
            encoded_input = self.tokenizer(
                text,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors='pt'
            )

            # 임베딩 생성 (gradient 계산 비활성화)
            with torch.no_grad():
                model_output = self.model(**encoded_input)

            # Mean pooling
            embedding = self._mean_pooling(model_output, encoded_input['attention_mask'])

            # 정규화 (L2 normalization)
            embedding = torch.nn.functional.normalize(embedding, p=2, dim=1)

            # numpy 배열로 변환 후 리스트로 반환
            embedding_list = embedding.cpu().numpy()[0].tolist()

            logger.debug(f"임베딩 생성 완료: {len(embedding_list)}차원")

            return embedding_list

        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            return None

    def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        여러 텍스트를 배치로 임베딩합니다.

        Args:
            texts: 임베딩할 텍스트 리스트

        Returns:
            임베딩 벡터 리스트 (실패한 항목은 None)
        """
        embeddings = []

        for text in texts:
            embedding = self.embed_text(text)
            embeddings.append(embedding)

            # 로컬 모델이므로 rate limit 없음 (sleep 제거)

        return embeddings

    def get_unembedded_news(self, db: Session, limit: int = 100) -> List[NewsArticle]:
        """
        아직 임베딩되지 않은 뉴스를 조회합니다.

        Args:
            db: 데이터베이스 세션
            limit: 조회할 최대 개수

        Returns:
            임베딩되지 않은 뉴스 리스트
        """
        try:
            # FAISS에서 이미 인덱싱된 뉴스 ID 조회
            from backend.llm.vector_search import get_vector_search

            vector_search = get_vector_search()
            embedded_news_ids = vector_search.get_indexed_news_ids()

            logger.info(f"FAISS에 이미 저장된 뉴스: {len(embedded_news_ids)}건")

        except Exception as e:
            logger.warning(f"FAISS 조회 실패 (모든 뉴스를 대상으로 처리): {e}")
            embedded_news_ids = set()

        # PostgreSQL에서 미임베딩 뉴스 조회
        if embedded_news_ids:
            unembedded_news = (
                db.query(NewsArticle)
                .filter(NewsArticle.id.notin_(embedded_news_ids))
                .order_by(NewsArticle.published_at.desc())
                .limit(limit)
                .all()
            )
        else:
            unembedded_news = (
                db.query(NewsArticle)
                .order_by(NewsArticle.published_at.desc())
                .limit(limit)
                .all()
            )

        logger.info(f"미임베딩 뉴스: {len(unembedded_news)}건")
        return unembedded_news

    def save_to_faiss(
        self, news_list: List[NewsArticle], embeddings: List[List[float]]
    ) -> int:
        """
        뉴스 임베딩을 FAISS에 저장합니다.

        Args:
            news_list: 뉴스 리스트
            embeddings: 임베딩 벡터 리스트

        Returns:
            저장된 레코드 수
        """
        if len(news_list) != len(embeddings):
            logger.error("뉴스와 임베딩 개수가 일치하지 않습니다")
            return 0

        try:
            # FAISS에 저장
            from backend.llm.vector_search import get_vector_search

            vector_search = get_vector_search()

            # 데이터 준비
            news_ids = [news.id for news in news_list]
            stock_codes = [news.stock_code or "" for news in news_list]
            published_timestamps = [
                int(news.published_at.timestamp()) for news in news_list
            ]

            # FAISS에 추가
            saved_count = vector_search.add_embeddings(
                news_ids=news_ids,
                embeddings=embeddings,
                stock_codes=stock_codes,
                published_timestamps=published_timestamps,
            )

            logger.info(f"FAISS에 {saved_count}건 저장 완료")
            return saved_count

        except Exception as e:
            logger.error(f"FAISS 저장 실패: {e}")
            return 0

    def embed_and_save_news(
        self, db: Session, batch_size: int = 100
    ) -> Tuple[int, int]:
        """
        미임베딩 뉴스를 임베딩하여 Milvus에 저장합니다.

        Args:
            db: 데이터베이스 세션
            batch_size: 배치 크기

        Returns:
            (성공 건수, 실패 건수) 튜플
        """
        logger.info("=" * 60)
        logger.info("🔤 뉴스 임베딩 작업 시작")
        logger.info("=" * 60)

        try:
            # 미임베딩 뉴스 조회
            unembedded_news = self.get_unembedded_news(db, limit=batch_size)

            if not unembedded_news:
                logger.info("임베딩할 뉴스가 없습니다")
                return 0, 0

            logger.info(f"임베딩 대상 뉴스: {len(unembedded_news)}건")

            # 텍스트 준비 (제목 + 본문)
            texts = [f"{news.title}\n{news.content}" for news in unembedded_news]

            # 임베딩 생성
            logger.info("로컬 임베딩 모델로 벡터 생성 중...")
            embeddings = self.embed_batch(texts)

            # 성공/실패 분류
            success_news = []
            success_embeddings = []
            fail_count = 0

            for news, embedding in zip(unembedded_news, embeddings):
                if embedding is not None:
                    success_news.append(news)
                    success_embeddings.append(embedding)
                else:
                    fail_count += 1
                    logger.warning(f"뉴스 ID {news.id} 임베딩 실패")

            # FAISS에 저장
            if success_embeddings:
                saved_count = self.save_to_faiss(success_news, success_embeddings)
                logger.info(
                    f"✅ 임베딩 완료: 성공 {saved_count}건, 실패 {fail_count}건"
                )
                return saved_count, fail_count
            else:
                logger.warning("저장할 임베딩이 없습니다")
                return 0, fail_count

        except Exception as e:
            logger.error(f"뉴스 임베딩 작업 중 에러: {e}", exc_info=True)
            return 0, 0


# 싱글톤 인스턴스
_news_embedder: Optional[NewsEmbedder] = None


def get_news_embedder() -> NewsEmbedder:
    """
    NewsEmbedder 싱글톤 인스턴스를 반환합니다.

    Returns:
        NewsEmbedder 인스턴스
    """
    global _news_embedder
    if _news_embedder is None:
        _news_embedder = NewsEmbedder()
    return _news_embedder


def run_daily_embedding(batch_size: int = 100) -> Tuple[int, int]:
    """
    일일 뉴스 임베딩 작업을 실행합니다.

    Args:
        batch_size: 배치 크기 (기본값: 100)

    Returns:
        (성공 건수, 실패 건수) 튜플
    """
    db = SessionLocal()
    embedder = get_news_embedder()

    try:
        return embedder.embed_and_save_news(db, batch_size=batch_size)
    finally:
        db.close()
