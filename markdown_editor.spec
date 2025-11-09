# -*- mode: python ; coding: utf-8 -*-

import os
import sys

# Явно указываем путь к текущей директории
current_dir = os.path.abspath('.')
sys.path.insert(0, current_dir)

block_cipher = None

a = Analysis(
    # Явно указываем полные пути к файлам
    [os.path.join(current_dir, 'main.py')],
    pathex=[current_dir],
    binaries=[],
    datas=[
        (os.path.join(current_dir, 'LICENSE'), '.'),
        (os.path.join(current_dir, 'markdown_editor_icon.ico'), '.'),
    ],
    hiddenimports=[
        'PyQt5.QtPrintSupport',
        'PyQt5.QtWebEngineWidgets',
        'PyQt5.QtWebChannel',
        'markdown.extensions.fenced_code',
        'markdown.extensions.codehilite',
        'markdown.extensions.tables',
        'markdown.extensions.nl2br',
        'markdown.extensions.sane_lists',
        'pygments.lexers',
        'pygments.formatters',
        'pygments.styles',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'IPython',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MarkdownEditor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(current_dir, 'markdown_editor_icon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MarkdownEditor',
)
