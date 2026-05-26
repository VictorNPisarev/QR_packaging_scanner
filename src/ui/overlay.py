"""Отрисовка интерфейса поверх видео"""

from datetime import datetime

import cv2
import numpy as np
import numpy.typing as npt

from src.scanner.detector import BarcodeDetection

Frame = npt.NDArray[np.uint8]


class OverlayRenderer:
    """Отрисовщик интерфейса на кадрах видео"""

    def __init__(self) -> None:
        # Шрифты
        self.font: int = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale_small: float = 0.5
        self.font_scale_normal: float = 0.7
        self.font_scale_large: float = 1.0
        self.font_thickness: int = 2

        # Цвета (BGR)
        self.green: tuple[int, int, int] = (0, 255, 0)
        self.red: tuple[int, int, int] = (0, 0, 255)
        self.blue: tuple[int, int, int] = (255, 0, 0)
        self.white: tuple[int, int, int] = (255, 255, 255)
        self.yellow: tuple[int, int, int] = (0, 255, 255)
        self.cyan: tuple[int, int, int] = (255, 255, 0)
        self.black: tuple[int, int, int] = (0, 0, 0)
        self.gray: tuple[int, int, int] = (128, 128, 128)

        # Анимация
        self._scan_line_pos: int = 0
        self._last_detection_time: float = 0.0

    def render(
        self,
        frame: Frame,
        detections: list[BarcodeDetection],
        total_count: int,
        scan_region: tuple[int, int, int, int] | None = None,
        layer_info: dict | None = None,
    ) -> Frame:
        """
        Основной метод отрисовки

        Args:
            frame: Исходный кадр
            detections: Список обнаруженных QR-кодов
            total_count: Общее количество обработанных кодов
            scan_region: Область сканирования (x, y, w, h)
            layer_info: Информация о слое (номер, заполненость и т.д.)
        """
        display_frame: Frame = frame.copy()

        # Отрисовка области сканирования
        if scan_region is not None:
            self._draw_scan_region(display_frame, scan_region)

        # Отрисовка найденных QR-кодов
        for detection in detections:
            self._draw_detection(display_frame, detection)

        # Статистика
        self._draw_stats_panel(display_frame, total_count, layer_info)

        # Подсказки управления
        self._draw_controls(display_frame)

        # Статусная строка
        self._draw_status_bar(display_frame, len(detections))

        return display_frame

    def _draw_scan_region(self, frame: Frame, region: tuple[int, int, int, int]) -> None:
        """Отрисовка области сканирования с анимацией"""
        x, y, w, h = region

        # Основная рамка
        cv2.rectangle(frame, (x, y), (x + w, y + h), self.green, 2)

        # Уголки для стиля
        corner_len: int = 20
        # Верхний левый
        cv2.line(frame, (x, y + corner_len), (x, y), self.green, 2)
        cv2.line(frame, (x, y), (x + corner_len, y), self.green, 2)
        # Верхний правый
        cv2.line(frame, (x + w - corner_len, y), (x + w, y), self.green, 2)
        cv2.line(frame, (x + w, y), (x + w, y + corner_len), self.green, 2)
        # Нижний левый
        cv2.line(frame, (x, y + h - corner_len), (x, y + h), self.green, 2)
        cv2.line(frame, (x, y + h), (x + corner_len, y + h), self.green, 2)
        # Нижний правый
        cv2.line(frame, (x + w - corner_len, y + h), (x + w, y + h), self.green, 2)
        cv2.line(frame, (x + w, y + h), (x + w, y + h - corner_len), self.green, 2)

        # Подпись
        label: str = "SCAN AREA"
        (tw, th), _ = cv2.getTextSize(label, self.font, 0.6, 1)
        cv2.rectangle(frame, (x, y - th - 10), (x + tw + 10, y), self.green, -1)
        cv2.putText(frame, label, (x + 5, y - 5), self.font, 0.6, self.black, 1)

        # Сканирующая линия (анимация)
        self._scan_line_pos = (self._scan_line_pos + 3) % h
        cv2.line(
            frame,
            (x, y + self._scan_line_pos),
            (x + w, y + self._scan_line_pos),
            self.green,
            1,
        )

    def _draw_detection(self, frame: Frame, detection: BarcodeDetection) -> None:
        """Отрисовка найденного QR-кода"""
        x, y, w, h = detection.position

        # Прямоугольник вокруг QR-кода
        cv2.rectangle(frame, (x, y), (x + w, y + h), self.red, 2)

        # Текст с данными
        text: str = f"{detection.data[:20]}"  # Обрезаем длинные строки
        (tw, th), _ = cv2.getTextSize(text, self.font, self.font_scale_small, 2)

        # Фон для текста
        cv2.rectangle(
            frame,
            (x, y - th - 15),
            (x + tw + 10, y),
            self.red,
            -1,
        )

        # Текст
        cv2.putText(
            frame,
            text,
            (x + 5, y - 5),
            self.font,
            self.font_scale_small,
            self.white,
            2,
        )

        # Точка в центре
        center_x: int = x + w // 2
        center_y: int = y + h // 2
        cv2.circle(frame, (center_x, center_y), 5, self.red, -1)

    def _draw_stats_panel(
        self,
        frame: Frame,
        total_count: int,
        layer_info: dict | None = None,
    ) -> None:
        """Отрисовка панели статистики"""
        panel_x: int = 10
        panel_y: int = 10
        panel_w: int = 280
        panel_h: int = 120

        # Полупрозрачный фон
        overlay = frame.copy()
        cv2.rectangle(
            overlay, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h), self.black, -1
        )
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

        # Рамка панели
        cv2.rectangle(
            frame, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h), self.white, 1
        )

        # Заголовок
        cv2.putText(
            frame,
            "STATISTICS",
            (panel_x + 10, panel_y + 25),
            self.font,
            self.font_scale_normal,
            self.cyan,
            2,
        )

        # Счетчик
        cv2.putText(
            frame,
            f"Total scanned: {total_count}",
            (panel_x + 10, panel_y + 55),
            self.font,
            self.font_scale_normal,
            self.white,
            1,
        )

        # Информация о слое
        if layer_info:
            layer_num: int = layer_info.get("current_layer", 0)
            total_layers: int = layer_info.get("total_layers", 0)
            cells_filled: int = layer_info.get("cells_filled", 0)
            total_cells: int = layer_info.get("total_cells", 0)

            cv2.putText(
                frame,
                f"Layer: {layer_num}/{total_layers}",
                (panel_x + 10, panel_y + 80),
                self.font,
                self.font_scale_normal,
                self.yellow,
                1,
            )

            cv2.putText(
                frame,
                f"Cells: {cells_filled}/{total_cells}",
                (panel_x + 10, panel_y + 105),
                self.font,
                self.font_scale_normal,
                self.yellow,
                1,
            )

    def _draw_controls(self, frame: Frame) -> None:
        """Отрисовка подсказок управления"""
        h: int = frame.shape[0]
        controls: list[tuple[str, str]] = [
            ("Q", "Quit"),
            ("S", "Select scan region"),
            ("R", "Reset counter"),
            ("Space", "Pause/Resume"),
        ]

        start_y: int = h - 20 - len(controls) * 25

        for i, (key, desc) in enumerate(controls):
            y_pos: int = start_y + i * 25
            # Клавиша
            cv2.putText(
                frame,
                f"[{key}]",
                (10, y_pos),
                self.font,
                self.font_scale_small,
                self.yellow,
                1,
            )
            # Описание
            cv2.putText(
                frame,
                desc,
                (50, y_pos),
                self.font,
                self.font_scale_small,
                self.white,
                1,
            )

    def _draw_status_bar(self, frame: Frame, active_detections: int) -> None:
        """Отрисовка статусной строки внизу"""
        h, w = frame.shape[:2]

        # Фон статус-бара
        cv2.rectangle(frame, (0, h - 30), (w, h), self.black, -1)
        cv2.rectangle(frame, (0, h - 30), (w, h), self.gray, 1)

        # Текущее время
        time_str: str = datetime.now().strftime("%H:%M:%S")
        cv2.putText(
            frame,
            time_str,
            (10, h - 8),
            self.font,
            self.font_scale_small,
            self.white,
            1,
        )

        # Статус
        status: str = f"Active detections: {active_detections}"
        cv2.putText(
            frame,
            status,
            (w - 200, h - 8),
            self.font,
            self.font_scale_small,
            self.green if active_detections > 0 else self.gray,
            1,
        )

        # Версия
        cv2.putText(
            frame,
            "v1.0.0",
            (w - 60, h - 8),
            self.font,
            self.font_scale_small,
            self.gray,
            1,
        )
