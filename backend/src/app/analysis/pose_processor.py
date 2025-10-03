"""
Модуль для инкапсуляции логики работы с MediaPipe.

Отвечает за обработку отдельных кадров для извлечения ключевых точек позы.
Использует новый API MediaPipe Tasks.
"""

import os
from typing import List, Optional, TypeAlias

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.framework.formats import landmark_pb2
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from numpy.typing import NDArray

# Определяем путь к модели относительно текущего файла.
# Это делает код независимым от того, откуда он запускается.
_MODEL_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(_MODEL_DIR, "pose_landmarker_lite.task")

# Создаем псевдоним типа для наглядности: массив NumPy с 8-битными целыми числами
# Явно указываем, что это TypeAlias для mypy в строгом режиме.
NDArrayU8: TypeAlias = NDArray[np.uint8]


class PoseProcessor:
    """
    Класс-обертка для MediaPipe PoseLandmarker, который обрабатывает изображения
    и извлекает координаты ключевых точек (landmarks).
    """

    def __init__(self) -> None:
        """Инициализирует модель MediaPipe PoseLandmarker."""
        base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
        # Настраиваем опции для детектора поз
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            # Режим обработки одиночных изображений
            running_mode=vision.RunningMode.IMAGE,
            # Искать только одного человека
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        # Создаем сам детектор
        self.landmarker = vision.PoseLandmarker.create_from_options(options)

    def get_landmarks(
        self, frame: NDArrayU8
    ) -> Optional[List[landmark_pb2.NormalizedLandmark]]:
        """
        Обрабатывает один кадр и возвращает список ключевых точек.

        Args:
            frame: Кадр видео в формате NumPy array (BGR, uint8).

        Returns:
            Список ключевых точек (landmarks) или None, если поза не обнаружена.
        """
        # MediaPipe ожидает RGB, а OpenCV по умолчанию использует BGR
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Конвертируем кадр в формат, понятный MediaPipe
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # Обнаруживаем позу на изображении
        detection_result = self.landmarker.detect(mp_image)

        if detection_result.pose_landmarks:
            # Возвращаем список точек для первого обнаруженного человека
            # Mypy не может вывести этот тип из-за неполных стабов в mediapipe,
            # поэтому мы явно его игнорируем.
            return detection_result.pose_landmarks[0]  # type: ignore[no-any-return]

        return None

    def close(self) -> None:
        """Освобождает ресурсы модели MediaPipe."""
        if hasattr(self.landmarker, "close"):
            self.landmarker.close()
