# 블로그 포스트 생성기 - Workflow Instructions

<critical>The workflow execution engine is governed by: {project-root}/.bmad/core/tasks/workflow.xml</critical>
<critical>You MUST have already loaded and processed: {project-root}/.bmad/custom/workflows/blog-post-generator/workflow.yaml</critical>
<critical>Communicate in {communication_language} throughout the workflow execution</critical>
<critical>⚠️ ABSOLUTELY NO TIME ESTIMATES - NEVER mention hours, days, weeks, months, or ANY time-based predictions</critical>

<workflow>

<step n="1" goal="사용자 입력 수집">
<ask>어떤 종목의 블로그 포스트를 생성할까요?

종목 코드를 입력해주세요 (예: 005930):
</ask>

<action>입력받은 종목 코드를 {{stock_code}}에 저장</action>

<ask>종목 이름을 입력해주세요 (예: 삼성전자):
</ask>

<action>입력받은 종목 이름을 {{stock_name}}에 저장</action>

<action>Azak URL 생성: {{azak_base_url}}/stocks/{{stock_code}}?token={{azak_token}}</action>
<action>{{azak_stock_url}}에 URL 저장</action>
</step>

<step n="2" goal="Playwright로 Azak 페이지 접근 및 분석">
<action>Playwright MCP를 사용하여 {{azak_stock_url}} 접근</action>

<critical>
Azak 시스템 이해:
- 사용자가 "AI에게 물어보는" 것이 아님
- 이미 자동 생성된 리포트를 "확인"하는 것임
- 10분마다 시장 동향 파악, 하루 3회 자동 리포트 생성
- 여러 AI 모델이 등록되어 있으며, A/B 모델만 화면에 비교 표시
</critical>

<critical>
⚠️ 저작권 주의사항:
- "뉴스", "기사" 같은 용어 사용 금지
- 대신 "시장 분석", "시장 동향", "시장 정보" 등으로 작성
- 예시:
  * ❌ "10분마다 뉴스를 수집"
  * ✅ "10분마다 시장 동향을 파악"
  * ❌ "최신 기사 분석"
  * ✅ "최신 시장 분석"
</critical>

<action>페이지 로드 후 3초 대기 (동적 콘텐츠 로딩)</action>

<action>페이지에서 다음 정보 추출:
1. 현재 주가 정보 (종가, 등락률, 시가, 고가, 저가)
2. 주가 차트 통계 정보 (신규 추가):
   - 데이터 포인트 수 (예: 22일)
   - 최고가 (예: 244,000원)
   - 최저가 (예: 187,900원)
   - AI 리포트 생성 건수 (예: 18건)
3. 최근 시장 동향 & AI 분석 정보 (신규 추가):
   - 최근 감지된 시장 시그널 건수 (긍정/부정 분류)
   - 가장 최근 시그널의 상세 정보:
     * 긍정/부정 구분
     * 신뢰도 (%)
     * 영향도 (높음/중간/낮음)
     * 긴급도 (긴급/주의/정상)
     * 생성 시각
4. Model A 정보:
   - 모델 이름
   - 신뢰도 (중간🟡/높음🟢)
   - 종합 의견
   - 단기/중기/장기 전략
   - 리스크 요인
   - 기회 요인
   - 최종 추천
5. Model B 정보: (동일 구조)
6. 리포트 생성 시각 (예: "8시간 5분 전")
7. 시장 동향 통계 (분석 건수, 알림 건수)
</action>

<action>추출한 정보를 각각의 변수에 저장:
- {{current_price}}, {{price_change_percent}}
- {{chart_data_points}}, {{chart_max_price}}, {{chart_min_price}}, {{chart_report_count}}
- {{market_signals_positive}}, {{market_signals_negative}}, {{latest_signal_type}}, {{latest_signal_confidence}}, {{latest_signal_impact}}, {{latest_signal_urgency}}, {{latest_signal_time}}
- {{model_a_name}}, {{model_a_reliability}}, {{model_a_opinion}}, etc.
- {{model_b_name}}, {{model_b_reliability}}, {{model_b_opinion}}, etc.
- {{report_update_time}}
</action>
</step>

<step n="2.5" goal="실시간 이슈 검색 (바이럴 대응)">
<critical>
블로그 바이럴을 위해 해당 종목의 당일 이슈사항을 반드시 확인한다.
AI 리포트만으로는 포착 못하는 실시간 이슈가 있을 수 있다.
</critical>

<action>WebSearch 도구를 사용하여 다음 검색 수행:
1. "{{stock_name}} {{date}} 이슈"
2. "{{stock_name}} 오늘 주가 급등 급락"
3. "{{stock_name}} 실적 신제품 출시"
</action>

<action>검색 결과 분석:
- 당일 주가 변동의 이유 파악 (신제품 출시, 실적 발표, 서버 장애 등)
- 바이럴 가능성 높은 이슈 확인 (논란, 화제성)
- 예: 엔씨소프트 아이온2 자정 출시 → 서버 대혼란 → 주가 폭락
</action>

<action>이슈 정보를 변수에 저장:
- {{real_time_issues}}: 발견된 이슈 목록
- {{issue_impact}}: 주가/시장에 미친 영향
- {{issue_details}}: 구체적 상황 (서버 장애, 시청자 수, 대기열 등)
</action>

<critical>
⚠️ 이슈 발견 시:
- 블로그 초반부에 "출시 당일 무슨 일이?" 같은 섹션 추가
- 구체적 숫자/팩트 포함 (25만 시청자, 3만 대기열 등)
- 긍정/부정 신호 모두 균형있게 제시

⚠️ 이슈 없을 시:
- 해당 섹션 생략하고 바로 AI 리포트로 진행
</critical>
</step>

<step n="3" goal="화면 캡처 자동화">
<critical>
프리뷰 페이지 스크린샷 규칙

Playwright MCP를 사용해 아래 페이지들을 캡처한다.
각 스크린샷은 블로그 글에서 서비스 소개용 이미지로 사용한다.
</critical>

<action>1. 종목 분석 목록 캡처
- URL: {{azak_base_url}}{{azak_stocks_list_path}}?token={{azak_token}}
- 파일명: {{screenshot_output}}/{{stock_code}}-stocks-list.png
- 전체 페이지 캡처
</action>

<action>3. 특정 종목 상세 페이지 캡처
- URL: {{azak_base_url}}{{azak_stock_detail_path}}?token={{azak_token}}
- 파일명: {{screenshot_output}}/{{stock_code}}-stock-detail.png
- 전체 페이지 캡처
</action>

<action>4. Model A/B 비교 컴포넌트 영역 캡처 (핵심!)
- 동일 페이지 (종목 상세)
- 셀렉터: Model A와 Model B 리포트가 나란히 보이는 비교 영역 전체
- 파일명: {{screenshot_output}}/{{stock_code}}-models-comparison.png
- 요소 영역만 캡처 (element screenshot)
- 이유: "와 이 사이트는 이렇게 바로 비교가 되네" 임팩트 전달
</action>

<action>5. 주가 차트 섹션 캡처 (AI 리포트 포인트 포함)
- 동일 페이지 (종목 상세)
- 셀렉터: 주가 차트와 AI 리포트 생성 포인트가 표시된 영역
- 파일명: {{screenshot_output}}/{{stock_code}}-chart-section.png
- 요소 영역만 캡처 (element screenshot)
- 포함 정보: 데이터 포인트 수, 최고가, 최저가, AI 리포트 건수
- 이유: AI가 지속적으로 모니터링하는 모습 시각화
</action>

<action>6. 최근 시장 동향 & AI 분석 섹션 캡처
- 동일 페이지 (종목 상세)
- 셀렉터: 최근 시장 동향 카드들이 나열된 영역
- 파일명: {{screenshot_output}}/{{stock_code}}-market-trends.png
- 요소 영역만 캡처 (element screenshot)
- 포함 정보: 시장 시그널 카드 (긍정/부정, 신뢰도, 영향도, 긴급도)
- 이유: 실시간 시장 모니터링 시스템의 가치 전달
</action>

<action>캡처된 이미지 경로를 변수에 저장:
- {{screenshot_stocks_list}}
- {{screenshot_stock_detail}}
- {{screenshot_models_comparison}}
- {{screenshot_chart_section}}
- {{screenshot_market_trends}}
</action>

<critical>
블로그 본문에 이미지 삽입 시 마크다운 형식:

⚠️ IMPORTANT: 이미지와 블로그 포스트는 같은 폴더에 저장!
- 블로그 포스트 위치: {output_folder}/blog-posts/{{date}}/{{stock_code}}-{{stock_name}}.md
- 이미지 위치: {output_folder}/blog-posts/{{date}}/{{stock_code}}-*.png
- 올바른 상대 경로: ./{{stock_code}}-*.png (같은 폴더이므로 ./ 사용)

주가 정보 섹션 직후 (실시간 이슈 섹션 전):
- ![주가 차트 with AI 리포트](./{{stock_code}}-chart-section.png)
- 섹션 제목: "📈 주가 차트로 보는 한 달"
- 내용: 데이터 포인트 수, 최고가, 최저가, AI 리포트 생성 건수

실시간 이슈 섹션 직후 (AI 리포트 확인 섹션 전):
- ![최근 시장 동향 분석](./{{stock_code}}-market-trends.png)
- 섹션 제목: "💡 최근 시장 동향도 심상치 않아요" (또는 상황에 맞게 변형)
- 내용: 최근 감지된 시장 시그널 요약 (긍정/부정, 신뢰도, 영향도, 긴급도)

AI 리포트 확인 섹션 (Model A/B 소개 직후):
- ![종목 목록 화면](./{{stock_code}}-stocks-list.png)
- ![종목 상세 분석 화면](./{{stock_code}}-stock-detail.png)

Model B 분석 직후:
- ![Model A/B 비교 분석](./{{stock_code}}-models-comparison.png) ← 핵심 차별화 포인트!

장황한 전체 화면보다 필요한 요소만 캡처해서 가독성을 높인다.
Model A/B 나란히 비교되는 이미지가 서비스의 핵심 가치를 보여준다.
차트와 시장 동향 섹션은 AI의 지속적 모니터링 가치를 시각적으로 전달한다.
</critical>
</step>

<step n="4" goal="블로그 제목 생성 (자연스럽게)">
<action>다음 규칙으로 제목 생성:

규칙:
- AI 티 나는 딱딱한 제목 금지
- 마침표(.) 금지
- "분석 리포트" 같은 격식 금지
- 반말 구어체 사용
- 흥미 유발 요소 포함

좋은 예:
- "{{stock_name}} AI 분석 돌렸더니 한 놈은 사라고 한 놈은 기다리래"
- "{{stock_name}} AI 2개 돌렸는데 결론이 정반대라 당황"
- "{{stock_name}} 살까? AI는 반반..."

나쁜 예:
- "{{stock_name}} AI 투자 분석 리포트" ❌
- "{{stock_name}} 종합 분석 결과" ❌
</action>

<action>생성된 제목을 {{blog_title}}에 저장</action>

<template-output>blog_title</template-output>
</step>

<step n="5" goal="주가 정보 섹션 작성 (존댓말)">
<action>현재 주가 정보를 명확하게 작성</action>

<action>톤: 존댓말 (정보 전달)</action>

<action>내용:
- 종가, 등락률
- 시가, 고가, 저가
- 간단한 설명 (1~2문장)
</action>

<template-output>price_section</template-output>
</step>

<step n="6" goal="차트 & 시장 동향 & 리포트 확인 섹션 작성 (존댓말)">
<action>주가 차트 통계 섹션 작성 (신규 추가)</action>

<action>섹션 제목: "📈 주가 차트로 보는 한 달"</action>

<action>내용 구성:
1. 아작 사이트의 주가 차트 확인했다는 설명
2. AI 모델들이 매일 리포트 생성한 흔적이 차트에 표시됨
3. 주요 통계 정리:
   - 데이터 포인트: N일
   - 최고가: XXX원
   - 최저가: XXX원 (오늘 또는 특정 날짜)
   - AI 리포트: N건 생성
4. 캡처 이미지 삽입: ![주가 차트 with AI 리포트](../../.playwright-mcp/{{stock_code}}-chart-section.png)
</action>

<action>톤: 존댓말, 간결하게</action>

<template-output>chart_section</template-output>

<action>시장 동향 분석 섹션 작성 (신규 추가)</action>

<action>섹션 제목: "💡 최근 시장 동향도 심상치 않아요" (또는 상황에 맞게 변형)</action>

<action>내용 구성:
1. 아작이 자동으로 수집한 시장 동향 확인
2. 최근 감지된 시장 시그널 요약 (긍정/부정 건수)
3. 가장 최근 시그널 상세 내용:
   - 긍정/부정 신호
   - 신뢰도: N%
   - 영향도: 높음/중간/낮음
   - 긴급도: 🔴 긴급 / 🟡 주의 / 🟢 정상
4. 캡처 이미지 삽입: ![최근 시장 동향 분석](../../.playwright-mcp/{{stock_code}}-market-trends.png)
</action>

<action>톤: 존댓말과 반말 혼용 (정보는 존댓말, 리액션은 반말)</action>

<template-output>market_trends_section</template-output>

<action>Azak AI 리포트 확인 섹션 작성</action>

<critical>
잘못된 표현 금지:
- "AI에게 물어봤습니다" ❌
- "분석을 요청했습니다" ❌

올바른 표현:
- "리포트를 확인했습니다" ✅
- "자동 생성된 분석 결과" ✅
- "사이트에서 리포트를 열어봤습니다" ✅
</critical>

<action>내용 구성:
1. 아작 사이트에서 리포트 확인했다는 설명
   - ⚠️ "10분마다 시장 동향을 파악" (뉴스 수집 X)
   - ⚠️ "하루 3번 자동으로 리포트 생성" (기사 분석 X)
2. 리포트 업데이트 시각 표시
3. 현재 A/B 테스트 설정 명시
4. Model A 분석 요약 (신뢰도, 추천, 핵심 근거)
5. Model B 분석 요약 (동일 구조)
6. 캡처 이미지 삽입
</action>

<action>톤: 존댓말</action>

<template-output>report_section</template-output>
</step>

<step n="7" goal="개인 생각 섹션 작성 (반말 → 존댓말 전환)">
<action>두 모델의 차이를 주린이 관점에서 솔직하면서도 세련되게 작성</action>

<critical>
톤 변경: 정보 섹션(존댓말) → 개인 생각(반말/존댓말 혼용)
⚠️ 부정적 표현 금지: "짜증나다", "답답하다", "화나다" 등
⚠️ 정형화된 표현 피하기: 기존 작성 글들을 참고하되, 똑같은 표현/구조 반복 금지
</critical>

<action>내용 구성 원칙 (예시를 그대로 따라하지 말고 원칙만 적용):
1. 두 모델의 차이점에 대한 개인적 반응 (다양한 방식으로 표현)
   - 호기심, 흥미, 의외성, 고민 등 다양한 감정 활용
   - 매번 다른 시작 문구 사용
   - 긍정적 톤 유지

2. 나름의 이해/해석 (자연스럽게 풀어쓰기)
   - Model A와 Model B가 어떤 관점 차이를 보이는지
   - 왜 그런 차이가 나왔을지 추론
   - 획일적인 구조("제가 이해한 건...") 피하고 자연스럽게

3. 개인적 판단과 고민 (종목/상황에 맞게)
   - 본인의 투자 스타일(장기/단기/가치/성장)과 연결
   - 실제 투자 결정의 고민 표현
   - 정직하고 솔직하게, 하지만 세련되게

4. 섹션 제목 다양화
   - "뭐가 맞는거야" 외에도 다양한 제목 사용
   - 예: "내가 본 포인트는", "이게 재밌는 게", "고민되는 부분", "내 판단은", "AI 분석 보고 드는 생각" 등
   - 종목 상황에 맞는 자연스러운 제목 선택
</action>

<action>작성 규칙:
- 마침표 적게 사용
- 이모지 적절히 사용 (😅, 🤔 등) - 하지만 매번 같은 위치/맥락 X
- 짧은 문장
- 솔직하지만 긍정적인 감정 표현
- 부정적 단어(짜증, 답답, 화) 금지
- 공개 블로그에 적합한 세련된 톤 유지
- **기존 작성 글과 구조/표현이 겹치지 않도록 의식적으로 변화 추구**
</action>

<critical>
⚠️ 반복 금지 체크리스트:
- "솔직히 이게 제일 흥미로운 부분이에요" → 매번 다른 표현 사용
- "제가 이해한 건 이거예요:" → 다양한 전개 방식
- "저는 장기로 갈 생각이라" → 상황에 맞게 변형
- 섹션 제목을 매번 "뭐가 맞는거야"로 고정하지 말 것
- 전체 흐름이 이전 글과 똑같이 느껴지지 않도록 주의
</critical>

<template-output>personal_thought</template-output>
</step>

<step n="8" goal="CTA 및 마무리 섹션 작성 (진솔한 톤)">
<action>아작 사이트 링크 및 Buy Me a Coffee CTA 작성 (필수)</action>

<critical>
CTA 톤: 거창하지 않고 진솔하게
- 스타트업 아님, 사이드 프로젝트임을 명시
- 실험용 프로젝트, 같이 배우는 느낌
- 부담 없는 후원 요청
⚠️ 정형화된 표현 피하기: 매번 똑같은 문구 X, 톤은 유지하되 표현은 다양하게
</critical>

<action>핵심 메시지 (반드시 포함, 하지만 표현은 다양하게):
1. 아작 사이트 소개
   - 아작(AZAK)은 개발 중
   - 외부 접속 시 로그인 화면만 보임

2. 후원 혜택
   - 후원자에게 직접 체험 가능한 로그인 계정 제공
   - 이메일로 전달

3. 후원금 사용처
   - 서버비와 데이터 구매비
   - 조용히 잘 쓰겠다는 진솔한 표현

4. Buy Me a Coffee 링크
   - https://buymeacoffee.com/atototo
</action>

<action>작성 가이드 (예시를 그대로 따라하지 말고 원칙만 적용):
- 시작 문구 다양화: "이 글이 도움이 되셨다면?", "도움이 되셨나요?", "유익하셨다면" 등
- 아작 소개 방식 변화: "개발 중이라", "아직 만들고 있어서", "준비 중이라서" 등
- 후원 요청 톤 변화: "커피 한 잔으로", "작게라도 후원해주신다면", "조금이라도 도움 주신다면" 등
- 이모지 위치/조합 다양화
- 문장 순서/구조 바꾸기

⚠️ 하지만 핵심 메시지 4가지는 반드시 모두 포함할 것
</action>

<action>템플릿 예시 (참고용 - 매번 다르게 작성):
"---

[시작 문구 다양화]

**아작 사이트 직접 써보기**: {{azak_base_url}}

아작(AZAK)은 [개발 중 표현 다양화]
외부에서는 로그인 화면만 보입니다.

### ☕ [후원 섹션 제목 다양화]

후원해주신 분들께는
직접 체험 가능한 로그인 계정을
감사의 의미로 이메일로 보내드릴게요 ☕🙏

후원해주신 커피는 서버비랑 데이터 구매비로만 [진솔한 표현] 🙏

👉 **[커피 한 잔으로 실험실 후원하기](https://buymeacoffee.com/atototo)**"
</action>

<critical>
⚠️ 반복 금지 체크리스트:
- "이 글이 도움이 되셨다면?" → 다양한 시작 문구
- "커피 한 잔으로 실험실 후원하기" → 제목 변형 가능
- "조용히 잘 쓰겠습니다" → "소중하게 쓰겠습니다", "알뜰하게 쓸게요" 등
- 전체 구조는 비슷해도 OK, 하지만 문구는 매번 달라야 함
</critical>

</action>

<action>면책 조항 작성 (필수)</action>

<action>내용:
"면책 조항

저도 주식을 배우는 중이라 투자 조언을 드릴 수 없습니다
이 글은 AI 분석 결과를 공유하는 것이며, 투자 판단은 본인의 책임으로 하셔야 합니다"
</action>

<action>모델 투명성 작성 (필수)</action>

<action>내용:
"사용한 AI 모델

**현재 A/B 설정**: {{model_a_name}} vs {{model_b_name}}

시스템에는 여러 AI 모델이 등록되어 있으며 비교 대상은 변경 가능합니다
모델 정보를 투명하게 공개합니다"
</action>

<template-output>cta_and_footer</template-output>
</step>

<step n="9" goal="자연스러운 글쓰기 변환 (전체 검토)">
<action>생성된 전체 초안을 검토하고 자연스럽게 변환</action>

<critical>
자연스러운 글쓰기 규칙 적용:

피해야 할 것:
- 마침표(.) 과다 사용
- 불릿 포인트(-) 나열식
- 이모지 과다 (섹션당 0~1개)
- "여러분", "~하세요" 클리셰
- 완벽한 띄어쓰기

사용해야 할 것:
- 구어체 종결어미: ~거든, ~거야, ~지, ~더라
- 지시어: 이거, 그거, 저거
- 접속사: 근데, 그래서, 솔직히, 일단
- 짧은 문장
- 솔직한 감정
- 자연스러운 띄어쓰기 오류 (적당히)
</critical>

<action>변환 작업:
1. 격식체 → 반말 (감정 섹션)
2. 긴 문장 → 짧은 문장 2개로 분리
3. 이모지 제거 (과도한 것)
4. 불릿 → 자연스러운 문장으로
5. 솔직한 리액션 추가 ("이거 진짜...", "ㅋㅋ")
</action>

<template-output>natural_blog_post</template-output>
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
경로: {output_folder}/blog-posts/{{stock_name}}-{{date}}.md
</action>

<action>사용자에게 다음 정보 전달:
1. 생성된 파일 경로
2. 캡처된 이미지 경로 ({screenshot_output}/)
3. 다음 단계 안내:
   - 이미지를 블로그에 업로드
   - 마크다운의 이미지 링크 수정
   - 네이버 블로그에 포스팅
</action>

<critical>
{communication_language}로 완료 메시지 작성:
"블로그 포스트가 생성되었습니다!

📁 파일: [경로]
🖼️ 이미지: [경로]

다음 단계:
1. 이미지를 블로그에 업로드하세요
2. 마크다운의 이미지 링크를 수정하세요
3. 네이버 블로그에 포스팅하세요

화이팅!"
</critical>
</step>

</workflow>
