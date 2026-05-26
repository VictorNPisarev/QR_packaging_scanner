"""Модели событий для обмена сообщениями"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
import json

@dataclass
class BarcodeScannedEvent:
    """Событие обнаружения штрихкода"""
    barcode: str
    barcode_type: str
    camera_id: str
    timestamp: str
    position: dict  # x, y, width, height

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> 'BarcodeScannedEvent':
        data = json.loads(json_str)
        return cls(**data)

@dataclass
class LayerCompletedEvent:
    """Событие заполнения слоя"""
    box_id: str
    layer_number: int
    cells_count: int
    timestamp: str

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
