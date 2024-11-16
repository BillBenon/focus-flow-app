from cx_Freeze import setup, Executable
import sys

build_exe_options = {
    "packages": [
        "cv2", "numpy", "dlib", "tkinter", "pystray", "win32gui",
        "win32con", "win32service", "PIL", "matplotlib"
    ],
    "include_files": [
        "icon.ico",
        "shape_predictor_68_face_landmarks.dat"
    ],
    "excludes": [],
    "include_msvcr": True
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="WellnessMonitor",
    version="1.0",
    description="AI-powered wellness monitor",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "main.py",
            base=base,
            icon="icon.ico",
            target_name="WellnessMonitor.exe"
        )
    ]
)