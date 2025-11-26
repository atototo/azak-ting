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

<!-- STEP 3: Custom blog-storyteller로 블로그용으로 다듬기 -->

<step n="3" goal="스토리텔링이 살아있는 블로그 글로 다듬기">
  <critical>
    custom agent(blog-storyteller)를 자동 호출하여 블로그 초안을 자연스럽게 다듬는다.
  </critical>

  <action>
    <agent-call src="{project-root}/.bmad/custom/agents/blog-storyteller.md">
      <param name="blog_draft">{{blog_draft}}</param>
      <param name="writing_style">{{writing_style}}</param>
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

<!-- STEP 5: 템플릿에 합치고 저장 -->

<step n="5" goal="최종 문서 생성 및 저장">
  <action>
  template.md에 정의된 자리표시자에
  {{blog_title}}, {{blog_body}},
  {{sns_twitter}}, {{sns_instagram}}, {{sns_linkedin}} 값을 채워 넣어
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
  - 다음 단계:
    1) 마크다운 열어서 이미지 경로와 링크 확인
    2) 블로그에 게시
    3) SNS 문구 복사해서 각 플랫폼에 붙여넣기
  </action>
</step>

</workflow>
