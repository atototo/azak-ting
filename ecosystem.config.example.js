module.exports = {
  apps: [
    // Backend (FastAPI)
    {
      name: 'azak-backend',
      cwd: '/Users/young/ai-work/craveny',
      script: 'uv',
      args: 'run python -m backend.main',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      max_memory_restart: '3G',  // 임베딩 모델 메모리 (~1GB) 추가
      env: {
        PYTHONUNBUFFERED: '1',
        DEBUG: 'false',
        // Supabase PostgreSQL (실제 값으로 교체 필요)
        POSTGRES_HOST: 'your-supabase-host.supabase.com',
        POSTGRES_PORT: '6543',
        POSTGRES_USER: 'postgres.your-project-id',
        POSTGRES_PASSWORD: 'your-password',
        POSTGRES_DB: 'postgres',
      },
      error_file: '/Users/young/ai-work/craveny/logs/backend-error.log',
      out_file: '/Users/young/ai-work/craveny/logs/backend-out.log',
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
