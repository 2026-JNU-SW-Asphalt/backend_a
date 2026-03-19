import time
import datetime
import uuid
from streamlit_webrtc import VideoProcessorBase
from frame_sampler import should_sample, optimize_frame
from dummy_interfaces import mock_ai_inference, send_to_backend_b

def build_detection_json(session_id, current_time, gps_data, detections):
    """
    [Phase 4: 포장해서 본사로 쏘기]
    백엔드 B 담당자와 약속한 'API 계약서'에 맞춰서 파이썬 딕셔너리(JSON)를 예쁘게 조립하는 공장입니다.
    """
    # 1. Timestamp (시간 도장) 생성
    # 서버 간 통신에서는 한국 시간, 미국 시간 헷갈리지 않게 무조건 'UTC(세계 표준시)'를 씁니다.
    # 포맷 예시: "2026-03-18T15:30:45Z" (뒤에 붙는 Z가 UTC라는 뜻입니다)
    timestamp_str = datetime.datetime.fromtimestamp(current_time, tz=datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # 2. GPS 데이터 안전 검사 (방어 로직)
    # 만약 스마트폰이 터널에 들어가서 GPS를 못 잡았다면? 프로그램이 터지면 안 됩니다.
    # 위도(lat)나 경도(lng)가 비어있으면 임시로 0.0을 넣고, '가짜 GPS'라고 표시(is_valid_gps=False)해 둡니다.
    is_valid_gps = True
    if not gps_data or gps_data.get("lat") is None or gps_data.get("lng") is None:
        is_valid_gps = False
        gps_data = {"lat": 0.0, "lng": 0.0} 

    # 3. 최종 JSON 상자 조립
    # 백엔드 B가 기대하는 모양 그대로 이름표(Key)를 붙여서 데이터를 넣습니다.
    final_json = {
        "source": "backend_a",         # 내가 누구인지 (Edge 장치)
        "session_id": session_id,      # 현재 접속한 스마트폰의 고유 번호
        "timestamp": timestamp_str,    # 사진이 찍힌 정확한 찰나의 시간
        "gps": {
            "lat": gps_data["lat"],    # 진짜 위도
            "lng": gps_data["lng"]     # 진짜 경도
        },
        "detections": detections,      # AI가 찾아낸 포트홀 정보 (bbox, confidence, class)
        "is_valid_gps": is_valid_gps   # 이 GPS가 믿을 만한 진짜인지 여부
    }
    
    return final_json


class PotholeVideoProcessor(VideoProcessorBase):
    """
    [Phase 2 & 3: 영상 수신, 정제, AI 호출]
    1초에 30장씩 쏟아지는 비디오 프레임을 받아내는 튼튼한 수문장(엔진) 클래스입니다.
    """
    def __init__(self):
        # 엔진 시동을 걸 때 기본 세팅을 합니다.
        self.last_sample_time = 0.0  # 마지막으로 사진을 뽑은 시간 기록
        self.interval = 1.0          # 1.0초마다 딱 1장만 뽑겠다! (데이터 다이어트)
        self.session_id = f"ses_{uuid.uuid4().hex[:8]}" # 접속할 때마다 고유한 8자리 명찰 발급
        
        # 외부(app.py)에서 진짜 GPS를 실시간으로 넣어줄 '주머니'를 미리 만들어 둡니다.
        # (기본값은 광주광역시청 인근 좌표)
        self.current_gps = {"lat": 35.1595, "lng": 126.8526} 

    def set_gps_data(self, gps_data):
        """
        app.py가 브라우저(스마트폰)에서 읽어온 진짜 위치를 
        이 함수를 통해 계속해서 업데이트(밀어넣기) 해줍니다.
        """
        self.current_gps = gps_data

    def recv(self, frame):
        """
        카메라가 켜져 있는 동안, 1초에 30번씩 미친 듯이 실행되는 핵심 컨베이어 벨트입니다.
        """
        # 1. 영상 프레임을 파이썬이 다루기 쉬운 이미지 배열(NumPy)로 바꿉니다.
        img = frame.to_ndarray(format="bgr24")
        current_time = time.time()

        # 2. [수문장 역할] 1초가 지났을 때만 아래 로직을 실행합니다! (나머지 29장은 그냥 통과)
        if should_sample(self.last_sample_time, current_time, self.interval):
            self.last_sample_time = current_time       # "지금 사진 1장 뽑았어" 라고 시간 갱신
            optimized_img = optimize_frame(img)        # AI가 먹기 좋게 640x640으로 크기 축소
            
            # 3. [Phase 3] AI에게 사진(optimized_img)을 던져주고 포트홀 분석 결과를 받아옵니다.
            detections = mock_ai_inference(optimized_img)
            
            # 4. [Phase 4] 바로 위에서 만든 공장 함수를 호출해서 JSON 상자를 예쁘게 포장합니다.
            # 이때 주머니(self.current_gps)에 들어있는 가장 따끈따끈한 진짜 위치를 같이 넣습니다!
            detection_json = build_detection_json(
                session_id=self.session_id, 
                current_time=current_time, 
                gps_data=self.current_gps,  
                detections=detections
            )
            
            # 5. 포장된 상자를 백엔드 B(DB 저장소)로 전송합니다.
            send_to_backend_b(detection_json)
            print(f"\n📦 [생성된 JSON]: {detection_json}")

        # Streamlit 화면에 영상을 계속 보여주기 위해 프레임을 그대로 다시 돌려보냅니다.
        return frame