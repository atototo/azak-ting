# Stock Blog with SNS - Workflow Instructions

<critical>The workflow execution engine is governed by: {project-root}/.bmad/core/tasks/workflow.xml</critical>
<critical>You MUST have already loaded and processed: {project-root}/.bmad/custom/workflows/stock-blog-with-sns/workflow.yaml</critical>
<critical>Communicate in {communication_language} throughout the workflow</critical>
<critical>⚠️ 시간 기반 예측(며칠 후 오른다 등)은 절대 하지 않는다</critical>

<workflow>

<!-- STEP 1: 사용자 입력 -->

<step n="1" goal="종목 정보 입력 받기">
  <ask>종목 코드를 입력해주세요 (예: 005930):</ask>
  <action>입력값을 {{stock_code}} 에 저장</action>

  <ask>종목 이름을 입력해주세요 (예: 삼성전자):</ask>
  <action>입력값을 {{stock_name}} 에 저장</action>

  <action>종목 코드와 종목 이름이 모두 비어있지 않은지 확인</action>
</step>

<!-- STEP 2: young의 blog-post-generator 호출 -->

<step n="2" goal="기본 블로그 초안 생성 (Azak 리포트 기반)">
  <critical>
  이 단계에서는 기존 커스텀 워크플로우 blog-post-generator 를 그대로 재사용한다.
  blog-post-generator는:
  - Azak 프리뷰 페이지 접속
  - 주가/AI 리포트 데이터 추출
  - 스크린샷 캡처
  - 블로그 초안(제목/본문/CTA 등) 생성
  을 담당한다.
  </critical>

  <action>다음 입력으로 blog-post-generator 워크플로우({blog_post_generator_workflow})를 호출한다:
  - stock_code: {{stock_code}}
  - stock_name: {{stock_name}}
  </action>

  <action>
  blog-post-generator 실행 결과에서:
  - 초안 전체 마크다운을 {{blog_draft}} 에 저장
  - 제목이 있다면 {{blog_title_raw}} 에 저장 (없으면 나중에 생성)
  - 스크린샷 경로 목록을 {{screenshot_paths}} 에 저장
  </action>
</step>

<!-- STEP 2.5: 바이럴 제목 리서치 -->

<step n="2.5" goal="바이럴 될 만한 제목 트렌드 리서치">
  <critical>
    블로그 제목이 바이럴의 핵심이다.
    고정된 패턴이 아니라 실제 트렌드와 당일 이슈를 반영한 제목을 만들기 위해 리서치를 먼저 수행한다.
  </critical>

  <action>WebSearch로 다음 검색 수행:
    1. "{{stock_name}} site:blog.naver.com" - 최근 인기 블로그 제목 패턴 분석
    2. "{{stock_name}} 주가" - 당일 주요 이슈/키워드 파악
    3. "주식 블로그 제목" OR "주식 썸네일 제목" - 바이럴 제목 트렌드
  </action>

  <action>검색 결과에서 다음 정보 추출:
    - 클릭 유도하는 제목 패턴 (질문형, 숫자 강조, 대비형, 이슈 기반)
    - 당일 해당 종목의 핵심 이슈 키워드
    - 사람들이 많이 쓰는 표현/밈
  </action>

  <action>바이럴 제목 후보 3~5개 생성:
    예시 패턴:
    - 이슈 기반: "튀르키예 MOU 터졌는데 {{stock_name}} 지금 사도 될까"
    - 숫자 강조: "PER 446배인데 5% 뛴 {{stock_name}}, 뭔 일이야"
    - 질문형: "{{stock_name}} 외국인은 팔고 개인은 사는 이유?"
    - 대비형: "거래처 거래중단 공시 떴는데 주가는 급등? 이게 뭐지"
    - AI 관점: "AI 2개 돌렸는데 결론이 정반대라서 당황"
  </action>

  <action>
    리서치 결과를 {{viral_title_research}} 에 저장:
    - 발견한 트렌드 패턴
    - 당일 핵심 이슈 키워드
    - 제목 후보 3~5개
  </action>
</step>

<!-- STEP 3: Custom blog-storyteller로 블로그용으로 다듬기 -->

<step n="3" goal="스토리텔링이 살아있는 블로그 글로 다듬기">
  <critical>
    custom agent(blog-storyteller)를 자동 호출하여 블로그 초안을 자연스럽게 다듬는다.
    Step 2.5에서 리서치한 바이럴 제목 정보를 활용하여 제목을 생성한다.
  </critical>

  <action>
    <agent-call src="{project-root}/.bmad/custom/agents/blog-storyteller.md">
      <param name="blog_draft">{{blog_draft}}</param>
      <param name="writing_style">{{writing_style}}</param>
      <param name="viral_title_research">{{viral_title_research}}</param>
      <param name="stock_name">{{stock_name}}</param>
      <param name="real_time_issues">{{real_time_issues}}</param>
    </agent-call>
  </action>

  <action>
    Generate outputs:
    - {{blog_title}}
    - {{blog_body}}
  </action>

  <template-output>blog_title</template-output>
  <template-output>blog_body</template-output>
</step>

<!-- STEP 4: Custom sns-copywriter로 SNS 캡션 생성 -->

<step n="4" goal="플랫폼별 SNS 공유용 문구 생성">

  <critical>
    custom agent(sns-copywriter)를 사용하여 Twitter/Instagram/LinkedIn SNS 문구 생성
  </critical>

  <action>
    <agent-call src="{project-root}/.bmad/custom/agents/sns-copywriter.md">
      <param name="blog_body">{{blog_body}}</param>
      <param name="stock_name">{{stock_name}}</param>
      <param name="sns_platforms">{{sns_platforms}}</param>
    </agent-call>
  </action>

  <template-output>sns_twitter</template-output>
  <template-output>sns_instagram</template-output>
  <template-output>sns_linkedin</template-output>
</step>

<!-- STEP 5: 바이럴 태그 30개 생성 -->

<step n="5" goal="블로그 바이럴 태그 30개 생성">
  <critical>
    custom agent(tag-generator)를 사용하여 검색 노출과 바이럴에 최적화된 태그 30개를 생성한다.
    네이버 블로그, 티스토리 등 국내 블로그 플랫폼에 적합한 태그를 만든다.
  </critical>

  <action>
    <agent-call src="{project-root}/.bmad/custom/agents/tag-generator.md">
      <param name="blog_body">{{blog_body}}</param>
      <param name="stock_name">{{stock_name}}</param>
      <param name="stock_code">{{stock_code}}</param>
    </agent-call>
  </action>

  <action>
    tag-generator 에이전트가 다음 카테고리별로 태그를 생성:
    - 종목 관련 태그 (7개): 종목명 변형, 종목코드
    - 섹터/테마 태그 (6개): 해당 종목의 섹터
    - 투자 일반 태그 (5개): 주식투자, 주린이 등
    - AI/기술 태그 (4개): AI분석, AI투자 등
    - 시의성 태그 (3개): 현재 이슈 관련
    - 브랜드 태그 (3개): 아작, Azak, 아작리포트
    - 바이럴 태그 (2개): 검색량 높은 일반 키워드
  </action>

  <action>
    생성된 태그를 {{blog_tags}} 에 저장
    형식: 쉼표로 구분된 문자열 (정확히 30개)
  </action>

  <template-output>blog_tags</template-output>
</step>

<!-- STEP 6: 이미지 생성 프롬프트 생성 -->

<step n="6" goal="블로그 보조 이미지용 프롬프트 생성">
  <critical>
    custom agent(image-prompt-generator)를 사용하여 블로그 가독성을 높여줄 이미지 생성용 프롬프트를 만든다.
    Midjourney, DALL-E, Ideogram 등에서 사용할 수 있는 프롬프트를 생성한다.
    한글 텍스트가 포함되어야 하는 경우 명시적으로 지정한다.
  </critical>

  <action>
    <agent-call src="{project-root}/.bmad/custom/agents/image-prompt-generator.md">
      <param name="blog_body">{{blog_body}}</param>
      <param name="stock_name">{{stock_name}}</param>
      <param name="stock_code">{{stock_code}}</param>
    </agent-call>
  </action>

  <action>
    image-prompt-generator 에이전트가 다음 기준으로 3~6개 이미지 프롬프트 생성:
    - 회사/기술 설명 → 인포그래픽/다이어그램
    - 뉴스/발표 → 일러스트/뉴스 스타일
    - 리스크/경고 → 캐릭터 일러스트
    - AI 모델 비교 → VS 인포그래픽
    - 숫자 강조 (급등률, 배수) → 숫자 강조 인포그래픽
  </action>

  <action>
    각 프롬프트에 포함되어야 하는 정보:
    - 이미지 제목
    - 삽입 위치 (블로그 섹션명)
    - 스타일 유형
    - 영문 프롬프트 (한글 텍스트 포함)
    - 한글 텍스트 목록 (별도 정리)
  </action>

  <action>
    생성된 프롬프트를 {{image_prompts}} 에 저장
    형식: 마크다운 섹션 (## 🎨 이미지 생성 프롬프트)
  </action>

  <template-output>image_prompts</template-output>
</step>

<!-- STEP 7: 템플릿에 합치고 저장 -->

<step n="7" goal="최종 문서 생성 및 저장">
  <action>
  template.md에 정의된 자리표시자에
  {{blog_title}}, {{blog_body}}, {{blog_tags}},
  {{sns_twitter}}, {{sns_instagram}}, {{sns_linkedin}},
  {{image_prompts}} 값을 채워 넣어
  최종 마크다운 문서를 생성한다.
  </action>

  <action>
  생성된 문서를 {default_output_file} 경로에 저장한다.
  </action>

  <action>
  {communication_language}로 완료 요약을 표시한다:

  - 생성된 파일 위치: {default_output_file}
  - 포함된 내용:
    - 블로그 본문
    - Twitter/X, Instagram, LinkedIn용 SNS 문구
    - 블로그 태그 30개
    - 이미지 생성 프롬프트 3~6개
  - 다음 단계:
    1) 마크다운 열어서 이미지 경로와 링크 확인
    2) 이미지 생성 프롬프트로 보조 이미지 생성 (Ideogram 권장)
    3) 블로그에 게시
    4) SNS 문구 복사해서 각 플랫폼에 붙여넣기
  </action>
</step>

</workflow>
