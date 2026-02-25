import cv2
import numpy as np

from app.operators.base import BaseOperator


class ChannelSplit(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        channel_str = str(self.params.get("channel", "RED")).upper()
        
        channel_idx = 2  # RED (Default)
        if channel_str == "BLUE":
            channel_idx = 0
        elif channel_str == "GREEN":
            channel_idx = 1
            
        # Return image as-is if it's already single-channel/grayscale
        if len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] == 1):
            return image
            
        # Split channels if image has 3 or more channels (e.g. BGR or BGRA)
        if len(image.shape) == 3 and image.shape[2] >= 3:
            channels = cv2.split(image)
            return channels[channel_idx]
            
        return image
