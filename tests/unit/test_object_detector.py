"""
Unit tests for the ObjectDetector class.
"""

import pytest
import numpy as np
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from src.object_detector import ObjectDetector
from src.models import Detection, BoundingBox


class TestObjectDetectorInitialization:
    """Tests for ObjectDetector initialization."""
    
    def test_init_with_valid_model_path(self):
        """Test initialization with a valid model path."""
        with patch('src.object_detector.YOLO') as mock_yolo:
            mock_model = Mock()
            mock_model.names = {0: 'person', 1: 'car'}
            mock_yolo.return_value = mock_model
            
            detector = ObjectDetector(
                model_path='yolov8n.pt',
                confidence_threshold=0.5
            )
            
            assert detector.model_path == 'yolov8n.pt'
            assert detector.confidence_threshold == 0.5
            assert detector.target_classes is None
            mock_yolo.assert_called_once_with('yolov8n.pt')
    
    def test_init_with_target_classes(self):
        """Test initialization with target classes filter."""
        with patch('src.object_detector.YOLO') as mock_yolo:
            mock_model = Mock()
            mock_model.names = {0: 'person', 1: 'car', 2: 'dog'}
            mock_yolo.return_value = mock_model
            
            target_classes = ['person', 'car']
            detector = ObjectDetector(
                model_path='yolov8n.pt',
                target_classes=target_classes
            )
            
            assert detector.target_classes == target_classes
    
    def test_init_fails_when_ultralytics_not_installed(self):
        """Test that initialization fails gracefully when Ultralytics is not installed."""
        with patch('src.object_detector.YOLO', None):
            with pytest.raises(RuntimeError, match="Ultralytics library is not installed"):
                ObjectDetector(model_path='yolov8n.pt')
    
    def test_init_fails_with_invalid_model_path(self):
        """Test that initialization fails with invalid model path."""
        with patch('src.object_detector.YOLO') as mock_yolo:
            mock_yolo.side_effect = Exception("Model file not found")
            
            with pytest.raises(RuntimeError, match="Failed to load YOLO model"):
                ObjectDetector(model_path='invalid_model.pt')


class TestObjectDetectorDetection:
    """Tests for ObjectDetector detect() method."""
    
    def test_detect_with_valid_frame(self):
        """Test detection with a valid frame."""
        with patch('src.object_detector.YOLO') as mock_yolo:
            # Setup mock model
            mock_model = Mock()
            mock_model.names = {0: 'person', 1: 'car'}
            
            # Setup mock detection results
            mock_result = Mock()
            mock_boxes = Mock()
            
            # Mock bounding boxes in xyxy format
            mock_boxes.xyxy.cpu().numpy.return_value = np.array([
                [100, 150, 180, 350],  # person: x1, y1, x2, y2
                [200, 100, 320, 220]   # car: x1, y1, x2, y2
            ])
            mock_boxes.conf.cpu().numpy.return_value = np.array([0.87, 0.92])
            mock_boxes.cls.cpu().numpy().astype.return_value = np.array([0, 1])
            
            mock_result.boxes = mock_boxes
            mock_model.predict.return_value = [mock_result]
            mock_yolo.return_value = mock_model
            
            # Create detector and run detection
            detector = ObjectDetector(model_path='yolov8n.pt', confidence_threshold=0.5)
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            detections = detector.detect(frame)
            
            # Verify results
            assert len(detections) == 2
            
            # Check first detection (person)
            assert detections[0].class_name == 'person'
            assert detections[0].confidence == 0.87
            assert detections[0].bbox.x == 100
            assert detections[0].bbox.y == 150
            assert detections[0].bbox.width == 80
            assert detections[0].bbox.height == 200
            
            # Check second detection (car)
            assert detections[1].class_name == 'car'
            assert detections[1].confidence == 0.92
            assert detections[1].bbox.x == 200
            assert detections[1].bbox.y == 100
            assert detections[1].bbox.width == 120
            assert detections[1].bbox.height == 120
    
    def test_detect_filters_by_confidence_threshold(self):
        """Test that detections below threshold are filtered out."""
        with patch('src.object_detector.YOLO') as mock_yolo:
            mock_model = Mock()
            mock_model.names = {0: 'person', 1: 'car', 2: 'dog'}
            
            mock_result = Mock()
            mock_boxes = Mock()
            
            # Three detections with varying confidence
            mock_boxes.xyxy.cpu().numpy.return_value = np.array([
                [100, 100, 150, 200],  # person: 0.9
                [200, 150, 280, 210],  # car: 0.6 (below threshold)
                [300, 200, 340, 250]   # dog: 0.75
            ])
            mock_boxes.conf.cpu().numpy.return_value = np.array([0.9, 0.6, 0.75])
            mock_boxes.cls.cpu().numpy().astype.return_value = np.array([0, 1, 2])
            
            mock_result.boxes = mock_boxes
            mock_model.predict.return_value = [mock_result]
            mock_yolo.return_value = mock_model
            
            # Create detector with 0.7 threshold
            detector = ObjectDetector(model_path='yolov8n.pt', confidence_threshold=0.7)
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            detections = detector.detect(frame)
            
            # Only person (0.9) and dog (0.75) should be returned
            assert len(detections) == 2
            assert detections[0].class_name == 'person'
            assert detections[1].class_name == 'dog'
    
    def test_detect_filters_by_target_classes(self):
        """Test that only target classes are returned."""
        with patch('src.object_detector.YOLO') as mock_yolo:
            mock_model = Mock()
            mock_model.names = {0: 'person', 1: 'car', 2: 'dog'}
            
            mock_result = Mock()
            mock_boxes = Mock()
            
            mock_boxes.xyxy.cpu().numpy.return_value = np.array([
                [100, 100, 150, 200],  # person
                [200, 150, 280, 210],  # car
                [300, 200, 340, 250]   # dog
            ])
            mock_boxes.conf.cpu().numpy.return_value = np.array([0.9, 0.85, 0.8])
            mock_boxes.cls.cpu().numpy().astype.return_value = np.array([0, 1, 2])
            
            mock_result.boxes = mock_boxes
            mock_model.predict.return_value = [mock_result]
            mock_yolo.return_value = mock_model
            
            # Create detector with target classes filter
            detector = ObjectDetector(
                model_path='yolov8n.pt',
                confidence_threshold=0.5,
                target_classes=['person', 'dog']
            )
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            detections = detector.detect(frame)
            
            # Only person and dog should be returned (car filtered out)
            assert len(detections) == 2
            assert detections[0].class_name == 'person'
            assert detections[1].class_name == 'dog'
    
    def test_detect_with_no_detections(self):
        """Test detection when no objects are found."""
        with patch('src.object_detector.YOLO') as mock_yolo:
            mock_model = Mock()
            mock_model.names = {0: 'person'}
            
            mock_result = Mock()
            mock_result.boxes = None  # No detections
            mock_model.predict.return_value = [mock_result]
            mock_yolo.return_value = mock_model
            
            detector = ObjectDetector(model_path='yolov8n.pt')
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            detections = detector.detect(frame)
            
            assert len(detections) == 0
    
    def test_detect_with_empty_boxes(self):
        """Test detection when boxes list is empty."""
        with patch('src.object_detector.YOLO') as mock_yolo:
            mock_model = Mock()
            mock_model.names = {0: 'person'}
            
            mock_result = Mock()
            mock_boxes = Mock()
            mock_boxes.__len__ = Mock(return_value=0)
            mock_result.boxes = mock_boxes
            mock_model.predict.return_value = [mock_result]
            mock_yolo.return_value = mock_model
            
            detector = ObjectDetector(model_path='yolov8n.pt')
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            detections = detector.detect(frame)
            
            assert len(detections) == 0
    
    def test_detect_with_invalid_frame_none(self):
        """Test that detect raises ValueError for None frame."""
        with patch('src.object_detector.YOLO') as mock_yolo:
            mock_model = Mock()
            mock_model.names = {0: 'person'}
            mock_yolo.return_value = mock_model
            
            detector = ObjectDetector(model_path='yolov8n.pt')
            
            with pytest.raises(ValueError, match="Invalid frame: must be a numpy array"):
                detector.detect(None)
    
    def test_detect_with_invalid_frame_empty(self):
        """Test that detect raises ValueError for empty frame."""
        with patch('src.object_detector.YOLO') as mock_yolo:
            mock_model = Mock()
            mock_model.names = {0: 'person'}
            mock_yolo.return_value = mock_model
            
            detector = ObjectDetector(model_path='yolov8n.pt')
            empty_frame = np.array([])
            
            with pytest.raises(ValueError, match="Invalid frame: empty array"):
                detector.detect(empty_frame)
    
    def test_detect_handles_inference_failure(self):
        """Test that detect handles YOLO inference failures."""
        with patch('src.object_detector.YOLO') as mock_yolo:
            mock_model = Mock()
            mock_model.names = {0: 'person'}
            mock_model.predict.side_effect = Exception("CUDA out of memory")
            mock_yolo.return_value = mock_model
            
            detector = ObjectDetector(model_path='yolov8n.pt')
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            with pytest.raises(RuntimeError, match="YOLO inference failed"):
                detector.detect(frame)
    
    def test_detect_timeout_mechanism(self):
        """Test that detect raises TimeoutError when processing exceeds limit."""
        with patch('src.object_detector.YOLO') as mock_yolo:
            mock_model = Mock()
            mock_model.names = {0: 'person'}
            
            # Simulate slow inference
            def slow_predict(*args, **kwargs):
                import time
                time.sleep(0.6)  # Sleep for 600ms
                mock_result = Mock()
                mock_result.boxes = None
                return [mock_result]
            
            mock_model.predict = slow_predict
            mock_yolo.return_value = mock_model
            
            detector = ObjectDetector(model_path='yolov8n.pt')
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            with pytest.raises(TimeoutError, match="Detection exceeded timeout limit"):
                detector.detect(frame, timeout_ms=500)


class TestObjectDetectorHelperMethods:
    """Tests for ObjectDetector helper methods."""
    
    def test_get_supported_classes(self):
        """Test getting list of supported classes."""
        with patch('src.object_detector.YOLO') as mock_yolo:
            mock_model = Mock()
            mock_model.names = {0: 'person', 1: 'bicycle', 2: 'car'}
            mock_yolo.return_value = mock_model
            
            detector = ObjectDetector(model_path='yolov8n.pt')
            classes = detector.get_supported_classes()
            
            assert classes == ['person', 'bicycle', 'car']
            assert len(classes) == 3
