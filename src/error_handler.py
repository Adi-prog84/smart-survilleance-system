"""
Error handling framework for the Smart Surveillance System.

This module provides centralized error handling and recovery mechanisms
for different types of errors that can occur during system operation.
"""

import logging
import sys
import time
from collections import defaultdict
from typing import Callable, Optional, Any


class ErrorHandler:
    """
    Centralized error handling and recovery for the surveillance system.
    
    This class manages different categories of errors:
    - Initialization errors (fatal - system cannot start)
    - Transient errors (recoverable - retry with backoff)
    - Processing errors (recoverable - skip and continue)
    - Output errors (degraded operation - disable component)
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the error handler.
        
        Args:
            logger: Logger instance for error reporting. If None, creates default logger.
        """
        self.logger = logger or logging.getLogger(__name__)
        self.error_counts: dict[str, int] = defaultdict(int)
        self._component_disabled: dict[str, bool] = defaultdict(bool)
    
    def handle_initialization_error(self, error: Exception, component: str) -> None:
        """
        Handle fatal initialization errors that prevent system startup.
        
        This method logs a critical error message and exits the application
        with a non-zero exit code.
        
        Args:
            error: The exception that occurred during initialization
            component: Name of the component that failed to initialize
        """
        self.logger.critical(f"{component} initialization failed: {error}")
        sys.exit(1)
    
    def handle_transient_error(
        self, 
        error: Exception, 
        operation: str, 
        retry_count: int
    ) -> bool:
        """
        Handle transient errors with retry logic.
        
        Transient errors are temporary failures that may succeed on retry,
        such as temporary network issues or resource unavailability.
        Uses exponential backoff for retries (max 3 attempts).
        
        Args:
            error: The exception that occurred
            operation: Description of the operation that failed
            retry_count: Current retry attempt number (1-indexed)
            
        Returns:
            True if the operation should be retried, False if max retries exceeded
        """
        self.logger.warning(f"{operation} failed (attempt {retry_count}): {error}")
        
        # Maximum 3 retry attempts
        if retry_count >= 3:
            self.logger.error(f"{operation} failed after {retry_count} attempts")
            return False
        
        # Exponential backoff: 2^(retry_count-1) seconds
        # retry_count=1: 1 second, retry_count=2: 2 seconds, retry_count=3: 4 seconds
        backoff_time = 2 ** (retry_count - 1)
        self.logger.info(f"Retrying {operation} in {backoff_time} seconds...")
        time.sleep(backoff_time)
        
        return True
    
    def handle_processing_error(self, error: Exception, frame_number: int) -> None:
        """
        Handle single frame processing errors.
        
        Processing errors occur when a single frame cannot be processed.
        The system logs the error and continues with the next frame.
        
        Args:
            error: The exception that occurred during processing
            frame_number: The frame number that failed to process
        """
        self.logger.error(f"Frame {frame_number} processing failed: {error}")
        self.error_counts['processing'] += 1
    
    def handle_output_error(self, error: Exception, component: str) -> bool:
        """
        Handle output component errors with automatic disabling.
        
        Output errors occur when output components (logger, snapshot saver, etc.)
        fail to perform their operations. After 5 consecutive errors, the component
        is automatically disabled to prevent error flooding.
        
        Args:
            error: The exception that occurred
            component: Name of the output component that failed
            
        Returns:
            True if the component should be disabled, False otherwise
        """
        self.error_counts[component] += 1
        self.logger.error(f"{component} error: {error}")
        
        # Disable component after 5 consecutive errors
        if self.error_counts[component] >= 5:
            self.logger.warning(f"Disabling {component} due to repeated errors")
            self._component_disabled[component] = True
            return True
        
        return False
    
    def is_component_disabled(self, component: str) -> bool:
        """
        Check if a component has been disabled due to repeated errors.
        
        Args:
            component: Name of the component to check
            
        Returns:
            True if the component is disabled, False otherwise
        """
        return self._component_disabled.get(component, False)
    
    def reset_error_count(self, component: str) -> None:
        """
        Reset the error count for a component.
        
        This can be called after a successful operation to reset the
        error counter, preventing premature component disabling.
        
        Args:
            component: Name of the component to reset
        """
        if component in self.error_counts:
            self.error_counts[component] = 0
    
    def get_error_count(self, component: str) -> int:
        """
        Get the current error count for a component.
        
        Args:
            component: Name of the component
            
        Returns:
            Number of errors recorded for the component
        """
        return self.error_counts.get(component, 0)
    
    def retry_with_backoff(
        self,
        operation: Callable[[], Any],
        operation_name: str,
        max_retries: int = 3
    ) -> Optional[Any]:
        """
        Execute an operation with automatic retry and exponential backoff.
        
        This is a convenience method that wraps an operation with retry logic.
        
        Args:
            operation: Callable that performs the operation
            operation_name: Description of the operation for logging
            max_retries: Maximum number of retry attempts (default: 3)
            
        Returns:
            Result of the operation if successful, None if all retries failed
            
        Example:
            result = error_handler.retry_with_backoff(
                lambda: webcam.connect(),
                "Webcam connection"
            )
        """
        for attempt in range(1, max_retries + 1):
            try:
                result = operation()
                if attempt > 1:
                    self.logger.info(f"{operation_name} succeeded on attempt {attempt}")
                return result
            except Exception as e:
                if not self.handle_transient_error(e, operation_name, attempt):
                    return None
        
        return None
