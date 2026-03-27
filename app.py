import json
import uuid
import datetime
import requests
import cv2
import numpy as np
import base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# --- (기존 유지) 더미 AI 추론 함수 ---
def mock_ai_inference(image_array):
    """나중에 실제 YOLOv11 모델로 교체될 함수입니다."""
    # 프론트에서 넘어온 1920x640 비율에 맞춘 가상의 BBox 반환
    return [
        {"bbox": [500, 300, 600, 350], "confidence": 0.88, "class": "pothole"}
    ]

# --- (기존 유지) 백엔드 B 전송 함수 ---
def send_to_backend_b(detection_json):
    """백엔드 A에서 조립한 최종 JSON을 메인 서버(백엔드 B)로 전송합니다."""
    backend_b_url = "http://localhost:8000/api/detections" # 실제 주소로 변경 필요
    try:
        response = requests.post(backend_b_url, json=detection_json, timeout=2.0)
        if response.status_code == 200:
            print("🚀 [전송 성공] Backend B로 데이터 전송 완료!")
            return True
        else:
            print(f"⚠️ [전송 실패] 상태 코드: {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("🚨 [연결 실패] Backend B 서버에 접속할 수 없습니다.")
        return False

# ==========================================
# 🔥 핵심: FastAPI 서버 및 웹소켓 설정 🔥
# ==========================================

app = FastAPI(title="광주형 포트홀 관제 (Backend A)")

# 프론트엔드(React)의 접근을 허용하는 CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/pothole")
async def websocket_endpoint(websocket: WebSocket):
    """
    프론트엔드(React)와 연결되는 전용 파이프(웹소켓)입니다.
    프론트에서 1초에 3번(3fps), WebP 이미지와 GPS를 묶어서 JSON으로 던져줍니다.
    """
    await websocket.accept()
    session_id = f"ses_{uuid.uuid4().hex[:8]}"
    print(f"✅ [웹소켓 연결됨] 프론트엔드 접속 (Session ID: {session_id})")

    try:
        while True:
            # 1. 프론트엔드가 보낸 택배(JSON 텍스트) 수신
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)

            # 2. 데이터 추출 (프론트엔드와 약속한 키 이름 사용)
            # 프론트엔드가 "data:image/webp;base64,..." 형태로 보낸다고 가정합니다.
            base64_image = data.get("image") 
            gps_data = data.get("gps")

            # 3. Base64 텍스트를 파이썬 이미지(OpenCV 배열)로 복원 (AI가 먹기 좋게)
            try:
                # "data:image/webp;base64," 같은 앞부분의 메타데이터 제거
                if "," in base64_image:
                    base64_image = base64_image.split(",")[1]
                
                img_bytes = base64.b64decode(base64_image)
                img_arr = np.frombuffer(img_bytes, dtype=np.uint8)
                cv_image = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
                # cv_image는 이제 프론트가 잘라준 1920x640 크기의 완벽한 사진입니다!
            except Exception as e:
                print(f"이미지 디코딩 에러: {e}")
                continue # 사진이 깨졌으면 이번 턴은 무시하고 다음 사진을 기다림

            # 4. AI 모델 추론 (YOLOv11 가짜 호출)
            detections = mock_ai_inference(cv_image)

            # 포트홀이 발견되었을 때만 처리 (데이터 다이어트!)
            if detections:
                # 5. 백엔드 B로 보낼 최종 JSON 조립
                # UTC 시간 생성
                timestamp_str = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
                
                # GPS 유효성 검사 방어 로직
                is_valid_gps = bool(gps_data and gps_data.get("lat") and gps_data.get("lng"))
                if not is_valid_gps:
                    gps_data = {"lat": 0.0, "lng": 0.0}

                final_json = {
                    "source": "backend_a",
                    "session_id": session_id,
                    "timestamp": timestamp_str,
                    "gps": {"lat": gps_data["lat"], "lng": gps_data["lng"]},
                    "detections": detections,
                    "is_valid_gps": is_valid_gps
                }

                # 6. 백엔드 B로 전송
                print(f"\n🎯 [포트홀 발견!] 백엔드 B로 전송합니다. GPS: {gps_data}")
                send_to_backend_b(final_json)

    except WebSocketDisconnect:
        print(f"❌ [웹소켓 끊김] 프론트엔드 연결 종료 (Session ID: {session_id})")
    except Exception as e:
        print(f"🚨 [서버 에러] 알 수 없는 에러 발생: {e}")