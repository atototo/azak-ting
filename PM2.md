---
title: "PM2 프로세스 관리 가이드"
created: 2025-11-20
updated: 2025-11-20
author: young
category: deployment
environment: production
---

# PM2 프로세스 관리 가이드

> **참고**: 전체 아키텍처 개요는 [Architecture Overview](docs/architecture/overview.md)를 참조하세요.

## 개요

PM2를 사용하여 백엔드(FastAPI), 프론트엔드(Next.js), ngrok을 데몬으로 실행합니다.
맥북을 덮어도 프로세스가 계속 실행되며, 크래시 시 자동으로 재시작됩니다.

## 설치

```bash
npm install -g pm2
```

## 서비스 시작

```bash
# 모든 서비스 시작
cd /Users/young/ai-work/azak
pm2 start ecosystem.config.js

# 또는 개별 서비스 시작
pm2 start ecosystem.config.js --only azak-backend
pm2 start ecosystem.config.js --only azak-frontend
pm2 start ecosystem.config.js --only azak-ngrok
```

## 상태 확인

```bash
# 모든 서비스 상태 확인
pm2 status

# 실시간 모니터링 (CPU, 메모리 사용량)
pm2 monit

# 특정 서비스 정보
pm2 show azak-backend
```

## 로그 확인

```bash
# 모든 서비스 로그 (실시간)
pm2 logs

# 특정 서비스 로그
pm2 logs azak-backend
pm2 logs azak-frontend
pm2 logs azak-ngrok

# 로그 파일 위치
ls -l logs/
# - backend-out.log, backend-error.log
# - frontend-out.log, frontend-error.log
# - ngrok-out.log, ngrok-error.log

# 로그 지우기
pm2 flush
```

## 재시작

```bash
# 모든 서비스 재시작
pm2 restart all

# 특정 서비스 재시작
pm2 restart azak-backend
pm2 restart azak-frontend
pm2 restart azak-ngrok

# 코드 변경 후 재시작 (다운타임 없이)
pm2 reload all
```

## 중지 및 삭제

```bash
# 모든 서비스 중지 (프로세스는 남음)
pm2 stop all

# 특정 서비스 중지
pm2 stop azak-backend

# 모든 서비스 삭제 (프로세스 제거)
pm2 delete all

# 특정 서비스 삭제
pm2 delete azak-backend
```

## 자동 시작 설정 (맥북 재부팅 시)

```bash
# 1. 현재 프로세스 목록 저장
pm2 save

# 2. 시작 스크립트 생성 (macOS launchd)
pm2 startup

# 3. 위 명령어가 출력하는 sudo 명령어를 실행
# 예: sudo env PATH=$PATH:/Users/young/.nvm/versions/node/v20.19.5/bin /Users/young/.nvm/versions/node/v20.19.5/lib/node_modules/pm2/bin/pm2 startup launchd -u young --hp /Users/young

# 자동 시작 해제
pm2 unstartup
```

## 서비스 URL

- **프론트엔드**: http://localhost:3030
- **백엔드 API**: http://localhost:8000
- **백엔드 Docs**: http://localhost:8000/docs
- **ngrok Public URL**: https://azak.ngrok.app

## 트러블슈팅

### 서비스가 시작되지 않을 때

```bash
# 로그 확인
pm2 logs azak-backend --lines 100

# 포트 충돌 확인
lsof -ti:3030  # 프론트엔드
lsof -ti:8000  # 백엔드

# 강제 재시작
pm2 delete all
pm2 start ecosystem.config.js
```

### 메모리 누수 의심 시

```bash
# 메모리 사용량 확인
pm2 monit

# 서비스 재시작
pm2 restart azak-backend
```

### ngrok이 연결되지 않을 때

```bash
# ngrok 상태 확인
curl http://127.0.0.1:4040/api/tunnels

# ngrok 재시작
pm2 restart azak-ngrok

# ngrok 로그 확인
pm2 logs azak-ngrok
```

## 유용한 명령어 모음

```bash
# CPU/메모리 사용량 확인
pm2 list

# 환경 변수 확인
pm2 env 0  # ID 0번 프로세스

# 프로세스 설정 업데이트
pm2 restart ecosystem.config.js --update-env

# 모든 로그 삭제
pm2 flush

# PM2 데몬 재시작
pm2 kill
pm2 start ecosystem.config.js
```

## 설정 파일 (ecosystem.config.js)

PM2 설정은 `ecosystem.config.js`에 정의되어 있습니다:
- 자동 재시작 활성화
- 메모리 제한 (백엔드 2GB, 프론트엔드 1GB)
- 로그 파일 경로 지정
- 환경 변수 설정

**주의**: `ecosystem.config.js`는 절대 경로를 포함하므로 Git에 커밋하지 않습니다.

### 예시 설정 파일

프로젝트 루트에 `ecosystem.config.js` 파일을 생성하세요:

```javascript
module.exports = {
  apps: [
    {
      name: 'azak-backend',
      script: 'uvicorn',
      args: 'backend.main:app --host 0.0.0.0 --port 8000',
      cwd: '/Users/young/ai-work/azak',
      interpreter: '/Users/young/ai-work/azak/.venv/bin/python',
      max_memory_restart: '2G',
      autorestart: true,
      watch: false,
      error_file: './logs/backend-error.log',
      out_file: './logs/backend-out.log',
      env: {
        PYTHONPATH: '/Users/young/ai-work/azak'
      }
    },
    {
      name: 'azak-frontend',
      script: 'npm',
      args: 'start',
      cwd: '/Users/young/ai-work/azak/frontend',
      max_memory_restart: '1G',
      autorestart: true,
      watch: false,
      error_file: '../logs/frontend-error.log',
      out_file: '../logs/frontend-out.log',
      env: {
        PORT: '3030'
      }
    },
    {
      name: 'azak-ngrok',
      script: 'ngrok',
      args: 'http --domain=azak.ngrok.app 3030',
      cwd: '/Users/young/ai-work/azak',
      autorestart: true,
      watch: false,
      error_file: './logs/ngrok-error.log',
      out_file: './logs/ngrok-out.log'
    }
  ]
};
```

### 설정 항목 설명

| 항목 | 설명 |
|------|------|
| `name` | PM2 프로세스 이름 |
| `script` | 실행할 스크립트/명령어 |
| `args` | 스크립트 인자 |
| `cwd` | 작업 디렉토리 (절대 경로) |
| `interpreter` | 인터프리터 경로 (Python 가상환경) |
| `max_memory_restart` | 메모리 제한 초과 시 자동 재시작 |
| `autorestart` | 크래시 시 자동 재시작 여부 |
| `watch` | 파일 변경 감지 (개발 시에만 true) |
| `error_file` | 에러 로그 파일 경로 |
| `out_file` | 표준 출력 로그 파일 경로 |
| `env` | 환경 변수 |

### 첫 실행 전 체크리스트

1. **절대 경로 수정**: `cwd`와 `interpreter` 경로를 본인 환경에 맞게 수정
2. **로그 디렉토리 생성**: `mkdir -p logs`
3. **Python 가상환경 활성화 확인**: `.venv/bin/python` 경로 확인
4. **ngrok 도메인 설정**: ngrok 대시보드에서 도메인 예약 필요
