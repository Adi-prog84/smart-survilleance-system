"""
Snapshot Saver module for the Smart Surveillance System.

This module handles saving frame snapshots when detections occur,
with rate limiting and error handling.
"""

import cv2
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import ProcessedFrame


class SnapshotSaver:
    """
    Saves frame images when detections occur.
    
    Features:
    - Rate limiting to prevent excessive storage usage
    - Automatic directory creation
    - JPEG format with configurable quality
    - Graceful error handling for disk issues
    """
    
    def __init__(
        self,
        output_directory: str,
        enabled: bool = True,
        rate_limit_seconds: float = 1.0,
        jpeg_quality: int = 90,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize snapshot saver.
        
        Args:
            output_directory: Directory for snapshot images
            enabled: Whether snapshot saving is enabled
            rate_limit_seconds: Minimum time between snapshots
            jpeg_quality: JPEG quality (0-100, default 90)
            logger: Logger instance for error reporting
        """
        self.output_directory = Path(output_directory)
        self.enabled = enabled
        self.rate_limit_seconds = rate_limit_seconds
        self.jpeg_quality = jpeg_quality
        self.logger = logger or logging.getLogger(__name__)
        
        self._last_snapshot_time = 0.0
        self._total_snapshots = 0
        self._failed_snapshots = 0
        
        # Create output directory if it doesn't exist
        if self.enabled:
            try:
                self.output_directory.mkdir(parents=True, exist_ok=True)
                self.logger.info(
                    f"Snapshot directory created/verified: {self.output_directory}"
                )
            except Exception as e:
                self.logger.error(f"Failed to create snapshot directory: {e}")
                self.enabled = False
    
    def save_snapshot(self, processed_frame: ProcessedFrame) -> Optional[str]:
        """
        Save a snapshot if rate limit allows.
        
        Args:
            processed_frame: ProcessedFrame with the frame to save
            
        Returns:
            Path to saved file, or None if rate limited or failed
        """
        if not self.enabled:
            return None
        
        # Check rate limit
        current_time = time.time()
        time_since_last = current_time - self._last_snapshot_time
        
        if time_since_last < self.rate_limit_seconds:
            # Rate limited - skip this snapshot
            return None
        
        # Generate filename with timestamp
        timestamp = processed_frame.metadata.timestamp
        filename = self._generate_filename(timestamp)
        filepath = self.output_directory / filename
        
        try:
            # Save frame as JPEG
            success = cv2.imwrite(
                str(filepath),
                processed_frame.original_frame,
                [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality]
            )
            
            if success:
                self._last_snapshot_time = current_time
                self._total_snapshots += 1
                self.logger.debug(f"Snapshot saved: {filepath}")
                return str(filepath)
            else:
                self._failed_snapshots += 1
                self.logger.error(f"Failed to save snapshot: {filepath}")
                return None
                
        except Exception as e:
            self._failed_snapshots += 1
            self.logger.error(f"Exception while saving snapshot: {e}")
            
            # Check if it's a disk space issue
            if "No space left on device" in str(e) or "Disk full" in str(e):
                self.logger.error("Disk full - disabling snapshot saving")
                self.enabled = False
            
            return None
    
    def _generate_filename(self, timestamp: datetime) -> str:
        """
        Generate filename for snapshot.
        
        Format: snapshot_YYYY-MM-DD_HH-MM-SS-mmm.jpg
        
        Args:
            timestamp: Timestamp for the snapshot
            
        Returns:
            Filename string
        """
        # Format: snapshot_2024-01-15_10-30-45-123.jpg
        date_str = timestamp.strftime("%Y-%m-%d")
        time_str = timestamp.strftime("%H-%M-%S")
        ms_str = f"{timestamp.microsecond // 1000:03d}"
        
        return f"snapshot_{date_str}_{time_str}-{ms_str}.jpg"
    
    def enable(self):
        """Enable snapshot saving."""
        if not self.enabled:
            # Try to create directory again
            try:
                self.output_directory.mkdir(parents=True, exist_ok=True)
                self.enabled = True
                self.logger.info("Snapshot saving enabled")
            except Exception as e:
                self.logger.error(f"Failed to enable snapshot saving: {e}")
    
    def disable(self):
        """Disable snapshot saving."""
        self.enabled = False
        self.logger.info("Snapshot saving disabled")
    
    def get_statistics(self) -> dict:
        """
        Get snapshot statistics.
        
        Returns:
            Dictionary with total and failed snapshot counts
        """
        return {
            "total_snapshots": self._total_snapshots,
            "failed_snapshots": self._failed_snapshots,
            "success_rate": (
                self._total_snapshots / (self._total_snapshots + self._failed_snapshots)
                if (self._total_snapshots + self._failed_snapshots) > 0
                else 0.0
            )
        }
