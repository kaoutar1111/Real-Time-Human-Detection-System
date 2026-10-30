
import os
import sys

print("=== YOLO Model Download and Test ===")
print()

# Set environment to avoid network issues
os.environ['YOLO_VERBOSE'] = 'False'

try:
    from ultralytics import YOLO
    print("1. Attempting to download YOLOv8n model using ultralytics...")
    print("   This may take a few minutes on first run...")
    print()
    
    # This will download from ultralytics servers (more reliable than GitHub)
    model = YOLO('yolov8n.pt')
    
    print()
    print("✓ Model downloaded successfully!")
    print(f"✓ Model: {model}")
    print(f"✓ Classes: {len(model.names)}")
    
    # Verify by running inference
    print()
    print("2. Testing model with dummy image...")
    import numpy as np
    test_img = np.zeros((640, 640, 3), dtype=np.uint8)
    results = model(test_img, verbose=False)
    print(f"✓ Inference successful! Results: {len(results)}")
    
    print()
    print("✓✓✓ Model is ready! You can now run main.py ✓✓✓")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    
    print()
    print("Alternative: Please download the model manually:")
    print("1. Visit: https://huggingface.co/ultralyticsplus/yolov8n/resolve/main/yolov8n.pt")
    print("2. Save the file as 'yolov8n.pt' in the project folder")
    print("3. Run the program again")
