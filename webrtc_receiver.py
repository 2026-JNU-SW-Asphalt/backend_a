import time
import datetime
import uuid
from streamlit_webrtc import VideoProcessorBase
from frame_sampler import should_sample, optimize_frame
from dummy_interfaces import mock_ai_inference, send_to_backend_b

# 👇 새롭게 추가된 'JSON 포장 전용' 함수입니다.
def build_detection_json(session_id, current_time, gps_data, detections):
    """
    백엔드 B와의 계약(API 명세서)에 정확히 맞춰서 파이썬 딕셔너리(JSON)를 조립합니다.
    """
    # 1. 시간 포맷 맞추기 (예: "2026-03-18T15:27:01Z")
    # UTC 기준으로 변환하여 뒤에 Z를 붙여주는 글로벌 표준(ISO 8601) 방식을 씁니다.
    timestamp_str = datetime.datetime.fromtimestamp(current_time, tz=datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # 2. GPS 데이터가 정상적으로 들어왔는지 확인 (위도/경도가 모두 있는지)
    is_valid_gps = True
    if not gps_data or gps_data.get("lat") is None or gps_data.get("lng") is None:
        is_valid_gps = False
        gps_data = {"lat": 0.0, "lng": 0.0} # 에러 방지용 기본값

    # 3. 계약서에 명시된 형태 그대로 딕셔너리(JSON) 생성
    final_json = {
        "source": "backend_a",
        "session_id": session_id,
        "timestamp": timestamp_str,
        "gps": {
            "lat": gps_data["lat"],
            "lng": gps_data["lng"]
        },
        "detections": detections, # AI가 준 리스트 [ {bbox...}, {bbox...} ] 가 그대로 들어갑니다.
        "is_valid_gps": is_valid_gps
    }
    
    return final_json

class PotholeVideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.last_sample_time = 0.0
        self.interval = 1.0 # 1초에 1장!
        self.session_id = f"ses_{uuid.uuid4().hex[:8]}" # 세션 ID도 여기서 관리

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        current_time = time.time()

        # 1초가 지났을 때만 실행!
        if should_sample(self.last_sample_time, current_time, self.interval):
            self.last_sample_time = current_time
            optimized_img = optimize_frame(img)
            
            # [Step 1] AI에게 사진을 주고 Detection 알맹이 받아오기
            detections = mock_ai_inference(optimized_img)
            
            # (임시) 현재는 스마트폰 GPS 연동 전이므로, 광주 좌표를 임시로 넣습니다.
            current_gps = {"lat": 35.1595, "lng": 126.8526}
            
            # [Step 2] 방금 만든 함수로 JSON 상자 예쁘게 포장하기 📦
            detection_json = build_detection_json(
                session_id=self.session_id, 
                current_time=current_time, 
                gps_data=current_gps, 
                detections=detections
            )
            
            # [Step 3] 포장된 상자를 백엔드 B로 배송(전송)하기 🚀
            send_to_backend_b(detection_json)
            print(f"\n📦 [생성된 JSON]: {detection_json}")

        return frame