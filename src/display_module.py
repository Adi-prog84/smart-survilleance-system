"""
Display Module for the Smart Surveillance System.

This module handles rendering the video feed with detection overlays,
alerts, and performance information.
"""

import cv2
import numpy as np
from typing import List

from .models import ProcessedFrame, Alert


class DisplayModule:
    """
    Renders the video feed with detection overlays and information.
    
    Displays:
    - Object detections with green bounding boxes
    - Motion regions with blue bounding boxes
    - Alerts as red banner at top
    - FPS and detection count in top-left corner
    """
    
    # Color constants (BGR format)
    COLOR_OBJECT_DETECTION = (0, 255, 0)  # Green
    COLOR_MOTION = (255, 0, 0)  # Blue
    COLOR_ALERT = (0, 0, 255)  # Red
    COLOR_TEXT = (255, 255, 255)  # White
    COLOR_TEXT_BG = (0, 0, 0)  # Black
    
    # Font settings
    FONT = cv2.FONT_HERSHEY_SIMPLEX
    FONT_SCALE = 0.6
    FONT_THICKNESS = 2
    FONT_SCALE_SMALL = 0.5
    FONT_THICKNESS_SMALL = 1
    
    # Box settings
    BOX_THICKNESS = 2
    
    def __init__(self, window_name: str = "Smart Surveillance"):
        """
        Initialize display window.
        
        Args:
            window_name: Name of the display window
        """
        self.window_name = window_name
        self._window_created = False
    
    def render(
        self,
        processed_frame: ProcessedFrame,
        fps: float,
        alerts: List[Alert] = None
    ):
        """
        Render frame with detection overlays.
        
        Args:
            processed_frame: Frame with detection results
            fps: Current frame rate for display
            alerts: List of active alerts to display
        """
        # Create a copy of the frame to draw on
        display_frame = processed_frame.original_frame.copy()
        
        # Draw motion regions (blue boxes)
        for motion_region in processed_frame.motion_regions:
            self._draw_bounding_box(
                display_frame,
                motion_region.bbox,
                self.COLOR_MOTION,
                label=f"Motion ({motion_region.area}px)"
            )
        
        # Draw object detections (green boxes)
        for detection in processed_frame.object_detections:
            label = f"{detection.class_name} {detection.confidence:.2f}"
            self._draw_bounding_box(
                display_frame,
                detection.bbox,
                self.COLOR_OBJECT_DETECTION,
                label=label
            )
        
        # Draw alerts banner at top if there are alerts
        if alerts and len(alerts) > 0:
            self._draw_alerts_banner(display_frame, alerts)
        
        # Draw performance info (FPS and detection count)
        detection_count = len(processed_frame.object_detections)
        self._draw_performance_info(display_frame, fps, detection_count)
        
        # Create window if not already created
        if not self._window_created:
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            self._window_created = True
        
        # Display the frame
        cv2.imshow(self.window_name, display_frame)
    
    def _draw_bounding_box(
        self,
        frame: np.ndarray,
        bbox,
        color: tuple,
        label: str = None
    ):
        """
        Draw a bounding box on the frame.
        
        Args:
            frame: Frame to draw on (modified in place)
            bbox: BoundingBox object
            color: Color in BGR format
            label: Optional label text to display above box
        """
        # Draw rectangle
        cv2.rectangle(
            frame,
            (bbox.x, bbox.y),
            (bbox.x + bbox.width, bbox.y + bbox.height),
            color,
            self.BOX_THICKNESS
        )
        
        # Draw label if provided
        if label:
            # Calculate text size for background
            (text_width, text_height), baseline = cv2.getTextSize(
                label,
                self.FONT,
                self.FONT_SCALE_SMALL,
                self.FONT_THICKNESS_SMALL
            )
            
            # Draw background rectangle for text
            label_y = bbox.y - 10 if bbox.y > 30 else bbox.y + bbox.height + 20
            cv2.rectangle(
                frame,
                (bbox.x, label_y - text_height - 5),
                (bbox.x + text_width + 5, label_y + baseline),
                color,
                -1  # Filled rectangle
            )
            
            # Draw text
            cv2.putText(
                frame,
                label,
                (bbox.x + 2, label_y - 2),
                self.FONT,
                self.FONT_SCALE_SMALL,
                self.COLOR_TEXT,
                self.FONT_THICKNESS_SMALL,
                cv2.LINE_AA
            )
    
    def _draw_alerts_banner(self, frame: np.ndarray, alerts: List[Alert]):
        """
        Draw red alert banner at top of frame.
        
        Args:
            frame: Frame to draw on (modified in place)
            alerts: List of Alert objects to display
        """
        height, width = frame.shape[:2]
        banner_height = 40
        
        # Draw red banner background
        cv2.rectangle(
            frame,
            (0, 0),
            (width, banner_height),
            self.COLOR_ALERT,
            -1  # Filled
        )
        
        # Combine alert messages
        alert_text = " | ".join([alert.message for alert in alerts])
        
        # Draw alert text
        cv2.putText(
            frame,
            f"ALERT: {alert_text}",
            (10, 25),
            self.FONT,
            self.FONT_SCALE,
            self.COLOR_TEXT,
            self.FONT_THICKNESS,
            cv2.LINE_AA
        )
    
    def _draw_performance_info(
        self,
        frame: np.ndarray,
        fps: float,
        detection_count: int
    ):
        """
        Draw FPS and detection count in top-left corner.
        
        Args:
            frame: Frame to draw on (modified in place)
            fps: Current frame rate
            detection_count: Number of objects detected in current frame
        """
        height, width = frame.shape[:2]
        
        # Prepare info text
        info_lines = [
            f"FPS: {fps:.1f}",
            f"Detections: {detection_count}"
        ]
        
        # Starting position (top-left with some padding)
        x = 10
        y = 30
        line_height = 25
        
        # Draw each line with background
        for i, line in enumerate(info_lines):
            current_y = y + (i * line_height)
            
            # Calculate text size for background
            (text_width, text_height), baseline = cv2.getTextSize(
                line,
                self.FONT,
                self.FONT_SCALE_SMALL,
                self.FONT_THICKNESS_SMALL
            )
            
            # Draw semi-transparent background
            overlay = frame.copy()
            cv2.rectangle(
                overlay,
                (x - 5, current_y - text_height - 5),
                (x + text_width + 5, current_y + baseline + 5),
                self.COLOR_TEXT_BG,
                -1
            )
            cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
            
            # Draw text
            cv2.putText(
                frame,
                line,
                (x, current_y),
                self.FONT,
                self.FONT_SCALE_SMALL,
                self.COLOR_TEXT,
                self.FONT_THICKNESS_SMALL,
                cv2.LINE_AA
            )
    
    def close(self):
        """Close display window."""
        if self._window_created:
            cv2.destroyWindow(self.window_name)
            self._window_created = False
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures window is closed."""
        self.close()
        return False
