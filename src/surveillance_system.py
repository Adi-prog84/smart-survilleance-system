"""
Main Surveillance System module.

This module implements the main SurveillanceSystem class that coordinates
all components and runs the main processing loop.
"""

import cv2
import logging
import time
import winsound
from typing import Optional

from .models import Configuration
from .config_manager import ConfigurationManager
from .video_capture import VideoCapture
from .processing_pipeline import ProcessingPipeline
from .display_module import DisplayModule
from .event_logger import EventLogger
from .snapshot_saver import SnapshotSaver
from .alert_generator import AlertGenerator
from .performance_monitor import PerformanceMonitor
from .error_handler import ErrorHandler


class SurveillanceSystem:
    """
    Main surveillance system that coordinates all components.
    
    This class implements the main processing loop that:
    1. Captures frames from webcam
    2. Processes frames through the pipeline
    3. Displays results with overlays
    4. Logs events and saves snapshots
    5. Generates alerts
    6. Monitors performance
    """
    
    # Keyboard control keys
    KEY_QUIT = ord('q')
    KEY_PAUSE = ord('p')
    KEY_RESUME = ord('r')
    KEY_SNAPSHOT = ord('s')
    
    # Performance metrics logging interval (seconds)
    METRICS_LOG_INTERVAL = 60
    
    def __init__(self, config: Configuration, logger: Optional[logging.Logger] = None):
        """
        Initialize surveillance system with configuration.
        
        Args:
            config: Configuration object with all system settings
            logger: Logger instance for system messages
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.error_handler = ErrorHandler(self.logger)
        
        self._running = False
        self._paused = False
        self._last_metrics_log_time = 0.0
        
        # Initialize all components
        self.logger.info("Initializing Smart Surveillance System...")
        
        try:
            # Video capture
            self.video_capture = VideoCapture(camera_index=0, logger=self.logger)
            if not self.video_capture.is_opened():
                raise RuntimeError("Failed to open webcam")
            
            # Processing pipeline
            self.pipeline = ProcessingPipeline(config, logger=self.logger)
            
            # Display module
            if config.display_enabled:
                self.display = DisplayModule(window_name=config.window_name)
            else:
                self.display = None
            
            # Event logger
            self.event_logger = EventLogger(
                log_directory=config.log_directory,
                max_file_size_mb=config.log_max_size_mb,
                logger=self.logger
            )
            
            # Snapshot saver
            self.snapshot_saver = SnapshotSaver(
                output_directory=config.snapshot_directory,
                enabled=config.snapshot_enabled,
                rate_limit_seconds=config.snapshot_rate_limit,
                logger=self.logger
            )
            
            # Alert generator
            self.alert_generator = AlertGenerator(
                alert_classes=config.alert_classes,
                cooldown_seconds=config.alert_cooldown
            )
            
            # Performance monitor
            self.performance_monitor = PerformanceMonitor(logger=self.logger)
            
            self.logger.info("Smart Surveillance System initialized successfully")
            
        except Exception as e:
            self.error_handler.handle_initialization_error(e, "SurveillanceSystem")
    
    def run(self):
        """
        Run the main processing loop.
        
        This method runs until the user presses 'q' or an unrecoverable error occurs.
        """
        self._running = True
        self.logger.info("Starting surveillance system...")
        self.logger.info("Controls: Q=Quit, P=Pause, R=Resume, S=Manual Snapshot")
        
        try:
            while self._running:
                # Handle pause state
                if self._paused:
                    self._handle_paused_state()
                    continue
                
                # Capture frame
                success, frame, metadata = self.video_capture.read_frame()
                
                if not success or frame is None:
                    self.logger.warning("Failed to capture frame, retrying...")
                    time.sleep(0.1)
                    continue
                
                # Process frame through pipeline
                processed_frame = self.pipeline.process_frame(frame, metadata)
                
                if processed_frame is None:
                    self.logger.warning(f"Failed to process frame {metadata.frame_number}")
                    continue
                
                # Check for alerts
                alerts = self.alert_generator.check_alerts(
                    processed_frame.object_detections
                )
                
                # Log events
                self._log_events(processed_frame, alerts)
                
                # Save snapshot if there are detections
                if len(processed_frame.object_detections) > 0:
                    self.snapshot_saver.save_snapshot(processed_frame)
                
                # Update performance monitor
                self.performance_monitor.record_frame(
                    processed_frame.processing_time_ms,
                    len(processed_frame.object_detections)
                )
                
                # Display frame with overlays
                if self.display is not None:
                    current_fps = self.performance_monitor.get_current_fps()
                    self.display.render(processed_frame, current_fps, alerts)
                
                # Log performance metrics periodically
                self._log_metrics_if_needed()
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if not self._handle_keyboard_input(key, processed_frame):
                    break
                
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt (Ctrl+C)")
        except Exception as e:
            self.logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
        finally:
            self._shutdown()
    
    def _handle_paused_state(self):
        """Handle the paused state - wait for resume or quit."""
        key = cv2.waitKey(100) & 0xFF
        
        if key == self.KEY_RESUME:
            self._paused = False
            self.logger.info("Surveillance resumed")
        elif key == self.KEY_QUIT:
            self._running = False
    
    def _handle_keyboard_input(self, key: int, processed_frame) -> bool:
        """
        Handle keyboard input.
        
        Args:
            key: Key code from cv2.waitKey()
            processed_frame: Current processed frame
            
        Returns:
            True to continue running, False to quit
        """
        if key == self.KEY_QUIT:
            self.logger.info("Quit command received")
            return False
        
        elif key == self.KEY_PAUSE:
            self._paused = True
            self.logger.info("Surveillance paused (press 'r' to resume)")
        
        elif key == self.KEY_SNAPSHOT:
            # Manual snapshot
            filepath = self.snapshot_saver.save_snapshot(processed_frame)
            if filepath:
                self.logger.info(f"Manual snapshot saved: {filepath}")
            else:
                self.logger.warning("Failed to save manual snapshot")
        
        return True
    
    def _log_events(self, processed_frame, alerts):
        """
        Log detection events and alerts.
        
        Args:
            processed_frame: ProcessedFrame with detection results
            alerts: List of Alert objects
        """
        # Log object detections
        for detection in processed_frame.object_detections:
            self.event_logger.log_object_detection(detection)
        
        # Log motion detections
        for motion_region in processed_frame.motion_regions:
            self.event_logger.log_motion_detection(motion_region)
        
                # Log alerts (if any)
        for alert in alerts:
            self.logger.info(
                f"ALERT: {alert.message}"
            )

            # Play alarm sound 5 times
            for _ in range(5):
                winsound.Beep(1000, 500)
                time.sleep(0.2)
                
    def _log_metrics_if_needed(self):
        """Log performance metrics every 60 seconds."""
        current_time = time.time()
        
        if current_time - self._last_metrics_log_time >= self.METRICS_LOG_INTERVAL:
            metrics = self.performance_monitor.get_metrics()
            self.event_logger.log_performance_metrics(metrics)
            
            # Also log to console
            self.logger.info(
                f"Performance: {metrics.current_fps:.1f} FPS, "
                f"{metrics.total_frames} frames, "
                f"{metrics.total_detections} detections"
            )
            
            self._last_metrics_log_time = current_time
    
    def _shutdown(self):
        """Gracefully shutdown all components and release resources."""
        self.logger.info("Shutting down surveillance system...")
        
        try:
            # Log final metrics
            metrics = self.performance_monitor.get_metrics()
            self.event_logger.log_performance_metrics(metrics)
            self.logger.info(self.performance_monitor.get_summary())
            
            # Close display
            if self.display is not None:
                self.display.close()
            
            # Close event logger
            self.event_logger.close()
            
            # Release webcam
            self.video_capture.release()
            
            # Destroy all OpenCV windows
            cv2.destroyAllWindows()
            
            self.logger.info("Surveillance system shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
    
    def stop(self):
        """Stop the surveillance system (can be called from another thread)."""
        self._running = False
