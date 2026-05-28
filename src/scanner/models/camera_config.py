"""Конфигурация камеры"""

from dataclasses import dataclass


@dataclass
class CameraConfig:
    """Конфигурация камеры"""

    device_id: int = 0
    width: int = 1280
    height: int = 720
    fps: int = 30
    auto_exposure: bool = True
    exposure_value: int = -6
