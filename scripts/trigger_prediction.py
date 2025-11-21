"""
gpt-5-mini 모델에 대한 예측을 수동으로 트리거하는 스크립트
"""
import sys
sys.path.insert(0, '/Users/young/ai-work/craveny')

from backend.utils.background_prediction import generate_predictions_for_recent_news
from backend.db.session import SessionLocal
from backend.db.models.model import Model

# gpt-5-mini 모델 ID 조회
db = SessionLocal()
try:
    model = db.query(Model).filter(Model.name.like('%gpt-5-mini%')).first()
    if not model:
        print("❌ gpt-5-mini 모델을 찾을 수 없습니다.")
        sys.exit(1)

    print(f"✅ 모델 찾음: {model.name} (ID: {model.id})")

    # 예측 생성 트리거
    print(f"\n🔄 최근 20개 뉴스에 대해 예측 생성 시작...")
    stats = generate_predictions_for_recent_news(
        model_ids=[model.id],
        limit=20,
        days=7,
        in_background=True
    )

    print(f"\n📊 결과:")
    print(f"   총 뉴스: {stats['total']}개")
    print(f"   스케줄됨: {stats['scheduled']}개")
    print(f"   스킵됨: {stats['skipped']}개")
    print(f"   Task ID: {stats.get('task_id', 'N/A')}")
    print(f"\n✅ 백그라운드에서 예측 생성 중입니다...")

finally:
    db.close()
