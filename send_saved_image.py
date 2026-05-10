import httpx
import os
import asyncio

# --- 🎯 1. 설정 (app.py와 동일하게 세팅) ---
AI_SERVER_URL = "https://braydon-unfused-else.ngrok-free.dev/predict"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "captured_images")

# 📸 [파일 지정] 전송하고 싶은 사진 파일 이름을 여기에 적으세요!
TARGET_FILE = "pothole_1777295949_1777295974.webp" # 👈 폴더에 있는 실제 파일명으로 수정!

async def send_to_ai():
    # 파일 전체 경로 조립
    file_path = os.path.join(IMAGE_DIR, TARGET_FILE)
    
    # 🔍 파일이 진짜 있는지 확인
    if not os.path.exists(file_path):
        print(f"❌ 에러: {file_path} 경로에 파일이 없습니다! 파일명을 확인해 주세요.")
        return

    print(f"🚀 AI 서버로 전송 시작: {TARGET_FILE}")

    async with httpx.AsyncClient() as client:
        try:
            # 📂 2. 파일을 바이너리(wb) 모드로 읽어서 AI 서버로 전송할 준비
            with open(file_path, "rb") as f:
                # 'file'이라는 이름표를 붙여서 AI 서버 양식에 맞게 포장합니다.
                files = {'file': (TARGET_FILE, f, 'image/webp')}
                
                # AI 서버로 발사!
                response = await client.post(AI_SERVER_URL, files=files, timeout=10.0)
            
            # 3. 결과 확인
            if response.status_code == 200:
                result = response.json()
                print("✅ AI 판독 결과 수신 성공!")
                print(f"📡 결과 데이터: {result}")
            else:
                print(f"⚠️ AI 서버 응답 에러: {response.status_code}")
                print(f"🔍 에러 사유: {response.text}")

        except Exception as e:
            print(f"❌ 전송 중 시스템 에러 발생: {e}")

# 스크립트 실행
if __name__ == "__main__":
    asyncio.run(send_to_ai())