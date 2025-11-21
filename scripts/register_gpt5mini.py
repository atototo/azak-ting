"""
gpt-5-mini 모델을 재등록하는 스크립트
"""
import sys
sys.path.insert(0, '/Users/young/ai-work/craveny')

import requests
import json

# 모델 등록 API 호출
url = "http://127.0.0.1:8000/api/models"
payload = {
    "name": "gpt-5-mini",
    "provider": "openrouter",
    "model_identifier": "openai/gpt-5-mini",
    "description": "OpenAI의 gpt-5-mini 모델 (OpenRouter 경유)"
}

print("🔄 gpt-5-mini 모델 등록 중...")
print(f"   Endpoint: {url}")
print(f"   Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

try:
    response = requests.post(url, json=payload)

    if response.status_code == 201:
        data = response.json()
        print(f"\n✅ 모델 등록 성공!")
        print(f"   ID: {data['id']}")
        print(f"   이름: {data['name']}")
        print(f"   프로바이더: {data['provider']}")
        print(f"   모델 식별자: {data['model_identifier']}")
        print(f"   활성화: {data['is_active']}")
        print(f"\n🔄 백그라운드에서 최근 뉴스 예측 생성이 시작됩니다...")
    else:
        print(f"\n❌ 모델 등록 실패!")
        print(f"   상태 코드: {response.status_code}")
        print(f"   응답: {response.text}")

except requests.exceptions.ConnectionError:
    print("\n❌ 백엔드 서버에 연결할 수 없습니다. 백엔드가 실행 중인지 확인하세요.")
except Exception as e:
    print(f"\n❌ 에러: {e}")
    import traceback
    traceback.print_exc()
