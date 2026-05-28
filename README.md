markdown
# QR Packaging Scanner

Сервис сканирования Data Matrix кодов на упаковке для автоматизации учёта и маркировки.

## Возможности

- Захват видео с USB/веб-камеры (неподвижно закреплённой над упаковкой)
- Распознавание Data Matrix (Честный знак), QR-кодов, штрихкодов
- Калибровка по форме и размерам индивидуальной упаковки
- Послойный учёт: фиксация заполнения слоя, переход к следующему
- Отправка событий в RabbitMQ для интеграции с ERP/MES/1С
- Автоматическая печать этикетки на коробку по заполнении
- Консольный UI с оверлеем поверх видео

## Стек

- **Python 3.12+**
- **OpenCV** — захват видео
- **zxing-cpp** — распознавание Data Matrix, QR, штрихкодов
- **RabbitMQ** — брокер сообщений
- **C# ASP.NET Core** — backend (отдельный репозиторий)

## Требования

- Python 3.12 или выше
- Веб-камера или USB-камера
- RabbitMQ (опционально, для отправки событий)
- Windows 10/11 (для Linux/Mac требуется заменить способ сборки)

## Установка

```powershell
    # Клонировать репозиторий
    git clone <repo-url>
    cd QR_packaging_scanner

    # Создать виртуальное окружение
    python -m venv venv
    .\venv\Scripts\Activate.ps1

    # Установить зависимости
    pip install -r requirements/base.txt
    Запуск
    powershell
    # Активировать окружение
    .\venv\Scripts\Activate.ps1

    # Запустить сканер
    python main.py
```

## Управление в процессе работы
Клавиша       Действие
Q               Выход
S               Выбор области сканирования
R               Сброс счётчика
Space	          Пауза/продолжить

## Дополнительно:  запуск RabbitMQ

```powershell
    docker-compose up -d
```
## Веб-интерфейс RabbitMQ: http://localhost:15672 (admin/admin)

## Сборка в EXE
```powershell
    # Установить PyInstaller
    pip install pyinstaller

    # Базовая сборка
    .\venv\Scripts\Activate.ps1

    pyinstaller --name="QR_Scanner" --add-data "src;src" --hidden-import zxingcpp --hidden-import cv2 --hidden-import numpy --hidden-import pika main.py

    # Или через spec-файл
    pyinstaller scanner.spec --clean --noconfirm
```
EXE появится в dist/QR_Scanner/QR_Scanner.exe.

## Уменьшение размера EXE
```powershell
    # Установить UPX (опционально)
    winget install upx

    # Собрать со сжатием
    pyinstaller scanner.spec --clean --noconfirm --upx-dir "C:\Program Files\upx"
```
## Калибровка
Поместите пустой слой (0-й слой) с калибровочными метками под камеру

Запустите сканер и нажмите S для выбора области

Укажите количество рядов и столбцов, форму упаковки

Калибровка сохранится в calibration.json

## Поддерживаемые формы:

circle — консервные банки, бутылки

square — квадратная упаковка

rectangle — прямоугольная (Tetrapack)

triangle, hexagon — прочие

## Интеграция
Сканер отправляет события в RabbitMQ:

barcode_events — очередь событий обнаружения кода

Формат: JSON с полями barcode, barcode_type, camera_id, timestamp, position

Backend на C# обрабатывает события, ведёт учёт слоёв, управляет принтером этикеток.

## Структура проекта

QR_packaging_scanner/
├── src/
│   ├── models/          # Модели данных
│   ├── camera/          # Захват видео
│   ├── scanner/         # Детектор и калибратор
│   ├── messaging/       # RabbitMQ клиент
│   ├── services/        # Основной сервис
│   └── ui/              # Оверлей и конфигурация
├── config/              # Конфигурационные файлы
├── hooks/               # Хуки для PyInstaller
├── requirements/        # Зависимости
├── main.py              # Точка входа
├── scanner.spec         # Спецификация PyInstaller
└── docker-compose.yml   # RabbitMQ

## Лицензия
MIT
