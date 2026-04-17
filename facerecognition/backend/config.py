"""
Backend Server Configuration
"""

import os

# ---- Server ----
HOST = "0.0.0.0"
PORT = 8000

# ---- Face Recognition ----
# InsightFace model pack: "buffalo_l" (high accuracy), "buffalo_s" (faster, lower accuracy)
INSIGHTFACE_MODEL = "buffalo_l"

# GPU device ID (0 = first GPU, -1 = CPU)
GPU_DEVICE_ID = -1  # -1 = CPU (for laptop testing), 0 = first GPU

# Detection size for InsightFace (used during enrollment)
DETECTION_SIZE = (640, 640)

# ---- Recognition Thresholds ----
# Cosine similarity threshold for positive match (higher = stricter)
RECOGNITION_THRESHOLD = 0.4

# ---- Face Database ----
# Path to the face embeddings database
FACE_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "face_db.json")

# Directory for storing enrolled face images (for reference)
ENROLLED_FACES_DIR = os.path.join(os.path.dirname(__file__), "data", "enrolled_faces")

# ---- Enrollment ----
MIN_ENROLLMENT_IMAGES = 3      # Minimum images needed to enroll a person
MAX_ENROLLMENT_IMAGES = 15     # Maximum images per enrollment
