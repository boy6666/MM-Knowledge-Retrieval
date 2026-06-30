"""
YOLOv8n ONNX 零件检测
"""
import numpy as np
import cv2
from pathlib import Path
from config.settings import settings


class YOLODetector:
    """YOLOv8n ONNX 推理引擎"""

    def __init__(self):
        self._session = None
        self._labels = [
            "零件", "螺栓", "螺母", "垫圈", "轴承",
            "火花塞", "活塞", "气缸", "齿轮", "链条",
            "工具-扳手", "工具-螺丝刀", "工具-套筒", "工具-塞尺",
        ]

    @property
    def session(self):
        if self._session is None:
            import onnxruntime
            model_path = settings.YOLO_MODEL_PATH
            if not Path(model_path).exists():
                raise FileNotFoundError(f"YOLO 模型未找到: {model_path}")
            self._session = onnxruntime.InferenceSession(model_path)
        return self._session

    def detect(self, image: np.ndarray) -> list[dict]:
        """
        检测单张图片中的零件/工具

        返回:
        [{"label": "火花塞", "confidence": 0.92, "bbox": [x1,y1,x2,y2]}, ...]
        """
        # 预处理
        h, w = image.shape[:2]
        input_blob = cv2.dnn.blobFromImage(
            image, 1/255.0, (640, 640), swapRB=True, crop=False
        )

        # 推理
        inputs = {self.session.get_inputs()[0].name: input_blob}
        outputs = self.session.run(None, inputs)

        # 后处理
        results = []
        detections = outputs[0][0]
        for det in detections:
            scores = det[4:]
            class_id = scores.argmax()
            confidence = scores[class_id].item()
            if confidence < settings.YOLO_CONFIDENCE:
                continue

            x_center, y_center, box_w, box_h = det[:4]
            x1 = int((x_center - box_w / 2) * w / 640)
            y1 = int((y_center - box_h / 2) * h / 640)
            x2 = int((x_center + box_w / 2) * w / 640)
            y2 = int((y_center + box_h / 2) * h / 640)

            results.append({
                "label": self._labels[class_id] if class_id < len(self._labels) else f"零件_{class_id}",
                "confidence": round(confidence, 3),
                "bbox": [x1, y1, x2, y2],
            })

        return results

    def detect_from_path(self, image_path: str) -> list[dict]:
        """从文件路径检测"""
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"图片不存在: {image_path}")
        return self.detect(image)

    def draw_boxes(self, image: np.ndarray, detections: list[dict]) -> np.ndarray:
        """在图片上绘制检测框"""
        img = image.copy()
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            label = f"{det['label']} {det['confidence']:.2f}"
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img, label, (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return img

    @property
    def is_loaded(self) -> bool:
        return self._session is not None


yolo = YOLODetector()
