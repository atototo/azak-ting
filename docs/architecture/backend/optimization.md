# 성능 최적화 & 보안

## 성능 최적화

### 데이터베이스 연결 풀

`backend/db/session.py`:
```python
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=30,        # 백그라운드 작업 대응
    max_overflow=50,     # 버스트 로드 대응
    pool_recycle=3600,   # 1시간마다 연결 재활용
    pool_pre_ping=True   # 연결 유효성 검사
)
```

### 예측 캐싱

`backend/llm/prediction_cache.py`:
- Redis 기반 예측 결과 캐싱
- 중복 API 호출 방지
- TTL 기반 자동 만료

### 백그라운드 작업 최적화

- 장 시간 체크: `is_market_open()`로 불필요한 작업 스킵
- 배치 처리: KIS API 호출 시 `batch_size` 파라미터
- 우선순위 필터링: 중요 종목 우선 처리 (Priority 1-2)

## 보안 고려사항

### 인증 & 권한

- JWT 토큰 기반 인증
- 비밀번호 bcrypt 해싱
- 세션 쿠키 HttpOnly 설정
- CORS 설정 검증

### API 키 관리

- 환경 변수로 관리 (`.env`)
- 버전 관리에서 제외 (`.gitignore`)
- 프로덕션: AWS Secrets Manager 또는 Vault 사용 권장

### SQL Injection 방지

- SQLAlchemy ORM 사용
- 파라미터화된 쿼리만 사용
- 사용자 입력 검증

## 문제 해결

### 일반적인 이슈

1. **DB 연결 에러**
   - PostgreSQL 서비스 실행 확인
   - `.env` 파일의 DB 자격증명 확인

2. **Milvus 연결 에러**
   - Milvus 서비스 실행 확인 (`docker-compose up milvus`)
   - 포트 19530 접근 가능 여부 확인

3. **스케줄러 작업 실행 안 됨**
   - APScheduler 로그 확인
   - 시스템 시간대 설정 확인 (한국 시간: Asia/Seoul)

4. **OpenAI API 에러**
   - API 키 유효성 확인
   - 요금 한도 확인
   - OpenRouter 대체 사용 고려

### 로그 확인

```bash
# 애플리케이션 로그
tail -f data/logs/app.log

# Docker 컨테이너 로그
docker logs azak-backend -f
```

## 연락처 및 지원

- 프로젝트 리포지토리: [GitHub]
- 이슈 트래커: [GitHub Issues]
- 문서: `/docs` 또는 FastAPI 자동 문서 `/docs`
