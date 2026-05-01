"""
Unit tests for the VideoCapture module.

Tests the video capture functionality including webcam initialization,
frame reading, metadata tracking, and error handling.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.video_capture import VideoCapture
from src.models import FrameMetadata


class TestVideoCaptureInitialization:
    """Tests for VideoCapture initialization."""
    
    @patch('cv2.VideoCapture')
    def test_successful_initialization(self, mock_cv2_capture):
        """Test successful webcam initialization."""
        # Setup mock
        mock_capture_instance = MagicMock()
        mock_capture_instance.isOpened.return_value = True
        mock_capture_instance.get.side_effect = lambda prop: {
            3: 640,  # CAP_PROP_FRAME_WIDTH
            4: 480,  # CAP_PROP_FRAME_HEIGHT
            5: 30.0  # CAP_PROP_FPS
        }.get(prop, 0)
        mock_cv2_capture.return_value = mock_capture_instance
        
        # Create VideoCapture
        video_capture = VideoCapture(camera_index=0)
        
        # Verify
        assert video_capture.is_opened() is True
        mock_cv2_capture.assert_called_once_with(0)
    
    @patch('cv2.VideoCapture')
    def test_initialization_failure(self, mock_cv2_capture):
        """Test webcam initialization failure."""
        # Setup mock to simulate failure
        mock_capture_instance = MagicMock()
        mock_capture_instance.isOpened.return_value = False
        mock_cv2_capture.return_value = mock_capture_instance
        
        # Create VideoCapture
        video_capture = VideoCapture(camera_index=0)
        
        # Verify
        assert video_capture.is_opened() is False


class TestVideoCaptureFrameReading:
    """Tests for frame reading functionality."""
    
    @patch('cv2.VideoCapture')
    def test_successful_frame_read(self, mock_cv2_capture):
        """Test successful frame capture with correct format."""
        # Setup mock
        mock_capture_instance = MagicMock()
        mock_capture_instance.isOpened.return_value = True
        mock_capture_instance.get.side_effect = lambda prop: {
            3: 640,  # CAP_PROP_FRAME_WIDTH
            4: 480,  # CAP_PROP_FRAME_HEIGHT
            5: 30.0  # CAP_PROP_FPS
        }.get(prop, 0)
        
        # Create a valid BGR frame
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_capture_instance.read.return_value = (True, test_frame)
        mock_cv2_capture.return_value = mock_capture_instance
        
        # Create VideoCapture and read frame
        video_capture = VideoCapture(camera_index=0)
        success, frame, metadata = video_capture.read_frame()
        
        # Verify
        assert success is True
        assert frame is not None
        assert isinstance(frame, np.ndarray)
        assert frame.shape == (480, 640, 3)
        assert frame.dtype == np.uint8
        assert metadata is not None
        assert isinstance(metadata, FrameMetadata)
        assert metadata.frame_number == 1
        assert metadata.width == 640
        assert metadata.height == 480
        assert isinstance(metadata.timestamp, datetime)
    
    @patch('cv2.VideoCapture')
    def test_frame_read_failure(self, mock_cv2_capture):
        """Test frame read failure handling."""
        # Setup mock
        mock_capture_instance = MagicMock()
        mock_capture_instance.isOpened.return_value = True
        mock_capture_instance.get.side_effect = lambda prop: {
            3: 640,
            4: 480,
            5: 30.0
        }.get(prop, 0)
        mock_capture_instance.read.return_value = (False, None)
        mock_cv2_capture.return_value = mock_capture_instance
        
        # Create VideoCapture and read frame
        video_capture = VideoCapture(camera_index=0)
        
        # Mock the reconnection to fail
        with patch.object(video_capture, '_attempt_reconnection', return_value=False):
            success, frame, metadata = video_capture.read_frame()
        
        # Verify
        assert success is False
        assert frame is None
        assert metadata is None
    
    @patch('cv2.VideoCapture')
    def test_frame_number_increment(self, mock_cv2_capture):
        """Test that frame numbers increment correctly."""
        # Setup mock
        mock_capture_instance = MagicMock()
        mock_capture_instance.isOpened.return_value = True
        mock_capture_instance.get.side_effect = lambda prop: {
            3: 640,
            4: 480,
            5: 30.0
        }.get(prop, 0)
        
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_capture_instance.read.return_value = (True, test_frame)
        mock_cv2_capture.return_value = mock_capture_instance
        
        # Create VideoCapture and read multiple frames
        video_capture = VideoCapture(camera_index=0)
        
        for expected_frame_num in range(1, 4):
            success, frame, metadata = video_capture.read_frame()
            assert success is True
            assert metadata.frame_number == expected_frame_num
    
    @patch('cv2.VideoCapture')
    def test_read_from_closed_webcam(self, mock_cv2_capture):
        """Test reading from a closed webcam."""
        # Setup mock
        mock_capture_instance = MagicMock()
        mock_capture_instance.isOpened.return_value = False
        mock_cv2_capture.return_value = mock_capture_instance
        
        # Create VideoCapture
        video_capture = VideoCapture(camera_index=0)
        success, frame, metadata = video_capture.read_frame()
        
        # Verify
        assert success is False
        assert frame is None
        assert metadata is None


class TestVideoCaptureFrameValidation:
    """Tests for frame format validation."""
    
    @patch('cv2.VideoCapture')
    def test_invalid_frame_format_not_numpy(self, mock_cv2_capture):
        """Test validation rejects non-numpy array frames."""
        # Setup mock
        mock_capture_instance = MagicMock()
        mock_capture_instance.isOpened.return_value = True
        mock_capture_instance.get.side_effect = lambda prop: {
            3: 640,
            4: 480,
            5: 30.0
        }.get(prop, 0)
        
        # Return invalid frame (not numpy array)
        mock_capture_instance.read.return_value = (True, "not_a_numpy_array")
        mock_cv2_capture.return_value = mock_capture_instance
        
        # Create VideoCapture and read frame
        video_capture = VideoCapture(camera_index=0)
        success, frame, metadata = video_capture.read_frame()
        
        # Verify
        assert success is False
        assert frame is None
        assert metadata is None
    
    @patch('cv2.VideoCapture')
    def test_invalid_frame_format_wrong_channels(self, mock_cv2_capture):
        """Test validation rejects frames with wrong number of channels."""
        # Setup mock
        mock_capture_instance = MagicMock()
        mock_capture_instance.isOpened.return_value = True
        mock_capture_instance.get.side_effect = lambda prop: {
            3: 640,
            4: 480,
            5: 30.0
        }.get(prop, 0)
        
        # Return frame with wrong channels (grayscale instead of BGR)
        invalid_frame = np.zeros((480, 640), dtype=np.uint8)
        mock_capture_instance.read.return_value = (True, invalid_frame)
        mock_cv2_capture.return_value = mock_capture_instance
        
        # Create VideoCapture and read frame
        video_capture = VideoCapture(camera_index=0)
        success, frame, metadata = video_capture.read_frame()
        
        # Verify
        assert success is False
        assert frame is None
        assert metadata is None


class TestVideoCaptureResourceManagement:
    """Tests for resource management (release, context manager)."""
    
    @patch('cv2.VideoCapture')
    def test_release(self, mock_cv2_capture):
        """Test webcam resource release."""
        # Setup mock
        mock_capture_instance = MagicMock()
        mock_capture_instance.isOpened.return_value = True
        mock_capture_instance.get.side_effect = lambda prop: {
            3: 640,
            4: 480,
            5: 30.0
        }.get(prop, 0)
        mock_cv2_capture.return_value = mock_capture_instance
        
        # Create VideoCapture and release
        video_capture = VideoCapture(camera_index=0)
        assert video_capture.is_opened() is True
        
        video_capture.release()
        
        # Verify
        mock_capture_instance.release.assert_called_once()
        assert video_capture.is_opened() is False
    
    @patch('cv2.VideoCapture')
    def test_context_manager(self, mock_cv2_capture):
        """Test VideoCapture as context manager."""
        # Setup mock
        mock_capture_instance = MagicMock()
        mock_capture_instance.isOpened.return_value = True
        mock_capture_instance.get.side_effect = lambda prop: {
            3: 640,
            4: 480,
            5: 30.0
        }.get(prop, 0)
        mock_cv2_capture.return_value = mock_capture_instance
        
        # Use as context manager
        with VideoCapture(camera_index=0) as video_capture:
            assert video_capture.is_opened() is True
        
        # Verify release was called
        mock_capture_instance.release.assert_called_once()


class TestVideoCaptureHelperMethods:
    """Tests for helper methods (get_fps, get_resolution)."""
    
    @patch('cv2.VideoCapture')
    def test_get_fps(self, mock_cv2_capture):
        """Test getting webcam FPS."""
        # Setup mock
        mock_capture_instance = MagicMock()
        mock_capture_instance.isOpened.return_value = True
        mock_capture_instance.get.side_effect = lambda prop: {
            3: 640,
            4: 480,
            5: 30.0
        }.get(prop, 0)
        mock_cv2_capture.return_value = mock_capture_instance
        
        # Create VideoCapture and get FPS
        video_capture = VideoCapture(camera_index=0)
        fps = video_capture.get_fps()
        
        # Verify
        assert fps == 30.0
    
    @patch('cv2.VideoCapture')
    def test_get_fps_when_closed(self, mock_cv2_capture):
        """Test getting FPS from closed webcam."""
        # Setup mock
        mock_capture_instance = MagicMock()
        mock_capture_instance.isOpened.return_value = False
        mock_cv2_capture.return_value = mock_capture_instance
        
        # Create VideoCapture and get FPS
        video_capture = VideoCapture(camera_index=0)
        fps = video_capture.get_fps()
        
        # Verify
        assert fps == 0.0
    
    @patch('cv2.VideoCapture')
    def test_get_resolution(self, mock_cv2_capture):
        """Test getting webcam resolution."""
        # Setup mock
        mock_capture_instance = MagicMock()
        mock_capture_instance.isOpened.return_value = True
        mock_capture_instance.get.side_effect = lambda prop: {
            3: 640,
            4: 480,
            5: 30.0
        }.get(prop, 0)
        mock_cv2_capture.return_value = mock_capture_instance
        
        # Create VideoCapture and get resolution
        video_capture = VideoCapture(camera_index=0)
        width, height = video_capture.get_resolution()
        
        # Verify
        assert width == 640
        assert height == 480
    
    @patch('cv2.VideoCapture')
    def test_get_resolution_when_closed(self, mock_cv2_capture):
        """Test getting resolution from closed webcam."""
        # Setup mock
        mock_capture_instance = MagicMock()
        mock_capture_instance.isOpened.return_value = False
        mock_cv2_capture.return_value = mock_capture_instance
        
        # Create VideoCapture and get resolution
        video_capture = VideoCapture(camera_index=0)
        width, height = video_capture.get_resolution()
        
        # Verify
        assert width == 0
        assert height == 0
