module.exports = {
  apps: [
    // API 서버 (FastAPI) - 가벼운 읽기/쓰기만
    {
      name: 'azak-api',
      cwd: '/Users/young/ai-work/craveny',
      script: 'uv',
      args: 'run python -m backend.main',
      interpreter: 'none',
      instances: 1,  // 필요시 2개 이상으로 확장 가능
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',  // ML 모델 없음, 가벼운 API만
      env: {
        PYTHONUNBUFFERED: '1',
        DEBUG: 'false',
        // Supabase PostgreSQL
        POSTGRES_HOST: 'aws-1-ap-northeast-2.pooler.supabase.com',
        POSTGRES_PORT: '6543',
        POSTGRES_USER: 'postgres.ospkwzuvbodskkyayoeh',
        POSTGRES_PASSWORD: 'dkwkr12!',
        POSTGRES_DB: 'postgres',
      },
      error_file: '/Users/young/ai-work/craveny/logs/api-error.log',
      out_file: '/Users/young/ai-work/craveny/logs/api-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
    },

    // 스케줄러 서버 (백그라운드 작업)
    {
      name: 'azak-scheduler',
      cwd: '/Users/young/ai-work/craveny',
      script: 'uv',
      args: 'run python -m backend.scheduler_main',
      interpreter: 'none',
      instances: 1,  // 반드시 1개만 (중복 실행 방지)
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '5G',  // ML 모델(1GB) + 스케줄러 작업 여유분
      env: {
        PYTHONUNBUFFERED: '1',
        DEBUG: 'false',
        // Supabase PostgreSQL
        POSTGRES_HOST: 'aws-1-ap-northeast-2.pooler.supabase.com',
        POSTGRES_PORT: '6543',
        POSTGRES_USER: 'postgres.ospkwzuvbodskkyayoeh',
        POSTGRES_PASSWORD: 'dkwkr12!',
        POSTGRES_DB: 'postgres',
      },
      error_file: '/Users/young/ai-work/craveny/logs/scheduler-error.log',
      out_file: '/Users/young/ai-work/craveny/logs/scheduler-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
    },

    // Frontend (Next.js)
    {
      name: 'azak-frontend',
      cwd: '/Users/young/ai-work/craveny/frontend',
      script: 'npm',
      args: 'run dev',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        PORT: '3030',
        NODE_ENV: 'development',
      },
      error_file: '/Users/young/ai-work/craveny/logs/frontend-error.log',
      out_file: '/Users/young/ai-work/craveny/logs/frontend-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
    },

    // ngrok
    {
      name: 'azak-ngrok',
      script: 'ngrok',
      args: 'http 3030 --domain=azak.ngrok.app',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      error_file: '/Users/young/ai-work/craveny/logs/ngrok-error.log',
      out_file: '/Users/young/ai-work/craveny/logs/ngrok-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
    },
  ],
};
