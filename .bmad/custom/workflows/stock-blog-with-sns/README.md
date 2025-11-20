# Stock Blog with SNS Workflow

종목 AI 리포트를 기반으로 블로그 포스트와 SNS용 짧은 문구까지 자동 생성하는 오케스트라 워크플로우입니다.

## 목적

이 워크플로우는 다음을 자동화합니다:

1. **Azak 시스템에서 AI 리포트 수집** (blog-post-generator 워크플로우 활용)
2. **스토리텔링이 살아있는 블로그 글 생성** (CIS storyteller 에이전트)
3. **플랫폼별 SNS 문구 생성** (CIS brainstorming-coach 에이전트)
   - Twitter/X (280자)
   - Instagram (2200자)
   - LinkedIn (3000자)

## 워크플로우 구조

```
stock-blog-with-sns/
├── workflow.yaml        # 워크플로우 설정
├── instructions.md      # 실행 단계 정의
├── template.md          # 출력 문서 템플릿
├── checklist.md         # 검증 체크리스트
└── README.md            # 이 문서
```

## 의존성

### 필수 워크플로우
- `blog-post-generator` - Azak 시스템 접속 및 초안 생성

### 필수 에이전트
- `/bmad:cis:agents:storyteller` - 블로그 글 다듬기
- `/bmad:cis:agents:brainstorming-coach` - SNS 문구 생성

## 사용 방법

### 호출 명령

```bash
/bmad:custom:workflows:stock-blog-with-sns
```

또는 BMAD 컴파일 후 IDE 명령 팔레트에서 선택

### 입력 파라미터

실행 시 다음 정보를 입력받습니다:

1. **종목 코드** (예: 005930)
2. **종목 이름** (예: 삼성전자)

### 출력

생성되는 파일:
- 경로: `docs/blog-posts/{{date}}/{{stock_code}}-{{stock_name}}-with-sns.md`
- 포함 내용:
  - 블로그 포스트 (제목 + 본문)
  - Twitter/X용 SNS 문구
  - Instagram용 SNS 문구
  - LinkedIn용 SNS 문구
  - 플랫폼별 사용 팁
  - 콘텐츠 활용 가이드

## 워크플로우 단계

1. **종목 정보 입력** - 사용자로부터 종목 코드/이름 수집
2. **블로그 초안 생성** - blog-post-generator로 Azak 리포트 기반 초안 작성
3. **스토리텔링 다듬기** - storyteller 에이전트로 자연스러운 블로그 글로 변환
4. **SNS 문구 생성** - brainstorming-coach로 플랫폼별 최적화된 문구 작성
5. **최종 문서 생성** - template.md에 모든 내용 결합 및 저장

## 특징

### 톤&매너
- **블로그**: '주식을 공부하면서 AI 도구를 직접 만든 주린이 블로거' 느낌
- **정보 설명**: 존댓말 사용
- **개인 감정/리액션**: 반말 허용 (혼합형)
- **투자 권유 금지**: 공부/기록/서비스 소개 톤 유지

### SNS 최적화
- **Twitter/X**: 간결하고 임팩트 있게, 280자 이내
- **Instagram**: 친근하고 시각적, 이모지 활용
- **LinkedIn**: 전문적이지만 접근하기 쉬운 톤

### 자동화 수준
- Autonomous workflow (최소한의 사용자 입력)
- CIS 에이전트 활용으로 고품질 콘텐츠 생성
- 멀티 플랫폼 동시 배포 지원

## 주의사항

⚠️ **시간 기반 예측 금지**: "며칠 후 오른다" 같은 표현 사용 안 함

⚠️ **투자 조언 금지**: 투자 권유가 아닌 공부/기록 목적으로 작성

⚠️ **의존성 확인**: blog-post-generator 워크플로우와 CIS 모듈 설치 필요

## 설치 및 컴파일

1. BMAD Method 설치 프로그램 실행
2. 프로젝트 폴더 선택
3. 'Compile Agents (Quick rebuild of all agent .md files)' 선택
4. 컴파일 완료 후 IDE 명령 팔레트에서 워크플로우 확인

## 문제 해결

### blog-post-generator를 찾을 수 없음
- `.bmad/custom/workflows/blog-post-generator/` 경로 확인
- workflow.yaml의 `blog_post_generator_workflow` 경로 확인

### CIS 에이전트를 찾을 수 없음
- CIS 모듈 설치 확인
- `/bmad:cis:agents:storyteller` 경로 확인
- `/bmad:cis:agents:brainstorming-coach` 경로 확인

### 출력 파일이 생성되지 않음
- `docs/blog-posts/` 디렉토리 존재 확인
- 날짜별 서브폴더 자동 생성 확인
- 파일 쓰기 권한 확인

## 향후 개선 계획

- [ ] 다른 SNS 플랫폼 지원 (네이버 블로그, 페이스북 등)
- [ ] 이미지 자동 최적화 및 워터마크 추가
- [ ] SEO 키워드 자동 추출 및 최적화
- [ ] 발행 시간 최적화 제안
- [ ] A/B 테스트용 다중 버전 생성

## 라이센스

이 워크플로우는 개인 프로젝트용으로 작성되었습니다.

## 문의

작성자: young
생성일: 2025-11-19
