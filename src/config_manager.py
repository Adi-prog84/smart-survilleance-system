"""
Configuration Manager for the Smart Surveillance System.

This module handles loading, validating, and providing access to
configuration settings from YAML files.
"""

import logging
import os
from typing import List, Optional
import yaml

from src.models import Configuration


logger = logging.getLogger(__name__)


class ConfigurationManager:
    """Manages system configuration loading and validation."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Load configuration from file.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
    
    def get_config(self) -> Configuration:
        """
        Get the loaded configuration object.
        
        Returns:
            Configuration object with all settings
        """
        return self.config
    
    def _load_config(self) -> Configuration:
        """
        Load configuration from YAML file with fallback to defaults.
        
        Returns:
            Configuration object
        """
        # Check if config file exists
        if not os.path.exists(self.config_path):
            logger.warning(
                f"Configuration file '{self.config_path}' not found. "
                "Using default configuration."
            )
            return self.get_default_config()
        
        try:
            # Load YAML file
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            if config_data is None:
                logger.warning(
                    f"Configuration file '{self.config_path}' is empty. "
                    "Using default configuration."
                )
                return self.get_default_config()
            
            # Parse configuration from YAML structure
            config = self._parse_config_data(config_data)
            
            # Validate configuration
            validation_errors = self.validate_config(config)
            if validation_errors:
                logger.warning(
                    f"Configuration validation errors found:\n" +
                    "\n".join(f"  - {error}" for error in validation_errors) +
                    "\nUsing default values for invalid settings."
                )
                # Apply defaults for invalid values
                config = self._apply_defaults_for_invalid_values(config, validation_errors)
            
            logger.info(f"Configuration loaded successfully from '{self.config_path}'")
            return config
            
        except yaml.YAMLError as e:
            logger.error(
                f"Failed to parse YAML configuration file '{self.config_path}': {e}. "
                "Using default configuration."
            )
            return self.get_default_config()
        except Exception as e:
            logger.error(
                f"Unexpected error loading configuration from '{self.config_path}': {e}. "
                "Using default configuration."
            )
            return self.get_default_config()
    
    def _parse_config_data(self, config_data: dict) -> Configuration:
        """
        Parse configuration data from YAML structure into Configuration object.
        
        Args:
            config_data: Dictionary loaded from YAML file
            
        Returns:
            Configuration object
        """
        # Get default config as base
        default = self.get_default_config()
        
        # Extract nested configuration sections
        obj_detect = config_data.get('object_detection', {})
        motion_detect = config_data.get('motion_detection', {})
        display = config_data.get('display', {})
        snapshot = config_data.get('snapshot', {})
        logging_config = config_data.get('logging', {})
        alerts = config_data.get('alerts', {})
        performance = config_data.get('performance', {})
        
        # Build Configuration object with values from YAML or defaults
        return Configuration(
            # Object Detection
            model_path=obj_detect.get('model_path', default.model_path),
            detection_threshold=obj_detect.get('detection_threshold', default.detection_threshold),
            target_classes=obj_detect.get('target_classes', default.target_classes),
            
            # Motion Detection
            motion_sensitivity=motion_detect.get('sensitivity', default.motion_sensitivity),
            motion_min_area=motion_detect.get('min_area', default.motion_min_area),
            
            # Display
            display_enabled=display.get('enabled', default.display_enabled),
            window_name=display.get('window_name', default.window_name),
            
            # Snapshot
            snapshot_enabled=snapshot.get('enabled', default.snapshot_enabled),
            snapshot_directory=snapshot.get('directory', default.snapshot_directory),
            snapshot_rate_limit=snapshot.get('rate_limit', default.snapshot_rate_limit),
            
            # Logging
            log_directory=logging_config.get('directory', default.log_directory),
            log_max_size_mb=logging_config.get('max_size_mb', default.log_max_size_mb),
            
            # Alerts
            alert_classes=alerts.get('classes', default.alert_classes),
            alert_cooldown=alerts.get('cooldown', default.alert_cooldown),
            
            # Performance
            target_fps=performance.get('target_fps', default.target_fps),
            preprocessing_enabled=performance.get('preprocessing_enabled', default.preprocessing_enabled),
            resize_width=performance.get('resize_width', default.resize_width),
        )
    
    @staticmethod
    def get_default_config() -> Configuration:
        """
        Get default configuration values.
        
        Returns:
            Configuration object with default values
        """
        return Configuration()
    
    @staticmethod
    def validate_config(config: Configuration) -> List[str]:
        """
        Validate configuration values.
        
        Args:
            config: Configuration object to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate detection_threshold range (0.1 to 0.9)
        if not isinstance(config.detection_threshold, (int, float)):
            errors.append(
                f"detection_threshold must be a number, got {type(config.detection_threshold).__name__}"
            )
        elif not (0.1 <= config.detection_threshold <= 0.9):
            errors.append(
                f"detection_threshold must be between 0.1 and 0.9, got {config.detection_threshold}"
            )
        
        # Validate motion_sensitivity enum
        valid_sensitivities = ['low', 'medium', 'high']
        if not isinstance(config.motion_sensitivity, str):
            errors.append(
                f"motion_sensitivity must be a string, got {type(config.motion_sensitivity).__name__}"
            )
        elif config.motion_sensitivity not in valid_sensitivities:
            errors.append(
                f"motion_sensitivity must be one of {valid_sensitivities}, "
                f"got '{config.motion_sensitivity}'"
            )
        
        # Validate motion_min_area (positive integer)
        if not isinstance(config.motion_min_area, int):
            errors.append(
                f"motion_min_area must be an integer, got {type(config.motion_min_area).__name__}"
            )
        elif config.motion_min_area < 1:
            errors.append(
                f"motion_min_area must be positive, got {config.motion_min_area}"
            )
        
        # Validate snapshot_rate_limit (positive number)
        if not isinstance(config.snapshot_rate_limit, (int, float)):
            errors.append(
                f"snapshot_rate_limit must be a number, got {type(config.snapshot_rate_limit).__name__}"
            )
        elif config.snapshot_rate_limit < 0:
            errors.append(
                f"snapshot_rate_limit must be non-negative, got {config.snapshot_rate_limit}"
            )
        
        # Validate log_max_size_mb (positive integer)
        if not isinstance(config.log_max_size_mb, int):
            errors.append(
                f"log_max_size_mb must be an integer, got {type(config.log_max_size_mb).__name__}"
            )
        elif config.log_max_size_mb < 1:
            errors.append(
                f"log_max_size_mb must be positive, got {config.log_max_size_mb}"
            )
        
        # Validate alert_cooldown (non-negative number)
        if not isinstance(config.alert_cooldown, (int, float)):
            errors.append(
                f"alert_cooldown must be a number, got {type(config.alert_cooldown).__name__}"
            )
        elif config.alert_cooldown < 0:
            errors.append(
                f"alert_cooldown must be non-negative, got {config.alert_cooldown}"
            )
        
        # Validate target_fps (positive integer)
        if not isinstance(config.target_fps, int):
            errors.append(
                f"target_fps must be an integer, got {type(config.target_fps).__name__}"
            )
        elif config.target_fps < 1:
            errors.append(
                f"target_fps must be positive, got {config.target_fps}"
            )
        
        # Validate target_classes (non-empty list of strings)
        if not isinstance(config.target_classes, list):
            errors.append(
                f"target_classes must be a list, got {type(config.target_classes).__name__}"
            )
        elif len(config.target_classes) == 0:
            errors.append("target_classes must not be empty")
        elif not all(isinstance(cls, str) for cls in config.target_classes):
            errors.append("target_classes must contain only strings")
        
        # Validate alert_classes (list of strings)
        if not isinstance(config.alert_classes, list):
            errors.append(
                f"alert_classes must be a list, got {type(config.alert_classes).__name__}"
            )
        elif not all(isinstance(cls, str) for cls in config.alert_classes):
            errors.append("alert_classes must contain only strings")
        
        # Validate resize_width (positive integer or None)
        if config.resize_width is not None:
            if not isinstance(config.resize_width, int):
                errors.append(
                    f"resize_width must be an integer or null, got {type(config.resize_width).__name__}"
                )
            elif config.resize_width < 1:
                errors.append(
                    f"resize_width must be positive, got {config.resize_width}"
                )
        
        # Validate boolean fields
        bool_fields = [
            ('display_enabled', config.display_enabled),
            ('snapshot_enabled', config.snapshot_enabled),
            ('preprocessing_enabled', config.preprocessing_enabled),
        ]
        for field_name, field_value in bool_fields:
            if not isinstance(field_value, bool):
                errors.append(
                    f"{field_name} must be a boolean, got {type(field_value).__name__}"
                )
        
        # Validate string fields (non-empty)
        string_fields = [
            ('model_path', config.model_path),
            ('window_name', config.window_name),
            ('snapshot_directory', config.snapshot_directory),
            ('log_directory', config.log_directory),
        ]
        for field_name, field_value in string_fields:
            if not isinstance(field_value, str):
                errors.append(
                    f"{field_name} must be a string, got {type(field_value).__name__}"
                )
            elif len(field_value.strip()) == 0:
                errors.append(f"{field_name} must not be empty")
        
        return errors
    
    def _apply_defaults_for_invalid_values(
        self, 
        config: Configuration, 
        validation_errors: List[str]
    ) -> Configuration:
        """
        Apply default values for configuration fields that have validation errors.
        
        Args:
            config: Configuration object with potentially invalid values
            validation_errors: List of validation error messages
            
        Returns:
            Configuration object with defaults applied for invalid fields
        """
        default = self.get_default_config()
        
        # Create a mapping of field names mentioned in errors to default values
        error_text = " ".join(validation_errors).lower()
        
        # Check each field and apply default if it appears in errors
        if 'detection_threshold' in error_text:
            config.detection_threshold = default.detection_threshold
            logger.info(f"Using default detection_threshold: {default.detection_threshold}")
        
        if 'motion_sensitivity' in error_text:
            config.motion_sensitivity = default.motion_sensitivity
            logger.info(f"Using default motion_sensitivity: {default.motion_sensitivity}")
        
        if 'motion_min_area' in error_text:
            config.motion_min_area = default.motion_min_area
            logger.info(f"Using default motion_min_area: {default.motion_min_area}")
        
        if 'snapshot_rate_limit' in error_text:
            config.snapshot_rate_limit = default.snapshot_rate_limit
            logger.info(f"Using default snapshot_rate_limit: {default.snapshot_rate_limit}")
        
        if 'log_max_size_mb' in error_text:
            config.log_max_size_mb = default.log_max_size_mb
            logger.info(f"Using default log_max_size_mb: {default.log_max_size_mb}")
        
        if 'alert_cooldown' in error_text:
            config.alert_cooldown = default.alert_cooldown
            logger.info(f"Using default alert_cooldown: {default.alert_cooldown}")
        
        if 'target_fps' in error_text:
            config.target_fps = default.target_fps
            logger.info(f"Using default target_fps: {default.target_fps}")
        
        if 'target_classes' in error_text:
            config.target_classes = default.target_classes
            logger.info(f"Using default target_classes: {default.target_classes}")
        
        if 'alert_classes' in error_text:
            config.alert_classes = default.alert_classes
            logger.info(f"Using default alert_classes: {default.alert_classes}")
        
        if 'resize_width' in error_text:
            config.resize_width = default.resize_width
            logger.info(f"Using default resize_width: {default.resize_width}")
        
        if 'display_enabled' in error_text:
            config.display_enabled = default.display_enabled
            logger.info(f"Using default display_enabled: {default.display_enabled}")
        
        if 'snapshot_enabled' in error_text:
            config.snapshot_enabled = default.snapshot_enabled
            logger.info(f"Using default snapshot_enabled: {default.snapshot_enabled}")
        
        if 'preprocessing_enabled' in error_text:
            config.preprocessing_enabled = default.preprocessing_enabled
            logger.info(f"Using default preprocessing_enabled: {default.preprocessing_enabled}")
        
        if 'model_path' in error_text:
            config.model_path = default.model_path
            logger.info(f"Using default model_path: {default.model_path}")
        
        if 'window_name' in error_text:
            config.window_name = default.window_name
            logger.info(f"Using default window_name: {default.window_name}")
        
        if 'snapshot_directory' in error_text:
            config.snapshot_directory = default.snapshot_directory
            logger.info(f"Using default snapshot_directory: {default.snapshot_directory}")
        
        if 'log_directory' in error_text:
            config.log_directory = default.log_directory
            logger.info(f"Using default log_directory: {default.log_directory}")
        
        return config
