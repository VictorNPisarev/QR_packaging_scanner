"""Панель конфигурации упаковки"""

from dataclasses import dataclass


@dataclass
class PackagingConfig:
    """Конфигурация упаковки"""

    cells_per_layer: int = 12  # Количество банок в слое
    total_layers: int = 5  # Количество слоев
    cell_shape: str = "circle"  # Форма: circle, square
    auto_print: bool = True  # Автоматическая печать этикетки
    printer_name: str | None = None  # Имя принтера

    @property
    def total_cells(self) -> int:
        """Общее количество ячеек в коробке"""
        return self.cells_per_layer * self.total_layers

    def to_dict(self) -> dict:
        """Сериализация в словарь"""
        return {
            "cells_per_layer": self.cells_per_layer,
            "total_layers": self.total_layers,
            "cell_shape": self.cell_shape,
            "auto_print": self.auto_print,
            "printer_name": self.printer_name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PackagingConfig":
        """Создание из словаря"""
        return cls(
            cells_per_layer=data.get("cells_per_layer", 12),
            total_layers=data.get("total_layers", 5),
            cell_shape=data.get("cell_shape", "circle"),
            auto_print=data.get("auto_print", True),
            printer_name=data.get("printer_name"),
        )


class ConfigPanel:
    """Консольная панель конфигурации (для тестов)"""

    @staticmethod
    def print_config(config: PackagingConfig) -> None:
        """Вывод конфигурации в консоль"""
        print("=" * 40)
        print("PACKAGING CONFIGURATION".center(40))
        print("=" * 40)
        print(f"Cells per layer: {config.cells_per_layer}")
        print(f"Total layers:   {config.total_layers}")
        print(f"Total cells:    {config.total_cells}")
        print(f"Cell shape:     {config.cell_shape}")
        print(f"Auto print:     {config.auto_print}")
        if config.printer_name:
            print(f"Printer:        {config.printer_name}")
        print("=" * 40)

    @staticmethod
    def interactive_config() -> PackagingConfig:
        """Интерактивная настройка через консоль"""
        print("\n=== Настройка упаковки ===\n")

        cells: str = input("Количество банок в слое [12]: ") or "12"
        layers: str = input("Количество слоев [5]: ") or "5"
        shape: str = input("Форма (circle/square) [circle]: ") or "circle"
        auto: str = input("Автопечать (y/n) [y]: ") or "y"

        return PackagingConfig(
            cells_per_layer=int(cells),
            total_layers=int(layers),
            cell_shape=shape,
            auto_print=auto.lower() == "y",
        )
