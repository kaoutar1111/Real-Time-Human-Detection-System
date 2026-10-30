
print("Downloading YOLOv8n model...")

import requests
import os

url = "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolov8n.pt"
output_path = "yolov8n.pt"

try:
    print(f"Downloading from: {url}")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    print(f"Total size: {total_size / (1024*1024):.2f} MB")
    
    downloaded = 0
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\rDownloading: {percent:.1f}% ({downloaded/(1024*1024):.2f} MB / {total_size/(1024*1024):.2f} MB)", end="", flush=True)
    
    print(f"\n✓ Download complete!")
    print(f"✓ File saved: {output_path}")
    print(f"✓ File size: {os.path.getsize(output_path) / (1024*1024):.2f} MB")
    
    # Verify the file
    print("\nVerifying model...")
    from ultralytics import YOLO
    model = YOLO(output_path)
    print(f"✓ Model loaded successfully!")
    print(f"✓ Model classes: {len(model.names)}")
    print(f"✓ Ready for person detection!")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
