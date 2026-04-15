"""
Raspberry Pi Configuration
"""

# ---- Backend Server ----
BACKEND_HOST = "192.168.1.100"  # Change to your backend server IP
BACKEND_PORT = 8000
BACKEND_WS_URL = f"ws://{BACKEND_HOST}:{BACKEND_PORT}/ws"
BACKEND_HTTP_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"

# ---- Camera ----
CAMERA_INDEX = 0            # 0 for default camera, or path like "/dev/video0"
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# ---- Face Detection (Haar Cascade) ----
# Scale factor: how much the image size is reduced at each scale (lower = more accurate but slower)
DETECTION_SCALE_FACTOR = 1.2    # 1.1 = very accurate/slow, 1.3 = fast/less accurate

# Min neighbors: how many neighbors each candidate rectangle should have (higher = fewer false positives)
DETECTION_MIN_NEIGHBORS = 5     # 3 = more detections, 7 = stricter filtering

# ---- Processing ----
SEND_INTERVAL = 1.0         # Minimum seconds between sending frames to backend
FACE_PADDING = 20           # Extra pixels around detected face crop
JPEG_QUALITY = 85           # JPEG compression quality (lower = smaller file)
MIN_FACE_SIZE = 60          # Minimum face size in pixels (width or height)
