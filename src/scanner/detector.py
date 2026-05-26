"""Детектор QR-кодов через OpenCV"""

import logging
from dataclasses import dataclass

import cv2
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class BarcodeDetection:
    """Результат детекции QR-кода"""

    data: str
    barcode_type: str = "QR"
    position: tuple[int, int, int, int] = (0, 0, 0, 0)  # x, y, width, height
    confidence: float = 1.0


class BarcodeDetector:
    """Детектор QR-кодов на изображении"""

    def __init__(self, scan_region: tuple[int, int, int, int] | None = None) -> None:
        self.scan_region: tuple[int, int, int, int] | None = scan_region
        self.qr_detector: cv2.QRCodeDetector = cv2.QRCodeDetector()

    def set_scan_region(self, region: tuple[int, int, int, int] | None) -> None:
        """Установка области сканирования"""
        self.scan_region = region
        if region is not None:
            x, y, w, h = region
            logger.info(f"Область сканирования: x={x}, y={y}, w={w}, h={h}")
        else:
            logger.info("Сканирование по всему кадру")

    def detect(self, frame: np.ndarray) -> list[BarcodeDetection]:
        """Поиск QR-кодов на кадре"""
        results: list[BarcodeDetection] = []

        try:
            # Вырезаем область интереса если задана
            if self.scan_region is not None:
                x, y, w, h = self.scan_region
                roi: np.ndarray = frame[y : y + h, x : x + w]
                data, points, straight_qrcode = self.qr_detector.detectAndDecode(roi)

                if data:
                    # Вычисляем позицию относительно ROI
                    if points is not None:
                        # points - это 4 угла QR-кода
                        px, py = int(points[0][0][0]), int(points[0][0][1])
                        pw = int(max(p[0][0] for p in points) - min(p[0][0] for p in points))
                        ph = int(max(p[0][1] for p in points) - min(p[0][1] for p in points))
                        position = (x + px, y + py, pw, ph)
                    else:
                        position = (x, y, w, h)

                    detection = BarcodeDetection(data=data, position=position, confidence=1.0)
                    results.append(detection)
            else:
                data, points, _ = self.qr_detector.detectAndDecode(frame)

                if data:
                    if points is not None:
                        px = int(points[0][0][0])
                        py = int(points[0][0][1])
                        pw = int(max(p[0][0] for p in points) - min(p[0][0] for p in points))
                        ph = int(max(p[0][1] for p in points) - min(p[0][1] for p in points))
                        position = (px, py, pw, ph)
                    else:
                        h, w = frame.shape[:2]
                        position = (0, 0, w, h)

                    detection = BarcodeDetection(data=data, position=position, confidence=1.0)
                    results.append(detection)

        except Exception as e:
            logger.error(f"Ошибка детекции QR-кода: {e}")

        return results

    def detect_multiple(self, frame: np.ndarray) -> list[BarcodeDetection]:
        """Поиск нескольких QR-кодов на кадре (более медленный, но точный)"""
        results: list[BarcodeDetection] = []

        try:
            # Используем детектор для множественных QR-кодов
            multi_detector = cv2.QRCodeDetector()

            if self.scan_region is not None:
                x, y, w, h = self.scan_region
                roi = frame[y : y + h, x : x + w]
                retval, decoded_info, points, straight_qrcode = multi_detector.detectAndDecodeMulti(
                    roi
                )

                if retval:
                    for i, data in enumerate(decoded_info):
                        if data:
                            if points is not None and i < len(points):
                                px = int(points[i][0][0][0])
                                py = int(points[i][0][0][1])
                                position = (x + px, y + py, 100, 100)  # Приблизительно
                            else:
                                position = (x, y, w, h)

                            results.append(BarcodeDetection(data=data, position=position))
            else:
                retval, decoded_info, points, _ = multi_detector.detectAndDecodeMulti(frame)

                if retval:
                    for i, data in enumerate(decoded_info):
                        if data:
                            position = (0, 0, 0, 0)
                            if points is not None and i < len(points):
                                px = int(points[i][0][0][0])
                                py = int(points[i][0][0][1])
                                position = (px, py, 100, 100)

                            results.append(BarcodeDetection(data=data, position=position))

        except Exception as e:
            logger.error(f"Ошибка множественной детекции QR-кодов: {e}")

        return results
