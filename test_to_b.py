import requests
from datetime import datetime, timezone

# 1. 백엔드 B의 진짜 주소!
backend_b_url = "http://10.10.126.83:8000/api/detections"

# 2. 명세서에 맞춘 가짜 포트홀 데이터 (Mock Data) 생성
mock_payload = {
    "source": "backend_a",
    "session_id": "test_pingpong_002",
    "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    "gps": {
        "lat": 35.1695,
        "lng": 126.9526
    },
    "detections": [
        {
            "bbox": [700, 400, 950, 450],
            "confidence": 0.99,
            "class": "pothole"
        }
    ],
    "is_valid_gps": True
}

print(f"🚚 배달 트럭이 백엔드 B({backend_b_url})로 출발합니다...")

# 3. 데이터 발사!
try:
    response = requests.post(backend_b_url, json=mock_payload, timeout=3.0)
    
    if response.status_code == 200:
        print("✅ [대성공] 백엔드 B가 데이터를 무사히 받았습니다!")
        print("백엔드 B의 응답:", response.json())
    elif response.status_code == 422:
        print("⚠️ [형식 에러] 백엔드 B에 도착은 했는데, 데이터 모양이 안 맞대요 (422 Error)")
        print("에러 상세:", response.text)
    else:
        print(f"🚨 [에러 발생] 상태 코드: {response.status_code}")
        print("이유:", response.text)

except requests.exceptions.ConnectionError:
    print("❌ [연결 실패] 백엔드 B 컴퓨터를 찾을 수 없습니다. 같은 와이파이인지, 백엔드 B 서버가 켜져 있는지 확인하세요!")
except requests.exceptions.Timeout:
    print("⏱️ [시간 초과] 백엔드 B가 3초 안에 응답하지 않습니다.")