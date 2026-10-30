
import os
import shutil

# Clean any local model files
model_files = ['yolov8n.pt', 'yolov8s.pt', 'yolov8m.pt', 'yolov8l.pt', 'yolov8x.pt']
for model in model_files:
    if os.path.exists(model):
        print(f"Removing local model file: {model}")
        os.remove(model)

# Clean ultralytics cache
home_dir = os.path.expanduser('~')
cache_dir = os.path.join(home_dir, '.cache', 'ultralytics')
if os.path.exists(cache_dir):
    print(f"Cleaning up model cache: {cache_dir}")
    try:
        shutil.rmtree(cache_dir)
        print("Cache cleaned successfully")
    except Exception as e:
        print(f"Error cleaning cache: {e}")

# Also check current directory for any model files
print("\nChecking current directory...")
current_dir = os.getcwd()
files = os.listdir(current_dir)
pt_files = [f for f in files if f.endswith('.pt')]
if pt_files:
    print(f"Found model files: {pt_files}")
    for f in pt_files:
        try:
            os.remove(f)
            print(f"Removed: {f}")
        except Exception as e:
            print(f"Error removing {f}: {e}")
else:
    print("No model files found in current directory")

print("\nModel cleanup complete!")
