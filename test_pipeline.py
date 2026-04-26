import requests
import sys
from datetime import datetime, timezone

# 🎯 목적지 주소
ai_url = "https://braydon-unfused-else.ngrok-free.dev/predict"
backend_b_url = "https://ila-dualistic-arrestingly.ngrok-free.dev/api/detections"

print("==================================================")
print("🚀 [Phase 1] AI 서버로 이미지 판독을 요청합니다...")
print("==================================================")

# 1. 진짜 포트홀 이미지 불러오기
image_path = "pothole.jpg"
try:
    with open(image_path, "rb") as f:
        image_data = f.read()
        print(f"📦 준비된 '{image_path}' 파일 용량: {len(image_data)} bytes")
except FileNotFoundError:
    print(f"❌ [에러] '{image_path}' 파일이 없습니다! 사진을 같은 폴더에 넣어주세요.")
    sys.exit()

# 2. 사진 포장
files = {'file': ('pothole.jpg', image_data, 'image/jpeg')}

try:
    # 3. AI 서버로 발사!
    ai_response = requests.post(ai_url, files=files, timeout=15.0)
    
    if ai_response.status_code == 200:
        ai_data = ai_response.json()
        
        # AI 결과 이름표 (data 또는 detections)
        detections = ai_data.get("data", ai_data.get("detections", []))
        
        print(f"✅ AI 판독 완료! (발견된 포트홀 수: {len(detections)}개)")
        print(f"💡 AI 결과물: {detections}\n")
        
        # 🎯 [핵심 실무 로직] 포트홀이 0개면 백엔드 B로 안 보내고 여기서 멈춤!
        if len(detections) == 0:
            print("🛑 포트홀이 발견되지 않았습니다. 백엔드 B로 전송하지 않고 프로세스를 깔끔하게 종료합니다.")
        
        # 🎯 포트홀이 1개 이상일 때만 Phase 2를 실행합니다!
        else:
            print("==================================================")
            print("🚚 [Phase 2] 발견된 포트홀 데이터를 백엔드 B로 전달합니다...")
            print("==================================================")
            
            # 4. 백엔드 B 명세서 조립
            payload_to_b = {
                "source": "backend_a",
                "session_id": "test_real_photo_003",
                "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                "gps": {
                    "lat": 35.1595,
                    "lng": 126.8526
                },
                "detections": detections,  # 진짜 AI 결과 삽입
                "is_valid_gps": True
            }
            
            # 5. 백엔드 B로 최종 발사!s
            b_response = requests.post(backend_b_url, json=payload_to_b, timeout=5.0)
            
            if b_response.status_code == 200:
                print("🎉 [최종 대성공] 백엔드 B에 데이터 저장 완료!")
                print("백엔드 B 응답:", b_response.json())
                print("==================================================")
                print("🛣️ 완벽한 데이터 고속도로(A -> AI -> B)가 개통되었습니다!")
            elif b_response.status_code == 422:
                print("⚠️ [형식 에러] 백엔드 B에서 422 에러 발생")
                print("이유:", b_response.text)
            else:
                print(f"🚨 [백엔드 B 통신 에러] 상태 코드: {b_response.status_code}")
                print(f"상세 이유: {b_response.text}")
                
    else:
        print(f"🚨 [AI 통신 에러] 상태 코드: {ai_response.status_code}")
        print("이유:", ai_response.text)

except Exception as e:
    print(f"❌ [시스템 에러] 파이프라인 실행 중 문제가 발생했습니다: {e}")