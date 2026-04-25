import base64
import httpx
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from datetime import datetime

app = FastAPI()

# 🎯 엔드포인트 설정 (실제 ngrok 주소로 업데이트 필요)
AI_SERVER_URL = "https://[AI_SERVER_NGROK_URL]/predict"
BACKEND_B_URL = "https://[BACKEND_B_NGROK_URL]/api/detections"
AUTH_TOKEN = "jnu_asphalt_12"

@app.websocket("/ws/pothole")
async def pothole_integration_pipeline(websocket: WebSocket, token: str = Query(None)):
    # 1. 인증 토큰 검사
    if token != AUTH_TOKEN:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    
    # 2. 세션 ID 생성 (숫자 형식)
    # 현재 타임스탬프를 정수로 변환하여 숫자로 된 세션 ID를 만듭니다.
    session_id = int(time.time()) 
    print(f"🚀 실시간 연결 성공 - 세션 ID: {session_id}")

    async with httpx.AsyncClient() as client:
        try:
            while True:
                # 3. 프론트엔드로부터 데이터 수신
                data = await websocket.receive_json()
                
                # 4. 이미지 처리 (Base64 -> Binary)
                try:
                    header, encoded = data['image'].split(",", 1)
                    image_bytes = base64.b64decode(encoded)
                except Exception:
                    continue

                # 5. AI 서버로 분석 요청 (Phase 1)
                files = {'file': ('image.webp', image_bytes, 'image/webp')}
                ai_res = await client.post(AI_SERVER_URL, files=files, timeout=10.0)
                
                if ai_res.status_code == 200:
                    ai_data = ai_res.json()
                    # AI 결과 추출 (detections 또는 data 키 확인)
                    detections = ai_data.get("detections", ai_data.get("data", []))
                    
                    # 6. 포트홀이 발견된 경우에만 백엔드 B로 전송 (빈 배열 제외)
                    if detections and len(detections) > 0:
                        print(f"📡 탐지 완료: 포트홀 {len(detections)}개 발견")
                        
                        # 7. 위치 정보(GPS) 처리 및 null 대응
                        gps_info = data.get('gps')
                        lat = None
                        lng = None
                        is_valid_gps = False
                        
                        # 프론트엔드에서 gps가 null로 들어오거나 내부 값이 null일 경우 처리
                        if gps_info is not None:
                            lat = gps_info.get('lat')
                            lng = gps_info.get('lng')
                            
                            # 위도와 경도가 모두 존재할 때만 유효한 GPS로 판단
                            if lat is not None and lng is not None:
                                is_valid_gps = True
                        
                        # 8. 백엔드 B 전송용 페이로드 조립 (이미지 포함)
                        payload_to_b = {
                            "source": "backend_a",
                            "session_id": session_id,  # 숫자로 된 세션 ID
                            "timestamp": data.get('timestamp'),
                            "gps": {
                                "lat": lat, # null일 경우 그대로 null로 전송
                                "lng": lng
                            },
                            "detections": detections,
                            "is_valid_gps": is_valid_gps, # null일 경우 false
                            "image": data['image'] # 프론트에서 받은 원본 이미지(Base64)
                        }
                        
                        # 9. 백엔드 B로 최종 전송 (Phase 2)
                        b_res = await client.post(BACKEND_B_URL, json=payload_to_b, timeout=5.0)
                        
                        if b_res.status_code == 200:
                            print(f"✅ [최종 성공] 세션 {session_id} 데이터를 백엔드 B로 전송했습니다.")
                
        except WebSocketDisconnect:
            print(f"📴 연결 종료 - 세션 ID: {session_id}")
        except Exception as e:
            print(f"❌ 시스템 에러: {e}")

if __name__ == "__main__":
    import uvicorn
    # 프론트엔드 접속을 위해 8080 포트 사용
    uvicorn.run(app, host="0.0.0.0", port=8080)