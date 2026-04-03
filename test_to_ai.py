import requests
import cv2
import numpy as np

# 1. AI 팀원이 준 주소 + 엔드포인트(/predict라고 가정)
ai_colab_url = "https://braydon-unfused-else.ngrok-free.dev/predict" 

# 2. 전송할 '가짜 이미지' 만들기 (1920x640 사이즈의 까만 화면)
print("📦 프론트엔드가 보낸 척하는 1920x640 더미 이미지를 만듭니다...")
dummy_image = np.zeros((640, 1920, 3), dtype=np.uint8)

# 3. 이미지를 파일 형태로 포장하기 (.jpg로 압축)
_, img_encoded = cv2.imencode('.jpg', dummy_image)
files = {'image': img_encoded.tobytes()}

print(f"🤖 AI 서버({ai_colab_url})로 사진을 쏩니다! (코랩 다녀오는 중...)")

# 4. 코랩으로 전송! (코랩은 GPU를 쓰더라도 쪼~금 걸릴 수 있으니 넉넉히 5초 대기)
try:
    response = requests.post(ai_colab_url, files=files, timeout=5.0)
    
    if response.status_code == 200:
        print("✅ [대성공] 코랩 AI가 사진을 분석하고 결과를 돌려줬습니다!")
        print("💡 코랩이 보낸 JSON 결과:", response.json())
    else:
        print(f"⚠️ [에러 발생] 상태 코드: {response.status_code}")
        print("이유:", response.text)

except requests.exceptions.ConnectionError:
    print("❌ [연결 실패] 코랩 서버가 꺼져있거나 주소가 틀렸습니다.")
except requests.exceptions.Timeout:
    print("⏱️ [시간 초과] 코랩 서버가 5초 안에 답을 주지 못하고 있습니다 (너무 느림!).")