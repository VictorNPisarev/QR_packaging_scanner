"""Проверка всех импортов в проекте"""

import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_imports() -> None:
    """Проверяем, что все модули импортируются"""
    modules_to_test: list[str] = [
        "src.camera.capture",
        "src.scanner.detector",
        "src.messaging.events",
        "src.messaging.broker",
        "src.services.deduplication",
        "src.services.scan_service",
        "src.ui.overlay",
    ]

    success_count: int = 0
    fail_count: int = 0

    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"✅ {module_name}")
            success_count += 1
        except ImportError as e:
            print(f"❌ {module_name}: {e}")
            fail_count += 1

    print(f"\n{'=' * 50}")
    print(f"Результат: {success_count}/{len(modules_to_test)} модулей импортировано")

    if fail_count > 0:
        print(f"❌ {fail_count} ошибок импорта")
        sys.exit(1)
    else:
        print("✅ Все модули импортируются корректно")


if __name__ == "__main__":
    test_imports()
