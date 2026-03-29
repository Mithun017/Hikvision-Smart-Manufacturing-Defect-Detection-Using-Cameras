import cv2
import numpy as np
from fastapi import FastAPI, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import asyncio
import json
import base64
import time
from datetime import datetime

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
        self.mode = "Demo"  # Demo or Live

state = SystemState()

# Mock AI Model (Simulated)
class MockDefectDetector:
    def __init__(self):
        self.clean_img = cv2.imread('data/sample_images/clean.png')
        self.defect_img = cv2.imread('data/sample_images/defective.png')
        if self.clean_img is not None:
            self.clean_img = cv2.resize(self.clean_img, (640, 480))
        if self.defect_img is not None:
            self.defect_img = cv2.resize(self.defect_img, (640, 480))

    def run_inference(self, frame):
        # Simulate defect detection logic
        # For demo, randomly assign defects to 15% of items
        defect_chance = np.random.rand()
        
        # Capture Time
        start_time = time.time()
        
        detections = []
        status = "OK"
        
        # Determine background frame
        if self.clean_img is not None and self.defect_img is not None:
            if defect_chance < 0.15:
                frame = self.defect_img.copy()
            else:
                frame = self.clean_img.copy()
        
        if defect_chance < 0.15: # 15% defect rate
            status = "REJECT"
            defect_types = ['Structural Crack', 'Surface Abrasion', 'Component Chip', 'Oxidation']
            defect = np.random.choice(defect_types)
            
            # Mock bounding box
            h, w, _ = frame.shape
            x1, y1 = np.random.randint(150, w-250), np.random.randint(150, h-250)
            x2, y2 = x1 + np.random.randint(40, 100), y1 + np.random.randint(40, 100)
            
            detections.append({
                "class": defect,
                "confidence": float(np.random.uniform(0.85, 0.99)),
                "bbox": [x1, y1, x2, y2]
            })
            
            # Draw on frame for demonstration
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
            # Add a stylish HUD label
            cv2.rectangle(frame, (x1, y1-30), (x1+180, y1), (0, 0, 255), -1)
            cv2.putText(frame, f"{defect}", (x1+5, y1-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        else:
            # Add a subtle "SCANNING" status for clean items
            cv2.putText(frame, "STATUS: PASSED", (30, 450), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        latency = (time.time() - start_time) * 1000 + np.random.uniform(5, 12) # Add some variable latency
        return frame, detections, status, latency

detector = MockDefectDetector()

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
    
    # Mock frame generator
    while state.is_running:
        # Create a blank grey frame (industrial conveyor look)
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 180
        # Add some texture/grit
        noise = np.random.randint(0, 20, (480, 640, 3), dtype=np.uint8)
        frame = cv2.add(frame, noise)
        
        # Run Mock Inference
        processed_frame, detections, status, latency = detector.run_inference(frame)
        
        # Update State
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

        # Encode frame to base64
        _, buffer = cv2.imencode('.jpg', processed_frame)
        jpg_as_text = base64.b64encode(buffer).decode('utf-8')
        
        # Broadcast via WebSocket
        data = {
            "image": jpg_as_text,
            "status": status,
            "detections": detections,
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
