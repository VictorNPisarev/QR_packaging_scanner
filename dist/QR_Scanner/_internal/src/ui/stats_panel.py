"""Панель детальной статистики"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

import cv2
import numpy as np
import numpy.typing as npt

Frame = npt.NDArray[np.uint8]


@dataclass
class ScanStats:
    """Статистика сканирования"""

    total_scanned: int = 0
    current_layer: int = 1
    total_layers: int = 5
    cells_in_layer: int = 12
    cells_filled: int = 0
    scan_rate: float = 0.0  # сканов в минуту
    session_start: datetime = field(default_factory=datetime.now)
    last_scan_time: datetime | None = None
    recent_scans: list[str] = field(default_factory=list)

    @property
    def session_duration(self) -> timedelta:
        """Длительность сессии"""
        return datetime.now() - self.session_start

    @property
    def layer_progress(self) -> float:
        """Прогресс заполнения слоя (0-100)"""
        if self.cells_in_layer == 0:
            return 0.0
        return (self.cells_filled / self.cells_in_layer) * 100

    @property
    def total_progress(self) -> float:
        """Общий прогресс упаковки (0-100)"""
        total_cells: int = self.total_layers * self.cells_in_layer
        if total_cells == 0:
            return 0.0
        return (self.total_scanned / total_cells) * 100


class StatsPanel:
    """Отрисовка детальной панели статистики"""

    def __init__(self, width: int = 400, height: int = 300) -> None:
        self.width: int = width
        self.height: int = height
        self.panel: Frame = np.zeros((height, width, 3), dtype=np.uint8)

    def render(self, stats: ScanStats) -> Frame:
        """Отрисовка панели статистики"""
        self.panel.fill(30)  # Темно-серый фон

        y: int = 20

        # Заголовок
        y = self._draw_text("SCANNING STATISTICS", 10, y, (0, 255, 255), 0.8)
        y += 10

        # Разделитель
        cv2.line(self.panel, (10, y), (self.width - 10, y), (100, 100, 100), 1)
        y += 10

        # Основные показатели
        y = self._draw_text(f"Total scanned: {stats.total_scanned}", 10, y, (255, 255, 255))
        y = self._draw_text(f"Session: {stats.session_duration}", 10, y, (200, 200, 200))
        y = self._draw_text(f"Scan rate: {stats.scan_rate:.1f}/min", 10, y, (200, 200, 200))
        y += 10

        # Прогресс слоя
        cv2.line(self.panel, (10, y), (self.width - 10, y), (100, 100, 100), 1)
        y += 10

        y = self._draw_text(
            f"Layer: {stats.current_layer}/{stats.total_layers}", 10, y, (255, 255, 0)
        )
        y = self._draw_progress_bar(
            f"Cells: {stats.cells_filled}/{stats.cells_in_layer}",
            stats.layer_progress,
            10,
            y,
            (0, 255, 0),
        )
        y += 10

        # Общий прогресс
        y = self._draw_progress_bar("Total progress", stats.total_progress, 10, y, (255, 255, 0))
        y += 15

        # Последние сканы
        cv2.line(self.panel, (10, y), (self.width - 10, y), (100, 100, 100), 1)
        y += 10

        y = self._draw_text("Recent scans:", 10, y, (200, 200, 200), 0.5)
        for scan in stats.recent_scans[-5:]:  # Последние 5
            y = self._draw_text(f"  • {scan}", 10, y, (150, 150, 150), 0.4)

        return self.panel

    def _draw_text(
        self,
        text: str,
        x: int,
        y: int,
        color: tuple[int, int, int],
        scale: float = 0.6,
    ) -> int:
        """Рисует текст и возвращает новую позицию Y"""
        cv2.putText(
            self.panel,
            text,
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            color,
            1,
        )
        return y + int(25 * scale)

    def _draw_progress_bar(
        self,
        label: str,
        progress: float,
        x: int,
        y: int,
        color: tuple[int, int, int],
    ) -> int:
        """Рисует прогресс-бар и возвращает новую позицию Y"""
        bar_width: int = self.width - x * 2
        bar_height: int = 20
        bar_y: int = y + 15

        # Фон прогресс-бара
        cv2.rectangle(
            self.panel,
            (x, bar_y),
            (x + bar_width, bar_y + bar_height),
            (50, 50, 50),
            -1,
        )

        # Заполнение
        fill_width: int = int(bar_width * progress / 100)
        if fill_width > 0:
            cv2.rectangle(
                self.panel,
                (x, bar_y),
                (x + fill_width, bar_y + bar_height),
                color,
                -1,
            )

        # Рамка
        cv2.rectangle(
            self.panel,
            (x, bar_y),
            (x + bar_width, bar_y + bar_height),
            (100, 100, 100),
            1,
        )

        # Текст
        cv2.putText(
            self.panel,
            f"{label} ({progress:.0f}%)",
            (x + 5, bar_y + 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )

        return bar_y + bar_height + 5
