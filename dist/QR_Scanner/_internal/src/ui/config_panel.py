"""Конфигурация упаковки"""

from dataclasses import dataclass, field
from typing import Any

from scanner.models.cell_shape import CellShape


@dataclass
class PackagingConfig:
    """Конфигурация упаковки"""

    # Размеры слоя
    cells_per_layer: int = 12
    rows: int = 3
    cols: int = 4

    # Слои
    total_layers: int = 5

    # Форма
    cell_shape: CellShape = CellShape.CIRCLE

    # Размеры индивидуальной упаковки (мм, опционально)
    cell_width_mm: float | None = None
    cell_height_mm: float | None = None

    # Печать
    auto_print: bool = True
    printer_name: str | None = None

    # Позиции (заполняются после калибровки)
    cell_positions: list[tuple[int, int, int, int]] = field(default_factory=list)

    @property
    def total_cells(self) -> int:
        """Общее количество ячеек в коробке"""
        return self.cells_per_layer * self.total_layers

    @property
    def cells_count(self) -> int:
        """Количество ячеек в слое (синоним)"""
        return self.cells_per_layer

    def to_dict(self) -> dict[str, Any]:
        """Сериализация в словарь"""
        return {
            "cells_per_layer": self.cells_per_layer,
            "rows": self.rows,
            "cols": self.cols,
            "total_layers": self.total_layers,
            "cell_shape": self.cell_shape.value,
            "cell_width_mm": self.cell_width_mm,
            "cell_height_mm": self.cell_height_mm,
            "auto_print": self.auto_print,
            "printer_name": self.printer_name,
            "cell_positions": [list(pos) for pos in self.cell_positions],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PackagingConfig":
        """Создание из словаря"""
        shape_raw = data.get("cell_shape", "circle")
        shape = CellShape(shape_raw) if shape_raw in CellShape.__members__ else CellShape.CIRCLE

        return cls(
            cells_per_layer=data.get("cells_per_layer", 12),
            rows=data.get("rows", 3),
            cols=data.get("cols", 4),
            total_layers=data.get("total_layers", 5),
            cell_shape=shape,
            cell_width_mm=data.get("cell_width_mm"),
            cell_height_mm=data.get("cell_height_mm"),
            auto_print=data.get("auto_print", True),
            printer_name=data.get("printer_name"),
            cell_positions=[tuple(pos) for pos in data.get("cell_positions", [])],
        )

    def update_from_calibration(
        self,
        rows: int,
        cols: int,
        cells: list[tuple[int, int, int, int]],
    ) -> None:
        """Обновить конфигурацию после калибровки"""
        self.rows = rows
        self.cols = cols
        self.cells_per_layer = rows * cols
        self.cell_positions = cells
