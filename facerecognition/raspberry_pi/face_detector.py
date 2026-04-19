"""
Face Detector using OpenCV Haar Cascades.
Optimized for CPU execution on Raspberry Pi.

Best for: Frontal face detection (person looking at camera)
- Ultra-fast on CPU (~15-25 FPS on Pi 4)
- Built into OpenCV, no extra model downloads needed
- Low memory footprint (~10 MB)
"""

import cv2
try:
    from config import (
        DETECTION_SCALE_FACTOR,
        DETECTION_MIN_NEIGHBORS,
        FACE_PADDING,
        MIN_FACE_SIZE,
    )
except ImportError:
    from .config import (
        DETECTION_SCALE_FACTOR,
        DETECTION_MIN_NEIGHBORS,
        FACE_PADDING,
        MIN_FACE_SIZE,
    )


class FaceDetector:
    """
    CPU-optimized face detector using Haar Cascade classifier.
    Ideal for frontal face detection on Raspberry Pi.
    """

    def __init__(self):
        # Load built-in Haar Cascade - no download needed!
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

        if self.face_cascade.empty():
            raise RuntimeError(f"Failed to load Haar Cascade from {cascade_path}")

        print("[FaceDetector] Initialized with Haar Cascade (CPU)")
        print(f"[FaceDetector] Scale Factor: {DETECTION_SCALE_FACTOR}")
        print(f"[FaceDetector] Min Neighbors: {DETECTION_MIN_NEIGHBORS}")

    def detect(self, frame):
        """
        Detect frontal faces in a frame.

        Args:
            frame: BGR image (numpy array) from camera

        Returns:
            list of dicts, each containing:
                - 'box': (x1, y1, x2, y2) bounding box
                - 'confidence': 1.0 (Haar doesn't provide confidence)
                - 'face': cropped face image (numpy array)
        """
        h, w = frame.shape[:2]

        # Convert to grayscale (Haar works on grayscale)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Equalize histogram for better detection under varying lighting
        gray = cv2.equalizeHist(gray)

        # Detect faces
        detections = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=DETECTION_SCALE_FACTOR,
            minNeighbors=DETECTION_MIN_NEIGHBORS,
            minSize=(MIN_FACE_SIZE, MIN_FACE_SIZE),
            flags=cv2.CASCADE_SCALE_IMAGE,
        )

        faces = []
        for (x, y, fw, fh) in detections:
            # Add padding around face
            x1 = max(0, x - FACE_PADDING)
            y1 = max(0, y - FACE_PADDING)
            x2 = min(w, x + fw + FACE_PADDING)
            y2 = min(h, y + fh + FACE_PADDING)

            # Crop face region (from original BGR frame, not grayscale)
            face_img = frame[y1:y2, x1:x2].copy()

            faces.append({
                "box": (x1, y1, x2, y2),
                "confidence": 1.0,
                "face": face_img,
            })

        return faces

    def draw_detections(self, frame, faces):
        """
        Draw bounding boxes on frame (for debugging).

        Args:
            frame: Original frame
            faces: List of detection dicts from detect()

        Returns:
            Frame with drawn detections
        """
        display = frame.copy()
        for face in faces:
            x1, y1, x2, y2 = face["box"]

            # Draw bounding box
            cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Draw "FACE" label
            label_y = y1 - 10 if y1 - 10 > 10 else y1 + 20
            cv2.putText(
                display, "FACE", (x1, label_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2,
            )

        return display
