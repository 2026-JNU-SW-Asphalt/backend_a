import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from webrtc_receiver import PotholeVideoProcessor

st.set_page_config(page_title="포트홀 관제 - Edge Input", layout="centered")

st.title("📱 스마트폰 입력 Edge (PoC)")
st.markdown("스마트폰 카메라는 영상만 보내고, 서버가 **1초마다 1장씩 샘플링**하여 결과를 처리합니다.")
st.success("💡 카메라는 웹 화면에 나오고, 1초마다 생성되는 JSON 로그는 VS Code의 [터미널] 창에서 확인하세요!")

# 카메라 화면 띄우기 (더 이상 여기서 무한 반복문을 돌리지 않습니다)
webrtc_streamer(
    key="pothole-cam",
    mode=WebRtcMode.SENDRECV,
    video_processor_factory=PotholeVideoProcessor,
    media_stream_constraints={"video": True, "audio": False},
    async_processing=True
)