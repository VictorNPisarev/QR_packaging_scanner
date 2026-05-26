from PyInstaller.utils.hooks import (  # type: ignore[import-untyped]
    collect_data_files,
    collect_submodules,
)

hiddenimports = collect_submodules("cv2", filter=lambda name: "cv2" in name)

excludedimports = [
    "cv2.cv2",
    "cv2.data",
    "cv2.mat_wrapper",
    "cv2.misc",
    "cv2.utils",
]

datas = collect_data_files("cv2")
