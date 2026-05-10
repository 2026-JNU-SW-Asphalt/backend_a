import asyncio
import websockets
import json
import base64
from datetime import datetime, timezone

async def test_connection():
    # 백엔드 A의 웹소켓 주소 (비밀번호 포함)
    uri = "ws://localhost:8080/ws/pothole?token=jnu_asphalt_12"
    
    print("1. 테스트 이미지를 Base64로 변환 중...")
    try:
        with open("test.jpg", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            # 프론트엔드가 보내는 규격에 맞게 헤더 추가
            base64_image = f"data:image/jpeg;base64,{encoded_string}"
    except FileNotFoundError:
        print("❌ 에러: 같은 폴더에 test.jpg 파일이 없습니다!")
        return

    print("2. 프론트엔드용 테스트 JSON 패키징 중...")
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "gps": {
            "lat": 35.1769,
            "lng": 126.9058,
            "accuracy": 12.5 # 테스트용 정확도 12.5m
        },
        "image": base64_image
    }

    print("3. 백엔드 A로 웹소켓 전송 시도...")
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ 웹소켓 연결 성공! 데이터를 전송합니다.")
            await websocket.send(json.dumps(payload))
            print("🚀 전송 완료! 백엔드 A(app.py)가 실행 중인 터미널 창을 확인해보세요.")
            
            # 백엔드 A가 AI 서버와 통신할 시간을 주기 위해 5초 대기
            await asyncio.sleep(5)
    except ConnectionRefusedError:
        print("❌ 에러: 백엔드 A 서버가 꺼져있습니다. app.py를 먼저 실행해주세요!")

# 스크립트 실행
asyncio.run(test_connection())