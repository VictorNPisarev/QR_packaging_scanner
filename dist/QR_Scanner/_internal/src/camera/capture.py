"""Модуль захвата видео с камеры"""

import logging
from dataclasses import dataclass

import cv2
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class CameraConfig:
    """Конфигурация камеры"""

    device_id: int = 0
    width: int = 1280
    height: int = 720
    fps: int = 30
    auto_exposure: bool = True
    exposure_value: int = -6  # Для USB камер часто лучше уменьшить


class CameraCapture:
    """Управление захватом видео с камеры"""

    def __init__(self, config: CameraConfig):
        self.config = config
        self.cap: cv2.VideoCapture | None = None
        self.is_running = False

    def start(self) -> bool:
        """Запуск захвата видео"""
        try:
            self.cap = cv2.VideoCapture(self.config.device_id)

            # Настройка параметров
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.config.fps)

            # Проверка, что камера открылась
            if not self.cap.isOpened():
                logger.error(f"Не удалось открыть камеру {self.config.device_id}")
                return False

            # Настройка автоэкспозиции
            if not self.config.auto_exposure:
                self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
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

    def get_frame(self) -> tuple[bool, np.ndarray | None]:
        """Получение кадра с камеры"""
        if not self.is_running or self.cap is None:
            return False, None

        ret, frame = self.cap.read()
        if not ret:
            logger.warning("Не удалось получить кадр")
            return False, None

        return True, frame

    def stop(self) -> None:
        """Остановка захвата"""
        self.is_running = False
        if self.cap:
            self.cap.release()
            logger.info("Камера остановлена")
