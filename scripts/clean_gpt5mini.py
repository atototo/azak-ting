"""
gpt-5-mini 모델과 예측 데이터를 삭제하는 스크립트
"""
import sys
sys.path.insert(0, '/Users/young/ai-work/craveny')

from backend.db.session import SessionLocal
from backend.db.models.model import Model
from backend.db.models.prediction import Prediction

db = SessionLocal()
try:
    # 1. gpt-5-mini 모델 조회
    model = db.query(Model).filter(Model.name.like('%gpt-5-mini%')).first()
    if not model:
        print("❌ gpt-5-mini 모델을 찾을 수 없습니다.")
        sys.exit(1)

    print(f"✅ 모델 찾음: {model.name} (ID: {model.id})")

    # 2. 예측 삭제
    predictions = db.query(Prediction).filter(Prediction.model_id == model.id).all()
    print(f"\n🗑️  예측 {len(predictions)}개 삭제 중...")

    for pred in predictions:
        db.delete(pred)

    db.commit()
    print(f"✅ 예측 {len(predictions)}개 삭제 완료")

    # 3. 모델 삭제
    print(f"\n🗑️  모델 '{model.name}' 삭제 중...")
    db.delete(model)
    db.commit()
    print(f"✅ 모델 삭제 완료")

    print(f"\n{'='*60}")
    print("✅ gpt-5-mini 완전 삭제 완료!")
    print("="*60)

except Exception as e:
    db.rollback()
    print(f"❌ 에러: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
