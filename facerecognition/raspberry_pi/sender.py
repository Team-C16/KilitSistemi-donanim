"""
Sender module - handles communication with the backend server.
Supports both WebSocket (real-time) and HTTP (fallback) modes.
"""

import cv2
import json
import time
import base64
import asyncio
import requests
import websockets
from config import BACKEND_WS_URL, BACKEND_HTTP_URL, JPEG_QUALITY


def encode_face(face_img):
    """
    Encode a face image to base64 JPEG string.
    
    Args:
        face_img: BGR numpy array of cropped face
    
    Returns:
        base64 encoded JPEG string
    """
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
    _, buffer = cv2.imencode(".jpg", face_img, encode_params)
    return base64.b64encode(buffer).decode("utf-8")


class WebSocketSender:
    """
    Real-time face sender using WebSocket connection.
    Maintains persistent connection for low-latency communication.
    """

    def __init__(self):
        self.ws = None
        self.connected = False

    async def connect(self):
        """Establish WebSocket connection to backend."""
        try:
            self.ws = await websockets.connect(
                BACKEND_WS_URL,
                ping_interval=20,
                ping_timeout=10,
            )
            self.connected = True
            print(f"[WebSocket] Connected to {BACKEND_WS_URL}")
        except Exception as e:
            self.connected = False
            print(f"[WebSocket] Connection failed: {e}")

    async def send_face(self, face_img, box, confidence, frame_height, face_count):
        """
        Send a detected face to the backend for recognition.

        Args:
            face_img:      Cropped face image (numpy array)
            box:           (x1, y1, x2, y2) bounding box
            confidence:    Detection confidence
            frame_height:  Full frame height in pixels (for proximity rule)
            face_count:    Total faces detected this frame (for anti-tailgating rule)

        Returns:
            dict with recognition result, or None on failure
        """
        if not self.connected:
            await self.connect()
            if not self.connected:
                return None

        try:
            x1, y1, x2, y2 = box
            face_height = y2 - y1
            face_height_ratio = face_height / frame_height if frame_height > 0 else 0.0

            payload = json.dumps({
                "type": "recognize",
                "face": encode_face(face_img),
                "box": list(box),
                "confidence": confidence,
                "face_height_ratio": round(face_height_ratio, 4),
                "face_count": face_count,
                "timestamp": time.time(),
            })

            await self.ws.send(payload)
            response = await asyncio.wait_for(self.ws.recv(), timeout=5.0)
            return json.loads(response)

        except (websockets.exceptions.ConnectionClosed, asyncio.TimeoutError) as e:
            print(f"[WebSocket] Error: {e}, reconnecting...")
            self.connected = False
            return None

    async def send_no_face(self):
        """
        Notify backend that no face is currently in the frame.
        This triggers the Ghost Blink Fix (Security Rule 4) on the backend,
        resetting the consecutive real-frames counter.

        Returns:
            dict with backend acknowledgement, or None on failure
        """
        if not self.connected:
            await self.connect()
            if not self.connected:
                return None

        try:
            payload = json.dumps({
                "type": "no_face",
                "timestamp": time.time(),
            })
            await self.ws.send(payload)
            response = await asyncio.wait_for(self.ws.recv(), timeout=5.0)
            return json.loads(response)

        except (websockets.exceptions.ConnectionClosed, asyncio.TimeoutError) as e:
            print(f"[WebSocket] Error: {e}, reconnecting...")
            self.connected = False
            return None

    async def close(self):
        """Close WebSocket connection."""
        if self.ws:
            await self.ws.close()
            self.connected = False
            print("[WebSocket] Disconnected")


class HTTPSender:
    """
    HTTP-based face sender (fallback mode).
    Simpler but slightly higher latency than WebSocket.
    """

    def __init__(self):
        self.session = requests.Session()
        self.url = f"{BACKEND_HTTP_URL}/recognize"
        print(f"[HTTP] Using endpoint: {self.url}")

    def send_face(self, face_img, box, confidence):
        """
        Send a detected face to the backend via HTTP POST.

        Args:
            face_img: Cropped face image (numpy array)
            box: (x1, y1, x2, y2) bounding box
            confidence: Detection confidence

        Returns:
            dict with recognition result, or None on failure
        """
        try:
            # Encode face as JPEG
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
            _, buffer = cv2.imencode(".jpg", face_img, encode_params)

            files = {"image": ("face.jpg", buffer.tobytes(), "image/jpeg")}
            data = {
                "box": json.dumps(list(box)),
                "confidence": str(confidence),
            }

            response = self.session.post(self.url, files=files, data=data, timeout=5)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"[HTTP] Error: {e}")
            return None

    def close(self):
        """Close HTTP session."""
        self.session.close()
        print("[HTTP] Session closed")
