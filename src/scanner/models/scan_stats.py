"""Статистика сканирования"""

from dataclasses import dataclass


@dataclass
class ScanStats:
    """Статистика сканирования"""

    cells_in_layer: int = 12
    total_layers: int = 5
    total_scanned: int = 0
    current_layer: int = 1
    cells_filled: int = 0

    @property
    def layer_progress(self) -> float:
        """Прогресс слоя (0-100)"""
        if self.cells_in_layer == 0:
            return 0.0
        return (self.cells_filled / self.cells_in_layer) * 100

    @property
    def total_progress(self) -> float:
        """Общий прогресс (0-100)"""
        total = self.total_layers * self.cells_in_layer
        if total == 0:
            return 0.0
        return (self.total_scanned / total) * 100
