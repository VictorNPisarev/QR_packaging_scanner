"""Точка входа в приложение"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.camera.capture import CameraConfig
from src.messaging.broker import MessageBroker
from src.services.scan_service import ScanService
from src.ui.config_panel import ConfigPanel, PackagingConfig
from src.ui.stats_panel import ScanStats

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("scanner.log", encoding="utf-8")],
)

logger = logging.getLogger(__name__)


def main() -> None:
    """Главная функция"""
    logger.info("=" * 50)
    logger.info("QR CODE PACKAGING SCANNER")
    logger.info("=" * 50)

    # Конфигурация упаковки
    config: PackagingConfig = PackagingConfig(
        cells_per_layer=12,
        total_layers=5,
        cell_shape="circle",
        auto_print=True,
    )

    # Показываем конфигурацию
    ConfigPanel.print_config(config)

    # Статистика
    stats: ScanStats = ScanStats(
        cells_in_layer=config.cells_per_layer,
        total_layers=config.total_layers,
    )

    # Конфигурация камеры
    camera_config: CameraConfig = CameraConfig(
        device_id=0,
        width=1280,
        height=720,
        fps=30,
    )

    # Брокер сообщений
    broker: MessageBroker = MessageBroker(
        host="localhost",
        port=5672,
        queue_name="barcode_events",
    )

    # Создаем и запускаем сервис
    service: ScanService = ScanService(
        camera_config=camera_config,
        broker=broker,
    )

    try:
        service.start()
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")
    finally:
        service.stop()
        logger.info(f"Сессия завершена. Обработано: {stats.total_scanned}")


if __name__ == "__main__":
    main()
