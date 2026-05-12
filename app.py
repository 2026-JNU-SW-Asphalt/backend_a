#라이브러리 불러오기
import base64 # 프론트가 보낸 base64(긴 텍스트)를 다시 사진으로 조립하는 도구
import httpx # 파이썬에서 다른 서버로 인터넷 요청을 보내는 도구
import time # 현재 시간을 가져오는 도구(세션 ID나 파일명 만들 때 사용)
import os # 내 맥북의 폴더나 파일 경로를 관리하는 도구
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query # 웹 서버와 웹소켓(프론트엔드와 실시간 통신함)을 만드는 핵심 도구
from fastapi.staticfiles import StaticFiles # 내 폴더의 사진을 인터넷 URI로 볼 수 있게 해주는 도구
from datetime import datetime, timezone # 날짜와 시간을 다루는 도구
import io
from PIL import Image

app = FastAPI() # FastAPI 서버의 앱을 만들기

# -- 서버 기본 셋업(사진 저장 폴더 세팅)--
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # 현재 app.py가 있는 폴더 위치
IMAGE_DIR = os.path.join(BASE_DIR, "captured_images")  # 그 안의 captured_images 폴더

# 만약 내 컴퓨터에 "captured_images" 폴더가 없다면, 새로 만들어라
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

# 외부에서 /images 경로로 접근하면 "captured_images" 폴더의 사진을 보여주도록 설정
app.mount("/images", StaticFiles(directory=IMAGE_DIR), name="images")

# --- 목적지 및 토큰 설정 ---
AI_SERVER_URL = "https://braydon-unfused-else.ngrok-free.dev/predict" # AI 서버 주소
BACKEND_B_URL = "https://ila-dualistic-arrestingly.ngrok-free.dev/api/detections" # 백엔드B 서버 주소
AUTH_TOKEN = "jnu_asphalt_12" #프론트엔드와 통신할 웹소켓 암호
MY_NGROK_URL = "https://dilute-distinct-unpack.ngrok-free.dev" # 나의 ngrok 주소

#웹소켓 길 열어두기 - 프론트엔드가 "ws://.../ws/pothole" 주소로 실시간 접속할 수 있게 엔드포인트 설정
@app.websocket("/ws/pothole")
async def pothole_integration_pipeline(websocket: WebSocket, token: str = Query(None)):
    # 인증 검사
    if token != AUTH_TOKEN:
        await websocket.close(code=1008) 
        return # 프론트가 접속할 때 다른 암호 대면 문 닫아버리고 함수 종료

    await websocket.accept() # 비밀번호가 맞으면 접속 승인
    
    session_id = int(time.time()) # 지금 접속한 사람에게 현재 시간 숫자로 바꿔서 세션 id 주기
    print(f"프론트와 실시간 연결 성공 - 세션 ID: {session_id}") # 터미널에 성공 로그 찍기

    # AI, B에 요청을 보낼 준비
    async with httpx.AsyncClient() as client:
        try:
            while True: # 무한루프: 프론트가 연결끊기 전까지 계속 데이터(사진, 위치) 기다리기
                data = await websocket.receive_json() #  프론트엔드가 쏜 데이터를 JSON형태로 받기
                
            
                # ----------------------------------------------------------------
                # 👀 [프론트엔드 확인용 로그]
                print("\n=== 📥 프론트엔드 원본 데이터 수신 내역 ===")
                print(f"⏱️ Timestamp: {data.get('timestamp')}")
                
                # ✨ GPS 데이터를 더 상세하고 예쁘게 출력하도록 수정!
                gps_data = data.get('gps')
                if gps_data:
                    print(f"📍 GPS 위도(lat): {gps_data.get('lat')}")
                    print(f"📍 GPS 경도(lng): {gps_data.get('lng')}")
                    print(f"🎯 GPS 정확도(accuracy): {gps_data.get('accuracy')}m")
                else:
                    print("⚠️ GPS 데이터가 아예 안 들어왔습니다 (null)")
                
                # Base64는 너무 기니까 길이와 앞/뒤 일부만 잘라서 보여줍니다.
                base64_str = data.get('image', '')
                if base64_str:
                    print(f"🖼️ Base64 길이: 총 {len(base64_str)}자")
                    print(f"🖼️ Base64 미리보기: {base64_str[:40]} ... (중략) ... {base64_str[-20:]}")
                else:
                    print("⚠️ Base64 이미지가 없습니다!")
                print("==========================================\n")
                # ----------------------------------------------------------------
                # 프론트엔드 이미지 디코딩 - 프론트가 준 base64 텍스트를 진짜 이미지로 바꿈.
                try:
                    # "data:image/jpeg;base64,"같은 header 잘라내고 핵심테스트 encoded만 분리
                    header, encoded = data['image'].split(",", 1) 
                    # 핵심테스트 encoded를 컴퓨터가 읽을 수 있는 이미지 데이터로 변환
                    image_bytes = base64.b64decode(encoded)
                    
                    # ==========================================================
                    # 🔄 [전처리 추가] AI 서버로 보내기 전 이미지 90도 강제 회전
                    # ==========================================================
                    # 1. 바이트 데이터를 이미지(PIL) 객체로 열기
                    img = Image.open(io.BytesIO(image_bytes))
                    
                    # 2. 90도 회전 (expand=True는 잘림 방지 필수 옵션!)
                    # 오른쪽으로 누워있다면 -90 (또는 270), 왼쪽으로 누워있다면 90
                    rotated_img = img.rotate(-90, expand=True) 
                    
                    # 3. 회전된 이미지를 다시 WEBP 바이트로 변환해서 덮어쓰기
                    img_byte_arr = io.BytesIO()
                    rotated_img.save(img_byte_arr, format='WEBP')
                    
                    # 핵심: 기존 image_bytes 변수를 회전된 이미지로 바꿔치기!
                    image_bytes = img_byte_arr.getvalue() 
                    # ==========================================================
                    
                    # ✨ [해상도 확인 코드] 변환된 이미지의 가로세로 길이를 재봅니다!
                    img_for_size = Image.open(io.BytesIO(image_bytes))
                    width, height = img_for_size.size
                    print(f"📏 이미지 해상도(가로x세로): {width} x {height} 픽셀")
                    
                except Exception as e:
                    print(f"디코딩 에러: {e}") 
                    continue # 변환 중 에러가 나면 로그만 찍고, 이번 데이터는 무시하고 다음 데이터 기다림

                # AI 서버로 분석 요청 
                # 변환한 이미지를 'image.webp'라는 이름 표 붙여서 ai 서버로 쏠 파일 만들기
                files = {'file': ('image.webp', image_bytes, 'image/webp')}
                # AI 서버로 post 요청하고 결과 기다리기(10초 대기)
                ai_res = await client.post(AI_SERVER_URL, files=files, timeout=10.0)
                
                # ✨ [추가됨] AI 서버가 무슨 상태 코드를 주는지 확인
                print(f"🤖 [AI 서버 상태 코드]: {ai_res.status_code}")
                
                # AI 서버가 "200"으로 응답하면
                if ai_res.status_code == 200:
                    # AI가 준 JSON를 파이썬에 보기좋게 풀기
                    ai_data = ai_res.json()
                    #답변 중에서 "detections" 목록만 빼오기
                    detections = ai_data.get("detections", ai_data.get("data", []))
                    
                    # 포트홀이 발견된 경우에만! 빈 배열 없앰.
                    if detections and len(detections) > 0:
                        print(f"✅ 탐지 완료: 포트홀 {len(detections)}개 발견했습니다.")
                        
                        # 이미지를 파일로 저장하고 URL 생성
                        # 저장할 파일 이름을 "pothole_세션아이디_현재시간.webp" 형식으로 만들기
                        filename = f"pothole_{session_id}_{int(time.time())}.webp"
                        # 내 노트북의 captured_images 폴더 안의 해당 파일명으로 전체 경로 합치기
                        file_path = os.path.join(IMAGE_DIR, filename)
                        
                        # 그 경로에 파일을 '쓰기 모드(wb)'로 열어서 아까 변환한 이미지 데이터를 진짜 파일로 저장
                        with open(file_path, "wb") as f:
                            f.write(image_bytes)
                        
                        #백엔드 B와 연결준비
                        #백엔드 B에게 줄 인터넷 주소 만들기
                        image_url = f"https://dilute-distinct-unpack.ngrok-free.dev/images/{filename}"

                        # 위치 정보(GPS) 처리 - 프론트가 보낸 데이터에서 위치 정보 가져오기
                        gps_info = data.get('gps')
                        lat, lng = None, None # 위도, 경도 초기값 none으로 설정
                        is_valid_gps = False # 거짓으로 초기값 설정
                        
                        if gps_info is not None: # gps 정보가 비어있지 않은 경우
                            lat = gps_info.get('lat') # 위도 꺼내기
                            lng = gps_info.get('lng') # 경도 꺼내기
                            if lat is not None and lng is not None: # 위도, 경도가 둘 다 숫자일때만 true로 인정
                                is_valid_gps = True
                                
                        # ⏱️ [방어 코드] 프론트가 timestamp를 안 주면 내 서버의 현재 시간을 강제로 찍어버림!
                        front_timestamp = data.get('timestamp')
                        if not front_timestamp:
                            front_timestamp = datetime.now(timezone.utc).isoformat()
                            
                        # 백엔드 B 전송용 페이로드
                        # 백엔드 B가 원하는 양식에 맞춰서 json 만들기
                        payload_to_b = {
                            "source": "backend_a", # 나는 백엔드 a
                            "session_id": session_id, # 세션 ID
                            "timestamp": data.get('timestamp'), # 프론트가 찍은 시간
                            "gps": {
                                "lat": lat,
                                "lng": lng,
                                "accuracy": gps_info.get('accuracy') if gps_info else None
                            }, # 프론트가 찍었을 때 위치정보
                            "detections": detections, # AI가 찾아준 포트홀 정보
                            "is_valid_gps": is_valid_gps, # GPS 정상인지
                            "image_url": image_url # 사진 URL
                        }
                        
                        # 백엔드 B로 최종 전송 - JSON 백엔드 B 주소로 post 요청(최대 5초 대기)
                        b_res = await client.post(BACKEND_B_URL, json=payload_to_b, timeout=5.0)
                        
                        # 백엔드 B가 "200"으로 응답했을 때 
                        if b_res.status_code == 200:
                            print(f"[최종 성공] 세션 {session_id} - URL 백엔드 B 전송 완료했습니다")
                        # 백엔드 B가 (400 에러 등) 거절하면?   
                        else:
                            print(f"❌ [전송 실패] 백엔드 B가 거절했습니다. 상태 코드: {b_res.status_code}")
                            print(f"B의 거절 사유: {b_res.text}")
                    
                    # ✨ [추가됨] 포트홀이 0개 잡혔을 때의 처리
                    else:
                        print("🤷 AI 분석 결과: 포트홀이 없습니다 (통과)")

                # ✨ [추가됨] AI 서버가 200 정상 코드를 안 줬을 때 (예: 500 에러 등)
                else:
                    print(f"❌ AI 서버 에러 발생! 사유: {ai_res.text}")
        
        # 프론트가 접속을 스스로 끊고 나갔을 때         
        except WebSocketDisconnect:
            print(f"프론트엔드와 웹소켓 연결 종료 - 세션 ID: {session_id}")
        # 코드 중간에 시스템 에러 발생했을 때 
        except Exception as e:
            print(f"시스템 에러: {e}")

# 서버 실행기 - 이 파일(app.py)을 직접 실행했을 때 Uvicorn(FastAPI 실행 도구)을 통해 8080 포트에서 서버를 킴
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)