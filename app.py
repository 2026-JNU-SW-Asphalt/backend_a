import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from webrtc_receiver import PotholeVideoProcessor
from streamlit_js_eval import get_geolocation

st.title("🚦 광주형 포트홀 실시간 관제 (Edge)")
st.write("스마트폰의 GPS 센서를 켭니다...")

# 1. 브라우저(스마트폰)에 GPS 좌표를 요청합니다.
location = get_geolocation()

# 2. GPS 정보를 담을 기본 주머니 (못 잡았을 때를 대비한 임시 좌표)
curr_gps = {"lat": 35.1595, "lng": 126.8526, "mock": True}

# 3. 사용자가 위치 '허용'을 누르면 진짜 좌표로 덮어씌웁니다.
if location:
    curr_gps = {
        "lat": location['coords']['latitude'],
        "lng": location['coords']['longitude'],
        "mock": False
    }
    st.success(f"📍 진짜 GPS 수신 완료: 위도 {curr_gps['lat']:.4f}, 경도 {curr_gps['lng']:.4f}")
else:
    st.warning("⚠️ 아직 GPS를 잡지 못했습니다. 권한을 허용해주세요.")

# 4. 카메라 스트리밍 시작
ctx = webrtc_streamer(
    key="pothole-edge",
    mode=WebRtcMode.SENDRECV,
    video_processor_factory=PotholeVideoProcessor,
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

# 💡 5. 가장 중요한 부분! 카메라가 켜져 있다면, 위에서 찾은 진짜 GPS를 계속 주입합니다.
if ctx.video_processor:
    ctx.video_processor.current_gps = curr_gps