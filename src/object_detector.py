"""
Object Detector module for the Smart Surveillance System.

This module provides object detection capabilities using YOLOv8 model
from the Ultralytics library.
"""

import time
from datetime import datetime
from typing import List, Optional
import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

from .models import Detection, BoundingBox


class ObjectDetector:
    """
    Detects and classifies objects in frames using the YOLO model.
    
    This class provides an interface to the YOLOv8 object detection model,
    with support for confidence threshold filtering, target class filtering,
    and timeout mechanisms to ensure real-time performance.
    """
    
    def __init__(
        self,
        model_path: str,
        confidence_threshold: float = 0.5,
        target_classes: Optional[List[str]] = None
    ):
        """
        Initialize object detector with YOLO model.
        
        Args:
            model_path: Path to YOLO model weights (e.g., 'yolov8n.pt')
            confidence_threshold: Minimum confidence for detections (0.0-1.0)
            target_classes: List of class names to detect (None = all classes)
            
        Raises:
            RuntimeError: If Ultralytics library is not installed
            RuntimeError: If model file cannot be loaded
        """
        if YOLO is None:
            raise RuntimeError(
                "Ultralytics library is not installed. "
                "Please install it with: pip install ultralytics"
            )
        
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.target_classes = target_classes
        
        # Load the YOLO model
        try:
            self.model = YOLO(model_path)
        except Exception as e:
            raise RuntimeError(
                f"Failed to load YOLO model from '{model_path}': {str(e)}"
            ) from e
        
        # Get class names from the model
        self.class_names = self.model.names  # Dict mapping class IDs to names
        
    def detect(self, frame: np.ndarray, timeout_ms: float = 500.0) -> List[Detection]:
        """
        Detect objects in a frame.
        
        Args:
            frame: Input frame (BGR format, numpy array)
            timeout_ms: Maximum processing time in milliseconds (default 500ms)
            
        Returns:
            List of Detection objects with class, confidence, and bounding box
            
        Raises:
            ValueError: If frame is invalid (None or wrong format)
            TimeoutError: If detection exceeds timeout limit
        """
        if frame is None or not isinstance(frame, np.ndarray):
            raise ValueError("Invalid frame: must be a numpy array")
        
        if frame.size == 0:
            raise ValueError("Invalid frame: empty array")
        
        # Record start time for timeout mechanism
        start_time = time.time()
        
        # Run YOLO inference
        try:
            # Run prediction with confidence threshold
            # verbose=False to suppress output
            results = self.model.predict(
                frame,
                conf=self.confidence_threshold,
                verbose=False
            )
        except Exception as e:
            raise RuntimeError(f"YOLO inference failed: {str(e)}") from e
        
        # Check if we exceeded timeout
        elapsed_ms = (time.time() - start_time) * 1000
        if elapsed_ms > timeout_ms:
            raise TimeoutError(
                f"Detection exceeded timeout limit: {elapsed_ms:.1f}ms > {timeout_ms}ms"
            )
        
        # Convert YOLO results to Detection objects
        detections = []
        timestamp = datetime.now()
        
        # YOLO returns a list of Results objects (one per image)
        # We only process one image at a time
        if results and len(results) > 0:
            result = results[0]
            
            # Extract boxes, confidences, and class IDs
            if result.boxes is not None and len(result.boxes) > 0:
                boxes = result.boxes.xyxy.cpu().numpy()  # Bounding boxes in xyxy format
                confidences = result.boxes.conf.cpu().numpy()  # Confidence scores
                class_ids = result.boxes.cls.cpu().numpy().astype(int)  # Class IDs
                
                # Process each detection
                for box, conf, class_id in zip(boxes, confidences, class_ids):
                    # Get class name
                    class_name = self.class_names.get(class_id, f"class_{class_id}")
                    
                    # Filter by target classes if specified
                    if self.target_classes is not None:
                        if class_name not in self.target_classes:
                            continue
                    
                    # Convert xyxy format to xywh format
                    x1, y1, x2, y2 = box
                    x = int(x1)
                    y = int(y1)
                    width = int(x2 - x1)
                    height = int(y2 - y1)
                    
                    # Create BoundingBox and Detection objects
                    bbox = BoundingBox(x=x, y=y, width=width, height=height)
                    detection = Detection(
                        class_name=class_name,
                        confidence=float(conf),
                        bbox=bbox,
                        timestamp=timestamp
                    )
                    
                    detections.append(detection)
        
        return detections
    
    def get_supported_classes(self) -> List[str]:
        """
        Get list of all classes the model can detect.
        
        Returns:
            List of class names supported by the model
        """
        # Return class names sorted by class ID
        return [self.class_names[i] for i in sorted(self.class_names.keys())]
