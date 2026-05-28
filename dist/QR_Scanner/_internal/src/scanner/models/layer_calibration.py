"""Калибровка слоя упаковки"""

from dataclasses import dataclass

from src.ui.config_panel import CellShape

from .cell_position import CellPosition


@dataclass
class LayerCalibration:
    """Калибровка одного слоя упаковки"""

    rows: int
    cols: int
    cell_width: int
    cell_height: int
    cell_shape: CellShape
    spacing_x: int
    spacing_y: int
    offset_x: int
    offset_y: int
    cells: list[CellPosition]
