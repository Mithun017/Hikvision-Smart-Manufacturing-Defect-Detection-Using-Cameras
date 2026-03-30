import cv2
import numpy as np
import os
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import asyncio
import json
import base64
import time
from datetime import datetime
from ultralytics import YOLO

# Initialize FastAPI
app = FastAPI(title="Hikvision Smart Vision Defect Detection")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State
class SystemState:
    def __init__(self):
        self.is_running = False
        self.fps = 0
        self.latency = 0
        self.total_inspected = 0
        self.defects_detected = 0
        self.last_detection = None
        self.detection_history = []
        self.threshold = 0.5
        self.mode = "Demo"  # Demo, Video, or Live
        self.video_source: Optional[str] = None
        self.is_video_mode = False
        self.last_item_seen_time = 0.0

state = SystemState()
DATASET_PATH = Path("../Test dataset")

# Real YOLOv8 Detector
class YOLOv8DefectDetector:
    def __init__(self, model_path='industrial_vision.pt'):
        try:
            self.model = YOLO(model_path)
            print(f"DEBUG: YOLO model loaded from {model_path}")
        except Exception as e:
            print(f"ERROR: Failed to load YOLO: {e}")
            self.model = None
            
        # Mock background for fallback
        self.clean_img = cv2.imread('data/sample_images/clean.png')
        self.defect_img = cv2.imread('data/sample_images/defective.png')
        self.video_cap = None

    def set_video_source(self, path: str):
        if self.video_cap:
            self.video_cap.release()
        self.video_cap = cv2.VideoCapture(path)

    def run_inference(self, frame):
        # Fallback if no frame is provided
        if frame is None:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "NO SIGNAL", (220, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
        start_time = time.time()
        detections = []
        status = "OK"

        if self.model:
            # Real YOLO Inference
            results = self.model(frame, verbose=False)[0]
            for box in results.boxes:
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                xyxy = box.xyxy[0].tolist()
                label = results.names[cls]
                
                if label == 'defective':
                    status = "REJECT"
                elif label == 'clean' and conf < 0.80:
                    status = "REJECT"
                    label = "anomaly"

                detections.append({
                    "class": label,
                    "confidence": conf,
                    "bbox": [int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])]
                })
                
                # Visuals on frame
                color = (0, 0, 255) if status == 'REJECT' else (0, 255, 0)
                cv2.rectangle(frame, (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3])), color, 2)
                cv2.putText(frame, f"{label} {conf:.2f}", (int(xyxy[0]), int(xyxy[1])-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        else:
            # Fallback mock logic if YOLO failed to load
            pass

        latency = (time.time() - start_time) * 1000
        return frame, detections, status, latency

detector = YOLOv8DefectDetector()

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# Background Processing Task
async def video_stream_task():
    global state
    # Sample video or mock frames
    # Real: cap = cv2.VideoCapture("rtsp://admin:password@192.168.1.104:554/Streaming/Channels/1")
    
    # Mock frame generator or Video Reader
    while state.is_running:
        frame = None
        
        if detector.video_cap is None or not detector.video_cap.isOpened():
            if state.is_video_mode and state.video_source:
                detector.set_video_source(state.video_source)
            else:
                detector.set_video_source(0) # Live Webcam
        
        if detector.video_cap and detector.video_cap.isOpened():
            ret, video_frame = detector.video_cap.read()
            if not ret and state.is_video_mode and state.video_source:
                # Loop video
                detector.set_video_source(state.video_source)
                ret, video_frame = detector.video_cap.read()
            
            if ret:
                frame = cv2.resize(video_frame, (640, 480))
        
        # Run Inference
        processed_frame, detections, status, latency = detector.run_inference(frame)
        
        # Update State - Debounce counting
        current_time = time.time()
        has_item = len(detections) > 0
        
        if has_item and (current_time - state.last_item_seen_time > 1.0):
            state.total_inspected += 1
            if status == "REJECT":
                state.defects_detected += 1
                state.last_detection = {
                    "timestamp": datetime.now().isoformat(),
                    "type": detections[0]['class'],
                    "confidence": detections[0]['confidence']
                }
                state.detection_history.append(state.last_detection)
                if len(state.detection_history) > 50:
                    state.detection_history.pop(0)
            state.last_item_seen_time = current_time

        # Encode frame to base64
        _, buffer = cv2.imencode('.jpg', processed_frame)
        jpg_as_text = base64.b64encode(buffer).decode('utf-8')
        
        # Broadcast via WebSocket
        data = {
            "image": jpg_as_text,
            "status": status,
            "detections": detections,
            "source": os.path.basename(state.video_source) if state.is_video_mode else "Live Demo",
            "stats": {
                "total": state.total_inspected,
                "defects": state.defects_detected,
                "latency": f"{latency:.2f}ms",
                "fps": 15 # Simulated
            }
        }
        
        await manager.broadcast(json.dumps(data))
        await asyncio.sleep(1/15) # 15 FPS

# Endpoints
@app.get("/status")
async def get_status():
    return {
        "status": "online" if state.is_running else "standby",
        "mode": state.mode,
        "total_inspected": state.total_inspected,
        "defects_detected": state.defects_detected,
        "reject_rate": f"{(state.defects_detected / max(1, state.total_inspected)) * 100:.2f}%"
    }

@app.post("/control/start")
async def start_system(background_tasks: BackgroundTasks):
    if not state.is_running:
        state.is_running = True
        background_tasks.add_task(video_stream_task)
    return {"message": "System started"}

@app.post("/control/stop")
async def stop_system():
    state.is_running = False
    return {"message": "System stopped"}

@app.get("/videos/list")
async def list_videos():
    try:
        videos = [f for f in os.listdir(DATASET_PATH) if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]
        return {"videos": videos}
    except Exception as e:
        return {"videos": [], "error": str(e)}

@app.post("/videos/select")
async def select_video(filename: str):
    video_path = str(DATASET_PATH / filename)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video not found")
    
    state.video_source = video_path
    state.is_video_mode = True
    state.mode = "Video"
    
    # Set the video source on the detector so it's ready
    detector.set_video_source(video_path)
    print(f"DEBUG: Source changed to {video_path}")
    
    return {"message": f"Selected video: {filename}"}

@app.post("/control/mode/demo")
async def set_demo_mode():
    state.is_video_mode = False
    state.mode = "Demo"
    detector.set_video_source(0)
    return {"message": "Switched to Demo mode"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text() # Keep alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
