"""
Event Logger module for the Smart Surveillance System.

This module handles logging of detection events and performance metrics
to structured JSON Lines format files.
"""

import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Detection, MotionRegion, PerformanceMetrics


class EventLogger:
    """
    Records detection events to structured log files.
    
    Uses JSON Lines format where each line is a complete JSON object.
    Implements daily log rotation and size-based rotation.
    """
    
    def __init__(
        self,
        log_directory: str,
        max_file_size_mb: int = 10,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize event logger.
        
        Args:
            log_directory: Directory for log files
            max_file_size_mb: Maximum size before log rotation (in MB)
            logger: Logger instance for error reporting
        """
        self.log_directory = Path(log_directory)
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.logger = logger or logging.getLogger(__name__)
        
        self._log_file = None
        self._current_log_path = None
        self._current_date = None
        self._buffer = []
        self._buffer_size = 10  # Flush after 10 events
        
        # Create log directory if it doesn't exist
        try:
            self.log_directory.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Log directory created/verified: {self.log_directory}")
        except Exception as e:
            self.logger.error(f"Failed to create log directory: {e}")
            raise
        
        # Initialize log file
        self._rotate_if_needed()
    
    def log_object_detection(self, detection: Detection):
        """
        Log an object detection event.
        
        Args:
            detection: Detection object to log
        """
        event = {
            "timestamp": detection.timestamp.isoformat(),
            "event_type": "object_detection",
            "class": detection.class_name,
            "confidence": detection.confidence,
            "bbox": {
                "x": detection.bbox.x,
                "y": detection.bbox.y,
                "width": detection.bbox.width,
                "height": detection.bbox.height
            }
        }
        
        self._write_event(event)
    
    def log_motion_detection(self, motion: MotionRegion):
        """
        Log a motion detection event.
        
        Args:
            motion: MotionRegion object to log
        """
        event = {
            "timestamp": motion.timestamp.isoformat(),
            "event_type": "motion_detection",
            "area": motion.area,
            "bbox": {
                "x": motion.bbox.x,
                "y": motion.bbox.y,
                "width": motion.bbox.width,
                "height": motion.bbox.height
            }
        }
        
        self._write_event(event)
    
    def log_performance_metrics(self, metrics: PerformanceMetrics):
        """
        Log performance statistics.
        
        Args:
            metrics: PerformanceMetrics object to log
        """
        event = {
            "timestamp": metrics.timestamp.isoformat(),
            "event_type": "performance_metrics",
            "current_fps": metrics.current_fps,
            "average_fps": metrics.average_fps,
            "total_frames": metrics.total_frames,
            "total_detections": metrics.total_detections,
            "average_processing_time_ms": metrics.average_processing_time_ms
        }
        
        self._write_event(event)
    
    def _write_event(self, event: dict):
        """
        Write an event to the log file.
        
        Args:
            event: Event dictionary to write
        """
        try:
            # Check if we need to rotate (new day or size limit)
            self._rotate_if_needed()
            
            # Add to buffer
            self._buffer.append(event)
            
            # Flush if buffer is full
            if len(self._buffer) >= self._buffer_size:
                self._flush_buffer()
                
        except Exception as e:
            # Log to stderr and continue operation
            print(f"Error writing event to log: {e}", file=sys.stderr)
            self.logger.error(f"Failed to write event: {e}")
    
    def _flush_buffer(self):
        """Flush buffered events to file."""
        if not self._buffer:
            return
        
        try:
            if self._log_file is None:
                self._open_log_file()
            
            # Write all buffered events
            for event in self._buffer:
                json_line = json.dumps(event) + '\n'
                self._log_file.write(json_line)
            
            # Flush to disk
            self._log_file.flush()
            
            # Clear buffer
            self._buffer.clear()
            
        except Exception as e:
            print(f"Error flushing log buffer: {e}", file=sys.stderr)
            self.logger.error(f"Failed to flush log buffer: {e}")
    
    def _rotate_if_needed(self):
        """Check if log rotation is needed and perform it."""
        current_date = datetime.now().date()
        
        # Check if we need to rotate due to date change
        if self._current_date != current_date:
            self._rotate_log_file(current_date)
            return
        
        # Check if we need to rotate due to size limit
        if self._current_log_path and self._current_log_path.exists():
            file_size = self._current_log_path.stat().st_size
            if file_size >= self.max_file_size_bytes:
                self._rotate_log_file(current_date, size_rotation=True)
    
    def _rotate_log_file(self, date: datetime.date, size_rotation: bool = False):
        """
        Rotate to a new log file.
        
        Args:
            date: Date for the new log file
            size_rotation: Whether this is a size-based rotation
        """
        # Flush any pending events
        self._flush_buffer()
        
        # Close current log file
        if self._log_file is not None:
            self._log_file.close()
            self._log_file = None
        
        # Update current date
        self._current_date = date
        
        # Generate new log file name
        if size_rotation:
            # Add sequence number for size-based rotation
            sequence = 1
            while True:
                filename = f"surveillance_{date.isoformat()}_{sequence:03d}.jsonl"
                log_path = self.log_directory / filename
                if not log_path.exists():
                    break
                sequence += 1
        else:
            filename = f"surveillance_{date.isoformat()}.jsonl"
            log_path = self.log_directory / filename
        
        self._current_log_path = log_path
        
        # Open new log file
        self._open_log_file()
        
        self.logger.info(f"Rotated to new log file: {self._current_log_path}")
    
    def _open_log_file(self):
        """Open the current log file for writing."""
        try:
            self._log_file = open(self._current_log_path, 'a', encoding='utf-8')
        except Exception as e:
            print(f"Error opening log file: {e}", file=sys.stderr)
            self.logger.error(f"Failed to open log file: {e}")
            raise
    
    def close(self):
        """Flush and close log file."""
        # Flush any remaining events
        self._flush_buffer()
        
        # Close file
        if self._log_file is not None:
            self._log_file.close()
            self._log_file = None
            self.logger.info("Event logger closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures log file is closed."""
        self.close()
        return False
