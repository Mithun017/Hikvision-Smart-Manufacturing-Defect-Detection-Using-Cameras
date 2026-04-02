# 🏭 Hikvision Smart Manufacturing Defect Detection

A production-grade industrial vision system designed for real-time defect detection in manufacturing lines. This system integrates high-performance Python AI backends with a premium React monitoring dashboard to provide actionable insights at sub-15ms latency.

---

## 🚀 Key Features

*   **Real-Time AI Inference**: Powered by a custom trained YOLOv8 model for exact and instantaneous defect identification.
*   **Anomaly Detection Layers**: Rejects low-confidence or unpredicted patterns as anomalies.
*   **Industrial Dashboard**: A high-contrast, dark-themed UI for live monitoring, analytics, and history tracking.
*   **Dual-Layer Analytics**: Live feed bounding boxes combined with hourly production metrics and rejection rates.
*   **Hardware Ready**: Designed to easily transition from simulation to physical Hikvision cameras via RTSP or local Webcams.

---

## 🧠 AI Model & Training System

### What model is used?
This project uses **YOLOv8 Nano (yolov8n.pt)** as its base architecture, which was fine-tuned and exported into a custom weight file: `industrial_vision.pt`. We use the nano version for ultra-fast, single-batch inference (ensuring latency stays below 50ms) which is critical for moving conveyor belts. 

### How is the model trained?
The project includes a fully automated dataset generation and training pipeline located in `backend/train_yolo.py` and `backend/scripts/generate_test_videos.py`. 
1. **Background Extraction**: The script reads sample/mock conveyor belt videos.
2. **Synthetic Defect Injection**: It uses OpenCV contours to find moving items. For 15-25% of the items, it automatically draws synthetic "cracks" (e.g., thick blue lines or red dots).
3. **Automated Bounding Boxes**: The script calculates the YOLO format bounding boxes for every item and writes them to `.txt` files.
4. **Fine-Tuning**: `yolov8n` is then trained for 10 epochs on this perfectly annotated synthetic dataset and exported out as `industrial_vision.pt`.

---

## 🏗️ Detailed Project Workflow

```mermaid
graph TD
    A[Camera / Video Stream] -->|Raw Frames| B(FastAPI Backend)
    B --> C{YOLOv8 Inference}
    C -->|Label: Defective| D[Status: REJECT]
    C -->|Label: Clean| E{Confidence Check}
    E -->|< 80%| F[Status: ANOMALY / REJECT]
    E -->|>= 80%| G[Status: ACCEPT]
    D --> H[State Manager]
    F --> H
    G --> H
    H -->|Debounce Counting| I[WebSocket Server]
    I -->|Base64 & Metrics @ 15FPS| J[React Dashboard]
    J --> K[Live Monitors & Analytics]
```

1. **Vision Acquisition (Camera/Video)**: The Python backend captures frames either from a live Webcam (Camera 0), an RTSP Stream, or a simulated MP4 test dataset.
2. **AI Inference Engine (YOLO)**: Each frame is passed to the Ultralytics YOLO model.
   - If it detects a defect directly, it flags a `REJECT`.
   - If it detects an item as 'clean' but with low confidence (< 80%), our **Anomaly Detection Rule** overrides the model and flags it as a `REJECT` / `anomaly`.
3. **Backend Control System**: The FastAPI backend manages global state, debounces counting (so an item sliding across the screen is only counted once), and packages the annotated Frame into a Base64 string.
4. **WebSocket Streaming**: Frame data, Latency, FPS, Total Counts, and Defect History are streamed at 15 FPS over a WebSocket to the frontend.
5. **Frontend Dashboard**: The React layer parses the WebSocket feed, constantly updating the Production Metrics chart, rendering the base64 image on-screen, and chiming red alerts for rejected items.

---

## ⚡ How to Run the Project

### Option A: Development Mode (One-Click)
For the absolute easiest developer experience, simply double-click the **`run_project.bat`** file in the root directory. 

This will automatically spin up two separate windows:
1.  The **FastAPI Backend**.
2.  The live **Vite/React Frontend** development server.
3.  Your browser will instantly open to **`http://localhost:5173`**.

*(Note: The startup terminal will display in Red (`COLOR 0C`) to indicate the Hikvision industrial theme).*

### Option B: Production Hosted Mode (Standalone)
Because the app is fully configured for production, you can bypass the `.bat` file entirely! The Python backend natively hosts the compiled React UI.
1. Open a terminal inside the `backend/` folder.
2. Run `python main.py`.
3. Navigate to **`http://localhost:8000/`** directly. 

The single Python server handles your WebSockets, routing, APIs, and the visual dashboard all at once!

---

## ⚙️ Manual Setup & Installation

If you prefer to run it manually or deploy it to a Linux server:

### 1. Prerequisites
- **Python 3.8+**
- **Node.js 18+**

### 2. Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # Linux/macOS

pip install -r requirements.txt
python main.py
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 4. Hosting the Frontend inside the Backend
To achieve the "Production Hosted Mode" mentioned above, we use Vite to build the raw HTML/JS/CSS of the dashboard, and then we tell our FastAPI Python server to physically host those HTML files.

**How to update the backend UI:**
1. Navigate to the `frontend/` folder and run the command **`npm run build`**.
2. This compiles the entire React app into a tiny, highly optimized folder called `dist/` (distribution).
3. Simply **copy** that `dist/` folder, navigate to your `backend/` folder, and **paste** it, overwriting the old one.

**How the Code Works:**
Inside `backend/main.py`, we added this crucial line of code:
```python
# Mount frontend static files last so API routes take precedence (imp to handle the dist)
app.mount("/", StaticFiles(directory=str(BASE_DIR / "dist"), html=True), name="frontend")
```
**Why is it added at the bottom?** 
FastAPI evaluates routing from top to bottom. If we placed the `StaticFiles` line at the top, it would aggressively hijack *everything*, and your other custom APIs (like `/status` or `/control/start`) would break and throw `405 Method Not Allowed` errors. 

By placing it at the very bottom, FastAPI processes all API requests first natively. If a request doesn't match an API (e.g. loading the website's root URL), it safely falls back to serving the React `dist` folder!

---

## 🎯 Usage Instructions

1.  **Open Dashboard**: Once running, go to `http://localhost:5173`.
2.  **Select a Dataset Video**: In the left-hand panel, use the dropdown to select one of the `conveyor_xx.mp4` testing videos.
3.  **Engage Pipeline**: Click the **"ENGAGE PIPELINE"** button.
4.  *(Optional)* **Live Demo Mode**: If you want to test the model with your actual physical Webcam, simply click "LIVE DEMO MODE", ensure no video is selected, and engage the pipeline.
5.  **Review the Flow**: Watch as items pass the lens. Valid items increment the "Total Items" count securely. Anomalies/defects are flagged with Red bounding boxes and added to the Defect History log on the right.

---

## 📷 Industrial Hardware Integration

To use with physical Hikvision IP cameras instead of Webcams:
- Open `backend/main.py`.
- Locate the VideoCapture instantiation logic.
- Replace `0` with your camera stream:
  ```python
  detector.set_video_source("rtsp://admin:password@192.168.1.64/Streaming/Channels/1")
  ```

---

## 🏁 Conclusion

This system bridges the gap between raw AI inference and industrial-grade production dashboards. By unifying rapid YOLO detection, customizable anomaly fault-tolerance, and an ultra-low latency WebSocket React UI, it delivers a complete, deployable Quality Assurance pipeline tailored for fast-paced manufacturing lines.

**Developer:** Hikvision - Mithun
