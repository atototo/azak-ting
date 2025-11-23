#!/usr/bin/env python3
"""
Supabase 마이그레이션 검증 스크립트
"""
import psycopg2

# Supabase 연결 정보
SUPABASE_URL = "postgresql://postgres.ospkwzuvbodskkyayoeh:dkwkr12!@aws-1-ap-northeast-2.pooler.supabase.com:6543/postgres"

try:
    print("🔌 Supabase 연결 중...")
    conn = psycopg2.connect(SUPABASE_URL)
    cur = conn.cursor()

    # 테이블 목록 확인
    print("\n📋 마이그레이션된 테이블 목록:")
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    tables = cur.fetchall()
    print(f"총 테이블 수: {len(tables)}")
    for table in tables:
        print(f"  - {table[0]}")

    # 주요 테이블 레코드 수 확인
    print("\n📊 주요 테이블 레코드 수:")

    main_tables = [
        'stock_prices_minute',
        'predictions',
        'news_articles',
        'stocks',
        'users',
        'kis_tokens'
    ]

    for table_name in main_tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cur.fetchone()[0]
            print(f"  {table_name}: {count:,} 건")
        except Exception as e:
            print(f"  {table_name}: 테이블 없음 또는 에러 ({str(e)[:50]})")

    # 함수 확인
    print("\n🔧 마이그레이션된 함수:")
    cur.execute("""
        SELECT routine_name
        FROM information_schema.routines
        WHERE routine_schema = 'public' AND routine_type = 'FUNCTION'
        ORDER BY routine_name
    """)
    functions = cur.fetchall()
    for func in functions:
        print(f"  - {func[0]}")

    cur.close()
    conn.close()

    print("\n✅ Supabase 마이그레이션 검증 완료!")

except Exception as e:
    print(f"\n❌ 에러 발생: {e}")
    import traceback
    traceback.print_exc()
