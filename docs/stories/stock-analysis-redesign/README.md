# 주식 분석 시스템 개편 - User Stories

**Epic**: [CRAVENY-EPIC-001](../../stock-analysis-redesign-epic.md)
**PRD**: [stock-analysis-redesign-prd.md](../../stock-analysis-redesign-prd.md)
**Brief**: [stock-analysis-redesign-brief.md](../../stock-analysis-redesign-brief.md)

---

## 📋 프로젝트 개요

뉴스 의존성을 제거하고 모든 활성 종목에 대해 펀더멘털 데이터 기반 분석을 제공하는 시스템 개편 프로젝트입니다.

### 핵심 목표
- ✅ **100% 분석 커버리지** (현재 ~60% → 목표 100%)
- ⚡ **즉시 분석 제공** (등록 후 1분 이내)
- 📊 **펀더멘털 분석 강화** (재무비율, 상품정보 추가)
- 🎯 **시스템 단순화** (Priority 제거)

---

## 📦 User Stories (6개)

### Phase 1: 데이터베이스 마이그레이션 (1주차)
**[US-001: DB 스키마 마이그레이션](US-001-db-migrations.md)**
- 스토리 포인트: 5
- 담당: 백엔드
- 내용:
  - product_info 테이블 생성
  - financial_ratios 테이블 생성
  - priority 컬럼 deprecated (모든 값 1로 설정)

---

### Phase 2: KIS API 통합 (1-2주차)
**[US-002: KIS API 통합](US-002-kis-api-integration.md)**
- 스토리 포인트: 8
- 담당: 백엔드
- 내용:
  - `get_financial_ratios()` 메서드 구현 (TR_ID: FHKST66430300)
  - `get_product_info()` 메서드 구현 (TR_ID: CTPF1604R)
  - 데이터 저장 함수 (`save_product_info`, `save_financial_ratios`)

---

### Phase 3: 데이터 수집 스케줄러 (2주차)
**[US-003: 데이터 수집 스케줄러](US-003-data-collection-scheduler.md)**
- 스토리 포인트: 5
- 담당: 백엔드
- 내용:
  - 상품정보 주간 수집 스케줄러 (일요일 새벽 1시)
  - 재무비율 주간 수집 스케줄러 (일요일 새벽 2시)
  - crawler_scheduler.py에 스케줄 등록

---

### Phase 4: 분석 로직 재설계 (2-3주차)
**[US-004: 분석 로직 재설계](US-004-analysis-logic-redesign.md)**
- 스토리 포인트: 13
- 담당: 백엔드
- 내용:
  - 종목 등록 즉시 분석 트리거 (`trigger_initial_analysis`)
  - DB 기반 리포트 생성 (`build_analysis_context_from_db`) - API 호출 0회
  - Priority 필터 제거 (crawler_scheduler.py 수정)
  - 적응형 분석 프롬프트 (데이터 가용성 기반)
  - 리포트 메타데이터 추가 (data_sources_used, limitations, confidence_level)

---

### Phase 5: 프론트엔드 업데이트 (3주차)
**[US-005: 프론트엔드 UI 업데이트](US-005-frontend-updates.md)**
- 스토리 포인트: 5
- 담당: 프론트엔드
- 내용:
  - Priority 드롭다운 제거
  - 데이터 소스 배지 컴포넌트 추가 (✅/❌ 표시)
  - 제한사항 섹션 추가 (⚠️)
  - 신뢰도 배지 추가 (🟢/🟡/🔴)

---

### Phase 6: 테스트 및 배포 (4주차)
**[US-006: 테스트 및 프로덕션 배포](US-006-testing-deployment.md)**
- 스토리 포인트: 8
- 담당: QA + DevOps
- 내용:
  - 통합 테스트 (7개 테스트 케이스)
  - 스테이징 배포 및 48시간 모니터링
  - Blue-Green 프로덕션 배포
  - 성공 지표 검증 (분석 커버리지 95%, 첫 분석 < 1분)

---

## 🗓️ 타임라인

| 주차 | Phase | Story | 예상 완료일 | 상태 |
|------|-------|-------|------------|------|
| 1주차 | Phase 1 | US-001 | 2025-11-22 | ☐ Todo |
| 1-2주차 | Phase 2 | US-002 | 2025-11-25 | ☐ Todo |
| 2주차 | Phase 3 | US-003 | 2025-11-27 | ☐ Todo |
| 2-3주차 | Phase 4 | US-004 | 2025-12-02 | ☐ Todo |
| 3주차 | Phase 5 | US-005 | 2025-12-06 | ☐ Todo |
| 4주차 | Phase 6 | US-006 | 2025-12-13 | ☐ Todo |

**총 스토리 포인트**: 44
**예상 기간**: 4주

---

## 🎯 성공 지표

| 지표 | 현재 | 목표 | 측정 방법 |
|------|------|------|----------|
| 분석 커버리지 | ~60% | 100% | (리포트 보유 종목 / 활성 종목) × 100 |
| 첫 분석까지 시간 | 무한대 | < 1분 | 등록 후 첫 리포트까지 평균 시간 |
| 리포트 생성 빈도 | Priority 1-2만 3회/일 | 모든 활성 종목 3회/일 | 종목당 일일 리포트 수 |
| API 효율성 | 리포트당 0-5회 | 리포트당 0회 | 리포트 생성 시 KIS API 호출 수 |

---

## 📚 관련 문서

- [Epic 문서](../../stock-analysis-redesign-epic.md) - 프로젝트 전체 개요
- [PRD](../../stock-analysis-redesign-prd.md) - 상세 요구사항 및 기술 사양
- [Brief](../../stock-analysis-redesign-brief.md) - 문제 분석 및 솔루션 개요

---

## 👥 팀 구성

| 역할 | 담당자 | 책임 |
|------|--------|------|
| Product Owner | - | 프로젝트 우선순위 및 승인 |
| Tech Lead | - | 기술 아키텍처 검토 |
| Backend Developer | - | US-001, US-002, US-003, US-004 |
| Frontend Developer | - | US-005 |
| QA Engineer | - | US-006 (테스트) |
| DevOps Engineer | - | US-006 (배포) |

---

**생성일**: 2025-11-17
**최종 수정일**: 2025-11-17
**상태**: Ready for Development
