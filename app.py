import base64
import httpx
import time
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.staticfiles import StaticFiles
from datetime import datetime

app = FastAPI()

# --- 🛠️ 1. 서버 기본 셋업 (문지기 배치) ---
IMAGE_DIR = "captured_images"
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

# 외부에서 /images 경로로 접근하면 폴더의 사진을 보여주도록 설정
app.mount("/images", StaticFiles(directory=IMAGE_DIR), name="images")

# --- 🎯 2. 목적지 및 토큰 설정 ---
AI_SERVER_URL = "https://braydon-unfused-else.ngrok-free.dev/predict"
BACKEND_B_URL = "https://ila-dualistic-arrestingly.ngrok-free.dev/api/detections"
AUTH_TOKEN = "jnu_asphalt_12"
MY_NGROK_URL = "https://dilute-distinct-unpack.ngrok-free.dev" # 대은님의 현재 ngrok 주소

@app.websocket("/ws/pothole")
async def pothole_integration_pipeline(websocket: WebSocket, token: str = Query(None)):
    # 인증 검사
    if token != AUTH_TOKEN:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    session_id = int(time.time()) 
    print(f"🚀 실시간 연결 성공 - 세션 ID: {session_id}")

    async with httpx.AsyncClient() as client:
        try:
            while True:
                data = await websocket.receive_json()
                
                # 프론트엔드 이미지 디코딩
                try:
                    header, encoded = data['image'].split(",", 1)
                    image_bytes = base64.b64decode(encoded)
                except Exception as e:
                    print(f"⚠️ 디코딩 에러: {e}")
                    continue

                # AI 서버로 분석 요청 (Phase 1)
                files = {'file': ('image.webp', image_bytes, 'image/webp')}
                ai_res = await client.post(AI_SERVER_URL, files=files, timeout=10.0)
                
                if ai_res.status_code == 200:
                    ai_data = ai_res.json()
                    detections = ai_data.get("detections", ai_data.get("data", []))
                    
                    # 포트홀이 발견된 경우에만!
                    if detections and len(detections) > 0:
                        print(f"📡 탐지 완료: 포트홀 {len(detections)}개 발견")
                        
                        # 🎯 [핵심] 이미지를 파일로 저장하고 URL 생성!
                        filename = f"pothole_{session_id}_{int(time.time())}.webp"
                        file_path = os.path.join(IMAGE_DIR, filename)
                        
                        with open(file_path, "wb") as f:
                            f.write(image_bytes)
                        
                        image_url = f"{wss://dilute-distinct-unpack.ngrok-free.dev/ws/pothole?token=jnu_asphalt_12}/images/{filename}"

                        # 위치 정보(GPS) 처리
                        gps_info = data.get('gps')
                        lat, lng = None, None
                        is_valid_gps = False
                        
                        if gps_info is not None:
                            lat = gps_info.get('lat')
                            lng = gps_info.get('lng')
                            if lat is not None and lng is not None:
                                is_valid_gps = True
                        
                        # 백엔드 B 전송용 페이로드 (Base64 빼고 URL 넣기)
                        payload_to_b = {
                            "source": "backend_a",
                            "session_id": session_id,
                            "timestamp": data.get('timestamp'),
                            "gps": {
                                "lat": lat,
                                "lng": lng
                            },
                            "detections": detections,
                            "is_valid_gps": is_valid_gps,
                            "image_url": image_url # ✨ 여기가 포인트입니다!
                        }
                        
                        # 백엔드 B로 최종 전송 (Phase 2)
                        b_res = await client.post(BACKEND_B_URL, json=payload_to_b, timeout=5.0)
                        
                        if b_res.status_code == 200:
                            print(f"✅ [최종 성공] 세션 {session_id} - URL 백엔드 B 전송 완료!")
                
        except WebSocketDisconnect:
            print(f"📴 연결 종료 - 세션 ID: {session_id}")
        except Exception as e:
            print(f"❌ 시스템 에러: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)