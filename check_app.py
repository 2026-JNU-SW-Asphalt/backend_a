import asyncio
import websockets
import json
import base64
from datetime import datetime, timezone

# 1. 설정값 (app.py와 맞춰야 함)
WS_URL = "ws://localhost:8080/ws/pothole?token=jnu_asphalt_12"
TEST_IMAGE = "pothole.jpg" # 테스트용 이미지 파일명

async def mock_frontend():
    try:
        # 2. 서버 연결
        async with websockets.connect(WS_URL) as websocket:
            print(f"📡 [연결 성공] {WS_URL}에 접속했습니다.")

            # 3. 이미지 읽기 및 Base64 변환
            with open(TEST_IMAGE, "rb") as f:
                encoded_image = base64.b64encode(f.read()).decode('utf-8')
                image_data_uri = f"data:image/jpeg;base64,{encoded_image}"

            # 4. 테스트 케이스 1: 정상 데이터 (GPS 포함)
            payload_normal = {
                "image": image_data_uri,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "gps": {
                    "lat": 35.1595,
                    "lng": 126.8526,
                    "accuracy": 5.0
                }
            }
            
            print("🚀 [Case 1] 정상 데이터 전송 중...")
            await websocket.send(json.dumps(payload_normal))
            await asyncio.sleep(2) # 서버 처리 대기

            # 5. 테스트 케이스 2: GPS가 Null인 경우 (대은님의 특수 요구사항 확인)
            payload_null_gps = {
                "image": image_data_uri,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "gps": None # GPS가 Null로 들어오는 경우
            }

            print("🚀 [Case 2] GPS Null 데이터 전송 중...")
            await websocket.send(json.dumps(payload_null_gps))
            await asyncio.sleep(2)

            print("🏁 테스트 데이터 전송을 마쳤습니다.")

    except Exception as e:
        print(f"❌ 테스트 중 에러 발생: {e}")

if __name__ == "__main__":
    asyncio.run(mock_frontend())