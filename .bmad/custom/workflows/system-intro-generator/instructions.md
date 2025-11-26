# 아작 시스템 소개 - Workflow Instructions

<critical>The workflow execution engine is governed by: {project-root}/.bmad/core/tasks/workflow.xml</critical>
<critical>You MUST have already loaded and processed: {project-root}/.bmad/custom/workflows/system-intro-generator/workflow.yaml</critical>
<critical>Communicate in {communication_language} throughout the workflow execution</critical>
<critical>⚠️ ABSOLUTELY NO TIME ESTIMATES - NEVER mention hours, days, weeks, months, or ANY time-based predictions</critical>

<workflow>

<step n="1" goal="워크플로우 시작 확인">
<action>사용자에게 시스템 소개 블로그 포스트 생성을 시작한다고 알림</action>
<action>현재 캡처 가능한 화면과 향후 추가될 화면을 안내</action>
</step>

<step n="2" goal="Playwright로 Azak 시스템 화면 캡처">
<critical>
시스템 소개용 캡처 전략:
- 종목 분석 글과 달리 "시스템 전체"를 보여줘야 함
- 핵심 가치: 멀티 AI 모델, 자동화, 데이터 파이프라인
- 확장 가능성: 향후 기능 추가를 고려한 구조
</critical>

<action>1. 대시보드 전체 캡처
- URL: {{azak_base_url}}{{azak_dashboard_path}}?token={{azak_token}}
- 파일명: system-dashboard.png
- 저장 경로: {{screenshot_output}}/system-dashboard.png
- 전체 페이지 캡처
- 목적: 시스템 전체 구조와 느낌 전달
</action>

<action>페이지 로드 후 3초 대기</action>

<action>2. 종목 목록 화면 캡처
- URL: {{azak_base_url}}{{azak_stocks_list_path}}?token={{azak_token}}
- 파일명: system-stocks-list.png
- 저장 경로: {{screenshot_output}}/system-stocks-list.png
- 전체 페이지 캡처
- 목적: 여러 종목이 관리되고 있음을 시각화
</action>

<action>페이지 로드 후 3초 대기</action>

<action>3. 종목 상세 페이지 캡처 (예시: 삼성전자)
- URL: {{azak_base_url}}/stocks/005930?token={{azak_token}}
- 파일명: system-stock-detail.png
- 저장 경로: {{screenshot_output}}/system-stock-detail.png
- 전체 페이지 캡처
- 목적: 자동 생성된 리포트의 완성도 보여주기
</action>

<action>4. Model A/B 비교 영역 캡처 (핵심!)
- 동일 페이지 (종목 상세)
- 파일명: system-models-comparison.png
- 저장 경로: {{screenshot_output}}/system-models-comparison.png
- 요소 영역만 캡처
- 목적: 시스템의 핵심 차별화 포인트 강조
</action>

<action>5. 최근 시장 동향 & AI 분석 영역 캡처
- 동일 페이지 (종목 상세)
- 파일명: system-market-analysis.png
- 저장 경로: {{screenshot_output}}/system-market-analysis.png
- 요소 영역만 캡처
- 목적: AI가 뉴스를 자동으로 분석하는 기능 보여주기
</action>

<action>6. AI 모델 관리 화면 캡처 (향후 추가)
- 파일명: system-model-management.png
- 저장 경로: {{screenshot_output}}/system-model-management.png
- 현재: 프리뷰 링크 없음 → 스킵
- TODO: 프리뷰 링크 생성되면 활성화
- 목적: 모델 등록/수정/삭제 기능 보여주기
</action>

<action>7. 모델 평가 UI 캡처 (향후 추가)
- 파일명: system-model-evaluation.png
- 저장 경로: {{screenshot_output}}/system-model-evaluation.png
- 현재: 기능 미구현 → 스킵
- TODO: 기능 구현되면 활성화
- 목적: 모델 성능 비교, 백테스트 결과 등
</action>

<critical>
⚠️ IMPORTANT: Playwright screenshot filename parameter 사용 시 주의!
- filename 파라미터에는 파일명만 지정 (예: "system-dashboard.png")
- 경로를 포함하지 말 것 (예: ".playwright-mcp/system-dashboard.png" ❌)
- Playwright가 자동으로 {{screenshot_output}} 디렉토리에 저장함
- 중복 경로 생성 방지를 위해 반드시 파일명만 전달
</critical>

<critical>
블로그 본문에 이미지 삽입 시 마크다운 형식:

⚠️ IMPORTANT: 이미지 경로는 반드시 상대 경로로 작성!
- 블로그 포스트 위치: {output_folder}/blog-posts/아작-시스템-소개-{{date}}.md
- 이미지 위치: {screenshot_output}/system-*.png
- 올바른 상대 경로: ../../.playwright-mcp/system-*.png

시스템 개요 섹션:
- ![아작 대시보드](../../.playwright-mcp/system-dashboard.png)

데이터 파이프라인 섹션:
- ![종목 관리 화면](../../.playwright-mcp/system-stocks-list.png)

AI 모델 구조 섹션:
- ![종목 상세 분석](../../.playwright-mcp/system-stock-detail.png)
- ![Model A/B 비교 기능](../../.playwright-mcp/system-models-comparison.png)

AI 뉴스 자동 분석 섹션:
- ![최근 시장 동향 & AI 분석](../../.playwright-mcp/system-market-analysis.png)

향후 기능 (현재 캡처 불가):
- AI 모델 관리: (프리뷰 링크 추가 예정)
- 모델 평가: (기능 개발 중)
</critical>
</step>

<step n="3" goal="블로그 제목 생성">
<action>다음 규칙으로 제목 생성:

규칙:
- 시스템의 핵심 가치를 담을 것
- 반말 구어체 사용
- 흥미 유발 요소 포함
- "멀티 AI 모델" 또는 "AI 비교" 키워드 포함

좋은 예:
- "여러 AI 모델 동시에 돌려서 투자 의견 비교하는 시스템 만들었어"
- "주식 AI 분석, 한 모델만 믿지 말고 여러 개 비교해봐"
- "AI 모델 A/B 테스트로 주식 분석하는 법"

나쁜 예:
- "아작 시스템 소개" ❌ (너무 딱딱함)
- "AI 주식 분석 시스템 개발기" ❌ (재미없음)
</action>

<action>생성된 제목을 {{blog_title}}에 저장</action>
</step>

<step n="4" goal="시스템 개요 섹션 작성 (존댓말)">
<action>왜 만들었는지, 어떤 문제를 해결하는지 작성</action>

<action>내용:
- 주식 처음 시작할 때의 막막함
- 전문가마다 의견이 다른 혼란
- "AI한테 물어보면 되지 않을까?" → 근데 AI도 모델마다 다름
- 그래서 여러 AI 모델을 동시에 돌려서 비교하는 시스템 만듦
</action>

<action>톤: 존댓말 (정보 전달)</action>

<action>이미지 삽입: 대시보드 캡처</action>
</step>

<step n="5" goal="전체 구조 설명 섹션 작성 (존댓말)">
<action>시스템이 어떻게 돌아가는지 전체 흐름 설명</action>

<action>내용:
1. 데이터 수집 (10분마다 뉴스, 5분마다 공시, 1~5분 실시간 주가)
2. 여러 AI 모델에 동시에 분석 요청
3. 각 모델이 독립적으로 리포트 생성
4. A/B 선택된 두 모델만 화면에 나란히 표시
5. 하루 3번 자동으로 업데이트
</action>

<action>톤: 존댓말</action>
</step>

<step n="6" goal="데이터 파이프라인 섹션 작성 (존댓말)">
<action>어떤 데이터를 어떻게 수집하는지 설명</action>

<action>내용:
- 실시간 주가 (한국투자증권 API)
- 뉴스 크롤링 (10분 주기)
- DART 공시 (5분 주기)
- 재무 지표 (ROE, PER, EPS, 부채비율 등)
- 투자자 수급 (외국인/기관/개인 순매수)
- 기술적 지표 (RSI, 이동평균 등)
</action>

<action>이미지 삽입: 종목 목록 캡처</action>

<action>톤: 존댓말</action>
</step>

<step n="7" goal="AI 모델 구조 섹션 작성 (존댓말 + 반말 혼합)">
<action>멀티 AI 모델 시스템의 핵심 가치 설명</action>

<action>내용:
**멀티 AI 모델 시스템 (핵심!)**

원하는 AI 모델을 자유롭게 등록할 수 있어요
- 현재 등록된 모델: Qwen3 Max, DeepSeek V3.2, Claude, GPT-4 등
- 모델 추가/수정/삭제 가능 (관리 화면은 나중에 공개 예정)

모든 모델이 같은 데이터로 분석합니다
- 공정한 비교를 위해 동일한 입력 데이터 사용
- 각 모델이 독립적으로 분석

A/B 모델 선택 → 화면에서 나란히 비교
- 오늘은 Qwen vs DeepSeek
- 내일은 Claude vs GPT-4
- 자유롭게 비교 대상 변경 가능

이미지 삽입:
- 종목 상세 분석 화면
- Model A/B 비교 캡처 (가장 중요!)
</action>

<action>톤: 존댓말 + 반말 혼합 (설명은 존댓말, 예시는 반말)</action>
</step>

<step n="8" goal="기술 스택 섹션 작성 (반말)">
<action>어떤 기술로 만들었는지 솔직하게 작성</action>

<action>내용:
솔직히 처음 만들어보는 거라 완벽하진 않아

**백엔드**
- 파이썬 + FastAPI
- PostgreSQL (데이터 저장)
- 크론잡 (자동화)

**프론트엔드**
- (실제 사용한 프레임워크 기재)

**AI API**
- OpenAI API
- Anthropic API
- Alibaba Cloud (Qwen)
- DeepSeek API

**기타**
- 한국투자증권 API (실시간 주가)
- DART API (공시)
- 뉴스 크롤러 (자체 구현)

유튜브 보면서 배웠는데 일단 돌아가긴 함ㅋㅋ
</action>

<action>톤: 반말 (솔직한 개발 후기)</action>
</step>

<step n="9" goal="향후 로드맵 섹션 작성 (존댓말)">
<action>앞으로 추가할 기능 소개</action>

<action>내용:
**향후 추가 예정 기능**

1. **AI 모델 관리 화면 공개**
   - 현재는 관리자만 접근 가능
   - 프리뷰 링크 생성 후 공개 예정
   - 모델 등록/수정/삭제 UI

2. **모델 평가 시스템**
   - 각 모델의 예측 정확도 추적
   - 백테스트 결과 시각화
   - 모델별 승률 비교

3. **사용자 커스터마이징**
   - 본인만의 A/B 세트 저장
   - 알림 설정
   - 관심 종목 등록

4. **커뮤니티 기능**
   - 모델 평가 공유
   - 투자 아이디어 토론
</action>

<action>톤: 존댓말</action>
</step>

<step n="10" goal="CTA 및 마무리 섹션 작성 (존댓말)">
<action>아작 사이트 링크 및 Buy Me a Coffee CTA 작성</action>

<action>내용:
"---

이 글이 도움이 되셨다면?

**아작 사이트 직접 써보기**: {{azak_base_url}}

커피 한 잔으로 응원해주세요
저도 주식 공부 자료 사는 데 쓰겠습니다

[Buy Me a Coffee 버튼]

**🎁 특별 혜택**: 기부해주시면 감사의 의미로 여러 AI 모델을 직접 평가해볼 수 있는 코드를 이메일로 보내드립니다"
</action>

<action>면책 조항 작성</action>

<action>내용:
"면책 조항

저도 주식을 배우는 중이라 투자 조언을 드릴 수 없습니다
이 시스템은 AI 분석 결과를 참고용으로 제공하며, 투자 판단은 본인의 책임으로 하셔야 합니다"
</action>

<action>오픈소스/GitHub 링크 (선택)</action>

<action>내용:
"기술 스택

**현재 등록된 AI 모델**
- Qwen3 Max
- DeepSeek V3.2
- Claude Sonnet
- GPT-4

모델은 언제든 추가/변경 가능합니다"
</action>
</step>

<step n="11" goal="자연스러운 글쓰기 변환">
<action>생성된 전체 초안을 검토하고 자연스럽게 변환</action>

<critical>
⚠️ 톤&매너 핵심 규칙 (CRITICAL!)

**절대 금지 사항**
- 마침표(.) 과다 사용 ❌ (AI 티남)
- 콜론(:) 과다 사용 ❌ (AI 티남)
- 불릿 포인트(-) 나열만 하는 것 ❌ (장황함, 안 읽힘)
- 음슴체 사용 ❌ (~합니다, ~됩니다 등 과도한 존댓말)
- 이모지 과다 (섹션당 0~1개)
- "여러분", "~하세요" 클리셰

**필수 사용 사항**
- 존댓말로 통일 (~요, ~예요, ~습니다)
- 구어체 종결어미 혼용: ~거든요, ~거예요, ~지, ~더라고요
- 지시어: 이거, 그거, 저거
- 접속사: 근데, 그래서, 솔직히, 일단
- 짧은 문장으로 끊기
- 솔직한 감정 표현 ("ㅋㅋ", "진짜", "솔직히")

**가독성을 위한 마크다운 활용**
- 장황한 설명은 테이블로 정리 (예: 데이터 수집 현황)
- 볼드체(**) 로 소제목 강조
- 적절한 불릿 포인트 사용 (단, 나열만 하지 말 것)
- 긴 설명은 나누고, 핵심만 간결하게

**톤&매너 균형**
- 시스템 설명: 존댓말 중심 (객관적 정보 전달)
- 개인 경험/후기: 자연스러운 구어체 (친근함)
- 예시: "유튜브 보면서 배웠는데 일단 돌아가긴 함ㅋㅋ 나중에 리팩토링 해야겠지만요"
</critical>

<action>변환 작업:
1. 전체 존댓말로 통일 (~요, ~예요, ~습니다)
2. 과도한 마침표(.), 콜론(:) 제거
3. 장황한 불릿 나열 → 테이블이나 간결한 문장으로
4. 긴 문장 → 짧은 문장으로 분리
5. 이모지 제거 (과도한 것)
6. 솔직한 리액션 적절히 추가 ("ㅋㅋ", "진짜")
7. 가독성 체크: 너무 장황하면 안 읽힘
</action>
</step>

<step n="12" goal="최종 블로그 포스트 생성 및 저장">
<action>템플릿에 모든 변수 삽입하여 최종 마크다운 생성</action>

<critical>
⚠️ ABSOLUTELY FORBIDDEN - 절대 포함하지 말 것:
- "🤖 Generated with [Claude Code](https://claude.com/claude-code)"
- "Co-Authored-By: Claude <noreply@anthropic.com>"
- 어떠한 형태의 AI 생성 표기도 금지
- 사용자가 명시적으로 요청하지 않는 한 절대 추가하지 말 것
</critical>

<action>파일 저장:
경로: {output_folder}/blog-posts/아작-시스템-소개-{{date}}.md
</action>

<action>사용자에게 다음 정보 전달:
1. 생성된 파일 경로
2. 캡처된 이미지 경로 ({screenshot_output}/)
3. 현재 캡처된 화면 (5종)
4. 향후 추가 예정 화면 (2종)
5. 다음 단계 안내:
   - 이미지를 블로그에 업로드
   - 마크다운의 이미지 링크 수정
   - 네이버 블로그에 포스팅
</action>

<critical>
{communication_language}로 완료 메시지 작성:
"시스템 소개 블로그 포스트가 생성되었습니다!

📁 파일: [경로]
🖼️ 현재 캡처된 이미지 (5종):
   - system-dashboard.png (대시보드 전체)
   - system-stocks-list.png (종목 목록)
   - system-stock-detail.png (종목 상세 분석)
   - system-models-comparison.png (Model A/B 비교 - 핵심!)
   - system-market-analysis.png (AI 뉴스 자동 분석)

⏳ 향후 추가 예정 (2종):
   - system-model-management.png (프리뷰 링크 생성 후)
   - system-model-evaluation.png (기능 개발 후)

다음 단계:
1. 이미지를 블로그에 업로드하세요
2. 마크다운의 이미지 링크를 수정하세요
3. 네이버 블로그에 포스팅하세요

화이팅!"
</critical>
</step>

</workflow>
