import cv2
from PIL import Image
import logging

class VideoProcessor:
    def __init__(self, video_path):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.frame_count / self.fps
        
        logging.info(f"Video loaded: {video_path} | FPS: {self.fps} | Duration: {self.duration:.2f}s")

    def get_frame_at_time(self, timestamp):
        """
        Retrieves a frame at a specific timestamp (in seconds).
        Returns PIL Image.
        """
        frame_number = int(timestamp * self.fps)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        # Optimization: Resize directly to CLIP input size (224x224)
        # This is the fastest possible approach as it minimizes data transfer and PIL conversion overhead
        frame = cv2.resize(frame, (224, 224))
        
        # Convert BGR (OpenCV) to RGB (PIL)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(frame_rgb)

    def close(self):
        self.cap.release()
