"""Формы индивидуальной упаковки"""

from enum import Enum


class CellShape(str, Enum):
    """Формы индивидуальной упаковки"""

    CIRCLE = "circle"
    SQUARE = "square"
    RECTANGLE = "rectangle"
    TRIANGLE = "triangle"
    HEXAGON = "hexagon"
