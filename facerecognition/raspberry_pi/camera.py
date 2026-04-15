"""
Camera module for Raspberry Pi.
Handles camera initialization, frame capture, and cleanup.
Supports both USB cameras and Raspberry Pi Camera Module.
"""

import cv2
import time
from config import CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS


class Camera:
    """
    Camera wrapper with auto-reconnect and frame rate management.
    """

    def __init__(self, index=None, width=None, height=None, fps=None):
        self.index = index or CAMERA_INDEX
        self.width = width or CAMERA_WIDTH
        self.height = height or CAMERA_HEIGHT
        self.fps = fps or CAMERA_FPS
        self.cap = None
        self._connect()

    def _connect(self):
        """Initialize or reconnect the camera."""
        if self.cap is not None:
            self.cap.release()

        print(f"[Camera] Connecting to camera {self.index}...")
        self.cap = cv2.VideoCapture(self.index)

        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open camera {self.index}")

        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)

        # Read actual settings
        actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        print(f"[Camera] Connected: {actual_w}x{actual_h} @ {actual_fps}fps")

    def read(self):
        """
        Read a frame from the camera.

        Returns:
            frame: BGR image (numpy array), or None if read failed
        """
        if self.cap is None or not self.cap.isOpened():
            try:
                self._connect()
            except RuntimeError:
                return None

        ret, frame = self.cap.read()

        if not ret:
            print("[Camera] Frame read failed, attempting reconnect...")
            time.sleep(1)
            try:
                self._connect()
            except RuntimeError:
                pass
            return None

        return frame

    def release(self):
        """Release the camera resource."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            print("[Camera] Released")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False
