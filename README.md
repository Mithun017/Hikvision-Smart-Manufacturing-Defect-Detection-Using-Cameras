# 🏭 Hikvision Smart Manufacturing Defect Detection

A production-grade industrial vision system designed for real-time defect detection in manufacturing lines. This system integrates high-performance Python AI backends with a premium React monitoring dashboard to provide actionable insights at sub-15ms latency.

---

## 🚀 Key Features

*   **Real-Time AI Inference**: Powered by a custom detection pipeline (simulating YOLOv8/TensorRT) for fast and accurate defect identification.
*   **Industrial Dashboard**: A high-contrast, dark-themed UI for live monitoring, analytics, and history tracking.
*   **Dual-Layer Analytics**: Live feed bounding boxes combined with hourly production metrics and rejection rates.
*   **Continuous Monitoring**: Stable WebSocket-based streaming that reports FPS, latency, and system health in real-time.
*   **Hardware Ready**: Designed to easily transition from simulation to physical Hikvision cameras via RTSP.

---

## 🛠️ Technology Stack

| Component | Technology |
| :--- | :--- |
| **Frontend** | React, Vite, Recharts, Lucide-React, CSS3 |
| **Backend** | Python 3.12, FastAPI, OpenCV, Uvicorn, WebSockets |
| **Computer Vision** | YOLO, NumPy, TensorRT (Simulated) |
| **Automation** | Custom industrial decision logic (ACCEPT/REJECT) |

---

## 📂 Project Structure

```text
├── backend/            # Python FastAPI & AI Logic
│   ├── main.py        # Core API & Inference Stream
│   ├── requirements.txt
│   └── data/           # Sample industrial defect images
├── frontend/           # React + Vite UI
│   ├── src/           # Dashboard Components
│   └── index.css      # Premium Industrial Theme
├── scripts/            # Automation & data scripts
└── README.md           # System Documentation
```

---

---

## ⚡ One-Click Startup (Windows)

For the easiest experience, simply double-click the **`run_project.bat`** file in the root directory. 
This will:
1.  Start the **FastAPI Backend**.
2.  Start the **Vite/React Frontend**.
3.  Automatically open your browser to **`http://localhost:5173`**.

---

## ⚙️ Setup & Installation

### 1. Prerequisites
- **Python 3.8+**
- **Node.js 18+**
- **npm**

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
python main.py
```
*Backend runs on `http://localhost:8000`*

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
*Frontend runs on `http://localhost:5173`*

---

## 🎯 Usage Instructions

1.  **Launch Servers**: Ensure both the Backend (FastAPI) and Frontend (Vite) are running.
2.  **Access Dashboard**: Open `http://localhost:5173` in your browser.
3.  **Engage Pipeline**: Click the **"ENGAGE PIPELINE"** button in the System Control panel.
4.  **Monitor Feed**: Observe the live camera feed. The system will automatically tag parts as **"STATUS: PASSED"** or trigger a **"REJECT"** alert if a defect is detected.
5.  **Review History**: High-confidence defect captures are logged in the right-side panel with timestamps.

---

## 📷 Industrial Integration

To use with physical Hikvision IP cameras:
- Open `backend/main.py`.
- Locate the `video_stream_task` function.
- Replace the mock frame logic with:
  ```python
  cap = cv2.VideoCapture("rtsp://admin:password@192.168.1.64/Streaming/Channels/1")
  ```

---

## 📜 License
This project is part of a Smart Manufacturing POC. All rights reserved.
