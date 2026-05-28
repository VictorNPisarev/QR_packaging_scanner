"""Модуль захвата видео с камеры"""

import logging

import cv2
import numpy as np
import numpy.typing as npt

from scanner.models.camera_config import CameraConfig

logger = logging.getLogger(__name__)

Frame = npt.NDArray[np.uint8]


class CameraCapture:
    """Управление захватом видео с камеры"""

    def __init__(self, config: CameraConfig) -> None:
        self.config: CameraConfig = config
        self.cap: cv2.VideoCapture | None = None
        self.is_running: bool = False

    def start(self) -> bool:
        """Запуск захвата видео"""
        try:
            # Передаём device_id как int — это допустимо
            self.cap = cv2.VideoCapture(self.config.device_id)

            if not self.cap.isOpened():
                logger.error(f"Не удалось открыть камеру {self.config.device_id}")
                return False

            # Настройка параметров
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.config.fps)

            if not self.config.auto_exposure:
                self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.0)
                self.cap.set(cv2.CAP_PROP_EXPOSURE, self.config.exposure_value)

            self.is_running = True
            logger.info(
                f"Камера {self.config.device_id} запущена: "
                f"{self.config.width}x{self.config.height}@{self.config.fps}fps"
            )
            return True

        except Exception as e:
            logger.exception(f"Ошибка запуска камеры: {e}")
            return False

    def get_frame(self) -> tuple[bool, Frame | None]:
        """Получение кадра с камеры"""
        if not self.is_running or self.cap is None:
            return False, None

        ret: bool
        raw_frame: np.ndarray | None
        ret, raw_frame = self.cap.read()

        if not ret or raw_frame is None:
            logger.warning("Не удалось получить кадр")
            return False, None

        # Явно приводим к нужному типу
        frame: Frame = np.asarray(raw_frame, dtype=np.uint8)

        return True, frame

    def stop(self) -> None:
        """Остановка захвата"""
        self.is_running = False
        if self.cap is not None:
            self.cap.release()
            logger.info("Камера остановлена")
