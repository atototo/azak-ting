# Azak 기능 소개 블로그 생성기 - Workflow Instructions

<critical>The workflow execution engine is governed by: {project-root}/.bmad/core/tasks/workflow.xml</critical>
<critical>You MUST have already loaded and processed: {project-root}/.bmad/custom/workflows/azak-feature-intro/workflow.yaml</critical>
<critical>Communicate in {communication_language} throughout the workflow execution</critical>
<critical>⚠️ ABSOLUTELY NO TIME ESTIMATES - NEVER mention hours, days, weeks, months, or ANY time-based predictions</critical>

<workflow>

<step n="1" goal="사용자 입력 수집 및 feature_slug 생성">
<ask>어떤 기능을 소개하는 블로그를 작성할까요?

기능 이름을 입력해주세요 (예: "비동기 리포트 생성 시스템"):
</ask>

<action>입력받은 기능명을 {{feature_name}}에 저장</action>
<action>feature_name을 영문 slug로 자동 변환하여 {{feature_slug}}에 저장
- 공백 → 하이픈(-)
- 한글 → 영문 의역
- 소문자 변환
- 예: "비동기 리포트 생성" → "async-report-system"
</action>

<ask>기능에 대한 간단한 설명을 입력해주세요 (1-2문장):
예: "AI 리포트 생성을 백그라운드에서 처리하고, 완료되면 실시간 알림으로 통지하는 시스템"
</ask>

<action>입력받은 설명을 {{feature_description}}에 저장</action>

<ask>주요 기능들을 입력해주세요 (쉼표로 구분):
예: "백그라운드 처리, Toast 알림, 5초 폴링, 진행 상태 추적"
</ask>

<action>입력받은 주요 기능들을 {{key_features}}에 저장</action>

<ask>프리뷰할 URL들을 입력해주세요 (쉼표로 구분, 필수):
예: /stocks/005930, /dashboard
</ask>

<action>입력받은 URL들을 {{preview_urls}}에 저장</action>

<ask>관련 파일 경로들을 입력해주세요 (쉼표로 구분, 선택사항):
예: backend/api/reports.py, frontend/components/ReportCard.tsx
비워두면 화면 중심으로 작성됩니다.
</ask>

<action>입력받은 파일 경로들을 {{related_files}}에 저장</action>

<ask>배경 설명이 있나요? (선택사항)
이 기능이 어떤 문제를 해결하는지, 왜 필요한지 설명해주세요.
비워두면 배경 섹션 없이 바로 기능 소개로 시작합니다.
</ask>

<action>입력받은 배경을 {{problem_context}}에 저장</action>
</step>

<step n="2" goal="프로젝트 코드 분석 (선택적)">
<critical>
기능 소개 블로그에서는 코드가 선택적
- {{related_files}}가 비어있으면 이 단계 건너뛰기
- 있으면 간단히 분석하되, 핵심 기능만 추출
- 전체 코드보다는 "이런 기술 사용" 수준으로
</critical>

<action>{{related_files}}가 비어있지 않으면 파일 읽기</action>

<action>파일이 있으면 다음 정보만 간단히 추출:
1. 사용된 주요 기술/라이브러리
2. 핵심 함수/클래스 이름만 (코드는 최소화)
3. API 엔드포인트 (있으면)
</action>

<action>추출한 정보를 {{tech_used}}에 저장</action>

<critical>
코드 스니펫은 꼭 필요할 때만:
- API 사용 방법 예시
- 설정 파일 예시
- 간단한 사용 코드
전체 구현 코드는 포함하지 않음!
</critical>
</step>

<step n="3" goal="프리뷰 화면 캡처 (필수)">
<critical>
기능 소개 블로그의 핵심은 "화면"!
- 사용자가 실제로 보는 화면을 캡처
- 사용 순서대로 여러 화면 캡처
- Before/After 비교도 좋음 (있으면)
</critical>

<action>{{preview_urls}}의 각 URL에 대해 Playwright MCP 사용</action>

<action>각 URL에 대해:
1. 완전한 URL 생성:
   - {{azak_base_url}} + URL + ?token={{azak_token}}

2. Playwright로 페이지 접근
3. 페이지 로드 후 3초 대기
4. 전체 페이지 또는 핵심 영역 캡처
   - 파일명: {{screenshot_output}}/feature-{{feature_slug}}-{순번}.png

5. 캡처한 화면에서 다음 정보 추출:
   - UI 요소 (버튼, 입력 필드 등)
   - 주요 데이터
   - 사용자 플로우 파악
</action>

<action>캡처된 이미지 경로를 {{screenshot_paths}}에 저장</action>
<action>각 화면에 대한 설명을 {{screenshot_descriptions}}에 저장</action>

<critical>
이미지 경로는 반드시 상대 경로:
- 블로그: {output_folder}/blog-posts/feature-{{feature_slug}}-{{date}}.md
- 이미지: {screenshot_output}/feature-{{feature_slug}}-*.png
- 상대 경로: ../../.playwright-mcp/feature-{{feature_slug}}-*.png
</critical>
</step>

<step n="3.5" goal="GIF 자동 생성 (선택적)">
<critical>
사용 흐름을 GIF로 보여주면 더 효과적!
- {{gif_urls}}가 비어있지 않으면 GIF 자동 생성
- 연속 스크린샷 → ffmpeg로 GIF 변환
- 동적인 사용 플로우를 보여주는 데 최적
</critical>

<action>{{gif_urls}}가 비어있는지 확인</action>

<action>{{gif_urls}}가 있으면 각 URL에 대해:

1. Playwright로 페이지 접근
   - URL: {{azak_base_url}} + gif_url + ?token={{azak_token}}

2. 연속 스크린샷 촬영
   - {{gif_duration}}초 동안 1초마다 1장 캡처
   - 파일명: {{screenshot_output}}/gif-{{feature_slug}}-{url_index}-{frame}.png
   - 총 {{gif_duration}}장의 이미지

3. 페이지 상호작용 (선택적)
   - 버튼 클릭, 스크롤 등 필요한 액션 수행
   - 각 액션 후 1초 대기 후 캡처

4. ffmpeg로 GIF 변환
   Bash 도구 사용:
   ```bash
   cd {{screenshot_output}}
   ffmpeg -framerate {{gif_framerate}} -pattern_type glob \
     -i 'gif-{{feature_slug}}-{url_index}-*.png' \
     -vf "scale={{gif_scale_width}}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
     -loop 0 \
     gif-{{feature_slug}}-{url_index}.gif
   ```

5. 원본 PNG 파일 삭제 (선택)
   ```bash
   rm gif-{{feature_slug}}-{url_index}-*.png
   ```
</action>

<action>생성된 GIF 경로를 {{gif_paths}}에 저장</action>
<action>각 GIF에 대한 설명을 {{gif_descriptions}}에 저장</action>

<critical>
GIF 삽입 시 마크다운:
![사용 흐름](../../.playwright-mcp/gif-{{feature_slug}}-1.gif)

⚠️ ffmpeg 필요:
- macOS: brew install ffmpeg
- Ubuntu: sudo apt install ffmpeg
- Windows: choco install ffmpeg
</critical>

<action>{{gif_urls}}가 비어있으면 이 단계 건너뛰기</action>
</step>

<step n="4" goal="블로그 제목 생성 (기능 소개형)">
<action>다음 규칙으로 제목 생성:

규칙:
- 기능 소개임을 명확히
- 친근하면서도 전문적으로
- 핵심 가치 포함

좋은 예:
- "Azak 비동기 리포트 시스템 - 기다림 없는 AI 분석"
- "실시간 Toast 알림으로 완성도 UP! Azak 리포트 시스템 소개"
- "Azak의 백그라운드 처리 시스템, 어떻게 동작할까?"
- "5초마다 폴링? Azak 리포트 상태 추적 시스템"

나쁜 예:
- "비동기 리포트 생성 시스템" ❌ (재미없음)
- "신기능 소개" ❌ (정보 없음)
- "개발기" ❌ (기능 소개가 아님)
</action>

<action>생성된 제목을 {{blog_title}}에 저장</action>

<template-output>blog_title</template-output>
</step>

<step n="5" goal="기능 개요 섹션 작성">
<action>기능에 대한 전체적인 소개 작성</action>

<critical>
톤: 친근하면서 설명 중심
- "~해요", "~할 수 있어요" 종결어미
- 기능의 핵심 가치를 3-4문장으로
- 누가, 언제, 왜 사용하는지
</critical>

<action>내용 구성:
1. 이 기능이 무엇인지 ({{feature_description}} 활용)
2. 어떤 가치를 제공하는지
3. 누가 사용하는지 (사용자 관점)

{{problem_context}}가 있으면:
- 배경 설명도 자연스럽게 포함
- "기존에는 ~했는데, 이제는 ~해요" 구조
</action>

<action>작성 예시 (참고용):
"비동기 리포트 생성 시스템은 AI 분석 리포트를 백그라운드에서 처리하는 기능이에요

기존에는 리포트 생성 시 30초 동안 화면이 멈춰있었는데
이제는 즉시 응답하고 백그라운드에서 처리해요

리포트가 완료되면 Toast 알림으로 바로 알려주니까
다른 작업 하면서 기다릴 수 있죠"
</action>

<template-output>overview_section</template-output>
</step>

<step n="6" goal="주요 기능 섹션 작성">
<action>{{key_features}}를 바탕으로 주요 기능들을 상세히 설명</action>

<critical>
각 기능마다:
- 무엇을 하는지
- 어떻게 동작하는지
- 왜 유용한지

화면 캡처가 있으면 각 기능 설명에 이미지 삽입
</critical>

<action>내용 구성:
{{key_features}}를 쉼표로 분리하여 각각에 대해:

### 기능 1: [기능명]
- 설명: 무엇을 하는지
- 동작: 어떻게 작동하는지
- 화면: 관련 이미지 삽입 (있으면)

예:
"### 백그라운드 처리

리포트 생성을 Celery Task로 백그라운드에서 처리해요
사용자는 즉시 다음 화면으로 넘어갈 수 있고
서버는 타임아웃 걱정 없이 처리할 수 있죠

![백그라운드 처리 화면](../../.playwright-mcp/feature-async-report-1.png)"
</action>

<template-output>features_section</template-output>
</step>

<step n="7" goal="사용 방법 섹션 작성 (화면 캡처 필수)">
<action>사용자가 이 기능을 어떻게 사용하는지 단계별로 설명</action>

<critical>
이 섹션이 기능 소개 블로그의 핵심!
- 단계별로 나누기 (Step 1, Step 2, ...)
- 각 단계마다 화면 캡처 포함
- 사용자 관점에서 작성
</critical>

<action>내용 구성:
1. 시작 방법
   - 어디서 시작하는지
   - 화면 캡처

2. 주요 단계들
   - Step 1: 무엇을 클릭/입력
   - Step 2: 무엇이 일어나는지
   - ...

3. 결과 확인
   - 최종 결과 화면
   - 무엇을 볼 수 있는지

각 단계마다 {{screenshot_paths}}의 이미지 삽입
</action>

<action>작성 예시 (참고용):
"## 사용 방법

### Step 1: 리포트 생성 요청

종목 상세 페이지에서 '리포트 생성' 버튼을 클릭하세요

![리포트 생성 버튼](../../.playwright-mcp/feature-async-report-1.png)

### Step 2: 즉시 응답

버튼 클릭하면 바로 화면이 전환되고
오른쪽 위에 'Toast 알림'이 뜹니다

![Toast 알림](../../.playwright-mcp/feature-async-report-2.png)

### Step 3: 완료 알림

백그라운드에서 리포트가 생성되면
자동으로 완료 알림이 뜨고 화면이 업데이트돼요

![완료 알림](../../.playwright-mcp/feature-async-report-3.png)"
</action>

<template-output>usage_section</template-output>
</step>

<step n="8" goal="기술 스택 섹션 작성 (코드 선택적)">
<action>이 기능에 사용된 기술 스택 정리</action>

<critical>
코드는 꼭 필요할 때만!
- API 사용 예시
- 설정 방법
- 간단한 통합 코드

전체 구현 코드는 넣지 않음
</critical>

<action>내용 구성:
1. 사용된 기술들 나열
   - 백엔드: Python, FastAPI, Celery, Redis
   - 프론트엔드: Next.js, React Query
   - 기타: ...

2. 핵심 기술 설명 (선택적)
   - Celery가 왜 필요했는지
   - Redis를 어떻게 사용하는지

3. 코드 예시 (선택적)
   - API 호출 방법
   - 설정 파일 예시
   - 간단한 통합 코드만

{{tech_used}}가 있으면 활용
</action>

<action>작성 예시 (참고용):
"## 기술 스택

**백엔드**
- Celery: 비동기 작업 처리
- Redis: 작업 큐 & 결과 캐싱
- FastAPI: API 엔드포인트

**프론트엔드**
- React Query: 5초 폴링 구현
- Toast 라이브러리: 알림 표시

**코드 예시 (선택적)**
프론트엔드에서 리포트 상태를 확인하는 방법:

```typescript
// 5초마다 폴링
const { data } = useQuery({
  queryKey: ['report-status', stockCode],
  queryFn: () => fetchReportStatus(stockCode),
  refetchInterval: 5000,
})
```"
</action>

<template-output>tech_stack_section</template-output>
</step>

<step n="9" goal="향후 계획 섹션 (선택적)">
<action>앞으로 추가될 기능이나 개선 계획 작성 (선택적)</action>

<critical>
이 섹션은 완전 선택적!
- 계획이 있으면 간단히 언급
- 없으면 섹션 자체를 생략
</critical>

<action>내용 구성 (있으면):
1. 추가 예정 기능
2. 개선 예정 사항
3. 사용자 피드백 반영 계획

톤: 긍정적이고 기대감 조성
"곧 추가될 예정이에요", "더 나아질 거예요" 등
</action>

<action>작성 예시 (참고용):
"## 향후 계획

현재는 5초 폴링 방식이지만
Server-Sent Events(SSE)로 업그레이드할 예정이에요

실시간성이 더 좋아지고
서버 부하도 줄일 수 있을 것 같아요

또한 진행률 표시 기능도 추가할 계획입니다"
</action>

<template-output>future_plans_section</template-output>
</step>

<step n="10" goal="최종 블로그 포스트 생성 및 저장">
<action>템플릿에 모든 변수 삽입하여 최종 마크다운 생성</action>

<critical>
⚠️ ABSOLUTELY FORBIDDEN - 절대 포함하지 말 것:
- "🤖 Generated with [Claude Code](https://claude.com/claude-code)"
- "Co-Authored-By: Claude <noreply@anthropic.com>"
- 어떠한 형태의 AI 생성 표기도 금지
</critical>

<action>파일 저장:
경로: {output_folder}/blog-posts/feature-{{feature_slug}}-{{date}}.md
</action>

<action>사용자에게 다음 정보 전달:
1. 생성된 파일 경로
2. 캡처된 이미지 경로 ({screenshot_output}/)
3. 포함된 화면 캡처 개수
4. 다음 단계 안내:
   - 이미지 검토
   - 블로그 포스팅
</action>

<critical>
{communication_language}로 완료 메시지 작성:
"기능 소개 블로그 포스트가 생성되었습니다!

📁 파일: [경로]
🖼️ 화면 캡처: N개
💻 코드 스니펫: N개 (있으면)

다음 단계:
1. 이미지를 블로그에 업로드하세요
2. 마크다운의 이미지 링크를 수정하세요
3. 블로그에 포스팅하세요

화이팅!"
</critical>
</step>

</workflow>
