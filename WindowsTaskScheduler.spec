# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec 文件 - 用于打包 WindowsTaskScheduler
"""

import sys
from pathlib import Path

# 分析主程序
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # 主要模块
        'app',
        'config',
        # GUI 模块
        'gui',
        'gui.main_window',
        'gui.task_list_widget',
        'gui.output_widget',
        'gui.system_tray',
        'gui.task_edit_dialog',
        'gui.settings_dialog',
        'gui.default_script_dialog',
        'gui.styles',
        'gui.styles.colors',
        # 核心模块
        'core',
        'core.scheduler',
        'core.task_executor',
        'core.condition_evaluator',
        'core.default_script',
        # 数据库模块
        'database',
        'database.db_manager',
        'database.models',
        # 工具模块
        'utils',
        'utils.logger',
        'utils.auto_start',
        'utils.data_manager',
        'utils.date_utils',
        'utils.emoji_handler',
        'utils.encoding_helper',
        # 资源模块
        'resources',
        'tools',
        # 第三方库
        'apscheduler',
        'apscheduler.schedulers',
        'apscheduler.schedulers.background',
        'apscheduler.triggers',
        'apscheduler.triggers.cron',
        'apscheduler.triggers.date',
        'apscheduler.executors',
        'apscheduler.executors.pool',
        'apscheduler.jobstores',
        'apscheduler.jobstores.memory',
        'dateutil',
        'dateutil.parser',
        'chardet',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

# 收集 PySide6 所有文件
pyinstaller_pyside6 = []
for item in a.binaries + a.datas:
    if 'PySide6' in item[0] or 'shiboken6' in item[0]:
        pyinstaller_pyside6.append(item)

# PYZ 压缩包
pyz = PYZ(a.pure)

# EXE 可执行文件
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='WindowsTaskScheduler',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
