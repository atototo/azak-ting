# Issue to Docs - 이슈 추적 및 문서화 워크플로우

<critical>The workflow execution engine is governed by: {project-root}/.bmad/core/tasks/workflow.xml</critical>
<critical>You MUST have already loaded and processed: {project-root}/.bmad/custom/workflows/issue-to-docs/workflow.yaml</critical>
<critical>Communicate in {communication_language} throughout the workflow</critical>
<critical>This is a Meta-Workflow that orchestrates multiple specialized agents for optimal results</critical>

<workflow>

<step n="0" goal="현재 상황 파악 및 워크플로우 진입점 결정">

<action>사용자에게 현재 상황을 물어보고 적절한 진입점을 결정합니다:</action>

<ask>현재 어느 단계에 있나요?

1. **문제 발견 직후** - 아직 수정 안 함, 이슈부터 만들고 싶음
2. **수정 작업 중** - 일부 수정했지만 체계적으로 정리 필요
3. **수정 완료** - 테스트만 남음
4. **모두 완료** - PR/문서만 만들면 됨

번호를 선택해주세요:
</ask>

<action>사용자 응답에 따라 {{current_stage}} 변수 설정:
- 1 → "discovered"
- 2 → "fixing"
- 3 → "testing"
- 4 → "done"
</action>

<action>현재 Git 상태 확인:</action>
<action>- 현재 브랜치 확인 (`git branch --show-current`)</action>
<action>- 변경된 파일 확인 (`git status`)</action>
<action>- 이미 작업 중인 브랜치가 있는지 확인</action>

<action>{{current_stage}} 값에 따라 다음 단계로 이동:
- "discovered" → Step 1부터 시작
- "fixing" → Step 4 확인 후 Step 5부터
- "testing" → Step 6부터
- "done" → Step 7부터
</action>

</step>

<step n="1" goal="문제 체계적 분석 (Analyst Agent)" if="current_stage == 'discovered'">

<action>사용자에게 발견한 문제나 구현할 기능에 대해 질문합니다:</action>

<ask>어떤 문제를 발견했거나 어떤 기능을 추가/수정하려고 하나요?

간단히 설명해주세요:
- 무엇이 문제인가요? (또는 어떤 기능인가요?)
- 어떤 상황에서 발생하나요?
- 예상되는 동작은 무엇인가요?
</ask>

<action>Analyst 에이전트를 활용하여 문제를 체계적으로 분석합니다.

**분석 관점**:
1. **근본 원인 (Root Cause)**
   - 왜 이 문제가 발생했는가?
   - 어떤 조건에서 재현되는가?
   - 관련된 시스템/컴포넌트는?

2. **영향도 평가 (Impact Assessment)**
   - 사용자에게 미치는 영향은?
   - 시스템에 미치는 영향은?
   - 데이터 무결성 영향은?
   - 긴급도는? (Critical/High/Medium/Low)

3. **해결 방안 옵션**
   - 가능한 해결 방법들
   - 각 방법의 장단점
   - 권장 접근법

4. **리스크 분석**
   - 수정 시 발생 가능한 부작용
   - 영향받는 다른 기능들
   - 회귀 테스트 필요 범위
</action>

<action>분석 결과를 기반으로 다음 정보를 수집합니다:
- {{issue_title}}: 이슈 제목 (명확하고 구체적으로)
- {{change_type}}: 변경 타입 (bug-fix, feature, refactor, enhancement, docs)
- {{change_title}}: 문서 파일명용 제목 (kebab-case)
</action>

<template-output>problem_analysis</template-output>

</step>

<step n="2" goal="AS-IS 상태 캡처 및 문서화 (Tech Writer + Playwright)" if="current_stage == 'discovered'">

<action>Tech Writer 에이전트와 함께 현재 상태를 문서화합니다.</action>

<critical>스크린샷 수집 전략 (혼합형):</critical>

<action>1. **Playwright MCP 자동 캡처 시도**</action>

<ask>스크린샷이 필요한 화면이 있나요? (웹 애플리케이션)

있다면 어떤 페이지인가요?
- Azak 대시보드
- Azak 종목 상세 페이지
- 다른 URL
- 없음 (백엔드 이슈 등)
</ask>

<action if="user wants screenshot">Playwright MCP를 사용하여 스크린샷 자동 캡처 시도:

**Azak 대시보드인 경우**:
- URL: {azak_base_url}{azak_dashboard_path}
- 토큰: {azak_token}

**Azak 종목 상세인 경우**:
- URL: {azak_base_url}{azak_stock_detail_path}
- 종목 코드 입력 받아 {{stock_code}} 설정

**기타 URL인 경우**:
- 사용자에게 URL 입력받기
- 로그인 필요 여부 확인
- 필요시 로그인 정보 요청

스크린샷을 {screenshots_folder}/{date}-as-is-{{description}}.png에 저장
</action>

<action>2. **자동 캡처 실패 시 수동 요청**</action>

<ask if="playwright failed">자동 캡처에 실패했습니다.

스크린샷을 직접 찍어서 이 대화에 첨부해주시겠어요?

다음 화면이 필요합니다:
- 문제가 발생하는 화면
- 에러 메시지가 보이는 화면
- 비교를 위한 정상 화면 (있다면)
</ask>

<action if="user provides screenshot">사용자가 첨부한 이미지를 분석하고:
- 이미지 내용 설명 생성
- {screenshots_folder}/{date}-as-is-{{description}}.png로 저장
- 문서에 삽입할 마크다운 링크 생성: ![AS-IS 상태](../screenshots/{date}-as-is-{{description}}.png)
</action>

<action>3. **에러 로그 수집**</action>

<ask>에러 로그나 콘솔 출력이 있나요?

있다면 관련 로그를 복사해서 붙여넣어 주세요:
- 백엔드 로그 (pm2 logs, 서버 로그)
- 프론트엔드 콘솔 에러
- 네트워크 에러
- 데이터베이스 에러
</ask>

<action if="user provides logs">로그를 분석하고 정리:
- 핵심 에러 메시지 추출
- 스택 트레이스 정리
- 관련 컨텍스트 보존
- {{error_logs}} 변수에 저장
</action>

<action>4. **AS-IS 상태 문서화**</action>

<action>Tech Writer 에이전트를 활용하여 현재 상태를 명확하게 문서화:

**포함 내용**:
- 현재 동작/문제 설명
- 재현 단계 (Step by step)
- 예상 동작 vs 실제 동작
- 스크린샷 (있는 경우)
- 에러 로그 (있는 경우)
- 영향받는 사용자/시스템
- 발생 빈도 및 조건

**스타일**:
- 명확하고 구체적으로
- 기술적 정확성 유지
- 재현 가능하도록 상세히
</action>

<template-output>as_is_documentation</template-output>

</step>

<step n="3" goal="GitHub 이슈 생성 (PM Agent)" if="current_stage == 'discovered' or current_stage == 'fixing'">

<action>기존 이슈가 있는지 확인:</action>

<ask>이미 생성된 GitHub 이슈가 있나요?

있다면 이슈 번호를 알려주세요 (예: #42)
없다면 "없음"이라고 입력해주세요:
</ask>

<action if="no existing issue">PM 에이전트를 활용하여 체계적인 GitHub 이슈를 생성합니다.</action>

<action>GitHub CLI를 사용하여 이슈 생성:

**이슈 템플릿**:
```markdown
## 문제 설명
{{problem_analysis}}

## 현재 상태 (AS-IS)
{{as_is_documentation}}

## 재현 방법
[단계별 재현 과정]

## 예상 동작
[올바른 동작 설명]

## 스크린샷
[스크린샷 이미지들]

## 에러 로그
\`\`\`
{{error_logs}}
\`\`\`

## 영향도
- **심각도**: {{severity}}
- **영향 범위**: {{impact_scope}}

## 제안 해결 방법
{{suggested_solutions}}
```
</action>

<action>이슈 생성 명령 실행:
```bash
gh issue create \
  --title "{{issue_title}}" \
  --body "$(cat <<'EOF'
[위 템플릿 내용]
EOF
)" \
  --label "{{change_type}}"
```
</action>

<action>생성된 이슈 번호를 {{issue_number}} 변수에 저장</action>

<action if="existing issue">사용자가 제공한 이슈 번호를 {{issue_number}} 변수에 저장</action>

<action>이슈 URL 출력: `https://github.com/[repo]/issues/{{issue_number}}`</action>

<template-output>github_issue</template-output>

</step>

<step n="4" goal="브랜치 생성 및 체크아웃 (Dev Agent)" if="current_stage == 'discovered' or current_stage == 'fixing'">

<action>현재 브랜치 상태 확인:</action>

<ask>이미 작업용 브랜치를 만들었나요?

만들었다면 브랜치 이름을 알려주세요
아니면 "없음"이라고 입력해주세요:
</ask>

<action if="no branch">Dev 에이전트를 활용하여 Git 브랜치를 생성합니다.</action>

<action if="no branch">브랜치 이름 생성:
- 패턴: {branch_prefix}{{issue_number}}-{{change_title}}
- 예: `feature/issue-42-fix-login-redirect`
</action>

<action if="no branch">브랜치 생성 및 체크아웃:
```bash
# 최신 상태로 업데이트
git checkout {base_branch}
git pull origin {base_branch}

# 브랜치 생성 및 전환
git checkout -b {branch_prefix}{{issue_number}}-{{change_title}}
```
</action>

<action if="branch exists">기존 브랜치로 체크아웃:
```bash
git checkout {{existing_branch_name}}
git status
```
</action>

<action>현재 작업 디렉토리 상태 확인 및 출력</action>

<template-output>branch_setup</template-output>

</step>

<step n="5" goal="수정 작업 수행 (Dev Agent)">

<action>수정 작업 상태 확인:</action>

<ask>코드 수정을 이미 완료했나요?

- **완료**: 수정 작업 끝남, 검토만 필요
- **진행 중**: 지금 수정하려고 함
- **아직**: 아직 시작 안 함

선택해주세요:
</ask>

<action if="not completed">Dev 에이전트를 활용하여 수정 작업을 수행합니다.

**수정 작업 가이드**:
1. **문제 분석 결과 기반**으로 수정
   - {{problem_analysis}}의 권장 해결 방법 참고

2. **코딩 표준 준수**
   - 프로젝트 코딩 스타일 따르기
   - 린트 규칙 준수
   - 타입 안정성 유지

3. **최소 변경 원칙**
   - 필요한 부분만 수정
   - 불필요한 리팩토링 지양
   - 관련 없는 코드 변경 최소화

4. **변경 사항 기록**
   - 어떤 파일을 수정했는지
   - 왜 그렇게 수정했는지
   - 주요 변경 로직 설명
</action>

<action>수정 완료 후 변경 사항 확인:
```bash
git status
git diff
```
</action>

<ask>수정한 내용을 간단히 설명해주세요:

- 어떤 파일들을 수정했나요?
- 주요 변경 내용은?
- 왜 그렇게 수정했나요?
</ask>

<action>변경 내용을 {{changes_made}} 변수에 저장</action>

<action>수정된 코드의 주요 부분을 {{code_snippets}} 변수에 저장 (문서화용)</action>

<template-output>code_changes</template-output>

</step>

<step n="6" goal="테스트 및 TO-BE 상태 캡처 (Dev Agent + Playwright)">

<action>Dev 에이전트를 활용하여 테스트를 수행합니다.</action>

<action>1. **자동 테스트 실행**</action>

<ask>프로젝트에 자동 테스트가 있나요?

있다면 테스트 명령어를 알려주세요 (예: `npm test`, `pytest`)
없다면 "없음"이라고 입력해주세요:
</ask>

<action if="tests exist">테스트 실행:
```bash
{{test_command}}
```

테스트 결과 확인 및 {{test_results}} 변수에 저장:
- 성공한 테스트 수
- 실패한 테스트 수
- 테스트 커버리지 (있는 경우)
- 실패 원인 (있는 경우)
</action>

<action if="tests failed">테스트 실패 시:
- 실패 원인 분석
- 코드 수정 필요 여부 확인
- 필요시 Step 5로 돌아가기
</action>

<action>2. **수동 테스트 수행**</action>

<ask>수동으로 기능을 테스트해보셨나요?

다음을 확인해주세요:
- 문제가 해결되었나요?
- 기대한 대로 동작하나요?
- 다른 기능에 영향은 없나요?

테스트 결과를 알려주세요:
</ask>

<action>3. **TO-BE 스크린샷 캡처**</action>

<action>Step 2와 동일한 방식으로 수정 후 스크린샷 캡처:

**Playwright MCP 자동 캡처**:
- AS-IS에서 캡처한 동일한 페이지
- 동일한 조건/상태
- {screenshots_folder}/{date}-to-be-{{description}}.png에 저장

**실패 시 수동 요청**:
</action>

<ask if="screenshot needed">수정 후 화면 스크린샷을 찍어서 첨부해주세요.

AS-IS 스크린샷과 비교할 수 있도록:
- 동일한 화면
- 동일한 상황
- 문제가 해결된 모습
</ask>

<action if="user provides screenshot">TO-BE 스크린샷 저장 및 문서용 링크 생성</action>

<action>4. **Before/After 비교**</action>

<action>AS-IS와 TO-BE를 비교 정리:
- 스크린샷 비교
- 로그 비교 (에러 사라짐 확인)
- 동작 비교
- 성능 비교 (필요시)
</action>

<action>5. **변경 사항 커밋**</action>

<action>Git 커밋 수행:
```bash
# 변경 파일 추가
git add [수정된 파일들]

# 커밋 메시지 작성
git commit -m "$(cat <<'EOF'
{{change_type}}: {{issue_title}}

- [주요 변경사항 1]
- [주요 변경사항 2]
- [주요 변경사항 3]

Fixes #{{issue_number}}
EOF
)"
```
</action>

<template-output>test_results_and_verification</template-output>

</step>

<step n="7" goal="Pull Request 생성 (SM Agent)">

<action>SM (Scrum Master) 에이전트를 활용하여 PR을 생성합니다.</action>

<action>1. **원격 브랜치 푸시**</action>

<action>변경사항을 원격 저장소에 푸시:
```bash
git push -u origin {branch_prefix}{{issue_number}}-{{change_title}}
```
</action>

<action>2. **PR 본문 작성**</action>

<action>PR 본문 템플릿 생성:

```markdown
## 변경 사항 요약
{{changes_made}}

## 관련 이슈
Fixes #{{issue_number}}

## 변경 타입
- [ ] Bug fix (버그 수정)
- [ ] New feature (새 기능)
- [ ] Refactoring (리팩토링)
- [ ] Documentation (문서)
- [ ] Other (기타): ___

## 변경 상세

### AS-IS (기존 상태)
{{as_is_documentation}}

### TO-BE (변경 후)
{{test_results_and_verification}}

### 주요 코드 변경
{{code_snippets}}

## 스크린샷 비교

### Before (AS-IS)
![AS-IS]({{as_is_screenshot_url}})

### After (TO-BE)
![TO-BE]({{to_be_screenshot_url}})

## 테스트 결과
{{test_results}}

## 체크리스트
- [ ] 로컬에서 테스트 완료
- [ ] 코드 리뷰 준비 완료
- [ ] 문서 업데이트 (필요시)
- [ ] 변경사항 문서 작성 예정

## 추가 정보
{{additional_notes}}
```
</action>

<action>3. **PR 생성**</action>

<action>GitHub CLI를 사용하여 PR 생성:
```bash
gh pr create \
  --title "{{change_type}}: {{issue_title}}" \
  --body "$(cat <<'EOF'
[위 템플릿 내용]
EOF
)" \
  --base {base_branch}
```
</action>

<action>생성된 PR URL을 {{pr_url}} 변수에 저장</action>

<action>PR URL 출력 및 사용자에게 알림</action>

<template-output>pull_request</template-output>

</step>

<step n="8" goal="변경사항 문서 생성 (Tech Writer Agent)">

<action>Tech Writer 에이전트를 활용하여 상세한 변경사항 문서를 생성합니다.</action>

<critical>참고 문서 스타일을 따릅니다: {reference_doc}</critical>

<action>문서 파일명 생성:
- 패턴: {date}-{{change_title}}.md
- 경로: {default_output_file}
- 예: `/docs/updates/2025-11-22-fix-login-redirect.md`
</action>

<action>템플릿을 사용하여 문서 생성:

템플릿 경로: {template}

다음 변수들을 채워 넣습니다:
- {{change_title}}: 변경사항 제목
- {{work_date}}: {date}
- {{author}}: {user_name}
- {{issue_number}}: GitHub 이슈 번호
- {{pr_url}}: Pull Request URL

- {{change_overview}}: 변경 개요
- {{as_is_state}}: AS-IS 상태 (스크린샷 포함)
- {{change_rationale}}: 변경 필요 사유
- {{to_be_state}}: TO-BE 상태 (스크린샷 포함)
- {{detailed_changes}}: 변경 사항 상세 (코드 비교)
- {{test_results}}: 테스트 결과
- {{usage_guide}}: 사용 방법
- {{references}}: 참고 사항

**문서 작성 원칙**:
1. 참고 문서 스타일 준수 (8-10개 섹션)
2. 스크린샷 적절히 배치
3. 코드 스니펫은 diff 형식 또는 before/after 비교
4. 상세하고 기술적으로 정확하게
5. 재현 가능한 수준의 상세도
6. 향후 참고를 위한 컨텍스트 제공
</action>

<action>문서를 {default_output_file} 경로에 저장</action>

<action>스크린샷 파일들을 {screenshots_folder}에 정리</action>

<action>문서 경로를 사용자에게 알림</action>

<template-output>change_documentation</template-output>

</step>

<step n="9" goal="최종 검증 및 완료">

<action>생성된 모든 산출물을 확인합니다:</action>

<action>**생성된 산출물 목록**:

1. ✅ **GitHub 이슈**: #{{issue_number}}
   - URL: https://github.com/[repo]/issues/{{issue_number}}

2. ✅ **Git 브랜치**: {branch_prefix}{{issue_number}}-{{change_title}}
   - 커밋 수: [확인]
   - 변경 파일 수: [확인]

3. ✅ **Pull Request**: {{pr_url}}
   - 상태: Open
   - 리뷰어: [할당 필요 시]

4. ✅ **변경사항 문서**: {default_output_file}
   - 섹션 수: [확인]
   - 스크린샷 수: [확인]
   - 코드 스니펫 수: [확인]

5. ✅ **스크린샷**: {screenshots_folder}
   - AS-IS 스크린샷: [개수]
   - TO-BE 스크린샷: [개수]
</action>

<action>Checklist 검증 수행:
- 체크리스트 파일: {validation}
- 모든 항목이 충족되었는지 확인
</action>

<action>최종 요약 출력:</action>

<action>```markdown
# 🎉 워크플로우 완료!

## 생성된 산출물

### 1. GitHub 이슈
- 번호: #{{issue_number}}
- 제목: {{issue_title}}
- 링크: [이슈 보기](https://github.com/[repo]/issues/{{issue_number}})

### 2. Pull Request
- 제목: {{change_type}}: {{issue_title}}
- 브랜치: {branch_prefix}{{issue_number}}-{{change_title}}
- 링크: [PR 보기]({{pr_url}})

### 3. 변경사항 문서
- 경로: {default_output_file}
- 스타일: 상세형 (참고 문서 기반)

### 4. 스크린샷
- AS-IS: {{as_is_screenshot_count}}개
- TO-BE: {{to_be_screenshot_count}}개
- 위치: {screenshots_folder}

## 다음 단계

1. **PR 리뷰 요청**
   ```bash
   gh pr review {{pr_url}} --request-reviewer [팀원]
   ```

2. **CI/CD 확인**
   - 자동 테스트 통과 확인
   - 빌드 성공 확인

3. **리뷰 반영**
   - 리뷰 코멘트 확인
   - 필요시 추가 커밋

4. **병합 후**
   - 브랜치 삭제
   - 이슈 자동 닫힘 확인
   - 배포 여부 확인

## 📝 문서 공유

변경사항 문서를 팀과 공유하세요:
- 파일: {default_output_file}
- 참고: 향후 유사한 작업 시 참고 자료로 활용
```
</action>

<ask>추가로 필요한 작업이 있나요?

- 문서 수정/보완
- 추가 스크린샷
- PR 설명 보완
- 기타

있다면 알려주세요. 없으면 "완료"라고 입력해주세요:
</ask>

<action if="user requests changes">필요한 수정 작업 수행</action>

<action if="user confirms completion">워크플로우 종료 메시지 출력:

```
✅ Issue to Docs 워크플로우가 성공적으로 완료되었습니다!

모든 산출물이 생성되었고, 체계적인 변경 관리 프로세스가 완료되었습니다.
팀원들과 공유하고 리뷰를 진행하세요! 🚀
```
</action>

</step>

</workflow>
