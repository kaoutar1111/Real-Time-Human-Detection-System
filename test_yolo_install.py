
import sys
import os

print("=== Python Environment ===")
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

print("\n=== Checking Dependencies ===")
try:
    import ultralytics
    print(f"✓ ultralytics installed: version {ultralytics.__version__}")
except ImportError as e:
    print(f"✗ ultralytics NOT installed: {e}")

try:
    import torch
    print(f"✓ torch installed: version {torch.__version__}")
except ImportError as e:
    print(f"✗ torch NOT installed: {e}")

try:
    import cv2
    print(f"✓ opencv installed: version {cv2.__version__}")
except ImportError as e:
    print(f"✗ opencv NOT installed: {e}")

try:
    import numpy as np
    print(f"✓ numpy installed: version {np.__version__}")
except ImportError as e:
    print(f"✗ numpy NOT installed: {e}")

print("\n=== Checking Model File ===")
current_dir = os.getcwd()
model_file = "yolov8n.pt"
model_path = os.path.join(current_dir, model_file)

if os.path.exists(model_path):
    size_mb = os.path.getsize(model_path) / (1024 * 1024)
    print(f"✓ Model file found: {model_path}")
    print(f"  File size: {size_mb:.2f} MB")
    
    # Try to load the model
    print("\n=== Testing Model Load ===")
    try:
        from ultralytics import YOLO
        model = YOLO(model_path)
        print(f"✓ Model loaded successfully!")
        print(f"  Model classes: {len(model.names)}")
        
        # Test with a simple image (dummy)
        test_img = np.zeros((640, 640, 3), dtype=np.uint8)
        results = model(test_img, verbose=False)
        print(f"✓ Model inference works!")
        
    except Exception as e:
        print(f"✗ Model load failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"✗ Model file not found: {model_path}")

print("\n=== Test Complete ===")
