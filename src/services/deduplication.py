"""Сервис дедупликации найденных QR-кодов"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class DeduplicationConfig:
    """Настройки дедупликации"""

    cooldown_seconds: float = 3.0  # Время блокировки повторов
    cleanup_interval: float = 5.0  # Интервал очистки старых записей
    max_total_codes: int = 1000  # Максимальное количество сохраняемых кодов


class BarcodeDeduplicator:
    """Предотвращает повторную обработку одних и тех же QR-кодов"""

    def __init__(self, config: DeduplicationConfig) -> None:
        self.config: DeduplicationConfig = config
        self._cooldowns: dict[str, datetime] = {}
        self._processed: set[str] = set()
        self._total_count: int = 0

    def is_new_barcode(self, barcode_data: str) -> bool:
        """Проверяет, нужно ли обрабатывать этот QR-код"""
        if not barcode_data:
            return False

        current_time: datetime = datetime.now()

        # Очистка старых cooldown-записей
        self._cleanup_old_entries(current_time)

        # Проверка, не в периоде охлаждения
        if barcode_data in self._cooldowns:
            time_passed: float = (current_time - self._cooldowns[barcode_data]).total_seconds()
            if time_passed < self.config.cooldown_seconds:
                return False

        # Проверяем лимит
        if len(self._processed) >= self.config.max_total_codes:
            logger.warning("Достигнут лимит сохраненных кодов, очистка...")
            self.reset()

        # Обновляем время последнего обнаружения
        self._cooldowns[barcode_data] = current_time
        self._processed.add(barcode_data)
        self._total_count += 1

        logger.debug(f"Новый уникальный QR-код: {barcode_data} (всего: {self._total_count})")
        return True

    def _cleanup_old_entries(self, current_time: datetime) -> None:
        """Удаление устаревших записей"""
        threshold: datetime = current_time - timedelta(seconds=self.config.cleanup_interval)
        self._cooldowns = {k: v for k, v in self._cooldowns.items() if v > threshold}

    @property
    def total_processed(self) -> int:
        """Общее количество обработанных уникальных QR-кодов"""
        return self._total_count

    def reset(self) -> None:
        """Сброс статистики"""
        self._cooldowns.clear()
        self._processed.clear()
        self._total_count = 0
        logger.info("Статистика сброшена")
