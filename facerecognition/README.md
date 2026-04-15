# Team C16 - Kamera (Face Recognition System)

A real-time face recognition system using a Raspberry Pi for edge detection and a GPU-powered backend for identification.

## Architecture

```
Raspberry Pi (Edge)                    Backend Server (GPU)
┌─────────────────┐                   ┌──────────────────────┐
│ Camera Feed     │                   │                      │
│      ↓          │   WebSocket       │  InsightFace         │
│ Haar Cascade    │ ── face.jpg ────▶ │  (ArcFace on GPU)    │
│ Face Detection  │                   │      ↓               │
│ (CPU, ~20fps)   │ ◀── identity ──── │  Compare embedding   │
│      ↓          │                   │  against face_db     │
│ Crop & Send     │                   │      ↓               │
│ only faces      │                   │  Return identity     │
└─────────────────┘                   └──────────────────────┘
```

## Project Structure

```
team-c16-kamera/
├── raspberry_pi/           # Edge device code (Raspberry Pi)
│   ├── config.py           # Pi configuration
│   ├── face_detector.py    # Haar Cascade face detection
│   ├── camera.py           # Camera capture module
│   ├── sender.py           # WebSocket client to send faces
│   ├── main.py             # Main entry point
│   └── requirements.txt
├── backend/                # Server code (GPU machine)
│   ├── config.py           # Server configuration
│   ├── face_recognizer.py  # InsightFace embedding extraction
│   ├── face_database.py    # Embedding storage & search
│   ├── api.py              # FastAPI REST + WebSocket server
│   ├── download_models.py  # Download InsightFace models
│   └── requirements.txt
├── scripts/                # Utility scripts
│   ├── enroll_face.py      # Scan & enroll face via webcam
│   └── test_recognition.py # Test recognition pipeline
└── models/                 # Model files (auto-downloaded)
```

## Quick Start

### 1. Backend Setup (GPU Server)

```bash
cd backend
pip install -r requirements.txt
python download_models.py
python api.py
```

### 2. Enroll Faces

```bash
cd scripts
python enroll_face.py --name "Ali Yilmaz" --captures 8
```

### 3. Raspberry Pi Setup

```bash
cd raspberry_pi
pip install -r requirements.txt
# Edit config.py with your backend server IP
python main.py
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/enroll` | Enroll a new face with images |
| POST | `/recognize` | Recognize a face from image |
| GET | `/people` | List all enrolled people |
| DELETE | `/people/{name}` | Remove a person |
| WS | `/ws` | Real-time face recognition stream |

## Tech Stack

- **Face Detection (CPU):** OpenCV Haar Cascades (frontal face)
- **Face Recognition (GPU):** InsightFace with ArcFace (buffalo_l)
- **Backend Framework:** FastAPI
- **Communication:** WebSocket + REST API
- **Database:** JSON file (upgradeable to PostgreSQL + pgvector)
