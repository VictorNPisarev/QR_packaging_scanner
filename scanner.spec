# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for QR Packaging Scanner
"""

import sys
from pathlib import Path

block_cipher = None

# Определяем пути
project_root = Path('.')
src_path = project_root / 'src'

# Собираем все .py файлы из src рекурсивно
py_files = []
for py_file in src_path.rglob('*.py'):
    py_files.append((str(py_file), str(py_file.parent.relative_to(project_root))))

a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # Добавляем все исходники (чтобы работали импорты)
        ('src', 'src'),
        # Конфигурационные файлы
        ('config', 'config'),
        # .env файл если есть
        ('.env', '.'),
    ],
    hiddenimports=[
        # OpenCV
        'cv2',
        'cv2.data',
        # numpy
        'numpy',
        'numpy.core._methods',
        'numpy.lib.format',
        # pika
        'pika',
        'pika.adapters',
        'pika.adapters.blocking_connection',
        'pika.channel',
        'pika.connection',
        'pika.spec',
        # pyzbar (если используется)
        # 'pyzbar',
        # 'pyzbar.pyzbar',
        # Прочие
        'yaml',
        'dotenv',
        'logging',
        'json',
        'datetime',
        'pathlib',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Исключаем лишнее для уменьшения размера
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
        'PIL',
        'cv2.cv2',
        'cv2.cv2.*',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Фильтруем бинарники OpenCV (оставляем только нужное)
def filter_binaries(py_files):
    """Убираем ненужные DLL чтобы уменьшить размер"""
    filtered = []
    for name, path, dest in py_files:
        # Оставляем только нужные dll
        if 'opencv_videoio_ffmpeg' in name.lower():
            continue  # Пропускаем ffmpeg, если не используется
        filtered.append((name, path, dest))
    return filtered

a.binaries = filter_binaries(a.binaries)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='QR_Scanner',  # Имя выходного файла
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,          # Сжатие UPX (установите отдельно для лучшего сжатия)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,      # True = консольное приложение (видно логи)
    # console=False,   # Раскомментируйте для GUI версии (без консоли)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='scanner.ico',  # Добавьте файл иконки при желании
)
