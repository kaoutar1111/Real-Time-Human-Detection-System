import cv2
import numpy as np
from ultralytics import YOLO

class YoloDetector:
    def __init__(self, model_name='yolov8n.pt'):
        self.model = None
        self.model_name = model_name
        self.conf_threshold = 0.5
        self.iou_threshold = 0.45
        self.enabled = False
        self.class_names = []

    def load_model(self, model_name=None):
        if model_name:
            self.model_name = model_name
        try:
            print(f"Loading YOLO model: {self.model_name}")
            self.model = YOLO(self.model_name)
            self.class_names = list(self.model.names.values())
            print(f"✓ YOLO model '{self.model_name}' loaded successfully!")
            print(f"  Number of classes: {len(self.class_names)}")
            return True
        except Exception as e:
            print(f"✗ Failed to load YOLO model: {e}")
            import traceback
            traceback.print_exc()
            return False

    def set_confidence(self, conf):
        self.conf_threshold = conf

    def set_iou(self, iou):
        self.iou_threshold = iou

    def toggle(self):
        self.enabled = not self.enabled
        if self.enabled and self.model is None:
            self.load_model()
        return self.enabled

    def detect(self, img):
        if not self.enabled or self.model is None:
            return img, []

        try:
            results = self.model(
                img,
                conf=self.conf_threshold,
                iou=self.iou_threshold,
                verbose=False
            )

            detections = []
            if results and len(results) > 0:
                result = results[0]
                if result.boxes is not None and len(result.boxes) > 0:
                    boxes = result.boxes.xyxy.cpu().numpy()
                    confs = result.boxes.conf.cpu().numpy()
                    classes = result.boxes.cls.cpu().numpy().astype(int)

                    for box, conf, cls in zip(boxes, confs, classes):
                        x1, y1, x2, y2 = map(int, box)
                        detections.append({
                            'bbox': [x1, y1, x2, y2],
                            'confidence': float(conf),
                            'class': int(cls),
                            'name': self.class_names[int(cls)] if int(cls) < len(self.class_names) else f'class_{cls}'
                        })

                        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

                        label = f"{detections[-1]['name']}: {conf:.2f}"
                        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                        cv2.rectangle(img, (x1, y1 - label_size[1] - 10), (x1 + label_size[0], y1), (0, 255, 0), -1)
                        cv2.putText(img, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

            return img, detections
        except Exception as e:
            print(f"YOLO detection error: {e}")
            return img, []
