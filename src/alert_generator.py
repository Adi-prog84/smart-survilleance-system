"""
Alert Generator module for the Smart Surveillance System.

This module generates alerts when specific detection conditions are met,
with cooldown mechanisms to prevent alert flooding.
"""

import time
from datetime import datetime
from typing import List, Dict

from .models import Detection, Alert


class AlertGenerator:
    """
    Generates alerts when specific detection conditions are met.
    
    Features:
    - Configurable alert classes (which objects trigger alerts)
    - Cooldown mechanism to prevent alert flooding
    - Per-class cooldown tracking
    """
    
    def __init__(
        self,
        alert_classes: List[str],
        cooldown_seconds: float = 5.0
    ):
        """
        Initialize alert generator.
        
        Args:
            alert_classes: Object classes that trigger alerts (e.g., ["person", "car"])
            cooldown_seconds: Minimum time between alerts for same class
        """
        self.alert_classes = set(alert_classes)  # Use set for faster lookup
        self.cooldown_seconds = cooldown_seconds
        
        # Track last alert time for each class
        self._last_alert_time: Dict[str, float] = {}
        
        # Statistics
        self._total_alerts = 0
        self._alerts_by_class: Dict[str, int] = {}
    
    def check_alerts(self, detections: List[Detection]) -> List[Alert]:
        """
        Check if detections trigger any alerts.
        
        Args:
            detections: List of Detection objects from current frame
            
        Returns:
            List of Alert objects (empty if no alerts triggered)
        """
        alerts = []
        current_time = time.time()
        
        for detection in detections:
            # Check if this class triggers alerts
            if detection.class_name not in self.alert_classes:
                continue
            
            # Check cooldown for this class
            last_alert = self._last_alert_time.get(detection.class_name, 0.0)
            time_since_last = current_time - last_alert
            
            if time_since_last < self.cooldown_seconds:
                # Still in cooldown period - skip alert
                continue
            
            # Generate alert
            alert = self._create_alert(detection)
            alerts.append(alert)
            
            # Update last alert time for this class
            self._last_alert_time[detection.class_name] = current_time
            
            # Update statistics
            self._total_alerts += 1
            self._alerts_by_class[detection.class_name] = (
                self._alerts_by_class.get(detection.class_name, 0) + 1
            )
        
        return alerts
    
    def _create_alert(self, detection: Detection) -> Alert:
        """
        Create an Alert object from a Detection.
        
        Args:
            detection: Detection that triggered the alert
            
        Returns:
            Alert object with formatted message
        """
        # Format class name for display (capitalize first letter)
        class_display = detection.class_name.capitalize()
        
        # Generate alert message
        message = f"{class_display} detected!"
        
        return Alert(
            message=message,
            class_name=detection.class_name,
            timestamp=datetime.now(),
            detection=detection
        )
    
    def add_alert_class(self, class_name: str):
        """
        Add a new class to trigger alerts.
        
        Args:
            class_name: Name of the object class
        """
        self.alert_classes.add(class_name)
    
    def remove_alert_class(self, class_name: str):
        """
        Remove a class from triggering alerts.
        
        Args:
            class_name: Name of the object class
        """
        self.alert_classes.discard(class_name)
    
    def reset_cooldown(self, class_name: str = None):
        """
        Reset cooldown timer(s).
        
        Args:
            class_name: Specific class to reset, or None to reset all
        """
        if class_name is None:
            self._last_alert_time.clear()
        else:
            self._last_alert_time.pop(class_name, None)
    
    def get_statistics(self) -> dict:
        """
        Get alert statistics.
        
        Returns:
            Dictionary with alert counts by class
        """
        return {
            "total_alerts": self._total_alerts,
            "alerts_by_class": dict(self._alerts_by_class),
            "active_alert_classes": list(self.alert_classes)
        }
