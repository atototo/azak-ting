"""
뉴스 크롤러 Base 클래스

모든 뉴스 크롤러의 기본 클래스를 정의합니다.
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime

import httpx


logger = logging.getLogger(__name__)


class NewsArticleData:
    """크롤링된 콘텐츠 데이터 클래스 (뉴스, Reddit, Twitter 등)"""

    def __init__(
        self,
        title: str,
        content: str,
        published_at: datetime,
        source: str,
        url: Optional[str] = None,
        company_name: Optional[str] = None,
        author: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Args:
            title: 콘텐츠 제목
            content: 콘텐츠 본문
            published_at: 발표 시간
            source: 소스 식별자 (예: "naver", "reddit:r/stocks")
            url: 콘텐츠 URL (선택)
            company_name: 관련 기업명 (선택)
            author: 작성자 (선택, Reddit/Twitter용)
            metadata: 플랫폼별 메타데이터 (선택)
        """
        self.title = title
        self.content = content
        self.published_at = published_at
        self.source = source
        self.url = url
        self.company_name = company_name
        self.author = author
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        return f"<NewsArticleData(title='{self.title[:30]}...', source='{self.source}')>"


class BaseNewsCrawler(ABC):
    """뉴스 크롤러 추상 베이스 클래스 (비동기)"""

    def __init__(
        self,
        source_name: str,
        timeout: int = 10,
        max_retries: int = 3,
        rate_limit_seconds: float = 1.0,
    ):
        """
        Args:
            source_name: 언론사 이름
            timeout: HTTP 요청 타임아웃 (초)
            max_retries: 최대 재시도 횟수
            rate_limit_seconds: Rate limiting 간격 (초)
        """
        self.source_name = source_name
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_seconds = rate_limit_seconds
        self.last_request_time: Optional[float] = None
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """
        비동기 HTTP 클라이언트를 반환합니다.

        Returns:
            httpx.AsyncClient 객체
        """
        if self._client is None or self._client.is_closed:
            # Retry 전략 설정
            transport = httpx.AsyncHTTPTransport(retries=self.max_retries)

            self._client = httpx.AsyncClient(
                transport=transport,
                timeout=self.timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Compatible; Azak/1.0)",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
                }
            )

        return self._client

    async def _apply_rate_limit(self) -> None:
        """Rate limiting을 적용합니다."""
        if self.last_request_time is not None:
            import time
            elapsed = time.time() - self.last_request_time
            if elapsed < self.rate_limit_seconds:
                sleep_time = self.rate_limit_seconds - elapsed
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}초")
                await asyncio.sleep(sleep_time)

        import time
        self.last_request_time = time.time()

    async def fetch_html(self, url: str) -> Optional[str]:
        """
        URL에서 HTML을 가져옵니다 (비동기).

        Args:
            url: 요청할 URL

        Returns:
            HTML 문자열 또는 None (실패 시)
        """
        await self._apply_rate_limit()

        try:
            logger.info(f"Fetching: {url}")
            client = await self._get_client()
            response = await client.get(url)
            response.raise_for_status()

            # 한글 인코딩 처리
            # 1. Content-Type 헤더에서 명시된 인코딩 확인
            if response.encoding and response.encoding != 'ISO-8859-1':
                return response.text

            # 2. HTML 메타 태그에서 charset 확인
            content = response.content

            # UTF-8로 시도
            try:
                return content.decode('utf-8')
            except UnicodeDecodeError:
                pass

            # charset 감지
            try:
                detected_encoding = response.charset_encoding or 'utf-8'
                return content.decode(detected_encoding)
            except (UnicodeDecodeError, LookupError):
                # 마지막 시도: EUC-KR (한국어 사이트용)
                try:
                    return content.decode('euc-kr')
                except UnicodeDecodeError:
                    logger.warning(f"인코딩 변환 실패: {url}, UTF-8로 무시하고 진행")
                    return content.decode('utf-8', errors='ignore')

        except httpx.TimeoutException:
            logger.error(f"Timeout error for {url}")
            return None

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for {url}: {e}")
            return None

        except httpx.RequestError as e:
            logger.error(f"Request error for {url}: {e}")
            return None

    @abstractmethod
    async def fetch_news(self, limit: int = 10) -> List[NewsArticleData]:
        """
        뉴스를 크롤링합니다 (비동기).

        Args:
            limit: 가져올 뉴스 개수

        Returns:
            NewsArticleData 리스트
        """
        pass

    async def close(self) -> None:
        """HTTP 클라이언트를 닫습니다."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self):
        """Async context manager 진입"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager 종료"""
        await self.close()
