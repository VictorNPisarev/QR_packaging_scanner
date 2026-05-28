"""Позиция ячейки на слое"""

from dataclasses import dataclass

from scanner.models.cell_shape import CellShape


@dataclass
class CellPosition:
    """Позиция одной ячейки на слое"""

    id: int
    x: int
    y: int
    width: int
    height: int
    shape: CellShape
    center: tuple[int, int]
