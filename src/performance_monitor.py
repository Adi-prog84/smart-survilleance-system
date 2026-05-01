"""
Performance Monitor module for the Smart Surveillance System.

This module tracks and reports system performance metrics including
frame rate, processing time, and detection counts.
"""

import time
import logging
from collections import deque
from datetime import datetime
from typing import Optional

from .models import PerformanceMetrics


class PerformanceMonitor:
    """
    Tracks and reports system performance metrics.
    
    Features:
    - Current FPS calculation using sliding window
    - Average FPS over longer time period
    - Processing time tracking
    - Detection count tracking
    - Performance warnings when FPS drops
    """
    
    # Sliding window size for FPS calculation
    FPS_WINDOW_SIZE = 30
    
    # Time window for average FPS (seconds)
    AVG_FPS_WINDOW = 60
    
    # FPS threshold for warnings
    LOW_FPS_THRESHOLD = 5.0
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize performance tracking.
        
        Args:
            logger: Logger instance for warnings
        """
        self.logger = logger or logging.getLogger(__name__)
        
        # Frame timing for current FPS (sliding window)
        self._frame_times = deque(maxlen=self.FPS_WINDOW_SIZE)
        
        # Frame timing for average FPS (time-based window)
        self._avg_frame_times = deque()
        
        # Cumulative statistics
        self._total_frames = 0
        self._total_detections = 0
        self._total_processing_time_ms = 0.0
        
        # Start time for average FPS calculation
        self._start_time = time.time()
        
        # Last warning time (to avoid spamming warnings)
        self._last_warning_time = 0.0
    
    def record_frame(self, processing_time_ms: float, detection_count: int):
        """
        Record metrics for a processed frame.
        
        Args:
            processing_time_ms: Time taken to process the frame in milliseconds
            detection_count: Number of objects detected in the frame
        """
        current_time = time.time()
        
        # Record frame time for FPS calculation
        self._frame_times.append(current_time)
        self._avg_frame_times.append(current_time)
        
        # Remove old frames from average window
        cutoff_time = current_time - self.AVG_FPS_WINDOW
        while self._avg_frame_times and self._avg_frame_times[0] < cutoff_time:
            self._avg_frame_times.popleft()
        
        # Update cumulative statistics
        self._total_frames += 1
        self._total_detections += detection_count
        self._total_processing_time_ms += processing_time_ms
        
        # Check for low FPS and generate warning
        current_fps = self.get_current_fps()
        if current_fps < self.LOW_FPS_THRESHOLD:
            # Only warn once per minute to avoid spam
            if current_time - self._last_warning_time > 60:
                self.logger.warning(
                    f"Performance warning: FPS dropped to {current_fps:.1f} "
                    f"(threshold: {self.LOW_FPS_THRESHOLD})"
                )
                self._last_warning_time = current_time
    
    def get_current_fps(self) -> float:
        """
        Get current frame rate using sliding window.
        
        Returns:
            Current FPS, or 0.0 if insufficient data
        """
        if len(self._frame_times) < 2:
            return 0.0
        
        # Calculate FPS from time difference between first and last frame
        time_span = self._frame_times[-1] - self._frame_times[0]
        
        if time_span <= 0:
            return 0.0
        
        # FPS = (number of frames - 1) / time span
        fps = (len(self._frame_times) - 1) / time_span
        
        return fps
    
    def get_average_fps(self) -> float:
        """
        Get average frame rate over last 60 seconds.
        
        Returns:
            Average FPS, or 0.0 if insufficient data
        """
        if len(self._avg_frame_times) < 2:
            return 0.0
        
        # Calculate FPS from time difference between first and last frame
        time_span = self._avg_frame_times[-1] - self._avg_frame_times[0]
        
        if time_span <= 0:
            return 0.0
        
        # FPS = (number of frames - 1) / time span
        fps = (len(self._avg_frame_times) - 1) / time_span
        
        return fps
    
    def get_metrics(self) -> PerformanceMetrics:
        """
        Get comprehensive performance metrics.
        
        Returns:
            PerformanceMetrics object with all statistics
        """
        avg_processing_time = (
            self._total_processing_time_ms / self._total_frames
            if self._total_frames > 0
            else 0.0
        )
        
        return PerformanceMetrics(
            current_fps=self.get_current_fps(),
            average_fps=self.get_average_fps(),
            total_frames=self._total_frames,
            total_detections=self._total_detections,
            average_processing_time_ms=avg_processing_time,
            timestamp=datetime.now()
        )
    
    def reset(self):
        """Reset all statistics."""
        self._frame_times.clear()
        self._avg_frame_times.clear()
        self._total_frames = 0
        self._total_detections = 0
        self._total_processing_time_ms = 0.0
        self._start_time = time.time()
        self.logger.info("Performance monitor reset")
    
    def get_summary(self) -> str:
        """
        Get a human-readable summary of performance metrics.
        
        Returns:
            Formatted string with key metrics
        """
        metrics = self.get_metrics()
        
        return (
            f"Performance Summary:\n"
            f"  Current FPS: {metrics.current_fps:.1f}\n"
            f"  Average FPS: {metrics.average_fps:.1f}\n"
            f"  Total Frames: {metrics.total_frames}\n"
            f"  Total Detections: {metrics.total_detections}\n"
            f"  Avg Processing Time: {metrics.average_processing_time_ms:.1f}ms"
        )
