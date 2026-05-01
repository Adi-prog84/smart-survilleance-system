# Smart Surveillance System

A real-time surveillance system that uses your laptop's webcam to detect objects and motion. Built with Python, OpenCV, and YOLOv8 for an image processing course project.

## Features

- **Real-time Object Detection**: Detects people, vehicles, animals, and more using YOLOv8 AI model
- **Motion Detection**: Identifies movement using background subtraction algorithms
- **Live Video Display**: Shows video feed with bounding boxes and labels
- **Event Logging**: Records all detections to structured JSON log files
- **Snapshot Capture**: Automatically saves images when objects are detected
- **Alert System**: Generates alerts for specific objects (e.g., person detected)
- **Performance Monitoring**: Tracks FPS and processing metrics
- **Configurable**: Easy YAML configuration for all settings

## Requirements

- Python 3.8 or higher
- Webcam (built-in or USB)
- Windows, macOS, or Linux

## Installation

1. **Clone or download this repository**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

The required packages are:
- opencv-python >= 4.8.0
- numpy >= 1.24.0
- ultralytics >= 8.0.0 (YOLOv8)
- pyyaml >= 6.0
- pytest >= 7.4.0 (for testing)
- hypothesis >= 6.82.0 (for property-based testing)

3. **First run** (downloads YOLOv8 model automatically):
```bash
python main.py
```

The YOLOv8 nano model (~6MB) will be downloaded automatically on first run.

## Usage

### Basic Usage

Run with default configuration:
```bash
python main.py
```

Run with custom configuration:
```bash
python main.py -c my_config.yaml
```

Run with verbose logging:
```bash
python main.py -v
```

### Keyboard Controls

While the system is running:
- **Q** - Quit the application
- **P** - Pause surveillance
- **R** - Resume surveillance (when paused)
- **S** - Save manual snapshot

### Configuration

Edit `config.yaml` to customize the system behavior:

```yaml
# Object Detection Settings
model_path: "yolov8n.pt"              # YOLO model (n=nano, s=small, m=medium, l=large, x=extra-large)
detection_threshold: 0.5               # Confidence threshold (0.1-0.9)
target_classes:                        # Objects to detect
  - person
  - car
  - dog
  - cat
  - bicycle
  - motorcycle

# Motion Detection Settings
motion_sensitivity: "medium"           # low, medium, or high
motion_min_area: 100                   # Minimum pixel area for motion

# Display Settings
display_enabled: true
window_name: "Smart Surveillance"

# Snapshot Settings
snapshot_enabled: true
snapshot_directory: "snapshots"
snapshot_rate_limit: 1.0              # Minimum seconds between snapshots

# Logging Settings
log_directory: "logs"
log_max_size_mb: 10                   # Max log file size before rotation

# Alert Settings
alert_classes:                         # Objects that trigger alerts
  - person
alert_cooldown: 5.0                   # Seconds between alerts for same class

# Performance Settings
target_fps: 10
preprocessing_enabled: false
resize_width: null                    # Set to resize frames (e.g., 640)
```

## Output

### Logs

Event logs are saved in the `logs/` directory in JSON Lines format:
- Filename: `surveillance_YYYY-MM-DD.jsonl`
- Each line is a JSON object with detection or performance data
- Automatic daily rotation and size-based rotation

Example log entry:
```json
{"timestamp": "2024-01-15T10:30:45.123Z", "event_type": "object_detection", "class": "person", "confidence": 0.87, "bbox": {"x": 100, "y": 150, "width": 80, "height": 200}}
```

### Snapshots

Snapshots are saved in the `snapshots/` directory:
- Filename: `snapshot_YYYY-MM-DD_HH-MM-SS-mmm.jpg`
- JPEG format with 90% quality
- Includes detection overlays (bounding boxes and labels)
- Rate-limited to prevent excessive storage usage

## Architecture

The system follows a modular pipeline architecture:

```
Webcam → Video Capture → Processing Pipeline → Display
                              ↓
                    Object Detection (YOLO)
                    Motion Detection (MOG2)
                              ↓
                    Event Logger, Snapshots, Alerts
```

### Components

- **VideoCapture**: Interfaces with webcam hardware
- **ObjectDetector**: YOLOv8-based object detection
- **MotionDetector**: Background subtraction for motion detection
- **ProcessingPipeline**: Orchestrates frame processing
- **DisplayModule**: Renders video with overlays
- **EventLogger**: Logs events to JSON files
- **SnapshotSaver**: Saves frame images
- **AlertGenerator**: Generates alerts for specific detections
- **PerformanceMonitor**: Tracks FPS and metrics

## Troubleshooting

### Webcam Not Found

**Error**: "Failed to open webcam"

**Solutions**:
- Check that your webcam is connected
- Close other applications using the webcam (Zoom, Skype, etc.)
- Try a different camera index: modify `VideoCapture(camera_index=0)` in code
- On Linux, check permissions: `sudo usermod -a -G video $USER`

### Low FPS / Slow Performance

**Solutions**:
- Use a smaller YOLO model: `yolov8n.pt` (nano) is fastest
- Enable preprocessing and resize: set `resize_width: 640` in config
- Reduce detection threshold to process fewer objects
- Close other resource-intensive applications
- Consider GPU acceleration (requires CUDA setup)

### Model Download Fails

**Error**: "Failed to load YOLO model"

**Solutions**:
- Check internet connection (model downloads on first run)
- Manually download model from [Ultralytics](https://github.com/ultralytics/assets/releases)
- Place model file in project directory and update `model_path` in config

### Permission Errors

**Error**: "Permission denied" when creating logs/snapshots

**Solutions**:
- Check write permissions for `logs/` and `snapshots/` directories
- Run with appropriate permissions
- Change output directories in config to a writable location

### Import Errors

**Error**: "ModuleNotFoundError"

**Solutions**:
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (requires 3.8+)
- Use virtual environment to avoid conflicts

## Testing

Run the test suite:
```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# Property-based tests
pytest tests/properties/ -v

# With coverage report
pytest tests/ -v --cov=src --cov-report=html
```

## Project Structure

```
smart-surveillance-system/
├── main.py                 # Entry point
├── config.yaml            # Configuration file
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── src/                  # Source code
│   ├── models.py         # Data models
│   ├── config_manager.py # Configuration management
│   ├── video_capture.py  # Webcam interface
│   ├── object_detector.py # YOLO object detection
│   ├── motion_detector.py # Motion detection
│   ├── processing_pipeline.py # Frame processing
│   ├── display_module.py # Video display
│   ├── event_logger.py   # Event logging
│   ├── snapshot_saver.py # Snapshot saving
│   ├── alert_generator.py # Alert generation
│   ├── performance_monitor.py # Performance tracking
│   ├── surveillance_system.py # Main system
│   └── error_handler.py  # Error handling
├── tests/                # Test suite
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   ├── properties/      # Property-based tests
│   └── fixtures/        # Test fixtures
├── logs/                # Event logs (created at runtime)
└── snapshots/           # Saved images (created at runtime)
```

## Performance

Typical performance on modern hardware:
- **FPS**: 15-30 FPS (depends on model size and hardware)
- **Detection Latency**: 50-200ms per frame
- **Memory Usage**: 200-500 MB
- **CPU Usage**: 30-60% (single core)

## Supported Object Classes

The YOLOv8 model can detect 80 object classes from the COCO dataset:

**People & Animals**: person, cat, dog, horse, sheep, cow, elephant, bear, zebra, giraffe

**Vehicles**: bicycle, car, motorcycle, airplane, bus, train, truck, boat

**Indoor Objects**: chair, couch, bed, dining table, toilet, tv, laptop, mouse, keyboard, cell phone, microwave, oven, toaster, sink, refrigerator, book, clock, vase, scissors, teddy bear, hair drier, toothbrush

**Outdoor Objects**: traffic light, fire hydrant, stop sign, parking meter, bench, bird, backpack, umbrella, handbag, tie, suitcase, frisbee, skis, snowboard, sports ball, kite, baseball bat, baseball glove, skateboard, surfboard, tennis racket

**Food**: bottle, wine glass, cup, fork, knife, spoon, bowl, banana, apple, sandwich, orange, broccoli, carrot, hot dog, pizza, donut, cake

Configure which classes to detect in `config.yaml` under `target_classes`.

## License

This project is created for educational purposes as part of an image processing course.

## Acknowledgments

- **YOLOv8** by [Ultralytics](https://github.com/ultralytics/ultralytics)
- **OpenCV** for computer vision functionality
- **COCO Dataset** for pre-trained model weights

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review the configuration options
3. Check the logs in `logs/` directory for error messages
4. Ensure all dependencies are correctly installed

## Future Enhancements

Potential improvements (not implemented):
- Multiple camera support
- Cloud storage integration
- Web-based dashboard
- Mobile notifications
- Object tracking across frames
- Custom model training
- GPU acceleration support
- Advanced analytics and heatmaps
