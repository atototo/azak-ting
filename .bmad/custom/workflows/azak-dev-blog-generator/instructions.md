# Azak 개발 블로그 생성기 - Workflow Instructions

<critical>The workflow execution engine is governed by: {project-root}/.bmad/core/tasks/workflow.xml</critical>
<critical>You MUST have already loaded and processed: {project-root}/.bmad/custom/workflows/azak-dev-blog-generator/workflow.yaml</critical>
<critical>Communicate in {communication_language} throughout the workflow execution</critical>
<critical>⚠️ ABSOLUTELY NO TIME ESTIMATES - NEVER mention hours, days, weeks, months, or ANY time-based predictions</critical>

<workflow>

<step n="1" goal="사용자 입력 수집 및 topic_slug 생성">
<ask>어떤 개발 내용을 블로그로 작성할까요?

개발 주제를 입력해주세요 (예: "비동기 리포트 생성 기능 개발"):
</ask>

<action>입력받은 주제를 {{topic}}에 저장</action>
<action>topic을 영문 slug로 자동 변환하여 {{topic_slug}}에 저장
- 공백 → 하이픈(-)
- 한글 → 영문 의역
- 소문자 변환
- 예: "비동기 리포트 생성" → "async-report-generation"
</action>

<ask>개발 유형을 선택해주세요:
1. 새 기능 개발
2. 버그 수정/트러블슈팅
3. 리팩토링/최적화
4. 기술 스택 도입
</ask>

<action>선택한 유형을 {{feature_type}}에 저장</action>

<ask>핵심 포인트를 입력해주세요 (예: "Celery + Redis, Toast 알림, 5초 폴링"):
</ask>

<action>입력받은 핵심 포인트를 {{key_points}}에 저장</action>

<ask>관련 파일 경로들을 입력해주세요 (쉼표로 구분, 선택사항):
예: backend/api/reports.py, frontend/components/ReportCard.tsx
</ask>

<action>입력받은 파일 경로들을 {{related_files}}에 저장</action>

<ask>프리뷰할 URL들을 입력해주세요 (쉼표로 구분, 선택사항):
예: /stocks/005930, /dashboard
</ask>

<action>입력받은 URL들을 {{preview_urls}}에 저장</action>
</step>

<step n="2" goal="프로젝트 코드 분석">
<critical>
개발 블로그의 핵심은 "실제 코드"를 보여주는 것
- 관련 파일들을 읽어서 어떤 코드가 추가/수정되었는지 파악
- 핵심 로직만 추출하여 블로그에 삽입
- Before/After 비교가 가능하면 더 좋음
</critical>

<action>{{related_files}}에 입력된 파일들을 Read 도구로 읽기</action>

<action>각 파일에서 다음 정보 추출:
1. 파일 목적 (API, 컴포넌트, 유틸리티 등)
2. 핵심 함수/클래스
3. 사용된 기술 스택 (import 문 확인)
4. 주요 로직 (async/await, API 호출, 상태 관리 등)
5. 주석/docstring에서 설명 추출
</action>

<action>추출한 정보를 변수에 저장:
- {{code_analysis}}: 전체 코드 분석 결과
- {{tech_stack_used}}: 실제 사용된 기술 스택
- {{key_functions}}: 핵심 함수들
- {{code_snippets}}: 블로그에 삽입할 코드 조각들
</action>

<critical>
코드 스니펫 작성 규칙:
- 전체 코드를 다 넣지 말고 핵심만
- 주석 포함하여 설명력 높이기
- 민감 정보 제거 (토큰, API 키 등)
- 언어 지정 (```python, ```typescript 등)
</critical>
</step>

<step n="2.5" goal="Git 히스토리 분석 (선택)">
<critical>
가능하면 Git 커밋 히스토리를 확인하여:
- 어떤 파일들이 변경되었는지
- 몇 줄이 추가/삭제되었는지
- 커밋 메시지에서 개발 의도 파악
</critical>

<action>Bash 도구를 사용하여 Git 로그 확인 (선택):
cd {project_path} && git log --oneline --all --grep="{{topic}}" -10
</action>

<action>관련 커밋이 있으면:
- 커밋 메시지 분석
- 변경된 파일 목록 확인
- Before/After 코드 비교 가능 여부 체크
</action>

<action>Git 정보를 {{git_history}}에 저장</action>
</step>

<step n="3" goal="프리뷰 화면 캡처 (Playwright)">
<critical>
개발한 기능이 실제로 동작하는 모습을 화면으로 보여주기
- 사용자가 입력한 preview_urls를 기반으로 화면 캡처
- Before/After 비교 가능하면 더 좋음
</critical>

<action>{{preview_urls}}가 비어있지 않으면 Playwright MCP 사용</action>

<action>각 URL에 대해:
1. 완전한 URL 생성:
   - {{azak_base_url}} + URL + ?token={{azak_token}}
   - 예: https://azak.ngrok.app/preview/stocks/005930?token=...

2. Playwright로 페이지 접근
3. 페이지 로드 후 3초 대기 (동적 콘텐츠 로딩)
4. 전체 페이지 또는 특정 영역 캡처
   - 파일명: {{screenshot_output}}/dev-{{topic_slug}}-{순번}.png

5. 캡처한 화면에서 주요 정보 추출:
   - 기능이 제대로 동작하는지 확인
   - UI/UX 변경사항 확인
   - 에러가 없는지 확인
</action>

<action>캡처된 이미지 경로를 {{screenshot_paths}}에 저장</action>

<critical>
블로그 본문에 이미지 삽입 시 마크다운 형식:

⚠️ IMPORTANT: 이미지 경로는 반드시 상대 경로로 작성!
- 블로그 포스트 위치: {output_folder}/blog-posts/dev-{{topic_slug}}-{{date}}.md
- 이미지 위치: {screenshot_output}/dev-{{topic_slug}}-*.png
- 올바른 상대 경로: ../../.playwright-mcp/dev-{{topic_slug}}-*.png

예시:
![개발한 기능 화면](../../.playwright-mcp/dev-{{topic_slug}}-1.png)
</critical>
</step>

<step n="3.5" goal="GIF 자동 생성 (선택적)">
<critical>
개발 과정이나 결과를 GIF로 보여주면 더 효과적!
- {{gif_urls}}가 비어있지 않으면 GIF 자동 생성
- 연속 스크린샷 → ffmpeg로 GIF 변환
- Before/After 비교나 동적인 변화를 보여주기 좋음
</critical>

<action>{{gif_urls}}가 비어있는지 확인</action>

<action>{{gif_urls}}가 있으면 각 URL에 대해:

1. Playwright로 페이지 접근
   - URL: {{azak_base_url}} + gif_url + ?token={{azak_token}}

2. 연속 스크린샷 촬영
   - {{gif_duration}}초 동안 1초마다 1장 캡처
   - 파일명: {{screenshot_output}}/gif-{{topic_slug}}-{url_index}-{frame}.png
   - 총 {{gif_duration}}장의 이미지

3. 페이지 상호작용 (선택적)
   - 버튼 클릭, 입력, 스크롤 등
   - 각 액션 후 1초 대기 후 캡처

4. ffmpeg로 GIF 변환
   Bash 도구 사용:
   ```bash
   cd {{screenshot_output}}
   ffmpeg -framerate {{gif_framerate}} -pattern_type glob \
     -i 'gif-{{topic_slug}}-{url_index}-*.png' \
     -vf "scale={{gif_scale_width}}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
     -loop 0 \
     gif-{{topic_slug}}-{url_index}.gif
   ```

5. 원본 PNG 파일 삭제 (선택)
   ```bash
   rm gif-{{topic_slug}}-{url_index}-*.png
   ```
</action>

<action>생성된 GIF 경로를 {{gif_paths}}에 저장</action>
<action>각 GIF에 대한 설명을 {{gif_descriptions}}에 저장</action>

<critical>
GIF 삽입 시 마크다운:
![개발 과정](../../.playwright-mcp/gif-{{topic_slug}}-1.gif)

⚠️ ffmpeg 필요:
- macOS: brew install ffmpeg
- Ubuntu: sudo apt install ffmpeg
- Windows: choco install ffmpeg
</critical>

<action>{{gif_urls}}가 비어있으면 이 단계 건너뛰기</action>
</step>

<step n="4" goal="블로그 제목 생성 (개발자스럽게)">
<action>다음 규칙으로 제목 생성:

규칙:
- 개발자스러운 톤 유지
- 기술 용어 포함 가능하지만 과하지 않게
- 구어체 사용 가능
- 흥미 유발 요소 포함

좋은 예:
- "Celery로 비동기 리포트 만들다가 삽질한 이야기"
- "5초 폴링이 답이었다 - Azak 리포트 시스템 개선기"
- "Redis Queue 붙였더니 속도가 10배 빨라진 썰"
- "Toast 알림 하나 추가하는데 왜 이렇게 고생했을까"

나쁜 예:
- "비동기 리포트 생성 시스템 개발" ❌ (너무 딱딱함)
- "Azak 프로젝트 성능 최적화 완료" ❌ (재미없음)
- "개발일지 #5" ❌ (정보 없음)
</action>

<action>생성된 제목을 {{blog_title}}에 저장</action>

<template-output>blog_title</template-output>
</step>

<step n="5" goal="문제 상황 섹션 작성 (구어체 + 개발자 톤)">
<action>개발을 시작하게 된 배경과 문제 상황 작성</action>

<critical>
톤: 구어체 + 개발자다운 표현
- "~거든", "~더라", "~지 뭐" 같은 종결어미
- "근데", "그래서", "일단" 같은 접속사
- 솔직한 감정 표현
- 기술 용어는 자연스럽게 녹여내기
</critical>

<action>내용 구성:
1. 어떤 문제가 있었는지
   - 사용자 불편사항
   - 시스템 한계
   - 성능 이슈 등

2. 왜 이걸 해결해야 했는지
   - 비즈니스 임팩트
   - 사용자 경험
   - 개발자 경험

3. 처음에 어떻게 접근하려 했는지
   - 초기 아이디어
   - 고려했던 옵션들
</action>

<action>작성 예시 (참고용):
"Azak에서 AI 리포트 생성하는데 30초씩 걸리더라

사용자는 그냥 화면 멈춰있고
나는 FastAPI 타임아웃 걱정하고
그래서 일단 비동기로 돌리기로 했지"
</action>

<template-output>problem_section</template-output>
</step>

<step n="6" goal="해결 과정 섹션 작성 (코드 포함)">
<action>실제로 어떻게 해결했는지 작성</action>

<critical>
이 섹션이 개발 블로그의 핵심!
- 코드 스니펫 필수 포함
- Before/After 비교 (가능하면)
- 왜 이 방법을 선택했는지 설명
- 삽질한 부분도 솔직하게
</critical>

<action>내용 구성:
1. 선택한 기술 스택 소개
   - 예: "Celery + Redis를 선택한 이유는..."
   - 다른 옵션과 비교 (선택사항)

2. 구현 과정
   a) 초기 시도
      - 코드 스니펫 1
      - 무엇이 문제였는지

   b) 개선/수정
      - 코드 스니펫 2
      - 어떻게 개선했는지

   c) 최종 구현
      - 코드 스니펫 3 (핵심 코드)
      - 작동 원리 설명

3. 트러블슈팅
   - 만난 버그/에러
   - 어떻게 해결했는지
   - 삽질한 이야기

4. 테스트/검증
   - 어떻게 테스트했는지
   - 성능 개선 결과 (숫자로)
</action>

<action>코드 스니펫 삽입 규칙:
- 핵심 코드만 (전체 파일 X)
- 주석 추가하여 설명력 높이기
- 언어 지정 필수 (```python, ```typescript)
- Before/After 비교 시 나란히 배치
</action>

<action>작성 예시 (참고용):
"## Celery Task 만들기

일단 비동기 작업을 위해 Celery task를 만들었어

```python
# backend/tasks/report_tasks.py
from celery import shared_task

@shared_task
def generate_report_async(stock_code: str, model_ids: list):
    \"\"\"비동기로 리포트 생성\"\"\"
    # AI 모델 호출 (30초 소요)
    result = generate_ai_report(stock_code, model_ids)

    # Redis에 결과 저장
    cache.set(f'report:{stock_code}', result, timeout=3600)

    return result
```

근데 문제는 프론트엔드에서 언제 완료되는지 모른다는 거

그래서 5초마다 폴링하는 방식으로..."
</action>

<template-output>solution_section</template-output>
</step>

<step n="7" goal="결과 섹션 작성 (화면 캡처 포함)">
<action>개발한 기능이 실제로 동작하는 모습 작성</action>

<critical>
화면 캡처 이미지 필수 포함!
- 사용자가 보는 최종 결과
- UI/UX 개선사항
- 성능 개선 수치
</critical>

<action>내용 구성:
1. 최종 결과물 소개
   - 어떤 기능이 추가되었는지
   - 사용자가 뭘 볼 수 있는지

2. 화면 캡처 삽입
   - {{screenshot_paths}}의 이미지들 삽입
   - 각 이미지에 대한 설명 추가
   - 상대 경로 사용 (../../.playwright-mcp/...)

3. 성능 개선 수치 (있으면)
   - Before: 30초 대기
   - After: 즉시 응답 + 백그라운드 처리
   - 정량적 지표

4. 사용자 경험 개선
   - Toast 알림으로 완료 통지
   - 대기 시간 제거
   - 더 나은 UX
</action>

<action>작성 예시 (참고용):
"## 결과: 기다림 없는 리포트 생성

이제 사용자는 버튼 클릭하면 바로 화면이 넘어가고
백그라운드에서 리포트가 생성되면 Toast 알림이 뜬다

![리포트 생성 화면](../../.playwright-mcp/dev-async-report-1.png)

보면 오른쪽 위에 '리포트 생성 중...' 알림이 뜨고
5초마다 폴링해서 완료되면 자동으로 화면이 업데이트돼"
</action>

<template-output>result_section</template-output>
</step>

<step n="8" goal="배운 점 / 느낀 점 섹션 (반말 + 회고)">
<action>이번 개발에서 배운 점과 느낀 점 작성</action>

<critical>
톤: 반말 구어체 (가장 솔직하게)
- 개인적인 감상
- 기술적 인사이트
- 다음에 더 잘할 수 있는 부분
- 아쉬운 점도 솔직하게
</critical>

<action>내용 구성:
1. 기술적으로 배운 점
   - 새로 알게 된 기술/개념
   - 삽질하면서 깨달은 것

2. 다음에 개선할 점
   - 더 나은 방법
   - 아쉬운 부분

3. 개인적 소감
   - 재밌었던 점
   - 힘들었던 점
   - 뿌듯한 점
</action>

<action>작성 예시 (참고용):
"## 배운 점

Celery는 써봤는데 폴링 방식은 처음이었거든
WebSocket이 더 좋을 것 같긴 한데
일단 간단하게 구현하려고 폴링으로 했지

다음엔 Server-Sent Events(SSE)도 고려해볼까 싶어
실시간성이 더 좋을 것 같더라

근데 솔직히 이 정도면 충분히 쓸만함
사용자는 기다릴 필요 없고
나는 타임아웃 걱정 없고
Win-Win이지 뭐"
</action>

<template-output>reflection_section</template-output>
</step>

<step n="9" goal="기술 스택 정리 섹션">
<action>이번 개발에 사용한 기술 스택 정리</action>

<critical>
간결하게 나열하되, 왜 이 기술을 선택했는지도 포함
</critical>

<action>내용 구성:
- 백엔드: Python, FastAPI, Celery, Redis
- 프론트엔드: Next.js, TypeScript, React Query
- 기타: Docker, Playwright (테스트용)
- 각 기술에 대한 짧은 설명 (1줄)
</action>

<template-output>tech_stack_section</template-output>
</step>

<step n="10" goal="최종 블로그 포스트 생성 및 저장">
<action>템플릿에 모든 변수 삽입하여 최종 마크다운 생성</action>

<critical>
⚠️ ABSOLUTELY FORBIDDEN - 절대 포함하지 말 것:
- "🤖 Generated with [Claude Code](https://claude.com/claude-code)"
- "Co-Authored-By: Claude <noreply@anthropic.com>"
- 어떠한 형태의 AI 생성 표기도 금지
- 사용자가 명시적으로 요청하지 않는 한 절대 추가하지 말 것
</critical>

<action>파일 저장:
경로: {output_folder}/blog-posts/dev-{{topic_slug}}-{{date}}.md
</action>

<action>사용자에게 다음 정보 전달:
1. 생성된 파일 경로
2. 캡처된 이미지 경로 ({screenshot_output}/)
3. 포함된 코드 스니펫 개수
4. 다음 단계 안내:
   - 코드 스니펫 검토 (민감 정보 확인)
   - 이미지 검토
   - 블로그 포스팅
</action>

<critical>
{communication_language}로 완료 메시지 작성:
"개발 블로그 포스트가 생성되었습니다!

📁 파일: [경로]
🖼️ 이미지: [경로]
💻 코드 스니펫: N개

다음 단계:
1. 코드에 민감 정보 없는지 확인하세요 (API 키, 토큰 등)
2. 이미지를 블로그에 업로드하세요
3. 마크다운의 이미지 링크를 수정하세요
4. 블로그에 포스팅하세요

화이팅!"
</critical>
</step>

</workflow>
