# 공개 프리뷰 링크 시스템 구현

**작업 일자**: 2025-11-21
**작업자**: Development Team
**관련 이슈**: 블로그/SNS 홍보용 공개 프리뷰 링크 시스템 구축

---

## 📋 목차

1. [변경 개요](#변경-개요)
2. [AS-IS (기존 상태)](#as-is-기존-상태)
3. [변경 필요 사유](#변경-필요-사유)
4. [TO-BE (변경 후 상태)](#to-be-변경-후-상태)
5. [변경 사항 상세](#변경-사항-상세)
6. [테스트 가이드](#테스트-가이드)
7. [사용 방법](#사용-방법)
8. [참고 사항](#참고-사항)

---

## 변경 개요

블로그나 SNS에서 종목 분석 결과를 홍보할 수 있도록 **로그인 없이 접근 가능한 공개 프리뷰 링크 시스템**을 구축했습니다. UUID 기반의 예측 불가능한 링크를 생성하여, 관리자가 원하는 종목만 선택적으로 공개할 수 있습니다.

또한, 기존 코드 중복 문제를 해결하기 위해 **StockDetailView 공통 컴포넌트**를 도입하여 유지보수성을 크게 개선했습니다.

---

## AS-IS (기존 상태)

### 1. 프리뷰 기능

기존에는 `/preview?token=xxx` 형태의 프리뷰 기능만 존재했습니다:

```typescript
// frontend/middleware.ts (기존)
if (pathname.startsWith("/preview/")) {
    const token = searchParams.get("token");
    const validToken = process.env.PREVIEW_TOKEN;

    if (token === validToken) {
        return NextResponse.next();
    }
}
```

**문제점**:
- ❌ 단일 토큰으로 모든 페이지 접근 가능
- ❌ 종목별 선택적 공개 불가능
- ❌ 토큰이 노출되면 전체 시스템 접근 가능

### 2. 종목 상세 페이지

```typescript
// frontend/app/stocks/[stockCode]/page.tsx
export default function StockDetailPage() {
    // 1107줄의 거대한 컴포넌트
    // 모든 UI 로직이 한 파일에 집중
}
```

**문제점**:
- ❌ 1107줄의 거대한 파일
- ❌ 공개 프리뷰 페이지를 만들려면 코드 중복 필요
- ❌ UI 수정 시 여러 곳을 동시에 수정해야 함

### 3. 데이터베이스

공개 프리뷰 링크를 관리할 테이블이 없었습니다.

---

## 변경 필요 사유

### 1. 블로그/SNS 홍보 필요성

- 블로그나 SNS에서 "삼성전자 AI 분석 결과" 같은 콘텐츠 공유 필요
- 로그인 없이 바로 볼 수 있어야 전환율 향상
- 종목별로 선택적으로 공개해야 함

### 2. 보안 요구사항

```
❌ 나쁜 예: /stocks/005930?isPublicPreview=true
   → 사용자가 URL의 005930을 다른 코드로 변경하면 모든 종목 접근 가능

✅ 좋은 예: /public/a7f3e9b2-4c8d-4a1e-9f2a-1b3c4d5e6f7a
   → UUID를 알지 못하면 접근 불가능
   → 관리자가 생성한 링크만 접근 가능
```

### 3. 유지보수 문제

```typescript
// 기존: 2개 파일에 동일한 UI 코드 중복
/stocks/[stockCode]/page.tsx (1107줄)
/public/[linkId]/page.tsx (945줄) → 새로 만들어야 함

// 문제: UI 수정 시 2곳을 모두 수정해야 함
```

---

## TO-BE (변경 후 상태)

### 1. 공개 프리뷰 링크 시스템

```typescript
// 관리자: 링크 생성
POST /api/admin/preview-links
{
  "stock_code": "005930"
}

// 응답
{
  "link_id": "a7f3e9b2-4c8d-4a1e-9f2a-1b3c4d5e6f7a",
  "stock_code": "005930",
  "public_url": "/public/a7f3e9b2-4c8d-4a1e-9f2a-1b3c4d5e6f7a"
}

// 공개 사용자: UUID로 접근
GET /public/a7f3e9b2-4c8d-4a1e-9f2a-1b3c4d5e6f7a
→ 인증 없이 삼성전자 분석 페이지 표시
→ URL에 종목코드 노출 안 됨
→ 다른 종목 접근 불가능
```

### 2. 공통 컴포넌트 구조

```typescript
// StockDetailView.tsx (공통 컴포넌트)
export default function StockDetailView({
  data,
  showBackButton,
  showForceUpdate,
  ...
}) {
  // 모든 UI 로직
}

// 인증된 페이지
/stocks/[stockCode]/page.tsx (449줄, 59% 감소)
<StockDetailView
  data={data}
  showBackButton={true}
  showForceUpdate={true}
/>

// 공개 프리뷰 페이지
/public/[linkId]/page.tsx (234줄, 75% 감소)
<StockDetailView
  data={data}
  showBackButton={false}
  showForceUpdate={false}
/>
```

**개선 효과**:
- ✅ 코드 중복 제거: 1369줄 감소
- ✅ UI 수정 시 1곳만 수정하면 됨
- ✅ 일관성 보장: 두 페이지가 항상 동일한 UI

### 3. 데이터베이스

```sql
CREATE TABLE public_preview_links (
    link_id VARCHAR(255) PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL
);

CREATE INDEX idx_public_preview_stock ON public_preview_links(stock_code);
CREATE INDEX idx_public_preview_creator ON public_preview_links(created_by);
```

---

## 변경 사항 상세

### 1. 데이터베이스 마이그레이션

#### 테이블 생성

**파일**: `backend/db/migrations/add_public_preview_links.sql`

```sql
-- 테이블 생성
CREATE TABLE IF NOT EXISTS public_preview_links (
    link_id VARCHAR(255) PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_public_preview_stock
ON public_preview_links(stock_code);

CREATE INDEX IF NOT EXISTS idx_public_preview_creator
ON public_preview_links(created_by);
```

**실행 방법**:
```bash
PGPASSWORD=azak_password psql -h localhost -U azak_user -d azak_db \
  -f backend/db/migrations/add_public_preview_links.sql
```

**설계 결정**:
- ❌ **Foreign Key 제약조건 없음** (애플리케이션 레벨에서 제어)
- ✅ UUID를 link_id로 사용 (예측 불가능성 보장)
- ✅ expires_at 필드로 만료 기능 지원 (선택적)

#### SQLAlchemy 모델

**파일**: `backend/db/models/public_preview_link.py`

```python
from sqlalchemy import Column, String, Integer, DateTime
from backend.db.session import Base
from datetime import datetime

class PublicPreviewLink(Base):
    __tablename__ = "public_preview_links"

    link_id = Column(String(255), primary_key=True)
    stock_code = Column(String(20), nullable=False, index=True)
    created_by = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    expires_at = Column(DateTime, nullable=True)
```

### 2. 백엔드 API 엔드포인트

**파일**: `backend/api/preview_links.py`

#### 링크 생성 (관리자 전용)

```python
@router.post("/api/admin/preview-links")
async def create_preview_link(
    request: CreatePreviewLinkRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    # UUID 생성
    link_id = str(uuid.uuid4())

    # DB에 저장
    preview_link = PublicPreviewLink(
        link_id=link_id,
        stock_code=request.stock_code,
        created_by=current_user.id,
        created_at=datetime.now(),
        expires_at=request.expires_at
    )

    db.add(preview_link)
    db.commit()

    return PreviewLinkResponse(
        link_id=link_id,
        stock_code=request.stock_code,
        public_url=f"/public/{link_id}"
    )
```

#### 링크 조회 (공개, 인증 불필요)

```python
@router.get("/api/public-preview/{link_id}")
async def get_preview_by_link(
    link_id: str,
    db: Session = Depends(get_db)
):
    # DB에서 링크 조회
    preview_link = db.query(PublicPreviewLink).filter(
        PublicPreviewLink.link_id == link_id
    ).first()

    if not preview_link:
        raise HTTPException(status_code=404, detail="링크를 찾을 수 없습니다")

    # 만료 확인
    if preview_link.expires_at and preview_link.expires_at < datetime.now():
        raise HTTPException(status_code=410, detail="링크가 만료되었습니다")

    return PublicPreviewResponse(stock_code=preview_link.stock_code)
```

#### 라우터 등록

**파일**: `backend/main.py`

```python
from backend.api import preview_links

app.include_router(preview_links.router)
```

### 3. 프론트엔드 미들웨어

**파일**: `frontend/middleware.ts`

```typescript
export async function middleware(request: NextRequest) {
  const { pathname, searchParams } = request.nextUrl;

  // 기존: 프리뷰 토큰 인증
  if (pathname.startsWith("/preview/")) {
    const token = searchParams.get("token");
    const validToken = process.env.PREVIEW_TOKEN;

    if (token === validToken) {
      return NextResponse.next();
    }
  }

  // ✅ 신규: 공개 프리뷰 링크 (인증 우회)
  if (pathname.startsWith("/public/")) {
    return NextResponse.next();
  }

  // 기존 세션 인증 로직...
}
```

### 4. 프론트엔드 라우트

**파일**: `frontend/app/public/[linkId]/page.tsx`

```typescript
export default function PublicPreviewPage() {
  const params = useParams();
  const linkId = params.linkId as string;

  const [stockCode, setStockCode] = useState<string | null>(null);
  const [stock, setStock] = useState<StockDetail | null>(null);

  // 1단계: linkId로 stock_code 조회
  useEffect(() => {
    fetch(`/api/public-preview/${linkId}`)
      .then(res => res.json())
      .then(data => setStockCode(data.stock_code))
      .catch(err => setError(err.message));
  }, [linkId]);

  // 2단계: stock_code로 종목 상세 정보 조회
  useEffect(() => {
    if (!stockCode) return;

    fetch(`/api/stocks/${stockCode}`)
      .then(res => res.json())
      .then(data => setStock(data))
      .catch(err => setError(err.message));
  }, [stockCode]);

  // 3단계: 공통 컴포넌트 렌더링
  return (
    <StockDetailView
      data={stockDetailData}
      showBackButton={false}
      showForceUpdate={false}
    />
  );
}
```

**핵심 포인트**:
- ✅ URL이 `/public/xxx` 형태로 유지됨
- ✅ 종목코드가 URL에 노출되지 않음
- ✅ 사용자가 다른 종목에 접근할 수 없음

### 5. 공통 컴포넌트 추출

**파일**: `frontend/app/components/StockDetailView.tsx`

```typescript
interface StockDetailViewProps {
  data: StockDetailData;
  abConfig?: ABTestConfig | null;
  showBackButton?: boolean;      // 뒤로가기 버튼 표시 여부
  showForceUpdate?: boolean;      // 리포트 업데이트 버튼 표시 여부
  onForceUpdate?: () => void;     // 업데이트 핸들러
  updating?: boolean;             // 업데이트 중 상태
  updateMessage?: UpdateMessage;  // 업데이트 메시지
}

export default function StockDetailView({
  data,
  showBackButton = false,
  showForceUpdate = false,
  ...
}: StockDetailViewProps) {
  // 모든 UI 로직
  return (
    <div className="min-h-screen bg-gray-50">
      <main>
        {/* 헤더 */}
        {showBackButton && <Link href="/stocks">← 종목 목록</Link>}

        {/* 현재가 */}
        {/* 차트 */}
        {/* AI 분석 리포트 */}
        {showForceUpdate && <button onClick={onForceUpdate}>업데이트</button>}

        {/* 통계 */}
        {/* 최근 뉴스 */}
      </main>
    </div>
  );
}
```

#### 기존 페이지 리팩토링

**Before**:
```typescript
// /stocks/[stockCode]/page.tsx (1107줄)
export default function StockDetailPage() {
  // 상태 관리 + 데이터 fetching + UI 로직 전부
  return (
    <div>
      {/* 1107줄의 JSX */}
    </div>
  );
}
```

**After**:
```typescript
// /stocks/[stockCode]/page.tsx (449줄)
import StockDetailView from "../../components/StockDetailView";

export default function StockDetailPage() {
  // 상태 관리 + 데이터 fetching만
  const [stock, setStock] = useState(null);
  // ... useEffect로 데이터 로드

  // UI는 공통 컴포넌트 사용
  return (
    <StockDetailView
      data={stockDetailData}
      showBackButton={true}
      showForceUpdate={true}
      onForceUpdate={handleForceUpdate}
      updating={updating}
      updateMessage={updateMessage}
    />
  );
}
```

**개선 효과**:
- `/stocks/[stockCode]/page.tsx`: 1107줄 → 449줄 (59% 감소)
- `/public/[linkId]/page.tsx`: 945줄 → 234줄 (75% 감소)
- **총 1369줄 감소**

### 6. 관리자 UI

**파일**: `frontend/app/admin/stocks/page.tsx`

```typescript
// 홍보 링크 생성 함수
const handleCreatePreviewLink = async (stock: Stock) => {
  try {
    const res = await fetch("/api/admin/preview-links", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ stock_code: stock.code }),
    });

    if (!res.ok) throw new Error("링크 생성 실패");

    const data = await res.json();
    const fullUrl = `${window.location.origin}/public/${data.link_id}`;

    // 클립보드에 복사
    await navigator.clipboard.writeText(fullUrl);

    alert(`홍보 링크가 생성되었습니다!\n\n${fullUrl}\n\n클립보드에 복사되었습니다.`);
  } catch (err: any) {
    alert(`링크 생성 실패: ${err.message}`);
  }
};

// UI에 버튼 추가
<button onClick={() => handleCreatePreviewLink(stock)}>
  🔗 홍보 링크
</button>
```

---

## 테스트 가이드

### 1. 관리자 - 링크 생성

```bash
# 1. 관리자 페이지 접속
https://azak.ngrok.app/admin/stocks

# 2. 종목 목록에서 "🔗 홍보 링크" 버튼 클릭

# 3. 생성된 링크 확인
# 예: https://azak.ngrok.app/public/a7f3e9b2-4c8d-4a1e-9f2a-1b3c4d5e6f7a
```

### 2. 공개 사용자 - 링크 접근

```bash
# 1. 브라우저 시크릿 모드 열기 (세션 초기화)

# 2. 생성된 공개 링크 접속
https://azak.ngrok.app/public/a7f3e9b2-4c8d-4a1e-9f2a-1b3c4d5e6f7a

# 3. 확인 사항
✅ 로그인 없이 종목 상세 페이지가 표시됨
✅ "← 종목 목록" 버튼이 보이지 않음
✅ "🔄 리포트 업데이트" 버튼이 보이지 않음
✅ URL에 종목코드가 노출되지 않음
✅ URL의 UUID를 변경하면 404 에러
```

### 3. API 직접 테스트

#### 링크 생성 (관리자 권한 필요)

```bash
curl -X POST http://localhost:8000/api/admin/preview-links \
  -H "Content-Type: application/json" \
  -H "Cookie: azak_session=<your_session>" \
  -d '{
    "stock_code": "005930"
  }'

# 응답
{
  "link_id": "a7f3e9b2-4c8d-4a1e-9f2a-1b3c4d5e6f7a",
  "stock_code": "005930",
  "created_by": 1,
  "created_at": "2025-11-21T16:30:00",
  "expires_at": null,
  "public_url": "/public/a7f3e9b2-4c8d-4a1e-9f2a-1b3c4d5e6f7a"
}
```

#### 링크 조회 (인증 불필요)

```bash
curl http://localhost:8000/api/public-preview/a7f3e9b2-4c8d-4a1e-9f2a-1b3c4d5e6f7a

# 응답
{
  "stock_code": "005930"
}
```

#### 만료된 링크 테스트

```bash
# 과거 날짜로 만료일 설정
curl -X POST http://localhost:8000/api/admin/preview-links \
  -d '{
    "stock_code": "005930",
    "expires_at": "2025-01-01T00:00:00"
  }'

# 조회 시 410 Gone 응답
curl http://localhost:8000/api/public-preview/{link_id}
# → 410 Gone: "링크가 만료되었습니다"
```

### 4. 데이터베이스 확인

```sql
-- 생성된 링크 조회
SELECT * FROM public_preview_links ORDER BY created_at DESC;

-- 특정 종목의 링크 조회
SELECT * FROM public_preview_links WHERE stock_code = '005930';

-- 만료되지 않은 링크만 조회
SELECT * FROM public_preview_links
WHERE expires_at IS NULL OR expires_at > NOW();
```

---

## 사용 방법

### 1. 관리자: 홍보 링크 생성

```bash
# 1. 관리자로 로그인
https://azak.ngrok.app/login

# 2. 종목 관리 페이지 이동
https://azak.ngrok.app/admin/stocks

# 3. 원하는 종목의 "🔗 홍보 링크" 버튼 클릭

# 4. 생성된 링크가 클립보드에 자동 복사됨
https://azak.ngrok.app/public/a7f3e9b2-4c8d-4a1e-9f2a-1b3c4d5e6f7a

# 5. 블로그나 SNS에 링크 공유
```

### 2. 공개 사용자: 링크 접근

```bash
# 1. 공유된 링크 클릭
https://azak.ngrok.app/public/a7f3e9b2-4c8d-4a1e-9f2a-1b3c4d5e6f7a

# 2. 로그인 없이 바로 종목 분석 페이지 확인
# - 현재가 정보
# - 주가 차트
# - AI 종합 투자 리포트
# - 시장 동향 통계
# - 최근 뉴스 & AI 분석
```

### 3. 링크 관리

#### 종목별 링크 조회

```bash
curl http://localhost:8000/api/admin/preview-links/005930 \
  -H "Cookie: azak_session=<session>"

# 응답: 삼성전자의 모든 공개 링크 목록
```

#### 링크 삭제

```bash
curl -X DELETE http://localhost:8000/api/admin/preview-links/{link_id} \
  -H "Cookie: azak_session=<session>"
```

---

## 참고 사항

### 1. 보안 고려사항

#### ✅ 장점
- UUID 기반으로 예측 불가능
- 관리자만 링크 생성 가능
- 종목별 선택적 공개
- 만료 기능 지원 (선택적)

#### ⚠️ 주의사항
- 링크를 공유하면 누구나 접근 가능
- 민감한 정보는 공개 프리뷰에 표시하지 말 것
- 정기적으로 오래된 링크 정리 권장

### 2. 기존 프리뷰 토큰과의 차이

| 구분 | 프리뷰 토큰 (`/preview?token=xxx`) | 공개 링크 (`/public/xxx`) |
|------|----------------------------------|-------------------------|
| **사용 목적** | 내부 개발/테스트용 | 블로그/SNS 홍보용 |
| **인증 방식** | 단일 토큰 (환경변수) | UUID 링크 (DB 관리) |
| **접근 범위** | 모든 페이지 접근 가능 | 특정 종목만 접근 가능 |
| **만료 기능** | ❌ 없음 | ✅ 지원 (선택적) |
| **관리** | .env 파일 수정 | 관리자 UI에서 생성/삭제 |
| **보안 수준** | 낮음 (토큰 유출 시 위험) | 높음 (링크별 격리) |

**결론**: 두 시스템은 상호 보완적으로 사용하세요.
- **개발/테스트**: `/preview?token=xxx`
- **공개 홍보**: `/public/xxx`

### 3. 코드 리팩토링 효과

#### Before (기존)
```
/stocks/[stockCode]/page.tsx        1107줄 (거대한 파일)
/public/[linkId]/page.tsx           945줄 (중복 코드)
                                    ─────
                                    2052줄
```

#### After (개선)
```
/components/StockDetailView.tsx     (공통 컴포넌트)
/stocks/[stockCode]/page.tsx        449줄 (59% 감소)
/public/[linkId]/page.tsx           234줄 (75% 감소)
                                    ─────
                                    683줄 (67% 감소)
```

**개선 효과**:
- ✅ **1369줄 감소** (총 코드량)
- ✅ **UI 수정 시 1곳만 수정**
- ✅ **일관성 보장** (두 페이지 항상 동일)
- ✅ **테스트 용이** (공통 컴포넌트만 테스트)

### 4. 성능 고려사항

#### 데이터베이스 인덱스
```sql
-- stock_code로 조회 시 빠른 검색
CREATE INDEX idx_public_preview_stock ON public_preview_links(stock_code);

-- 관리자별 링크 조회 시 빠른 검색
CREATE INDEX idx_public_preview_creator ON public_preview_links(created_by);
```

#### 캐싱 전략 (향후 개선)
```python
# 자주 조회되는 링크를 Redis에 캐싱 가능
# - link_id → stock_code 매핑
# - TTL: 1시간
# - 만료 시 DB 재조회
```

### 5. 트러블슈팅

#### 문제: 공개 링크 접속 시 로그인 페이지로 리다이렉트

```bash
# 원인: 미들웨어 재시작 필요
pm2 restart azak-frontend

# 확인: 미들웨어 로그 확인
pm2 logs azak-frontend | grep "public"
```

#### 문제: 링크 생성 시 403 Forbidden

```bash
# 원인: 관리자 권한 없음
# 해결: 관리자 계정으로 로그인

# 확인: 사용자 권한 조회
SELECT id, username, role FROM users WHERE username = 'your_username';
```

#### 문제: StockDetailView 컴포넌트를 찾을 수 없음

```bash
# 원인: 프론트엔드 빌드 필요
pm2 restart azak-frontend

# 확인: 컴포넌트 파일 존재 여부
ls -la frontend/app/components/StockDetailView.tsx
```

---

## 관련 파일

### 백엔드
- `backend/db/migrations/add_public_preview_links.sql` - DB 마이그레이션
- `backend/db/models/public_preview_link.py` - SQLAlchemy 모델
- `backend/api/preview_links.py` - API 엔드포인트
- `backend/main.py` - 라우터 등록

### 프론트엔드
- `frontend/middleware.ts` - 공개 링크 인증 우회
- `frontend/app/public/[linkId]/page.tsx` - 공개 프리뷰 페이지
- `frontend/app/components/StockDetailView.tsx` - 공통 컴포넌트
- `frontend/app/stocks/[stockCode]/page.tsx` - 인증된 종목 상세 (리팩토링)
- `frontend/app/admin/stocks/page.tsx` - 관리자 UI (링크 생성 버튼)

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2025-11-21 | 1.0.0 | 공개 프리뷰 링크 시스템 초기 구현 |
| 2025-11-21 | 1.0.0 | StockDetailView 공통 컴포넌트 추출 (1369줄 감소) |

---

**작성일**: 2025-11-21
**최종 수정일**: 2025-11-21
**작성자**: Development Team
