"""
条件抽帧 + 异步视频分析
"""
import cv2
import numpy as np
from typing import Callable
from collections import deque


class FrameSampler:
    """条件抽帧器

    三个触发条件：
    A. 画面差分 > 阈值 (OpenCV diff)
    B. 外部触发 (语音提问 / 手动截图)
    C. 定时兜底 (每 30 秒强制抽一帧)
    """

    def __init__(self, diff_threshold: float = 30.0, cooldown: float = 2.0):
        self._prev_frame: np.ndarray | None = None
        self._diff_threshold = diff_threshold
        self._cooldown = cooldown  # 同一触发源冷却时间(秒)
        self._last_trigger_time: dict[str, float] = {}
        self.buffer: deque = deque(maxlen=10)  # 保留最近 10 帧

    def process_frame(self, frame: np.ndarray, timestamp: float, force: bool = False) -> bool:
        """
        处理一帧，判断是否需要触发分析

        返回 True 表示触发分析
        """
        self.buffer.append(frame)

        # 条件 C: 定时兜底 (30秒强制)
        if force:
            return True

        # 条件 A: 画面差分
        if self._prev_frame is not None:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            prev_gray = cv2.cvtColor(self._prev_frame, cv2.COLOR_BGR2GRAY)
            prev_gray = cv2.GaussianBlur(prev_gray, (21, 21), 0)

            diff = cv2.absdiff(gray, prev_gray)
            mean_diff = diff.mean()

            if mean_diff > self._diff_threshold:
                cooldown_key = "motion"
                if timestamp - self._last_trigger_time.get(cooldown_key, 0) > self._cooldown:
                    self._last_trigger_time[cooldown_key] = timestamp
                    self._prev_frame = frame.copy()
                    return True

        self._prev_frame = frame.copy()
        return False

    def trigger_external(self, source: str = "voice"):
        """条件 B: 外部触发"""
        self._last_trigger_time[source] = 0  # 重置冷却
        return True

    def get_latest_frame(self) -> np.ndarray | None:
        """获取最新的可用帧"""
        if self.buffer:
            return self.buffer[-1]
        return None

    def reset(self):
        self._prev_frame = None
        self._last_trigger_time.clear()
        self.buffer.clear()


class VideoAnalyzer:
    """视频分析异步 Worker 池"""

    def __init__(self):
        self.sampler = FrameSampler()

    def analyze_frame(self, frame: np.ndarray, parts_detected: list[str]) -> dict:
        """
        分析一帧 (由 Worker 调用)

        返回:
        {
            "parts": [{"label": "火花塞", "bbox": [...]}],
            "description": "画面中是一个火花塞...",
            "workflow": [...],
        }
        """
        from vision.yolo_detector import yolo
        from knowledge_graph.age_client import age

        result = {"parts": [], "description": "", "workflow": []}

        # 1. YOLO 检测零件
        detections = yolo.detect(frame)
        result["parts"] = detections

        # 2. 如果检测到零件, 查询 AGE 图谱获取步骤
        new_parts = [d["label"] for d in detections if d["label"] not in parts_detected]
        for part in new_parts:
            try:
                steps = age.get_workflow(part)
                if steps:
                    result["workflow"].extend(steps)
            except Exception:
                pass

        return result


analyzer = VideoAnalyzer()
