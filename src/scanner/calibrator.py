"""Калибровщик позиций упаковки по форме и размерам"""

import json
import logging
from pathlib import Path

import cv2
import numpy as np
import numpy.typing as npt

from src.scanner.models import CellPosition, LayerCalibration
from src.ui.config_panel import CellShape

logger = logging.getLogger(__name__)


class PackagingCalibrator:
    """Калибровщик упаковки по форме и слою"""

    # Калибровочные маркеры (ArUco или круги)
    CALIBRATION_MARKER_SIZE = 20  # мм

    def __init__(self) -> None:
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        self.aruco_params = cv2.aruco.DetectorParameters()
        self.aruco_detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)

    def detect_calibration_sheet(
        self, frame: npt.NDArray[np.uint8]
    ) -> tuple[bool, list[tuple[int, int]]]:
        """
        Обнаружение калибровочного листа с маркерами.
        Ожидает 4 ArUco маркера по углам листа.

        Returns:
            (success, corners) - углы листа
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = self.aruco_detector.detectMarkers(gray)

        if ids is None or len(ids) < 4:
            return False, []

        # Находим угловые точки
        pts = []
        for corner in corners[:4]:
            cx = int(corner[0][:, 0].mean())
            cy = int(corner[0][:, 1].mean())
            pts.append((cx, cy))

        # Сортируем: верхний-левый, верхний-правый, нижний-правый, нижний-левый
        pts = sorted(pts, key=lambda p: p[1])  # По Y
        top = sorted(pts[:2], key=lambda p: p[0])
        bottom = sorted(pts[2:], key=lambda p: p[0])
        ordered = [top[0], top[1], bottom[1], bottom[0]]

        return True, ordered

    def calibrate_layer(
        self,
        frame: npt.NDArray[np.uint8],
        rows: int,
        cols: int,
        shape: CellShape,
        cell_width_mm: float | None = None,
        cell_height_mm: float | None = None,
    ) -> LayerCalibration | None:
        """
        Калибровка слоя по изображению.

        Args:
            frame: Изображение пустого слоя (0-й слой)
            rows: Количество рядов
            cols: Количество столбцов
            shape: Форма упаковки
            cell_width_mm: Ширина упаковки в мм (опционально)
            cell_height_mm: Высота упаковки в мм (опционально)
        """
        # Ищем калибровочный лист
        success, sheet_corners = self.detect_calibration_sheet(frame)

        if success:
            # Калибровка по маркерам
            return self._calibrate_from_markers(
                sheet_corners,
                rows,
                cols,
                shape,
                cell_width_mm,
                cell_height_mm,
                frame.shape[1],  # ширина кадра
            )
        else:
            # Авто-калибровка по контурам
            logger.info("Маркеры не найдены, авто-калибровка...")
            return self._calibrate_from_contours(frame, rows, cols, shape)

    def _calibrate_from_markers(
        self,
        corners: list[tuple[int, int]],
        rows: int,
        cols: int,
        shape: CellShape,
        cell_w_mm: float | None,
        cell_h_mm: float | None,
        frame_width: int,  # <-- передаём ширину кадра явно
    ) -> LayerCalibration:
        """Калибровка по ArUco маркерам"""
        # Вычисляем размеры ячеек в пикселях
        if cell_w_mm and cell_h_mm:
            # Размер калибровочного листа (A4 альбомная)
            sheet_w = 297  # мм
            pixel_per_mm = frame_width / sheet_w
            cell_w = int(cell_w_mm * pixel_per_mm)
            cell_h = int(cell_h_mm * pixel_per_mm)
        else:
            # Авто-расчёт по углам
            x1, _ = corners[0]
            x2, _ = corners[1]
            _, y1 = corners[0]
            _, y4 = corners[3]
            total_w = abs(x2 - x1)
            total_h = abs(y4 - y1)
            cell_w = total_w // cols
            cell_h = total_h // rows

        return self._generate_grid(
            corners[0][0],
            corners[0][1],
            cell_w,
            cell_h,
            rows,
            cols,
            shape,
        )

    def _calibrate_from_contours(
        self,
        frame: npt.NDArray[np.uint8],
        rows: int,
        cols: int,
        shape: CellShape,
    ) -> LayerCalibration | None:
        """Авто-калибровка по контурам на пустом слое"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        # Ищем контуры
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            logger.warning("Контуры не найдены")
            # Ручной режим
            return self._manual_calibration(frame, rows, cols, shape)

        # Фильтруем и сортируем контуры
        h, w = frame.shape[:2]
        min_area = (w * h) * 0.001  # Минимум 0.1% от кадра
        valid_contours = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > min_area:
                x, y, cw, ch = cv2.boundingRect(cnt)
                valid_contours.append((x, y, cw, ch))

        if len(valid_contours) < 2:
            logger.warning("Недостаточно контуров")
            return self._manual_calibration(frame, rows, cols, shape)

        # Определяем размер ячейки по медиане
        widths = [c[2] for c in valid_contours]
        heights = [c[3] for c in valid_contours]
        cell_w = int(np.median(widths))
        cell_h = int(np.median(heights))

        # Определяем отступы
        xs = [c[0] for c in valid_contours]
        ys = [c[1] for c in valid_contours]
        offset_x = min(xs)
        offset_y = min(ys)

        return self._generate_grid(
            offset_x,
            offset_y,
            cell_w,
            cell_h,
            rows,
            cols,
            shape,
        )

    def _manual_calibration(
        self,
        frame: npt.NDArray[np.uint8],
        rows: int,
        cols: int,
        shape: CellShape,
    ) -> LayerCalibration:
        """Ручная калибровка — пользователь выделяет область"""
        logger.info("Ручная калибровка: выделите область слоя")

        # Выделение области
        region = cv2.selectROI("Select layer area", frame, False)
        cv2.destroyWindow("Select layer area")

        x, y, w, h = region
        cell_w = w // cols
        cell_h = h // rows

        return self._generate_grid(x, y, cell_w, cell_h, rows, cols, shape)

    def _generate_grid(
        self,
        offset_x: int,
        offset_y: int,
        cell_w: int,
        cell_h: int,
        rows: int,
        cols: int,
        shape: CellShape,
    ) -> LayerCalibration:
        """Генерация сетки позиций"""
        cells: list[CellPosition] = []
        cell_id = 0

        for row in range(rows):
            for col in range(cols):
                cx = offset_x + col * cell_w + cell_w // 2
                cy = offset_y + row * cell_h + cell_h // 2

                # Для круглых упаковок — ROI квадратный с центром
                if shape == CellShape.CIRCLE:
                    roi_size = min(cell_w, cell_h)
                    x = cx - roi_size // 2
                    y = cy - roi_size // 2
                    w = h = roi_size
                else:
                    x = offset_x + col * cell_w
                    y = offset_y + row * cell_h
                    w = cell_w
                    h = cell_h

                cells.append(
                    CellPosition(
                        id=cell_id,
                        x=int(x),
                        y=int(y),
                        width=int(w),
                        height=int(h),
                        shape=shape,
                        center=(int(cx), int(cy)),
                    )
                )
                cell_id += 1

        spacing_x = cell_w
        spacing_y = cell_h

        return LayerCalibration(
            rows=rows,
            cols=cols,
            cell_width=cell_w,
            cell_height=cell_h,
            cell_shape=shape,
            spacing_x=spacing_x,
            spacing_y=spacing_y,
            offset_x=offset_x,
            offset_y=offset_y,
            cells=cells,
        )

    def save_calibration(self, calibration: LayerCalibration, filepath: str | Path) -> None:
        """Сохранение калибровки в JSON"""
        data = {
            "rows": calibration.rows,
            "cols": calibration.cols,
            "cell_width": calibration.cell_width,
            "cell_height": calibration.cell_height,
            "cell_shape": calibration.cell_shape.value,
            "spacing_x": calibration.spacing_x,
            "spacing_y": calibration.spacing_y,
            "offset_x": calibration.offset_x,
            "offset_y": calibration.offset_y,
            "cells": [
                {
                    "id": c.id,
                    "x": c.x,
                    "y": c.y,
                    "width": c.width,
                    "height": c.height,
                    "center_x": c.center[0],
                    "center_y": c.center[1],
                }
                for c in calibration.cells
            ],
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Калибровка сохранена: {filepath}")

    @classmethod
    def load_calibration(cls, filepath: str | Path) -> LayerCalibration | None:
        """Загрузка калибровки из JSON"""
        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)

            cells = []
            for c in data["cells"]:
                cells.append(
                    CellPosition(
                        id=c["id"],
                        x=c["x"],
                        y=c["y"],
                        width=c["width"],
                        height=c["height"],
                        shape=CellShape(data["cell_shape"]),
                        center=(c["center_x"], c["center_y"]),
                    )
                )

            return LayerCalibration(
                rows=data["rows"],
                cols=data["cols"],
                cell_width=data["cell_width"],
                cell_height=data["cell_height"],
                cell_shape=CellShape(data["cell_shape"]),
                spacing_x=data["spacing_x"],
                spacing_y=data["spacing_y"],
                offset_x=data["offset_x"],
                offset_y=data["offset_y"],
                cells=cells,
            )
        except (FileNotFoundError, KeyError) as e:
            logger.error(f"Ошибка загрузки калибровки: {e}")
            return None

    def draw_calibration_overlay(
        self,
        frame: npt.NDArray[np.uint8],
        calibration: LayerCalibration,
    ) -> npt.NDArray[np.uint8]:
        """Отрисовка калибровочной сетки"""
        display = frame.copy()

        for cell in calibration.cells:
            color = (0, 255, 0)  # Зелёный

            if cell.shape == CellShape.CIRCLE:
                cv2.circle(display, cell.center, cell.width // 2, color, 2)
            elif cell.shape == CellShape.TRIANGLE:
                pts = np.array(
                    [
                        [cell.center[0], cell.y],
                        [cell.x, cell.y + cell.height],
                        [cell.x + cell.width, cell.y + cell.height],
                    ],
                    np.int32,
                )
                cv2.polylines(display, [pts], True, color, 2)
            else:
                cv2.rectangle(
                    display,
                    (cell.x, cell.y),
                    (cell.x + cell.width, cell.y + cell.height),
                    color,
                    2,
                )

            # Номер ячейки
            cv2.putText(
                display,
                str(cell.id),
                (cell.center[0] - 10, cell.center[1] + 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                color,
                1,
            )

        # Инфо
        info = (
            f"{calibration.cell_shape.value} | "
            f"{calibration.rows}x{calibration.cols} | "
            f"{len(calibration.cells)} cells"
        )
        cv2.putText(
            display,
            info,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 0),
            2,
        )

        return display
