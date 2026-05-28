"""Основной сервис сканирования - оркестратор"""

import logging
from datetime import datetime

import cv2
import numpy as np

from src.camera.capture import CameraCapture, CameraConfig
from src.messaging.broker import MessageBroker
from src.messaging.events import BarcodeScannedEvent
from src.scanner.detector import BarcodeDetector
from src.scanner.models import BarcodeDetection
from src.services.deduplication import BarcodeDeduplicator, DeduplicationConfig
from src.ui.overlay import OverlayRenderer

logger = logging.getLogger(__name__)


class ScanService:
    """Главный сервис, объединяющий все компоненты"""

    def __init__(
        self,
        camera_config: CameraConfig,
        broker: MessageBroker,
        scan_region: tuple[int, int, int, int] | None = None,
    ) -> None:
        self.camera: CameraCapture = CameraCapture(camera_config)
        self.detector: BarcodeDetector = BarcodeDetector(scan_region)
        self.deduplicator: BarcodeDeduplicator = BarcodeDeduplicator(DeduplicationConfig())
        self.broker: MessageBroker = broker
        self.overlay: OverlayRenderer = OverlayRenderer()

        self.camera_id: str = f"CAM_{camera_config.device_id}"
        self.is_running: bool = False

    def start(self) -> None:
        """Запуск сервиса"""
        logger.info("Запуск сервиса сканирования...")

        # Подключаем брокер
        self.broker.connect()

        # Запускаем камеру
        if not self.camera.start():
            raise RuntimeError("Не удалось запустить камеру")

        self.is_running = True
        self._main_loop()

    def _main_loop(self) -> None:
        """Главный цикл обработки"""
        logger.info("Сервис запущен. Нажмите 'q' для выхода, 's' для выбора области")

        while self.is_running:
            # Получаем кадр
            success: bool
            frame: np.ndarray | None
            success, frame = self.camera.get_frame()

            if not success or frame is None:
                continue

            # Детектируем QR-коды
            detections: list[BarcodeDetection] = self.detector.detect(frame)

            # Обрабатываем новые QR-коды
            for detection in detections:
                if self.deduplicator.is_new_barcode(detection.data):
                    self._process_new_barcode(detection)

            # Отрисовываем UI
            display_frame: np.ndarray = self.overlay.render(
                frame,
                detections,
                self.deduplicator.total_processed,
                self.detector.scan_region,
            )

            # Показываем результат
            cv2.imshow("Barcode Scanner", display_frame)

            # Обработка клавиш
            key: int = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                self.stop()
            elif key == ord("s"):
                self._select_scan_region(frame)

    def _process_new_barcode(self, detection: BarcodeDetection) -> None:
        """Обработка нового уникального QR-кода"""
        # Создаем событие
        event: BarcodeScannedEvent = BarcodeScannedEvent(
            barcode=detection.data,
            barcode_type=detection.barcode_type,
            camera_id=self.camera_id,
            timestamp=datetime.now().isoformat(),
            position={
                "x": detection.position[0],
                "y": detection.position[1],
                "width": detection.position[2],
                "height": detection.position[3],
            },
        )

        # Отправляем в брокер
        self.broker.publish_barcode(event)

        # Логируем
        logger.info(f"Новый QR-код: {detection.data} (тип: {detection.barcode_type})")

    def _select_scan_region(self, frame: np.ndarray[tuple[int, ...], np.dtype[np.uint8]]) -> None:
        """Выбор области сканирования"""
        raw_region = cv2.selectROI("Select Scan Region", frame, False)
        cv2.destroyWindow("Select Scan Region")

        # Преобразуем Rect в кортеж
        x: int = int(raw_region[0])
        y: int = int(raw_region[1])
        w: int = int(raw_region[2])
        h: int = int(raw_region[3])
        region: tuple[int, int, int, int] = (x, y, w, h)

        if region != (0, 0, 0, 0):
            self.detector.set_scan_region(region)
            logger.info(f"Установлена область сканирования: {region}")

    def stop(self) -> None:
        """Остановка сервиса"""
        logger.info("Остановка сервиса...")
        self.is_running = False
        self.camera.stop()
        self.broker.close()
        cv2.destroyAllWindows()
        logger.info(f"Всего обработано: {self.deduplicator.total_processed} QR-кодов")
