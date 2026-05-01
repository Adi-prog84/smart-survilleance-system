"""
Main entry point for the Smart Surveillance System.

This script initializes the system, loads configuration, and starts
the surveillance loop.
"""

import sys
import argparse
import logging
from pathlib import Path

from src.config_manager import ConfigurationManager
from src.surveillance_system import SurveillanceSystem


def setup_logging(verbose: bool = False) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        verbose: Enable verbose (DEBUG) logging
        
    Returns:
        Configured logger instance
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    return logging.getLogger(__name__)


def parse_arguments():
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description='Smart Surveillance System - Real-time object and motion detection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Run with default config.yaml
  python main.py -c custom.yaml     # Run with custom configuration
  python main.py -v                 # Run with verbose logging
  
Keyboard Controls:
  Q - Quit the application
  P - Pause surveillance
  R - Resume surveillance
  S - Save manual snapshot
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose (DEBUG) logging'
    )
    
    return parser.parse_args()


def display_startup_info(config, logger):
    """
    Display startup information.
    
    Args:
        config: Configuration object
        logger: Logger instance
    """
    logger.info("=" * 60)
    logger.info("Smart Surveillance System")
    logger.info("=" * 60)
    logger.info(f"Model: {config.model_path}")
    logger.info(f"Detection Threshold: {config.detection_threshold}")
    logger.info(f"Target Classes: {', '.join(config.target_classes)}")
    logger.info(f"Motion Sensitivity: {config.motion_sensitivity}")
    logger.info(f"Snapshot Enabled: {config.snapshot_enabled}")
    logger.info(f"Alert Classes: {', '.join(config.alert_classes)}")
    logger.info("=" * 60)


def main():
    """Main entry point."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Set up logging
    logger = setup_logging(verbose=args.verbose)
    
    try:
        # Load configuration
        logger.info(f"Loading configuration from: {args.config}")
        config_manager = ConfigurationManager(args.config)
        config = config_manager.get_config()
        
        # Display startup information
        display_startup_info(config, logger)
        
        # Create and run surveillance system
        system = SurveillanceSystem(config, logger=logger)
        system.run()
        
        logger.info("Surveillance system exited normally")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        logger.info("Using default configuration...")
        
        try:
            # Try with default configuration
            config = ConfigurationManager.get_default_config()
            display_startup_info(config, logger)
            
            system = SurveillanceSystem(config, logger=logger)
            system.run()
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to start with default configuration: {e}")
            return 1
    
    except RuntimeError as e:
        logger.error(f"Initialization error: {e}")
        logger.error("Please check:")
        logger.error("  1. Webcam is connected and not in use by another application")
        logger.error("  2. YOLO model file exists (will be downloaded on first run)")
        logger.error("  3. Required dependencies are installed (pip install -r requirements.txt)")
        return 1
    
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt (Ctrl+C)")
        return 0
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
