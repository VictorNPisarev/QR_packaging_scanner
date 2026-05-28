"""Результат детекции кода"""

from dataclasses import dataclass


@dataclass
class BarcodeDetection:
    """Результат детекции кода"""

    data: str
    barcode_type: str = "DataMatrix"
    position: tuple[int, int, int, int] = (0, 0, 0, 0)
    confidence: float = 1.0
