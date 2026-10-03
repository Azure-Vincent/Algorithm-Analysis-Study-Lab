# PyInstaller build configuration for the desktop executable (committed on purpose: it is the
# reproducible build recipe). Build with build.bat (Windows) or build.sh (macOS/Linux), or:
#     pyinstaller --noconfirm --clean AlgorithmStudy.spec
# Output: dist/AlgorithmStudy.exe (Windows) or dist/AlgorithmStudy (macOS/Linux).
# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None
ROOT = os.path.abspath(SPECPATH)

a = Analysis(
    [os.path.join(ROOT, "launcher.py")],
    pathex=[ROOT],
    binaries=[],
    # Read-only assets Flask loads from disk. Writable data (the SQLite database and the
    # session key) lives in the per-user data folder chosen by launcher.py, never in here.
    datas=[
        (os.path.join(ROOT, "templates"), "templates"),
        (os.path.join(ROOT, "static"), "static"),
    ],
    hiddenimports=[
        "engine.sandbox_worker",     # run by the app itself as the pseudocode sandbox (see engine/sandbox.py)
        "waitress",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Not used by the app; keeps the executable small if they happen to be installed.
    excludes=["tkinter", "numpy", "matplotlib", "IPython", "pytest", "playwright", "PIL", "pandas",
              "scipy", "gmpy2"],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="AlgorithmStudy",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                 # UPX-packed executables trigger more antivirus false positives
    runtime_tmpdir=None,
    console=True,              # the small window shows the address and closes the app when closed
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
