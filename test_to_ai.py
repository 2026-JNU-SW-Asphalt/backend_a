import requests
import cv2
import numpy as np

# 1. AI 팀원이 알려준 대문 주소 + 진짜 방 번호(/predict)
ai_colab_url = "https://braydon-unfused-else.ngrok-free.dev/predict" 

print("📦 프론트엔드가 보낸 척하는 1920x640 더미 이미지를 만듭니다...")
dummy_image = np.zeros((640, 1920, 3), dtype=np.uint8)

_, img_encoded = cv2.imencode('.jpg', dummy_image)

# 2. 🎯 이름표를 AI가 원하는 'file'로 정확하게 수정!
# 'file'이라는 키값에 (파일명, 데이터, 파일타입) 형태로 묶어서 보냅니다!
files = {'file': ('dummy.jpg', img_encoded.tobytes(), 'image/jpeg')}

print(f"🤖 AI 서버({ai_colab_url})로 사진을 쏩니다! (코랩 다녀오는 중...)")

try:
    response = requests.post(ai_colab_url, files=files, timeout=10.0)
    
    if response.status_code == 200:
        print("✅ [대성공] 코랩 AI가 200 OK를 보냈습니다!")
        print("💡 코랩 응답 데이터:", response.json())
    else:
        print(f"⚠️ [에러 발생] 상태 코드: {response.status_code}")
        print("이유:", response.text)

except Exception as e:
    print(f"❌ [기타 에러] {e}")