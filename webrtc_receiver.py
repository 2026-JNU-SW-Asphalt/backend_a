import time
import datetime
import uuid
from streamlit_webrtc import VideoProcessorBase
from frame_sampler import should_sample, optimize_frame
from dummy_interfaces import mock_ai_inference, send_to_backend_b

# (JSON 포장 전용 함수는 올려주신 그대로 완벽합니다!)
def build_detection_json(session_id, current_time, gps_data, detections):
    """
    백엔드 B와의 계약(API 명세서)에 정확히 맞춰서 파이썬 딕셔너리(JSON)를 조립합니다.
    """
    timestamp_str = datetime.datetime.fromtimestamp(current_time, tz=datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    is_valid_gps = True
    if not gps_data or gps_data.get("lat") is None or gps_data.get("lng") is None:
        is_valid_gps = False
        gps_data = {"lat": 0.0, "lng": 0.0} 

    final_json = {
        "source": "backend_a",
        "session_id": session_id,
        "timestamp": timestamp_str,
        "gps": {
            "lat": gps_data["lat"],
            "lng": gps_data["lng"]
        },
        "detections": detections, 
        "is_valid_gps": is_valid_gps
    }
    
    return final_json


class PotholeVideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.last_sample_time = 0.0
        self.interval = 1.0 # 1초에 1장!
        self.session_id = f"ses_{uuid.uuid4().hex[:8]}" 
        
        # 👇 [추가 1] 외부에서 진짜 GPS를 받아둘 '주머니'를 만듭니다. (기본값 세팅)
        self.current_gps = {"lat": 35.1595, "lng": 126.8526} 

    # 👇 [추가 2] app.py가 브라우저에서 읽어온 위치를 1초마다 여기로 밀어넣어 줍니다.
    def set_gps_data(self, gps_data):
        self.current_gps = gps_data

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        current_time = time.time()

        # 1초가 지났을 때만 실행!
        if should_sample(self.last_sample_time, current_time, self.interval):
            self.last_sample_time = current_time
            optimized_img = optimize_frame(img)
            
            # [Step 1] AI에게 사진을 주고 Detection 알맹이 받아오기
            detections = mock_ai_inference(optimized_img)
            
            # ❌ [삭제] 아까 있던 고정된 임시 좌표(current_gps = {...})는 지웠습니다!
            
            # [Step 2] JSON 상자 예쁘게 포장하기 📦
            # 👇 [변경] 새로 만든 주머니(self.current_gps)를 통째로 넣습니다.
            detection_json = build_detection_json(
                session_id=self.session_id, 
                current_time=current_time, 
                gps_data=self.current_gps,  # <--- 진짜 위도/경도가 들어갑니다!
                detections=detections
            )
            
            # [Step 3] 포장된 상자를 백엔드 B로 배송(전송)하기 🚀
            send_to_backend_b(detection_json)
            print(f"\n📦 [생성된 JSON]: {detection_json}")

        return frame