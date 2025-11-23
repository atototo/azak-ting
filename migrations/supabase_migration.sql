-- ============================================
-- Supabase Migration Script
-- ============================================
-- 이 스크립트는 로컬 PostgreSQL에서 Supabase로 마이그레이션합니다.
--
-- 포함 내용:
-- 1. 기존 스키마 전체 (23개 테이블) - schema_dump.sql 참조
-- 2. KIS 토큰 관리 테이블 (Redis 대체 - 토큰만)
-- 3. 1분봉 보관 정책용 함수
--
-- 예측 캐싱: aiocache 메모리 캐싱 사용 (테이블 불필요!)
-- ============================================

-- KIS 토큰 관리 테이블 (Redis 대체)
-- ============================================

CREATE TABLE IF NOT EXISTS public.kis_tokens (
    id SERIAL PRIMARY KEY,
    token_type VARCHAR(50) NOT NULL,
    token_value TEXT NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_kis_token_type ON public.kis_tokens(token_type);

COMMENT ON TABLE public.kis_tokens IS 'KIS API 토큰 관리 (Redis 대체)';
COMMENT ON COLUMN public.kis_tokens.token_type IS '토큰 타입 (예: access_token)';
COMMENT ON COLUMN public.kis_tokens.token_value IS '토큰 값';
COMMENT ON COLUMN public.kis_tokens.expires_at IS '토큰 만료 시간';

-- 1분봉 데이터 정리 함수
-- ============================================

CREATE OR REPLACE FUNCTION public.cleanup_old_minute_data()
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- 30일 이상 된 1분봉 데이터 삭제
    DELETE FROM public.stock_prices_minute
    WHERE datetime < NOW() - INTERVAL '30 days';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    RAISE NOTICE '1분봉 데이터 정리 완료: % 건 삭제됨', deleted_count;
END;
$$;

COMMENT ON FUNCTION public.cleanup_old_minute_data() IS '30일 이상 된 1분봉 데이터를 삭제하여 용량 관리 (월 95MB 증가 방지)';

-- ============================================
-- 마이그레이션 순서
-- ============================================
--
-- 1. 이 파일(supabase_migration.sql) 실행
-- 2. schema_dump.sql 실행 (기존 23개 테이블 생성)
-- 3. data_dump.sql 실행 (모든 데이터 복원)
--
-- 총 테이블: 24개 (기존 23개 + kis_tokens 1개)
-- ============================================
