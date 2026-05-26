"""Клиент для работы с RabbitMQ"""

import logging
from typing import Any

import pika

from src.messaging.events import BarcodeScannedEvent

logger = logging.getLogger(__name__)


class MessageBroker:
    """Клиент для отправки сообщений в RabbitMQ"""

    def __init__(
        self, host: str = "localhost", port: int = 5672, queue_name: str = "barcode_events"
    ) -> None:
        self.host: str = host
        self.port: int = port
        self.queue_name: str = queue_name
        self.connection: pika.BlockingConnection | None = None
        self._channel: Any | None = None  # pika плохо типизирована
        self.is_connected: bool = False

    @property
    def channel(self) -> Any:
        """Возвращает канал, если инициализирован"""
        if self._channel is None:
            raise RuntimeError("Канал не инициализирован")
        return self._channel

    def connect(self) -> bool:
        """Подключение к RabbitMQ"""
        try:
            parameters: pika.ConnectionParameters = pika.ConnectionParameters(
                host=self.host, port=self.port, heartbeat=600, blocked_connection_timeout=300
            )
            self.connection = pika.BlockingConnection(parameters)
            self._channel = self.connection.channel()

            # Проверяем канал
            if self._channel is None:
                logger.error("Не удалось создать канал RabbitMQ")
                self.is_connected = False
                return False

            # Создаем очередь
            self._channel.queue_declare(queue=self.queue_name, durable=True)

            self.is_connected = True
            logger.info(f"✓ Подключено к RabbitMQ: {self.host}:{self.port}")
            return True

        except Exception as e:
            logger.warning(f"⚠ RabbitMQ недоступен ({e}). Продолжаем без брокера сообщений.")
            self.is_connected = False
            return False

    def publish_barcode(self, event: BarcodeScannedEvent) -> None:
        """Отправка события о найденном QR-коде"""
        if not self.is_connected:
            logger.debug("Брокер не подключен, пропускаем сообщение")
            return

        if self._channel is None:
            logger.error("Канал RabbitMQ не инициализирован")
            return

        try:
            properties: pika.BasicProperties = pika.BasicProperties(
                delivery_mode=2,  # Сообщения сохраняются на диск
                content_type="application/json",
            )
            self._channel.basic_publish(
                exchange="",
                routing_key=self.queue_name,
                body=event.to_json(),
                properties=properties,
            )
            logger.debug(f"✓ Отправлено сообщение: {event.barcode}")

        except Exception as e:
            logger.error(f"✗ Ошибка отправки сообщения: {e}")
            self.is_connected = False

    def close(self) -> None:
        """Закрытие соединения с брокером"""
        if self.connection is not None and self.connection.is_open:
            self.connection.close()
            logger.info("✓ Соединение с RabbitMQ закрыто")
