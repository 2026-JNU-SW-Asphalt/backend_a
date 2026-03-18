import cv2

def should_sample(last_sample_time, current_time, interval=1.0):
    # 이전 시간과 현재 시간을 비교해서 1초(interval)가 지났는지 확인합니다.
    return (current_time - last_sample_time) >= interval

def optimize_frame(image_array, size=(640, 640)):
    # AI가 분석하기 좋게, 그리고 인터넷 데이터 낭비가 없게 사진 크기를 줄입니다.
    return cv2.resize(image_array, size)