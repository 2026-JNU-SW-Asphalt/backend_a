from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# --- 🤖 가짜 AI 서버 역할 ---
@app.post("/predict")
async def mock_ai_predict(file: UploadFile = File(...)):
    print(f"📸 [AI Mock] 이미지 수신 완료: {file.filename}")
    # 무조건 포트홀 1개를 발견한 것으로 응답
    return {
        "detections": [
            {"bbox": [100, 100, 200, 200], "confidence": 0.98, "class": "pothole"}
        ]
    }

# --- 📊 가짜 백엔드 B 서버 역할 ---
@app.post("/api/detections")
async def mock_backend_b(data: dict):
    print("🚚 [Backend B Mock] 데이터를 받았습니다!")
    print(f"📍 GPS: {data.get('gps')}")
    print(f"🆔 세션 ID: {data.get('session_id')} (타입: {type(data.get('session_id'))})")
    print(f"🖼️ 이미지 포함 여부: {'Yes' if data.get('image') else 'No'}")
    return {"status": "success", "message": "Data saved to mock DB"}

if __name__ == "__main__":
    import uvicorn
    # 8000번 포트에서 가짜 서버들을 실행합니다.
    uvicorn.run(app, host="0.0.0.0", port=8000)