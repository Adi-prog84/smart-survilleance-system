"""
Video capture module for the Smart Surveillance System.

This module provides the VideoCapture class that interfaces with the webcam
hardware and provides frames to the processing pipeline.
"""

import cv2
import logging
from datetime import datetime
from typing import Optional, Tuple
import numpy as np

from .models import FrameMetadata
from .error_handler import ErrorHandler


class VideoCapture:
    """
    Interface with webcam hardware and provide frames to the processing pipeline.
    
    This class wraps OpenCV's VideoCapture functionality with additional features:
    - Frame metadata tracking (frame number, timestamp)
    - Reconnection logic for transient failures
    - Frame validation
    """
    
    def __init__(self, camera_index: int = 0, logger: Optional[logging.Logger] = None):
        """
        Initialize webcam connection.
        
        Args:
            camera_index: Index of the camera device (default: 0 for primary webcam)
            logger: Logger instance for error reporting. If None, creates default logger.
        """
        self.camera_index = camera_index
        self.logger = logger or logging.getLogger(__name__)
        self.error_handler = ErrorHandler(self.logger)
        
        self._capture: Optional[cv2.VideoCapture] = None
        self._frame_number = 0
        self._is_opened = False
        
        # Initialize the webcam connection
        self._initialize_capture()
    
    def _initialize_capture(self) -> None:
        """Initialize the cv2.VideoCapture object."""
        try:
            self._capture = cv2.VideoCapture(self.camera_index)
            
            if self._capture is None or not self._capture.isOpened():
                self._is_opened = False
                self.logger.error(f"Failed to open webcam at index {self.camera_index}")
            else:
                self._is_opened = True
                width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = self._capture.get(cv2.CAP_PROP_FPS)
                self.logger.info(
                    f"Webcam initialized successfully: {width}x{height} @ {fps:.1f} FPS"
                )
        except Exception as e:
            self._is_opened = False
            self.logger.error(f"Exception during webcam initialization: {e}")
    
    def is_opened(self) -> bool:
        """
        Check if webcam is successfully opened.
        
        Returns:
            True if webcam is opened and ready, False otherwise
        """
        return self._is_opened and self._capture is not None and self._capture.isOpened()
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray], Optional[FrameMetadata]]:
        """
        Read a single frame from the webcam.
        
        Returns:
            Tuple containing:
                - success: Whether frame was successfully captured
                - frame: The captured frame as numpy array (BGR format), or None if failed
                - metadata: Frame timestamp and frame number, or None if failed
        """
        if not self.is_opened():
            self.logger.warning("Attempted to read frame from closed webcam")
            return False, None, None
        
        try:
            success, frame = self._capture.read()
            
            if not success or frame is None:
                self.logger.warning(f"Failed to read frame {self._frame_number + 1}")
                # Attempt reconnection for transient failures
                if self._attempt_reconnection():
                    # Try reading again after reconnection
                    success, frame = self._capture.read()
                    if not success or frame is None:
                        return False, None, None
                else:
                    return False, None, None
            
            # Validate frame format
            if not self._validate_frame(frame):
                self.logger.error(f"Invalid frame format at frame {self._frame_number + 1}")
                return False, None, None
            
            # Increment frame counter
            self._frame_number += 1
            
            # Create metadata
            timestamp = datetime.now()
            height, width = frame.shape[:2]
            metadata = FrameMetadata(
                frame_number=self._frame_number,
                timestamp=timestamp,
                width=width,
                height=height
            )
            
            return True, frame, metadata
            
        except Exception as e:
            self.logger.error(f"Exception while reading frame: {e}")
            return False, None, None
    
    def _validate_frame(self, frame: np.ndarray) -> bool:
        """
        Validate that the frame has the correct format.
        
        Args:
            frame: Frame to validate
            
        Returns:
            True if frame is valid, False otherwise
        """
        if frame is None:
            return False
        
        # Check if it's a numpy array
        if not isinstance(frame, np.ndarray):
            return False
        
        # Check if it has 3 dimensions (height, width, channels)
        if len(frame.shape) != 3:
            return False
        
        # Check if it has 3 channels (BGR)
        if frame.shape[2] != 3:
            return False
        
        # Check if dtype is uint8
        if frame.dtype != np.uint8:
            return False
        
        return True
    
    def _attempt_reconnection(self) -> bool:
        """
        Attempt to reconnect to the webcam after a failure.
        
        Returns:
            True if reconnection successful, False otherwise
        """
        self.logger.info("Attempting to reconnect to webcam...")
        
        def reconnect_operation():
            # Release the current capture
            if self._capture is not None:
                self._capture.release()
            
            # Reinitialize
            self._initialize_capture()
            
            if not self.is_opened():
                raise RuntimeError("Failed to reopen webcam")
            
            return True
        
        result = self.error_handler.retry_with_backoff(
            reconnect_operation,
            "Webcam reconnection",
            max_retries=3
        )
        
        return result is not None
    
    def release(self) -> None:
        """
        Release webcam resource.
        
        This should be called when the system shuts down to properly
        release the webcam hardware.
        """
        if self._capture is not None:
            self._capture.release()
            self._is_opened = False
            self.logger.info("Webcam released")
    
    def get_fps(self) -> float:
        """
        Get the webcam's native frame rate.
        
        Returns:
            Frame rate in frames per second, or 0.0 if unavailable
        """
        if not self.is_opened():
            return 0.0
        
        try:
            fps = self._capture.get(cv2.CAP_PROP_FPS)
            # Some webcams return 0 for FPS, default to 30 in that case
            return fps if fps > 0 else 30.0
        except Exception as e:
            self.logger.warning(f"Failed to get FPS: {e}")
            return 0.0
    
    def get_resolution(self) -> Tuple[int, int]:
        """
        Get frame width and height.
        
        Returns:
            Tuple of (width, height) in pixels, or (0, 0) if unavailable
        """
        if not self.is_opened():
            return (0, 0)
        
        try:
            width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            return (width, height)
        except Exception as e:
            self.logger.warning(f"Failed to get resolution: {e}")
            return (0, 0)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures webcam is released."""
        self.release()
        return False
