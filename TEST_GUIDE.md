# Quick Test Guide

## How to Test Your Surveillance System

### Step 1: Start the System

```bash
python main.py
```

Wait for:
- "Smart Surveillance System initialized successfully"
- Video window to open

### Step 2: Test Each Object

**Test 1: Person Detection** 👤
- Stand in front of the camera
- You should see a **green box** around you
- Label: "person 0.XX" (confidence score)
- **Red banner** at top: "ALERT: Person detected!"

**Test 2: Book Detection** 📚
- Hold a book in front of the camera
- Show the cover clearly
- You should see a **green box** around the book
- Label: "book 0.XX"

**Test 3: Phone Detection** 📱
- Hold your phone in front of the camera
- Show the screen or back
- You should see a **green box** around the phone
- Label: "cell phone 0.XX"

**Test 4: Bottle/Pen Detection** 🖊️
- Hold a bottle or pen vertically
- Keep it in view for a moment
- You should see a **green box**
- Label: "bottle 0.XX"

**Test 5: Motion Detection** 💨
- Wave your hand in front of the camera
- You should see **blue boxes** around moving areas
- Label: "Motion (XXXXpx)"

### Step 3: Check Outputs

**Snapshots** (saved automatically):
```bash
# Check the snapshots folder
ls snapshots/
# or on Windows:
dir snapshots\
```

You should see files like:
- `snapshot_2024-01-15_10-30-45-123.jpg`

**Event Logs**:
```bash
# Check the logs folder
ls logs/
# or on Windows:
dir logs\
```

You should see files like:
- `surveillance_2024-01-15.jsonl`

View the log:
```bash
# On Linux/Mac:
cat logs/surveillance_*.jsonl

# On Windows:
type logs\surveillance_*.jsonl
```

### Step 4: Keyboard Controls

While the system is running:

- **Q** - Quit the system
- **P** - Pause (freezes detection)
- **R** - Resume (after pause)
- **S** - Save manual snapshot

### What You Should See

**On Screen:**
```
┌─────────────────────────────────────────┐
│ FPS: 25.3                               │ ← Performance info
│ Detections: 2                           │
│                                         │
│     ┌──────────────┐                   │
│     │ person 0.87  │ ← Green box       │
│     └──────────────┘                   │
│                                         │
│         ┌────────────┐                 │
│         │ book 0.72  │ ← Green box     │
│         └────────────┘                 │
│                                         │
│    ┌─────────────┐                     │
│    │ Motion (1500px) │ ← Blue box      │
│    └─────────────┘                     │
└─────────────────────────────────────────┘
```

**If Alert Triggered:**
```
┌─────────────────────────────────────────┐
│ ALERT: Person detected!                 │ ← Red banner
├─────────────────────────────────────────┤
│ FPS: 25.3                               │
│ Detections: 1                           │
│     ┌──────────────┐                   │
│     │ person 0.87  │                   │
│     └──────────────┘                   │
└─────────────────────────────────────────┘
```

### Troubleshooting

**Nothing detected?**
1. Check lighting - make sure room is bright
2. Move closer to camera (arm's length)
3. Hold objects clearly in view
4. Wait a moment (detection takes 50-200ms)

**Low FPS (< 10)?**
1. Close other applications
2. Use better lighting (reduces processing)
3. Your computer might be slower - this is normal

**Webcam not opening?**
1. Close other apps using webcam (Zoom, Skype, etc.)
2. Check webcam permissions
3. Try unplugging and replugging USB webcam

**Objects detected incorrectly?**
- This is normal! AI isn't perfect
- Try different angles
- Ensure good lighting
- Hold objects more clearly

### Expected Performance

- **FPS**: 10-30 (depends on your computer)
- **Detection Time**: 50-200ms per frame
- **Objects**: person, book, cell phone, bottle

### Success Criteria

✅ Video window opens
✅ You can see yourself (person detected)
✅ Green boxes appear around objects
✅ Blue boxes appear when you move
✅ Red alert appears when person detected
✅ Snapshots saved to snapshots/ folder
✅ Events logged to logs/ folder
✅ Keyboard controls work (Q to quit)

If all of the above work, **your system is working perfectly!** 🎉

### Next Steps

1. **Show it off** - Demonstrate to your instructor
2. **Customize** - Edit config.yaml to change settings
3. **Document** - Take screenshots for your report
4. **Experiment** - Try different objects and lighting

Enjoy your Smart Surveillance System! 🎥
