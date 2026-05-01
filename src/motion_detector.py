"""
Motion Detector module for the Smart Surveillance System.

This module implements motion detection using OpenCV's MOG2 background
subtraction algorithm with morphological operations for noise reduction.
"""

import cv2
import numpy as np
from datetime import datetime
from typing import List, Tuple
from .models import MotionRegion, BoundingBox


class MotionDetector:
    """
    Detects motion in video frames using background subtraction.
    
    Uses OpenCV's MOG2 (Mixture of Gaussians) algorithm for adaptive
    background modeling that handles gradual lighting changes.
    """
    
    # Sensitivity parameter mappings
    SENSITIVITY_PARAMS = {
        'low': {'history': 500, 'var_threshold': 50},
        'medium': {'history': 200, 'var_threshold': 25},
        'high': {'history': 100, 'var_threshold': 16}
    }
    
    def __init__(self, sensitivity: str = 'medium', min_area: int = 100):
        """
        Initialize motion detector with background subtractor.
        
        Args:
            sensitivity: Motion sensitivity level ('low', 'medium', or 'high')
            min_area: Minimum pixel area to consider as motion
            
        Raises:
            ValueError: If sensitivity is not one of the valid options
        """
        if sensitivity not in self.SENSITIVITY_PARAMS:
            raise ValueError(
                f"Invalid sensitivity '{sensitivity}'. "
                f"Must be one of: {list(self.SENSITIVITY_PARAMS.keys())}"
            )
        
        self.sensitivity = sensitivity
        self.min_area = min_area
        
        # Get parameters for the selected sensitivity level
        params = self.SENSITIVITY_PARAMS[sensitivity]
        
        # Create MOG2 background subtractor
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=params['history'],
            varThreshold=params['var_threshold'],
            detectShadows=True
        )
        
        # Morphological kernel for noise reduction
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    
    def detect_motion(self, frame: np.ndarray) -> List[MotionRegion]:
        """
        Detect motion in frame compared to background model.
        
        Args:
            frame: Current frame in BGR format
            
        Returns:
            List of MotionRegion objects with bounding boxes and areas
        """
        # Apply background subtraction
        fg_mask = self.bg_subtractor.apply(frame)
        
        # Remove shadows (MOG2 marks shadows as 127, we want only foreground at 255)
        _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
        
        # Apply morphological operations to reduce noise
        # Erosion removes small noise
        fg_mask = cv2.erode(fg_mask, self.kernel, iterations=1)
        # Dilation fills gaps in detected regions
        fg_mask = cv2.dilate(fg_mask, self.kernel, iterations=2)
        
        # Find contours in the foreground mask
        contours, _ = cv2.findContours(
            fg_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Convert contours to MotionRegion objects
        motion_regions = []
        timestamp = datetime.now()
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Filter out small regions (noise)
            if area < self.min_area:
                continue
            
            # Get bounding rectangle for the contour
            x, y, w, h = cv2.boundingRect(contour)
            
            # Create MotionRegion object
            bbox = BoundingBox(x=x, y=y, width=w, height=h)
            motion_region = MotionRegion(
                bbox=bbox,
                area=int(area),
                timestamp=timestamp
            )
            motion_regions.append(motion_region)
        
        return motion_regions
    
    def reset_background(self):
        """
        Reset the background model.
        
        Useful after scene changes or when the background model
        becomes corrupted.
        """
        # Get current parameters
        params = self.SENSITIVITY_PARAMS[self.sensitivity]
        
        # Recreate the background subtractor
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=params['history'],
            varThreshold=params['var_threshold'],
            detectShadows=True
        )
