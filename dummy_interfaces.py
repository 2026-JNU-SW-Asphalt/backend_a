import requests  # 서버 간 통신을 위한 필수 라이브러리입니다.

def mock_ai_inference(image_array):
    """(기존과 동일) AI 파트가 나중에 줄 함수를 흉내 냅니다."""
    return [
        {"bbox": [100, 200, 150, 250], "confidence": 0.85, "class": "pothole"}
    ]

# 👇 이름도 mock_send... 에서 진짜 send_to_backend_b 로 바꿉니다!
def send_to_backend_b(detection_json):
    """
    백엔드 A에서 조립한 JSON을 백엔드 B 서버로 전송합니다.
    (HTTP POST 방식 사용)
    """
    # 백엔드 B 담당자가 나중에 알려줄 실제 서버 주소입니다.
    # (지금은 테스트를 위해 가짜 로컬 주소를 적어둡니다.)
    backend_b_url = "http://localhost:8000/api/detections"
    
    try:
        # 배달 트럭(requests.post) 출발!
        # json=detection_json 을 넣으면 파이썬이 알아서 예쁘게 포장해서 보냅니다.
        # timeout=2.0 은 "2초 안에 백엔드 B가 대답 안 하면 그냥 끊어버려!" 라는 뜻입니다. (영상 멈춤 방지)
        response = requests.post(backend_b_url, json=detection_json, timeout=2.0)
        
        # 백엔드 B가 "잘 받았어!(200 OK)"라고 영수증을 줬는지 확인
        if response.status_code == 200:
            print("🚀 [전송 성공] Backend B가 데이터를 무사히 받았습니다!")
            return True
        else:
            print(f"⚠️ [전송 실패] Backend B가 에러를 뱉었습니다. 상태 코드: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        # 백엔드 B 서버가 아예 꺼져있거나 인터넷이 끊긴 경우
        print(f"🚨 [연결 실패] Backend B 서버에 접속할 수 없습니다. (아직 안 켜진 것 같습니다.)")
        return False