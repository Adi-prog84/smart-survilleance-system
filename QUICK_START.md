# Quick Start Guide

Get your Smart Surveillance System running in 3 simple steps!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- OpenCV (video processing)
- YOLOv8 (object detection AI)
- NumPy (numerical operations)
- PyYAML (configuration)
- Testing libraries

## Step 2: Run the System

```bash
python main.py
```

On first run, YOLOv8 will automatically download (~6MB). This takes about 30 seconds.

## Step 3: Use the System

The video window will open showing your webcam feed.

**Keyboard Controls:**
- **Q** - Quit
- **P** - Pause
- **R** - Resume
- **S** - Save snapshot

## What You'll See

- **Green boxes** = Detected objects (person, car, etc.)
- **Blue boxes** = Motion detected
- **Red banner** = Alert (when person detected)
- **Top-left corner** = FPS and detection count

## Output Files

- **logs/** - Detection events in JSON format
- **snapshots/** - Saved images with detections

## Customize Settings

Edit `config.yaml` to change:
- Which objects to detect
- Motion sensitivity
- Alert settings
- And more!

## Troubleshooting

**Webcam not working?**
- Close other apps using the webcam (Zoom, Skype, etc.)
- Check webcam permissions

**Slow performance?**
- The system runs at 10-30 FPS depending on your hardware
- Lower detection threshold in config.yaml for better performance

**Need help?**
- Check README.md for detailed documentation
- Review logs/ directory for error messages

## Example Configuration

Want to detect only people and cars?

Edit `config.yaml`:
```yaml
object_detection:
  target_classes:
    - person
    - car
```

Want higher motion sensitivity?

```yaml
motion_detection:
  sensitivity: "high"  # Options: low, medium, high
```

## Next Steps

- Review README.md for full documentation
- Explore the logs/ directory to see detection data
- Check snapshots/ for saved images
- Customize config.yaml for your needs

Enjoy your Smart Surveillance System! 🎥
