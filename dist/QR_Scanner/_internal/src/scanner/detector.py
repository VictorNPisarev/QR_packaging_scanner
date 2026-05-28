"""Детектор кодов через zxing-cpp"""

import logging

import cv2
import numpy as np
import numpy.typing as npt

from scanner.models.cell_shape import CellShape
from src.scanner.models import BarcodeDetection, CellPosition

logger = logging.getLogger(__name__)

try:
    import zxingcpp  # type: ignore

    ZXING_AVAILABLE = True
    logger.info("✓ zxing-cpp готов")
except ImportError:
    ZXING_AVAILABLE = False
    logger.error("zxing-cpp не установлен! Выполните: pip install zxing-cpp")


class BarcodeDetector:
    """Детектор Data Matrix и других кодов через zxing-cpp"""

    def __init__(
        self,
        scan_region: tuple[int, int, int, int] | None = None,
    ) -> None:
        if not ZXING_AVAILABLE:
            raise RuntimeError("zxing-cpp не установлен. pip install zxing-cpp")
        self.scan_region = scan_region

    def set_scan_region(self, region: tuple[int, int, int, int] | None) -> None:
        """Установка области сканирования"""
        self.scan_region = region
        if region is not None:
            x, y, w, h = region
            logger.info(f"Область сканирования: x={x}, y={y}, w={w}, h={h}")
        else:
            logger.info("Сканирование по всему кадру")

    def detect(self, frame: npt.NDArray[np.uint8]) -> list[BarcodeDetection]:
        results: list[BarcodeDetection] = []

        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame

            # Пробуем разные варианты яркости
            for alpha, beta in [(1.0, 0), (1.3, -20), (0.8, 30)]:
                adjusted = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)

                if self.scan_region:
                    x, y, w, h = self.scan_region
                    roi = adjusted[y : y + h, x : x + w]
                else:
                    roi = adjusted
                    x, y = 0, 0

                barcodes = zxingcpp.read_barcodes(roi)

                for barcode in barcodes:
                    if barcode.valid and barcode.text:  # noqa: SIM102
                        # Проверяем, не нашли ли уже этот код
                        if barcode.text not in [r.data for r in results]:
                            results.append(
                                BarcodeDetection(
                                    data=barcode.text,
                                    barcode_type=str(barcode.format).split(".")[-1],
                                    position=(
                                        x + barcode.position.left,
                                        y + barcode.position.top,
                                        barcode.position.width,
                                        barcode.position.height,
                                    ),
                                )
                            )

                if results:
                    break  # Нашли — хватит

        except Exception as e:
            logger.error(f"Ошибка детекции: {e}")

        return results

    def detect_in_cells(
        self,
        frame: npt.NDArray[np.uint8],
        cells: list[CellPosition],
    ) -> dict[int, BarcodeDetection | None]:
        """
        Детекция кодов в конкретных ячейках.

        Returns:
            Словарь {cell_id: detection или None}
        """
        results: dict[int, BarcodeDetection | None] = {}
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame

        for cell in cells:
            # Вырезаем ROI ячейки
            roi = gray[
                max(0, cell.y) : min(gray.shape[0], cell.y + cell.height),
                max(0, cell.x) : min(gray.shape[1], cell.x + cell.width),
            ]

            if roi.size == 0:
                results[cell.id] = None
                continue

            # Для круглых — дополнительная маска
            if cell.shape == CellShape.CIRCLE:
                mask = np.zeros(roi.shape, dtype=np.uint8)
                cv2.circle(
                    mask,
                    (roi.shape[1] // 2, roi.shape[0] // 2),
                    min(roi.shape) // 2,
                    255,
                    -1,
                )
                roi = cv2.bitwise_and(roi, roi, mask=mask)

            # Детекция
            try:
                barcodes = zxingcpp.read_barcodes(roi)
                found = None
                for barcode in barcodes:
                    if barcode.valid and barcode.text:
                        found = BarcodeDetection(
                            data=barcode.text,
                            barcode_type=str(barcode.format).split(".")[-1],
                            position=(
                                cell.x + barcode.position.left,
                                cell.y + barcode.position.top,
                                barcode.position.width,
                                barcode.position.height,
                            ),
                        )
                        break
                results[cell.id] = found
            except Exception as e:
                logger.error(f"Ошибка в ячейке {cell.id}: {e}")
                results[cell.id] = None

        return results
