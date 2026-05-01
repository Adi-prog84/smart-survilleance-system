# Detected Objects Configuration

Your system is now configured to detect these everyday objects:

## Currently Detecting

✅ **person** - Detects people/humans
✅ **book** - Detects books
✅ **cell phone** - Detects mobile phones/smartphones
✅ **bottle** - Detects bottles (sometimes picks up pens)

## Important Notes

### About Pen Detection
Unfortunately, YOLO's COCO dataset doesn't have a "pen" class. However:
- Pens are sometimes detected as **"bottle"** (similar shape)
- You can try holding the pen vertically for better detection
- Larger pens work better than small ones

### Detection Tips

**For Best Results:**
1. **Good Lighting** - Make sure the room is well-lit
2. **Clear View** - Hold objects in front of the camera
3. **Proper Distance** - Not too close, not too far (arm's length is good)
4. **Steady Hold** - Keep objects still for a moment

**Object-Specific Tips:**
- **Person**: Full face or upper body works best
- **Book**: Show the cover clearly, hold it flat
- **Cell Phone**: Hold it so the screen/back is visible
- **Bottle/Pen**: Hold vertically for better detection

## YOLO COCO Classes Available

If you want to detect other small objects, here are more options:

**Small Objects:**
- book
- cell phone
- bottle
- cup
- wine glass
- fork
- knife
- spoon
- bowl
- laptop
- mouse (computer mouse)
- keyboard
- remote
- scissors
- teddy bear
- hair drier
- toothbrush
- clock
- vase

**To Add More Objects:**
Edit `config.yaml` and add to the `target_classes` list:

```yaml
object_detection:
  target_classes:
    - person
    - book
    - cell phone
    - bottle
    - laptop      # Add this
    - keyboard    # Add this
    - mouse       # Add this
```

## Current Configuration

Your `config.yaml` is set to:
- Detect: person, book, cell phone, bottle
- Alert on: person only
- Confidence threshold: 0.5 (50%)

## Testing Your Setup

1. **Run the system**: `python main.py`
2. **Test each object**:
   - Stand in front of camera (person)
   - Hold up a book
   - Hold up your phone
   - Hold up a bottle or pen
3. **Watch for green boxes** around detected objects
4. **Check the label** above each box

## Troubleshooting

**Object not detected?**
- Increase lighting
- Move closer/farther from camera
- Hold object more clearly
- Lower detection threshold in config.yaml (try 0.3)

**Too many false detections?**
- Increase detection threshold (try 0.7)
- Ensure good lighting
- Remove clutter from background

**Pen not detected?**
- Try holding it vertically like a bottle
- Use a larger/thicker pen
- Consider adding "scissors" to detect pen-like objects

Enjoy your simplified surveillance system! 📱📚🖊️
