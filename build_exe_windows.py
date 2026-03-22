#!/usr/bin/env python3
"""
Windows环境下的EXE打包脚本
需要在Windows环境中运行，使用PyInstaller
"""

import os
import sys
import shutil
from pathlib import Path

def build_exe_windows():
    """在Windows环境中构建EXE文件"""
    print("🚀 Windows定时任务管理器 - EXE打包脚本")
    print("=" * 60)
    print("注意：此脚本需要在Windows环境中运行")
    print("需要先安装: pip install pyinstaller")
    print("=" * 60)
    
    # 检查是否在Windows环境
    if sys.platform != "win32":
        print("❌ 错误：此脚本只能在Windows环境中运行")
        print(f"当前系统: {sys.platform}")
        print("请在Windows环境中运行此脚本")
        return False
    
    try:
        import PyInstaller
        print(f"✅ PyInstaller版本: {PyInstaller.__version__}")
    except ImportError:
        print("❌ 未找到PyInstaller，请先安装:")
        print("pip install pyinstaller")
        return False
    
    # 项目根目录
    project_root = Path(__file__).parent
    
    # 创建构建目录
    build_dir = project_root / "build"
    dist_dir = project_root / "dist"
    
    # 清理旧的构建目录
    for dir_path in [build_dir, dist_dir]:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"🧹 清理目录: {dir_path}")
    
    # PyInstaller命令参数
    # 注意：这里使用了简化的参数，实际使用时可能需要调整
    pyinstaller_args = [
        "pyinstaller",
        "--name=WindowsTaskScheduler",
        "--onefile",  # 单文件模式
        "--windowed",  # 窗口模式（不显示控制台）
        "--icon=icon.ico",  # 图标文件（需要准备）
        "--add-data=database;database",  # 包含数据库目录
        "--add-data=gui;gui",  # 包含GUI目录
        "--add-data=utils;utils",  # 包含工具目录
        "--add-data=core;core",  # 包含核心目录
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=apscheduler",
        "--hidden-import=apscheduler.triggers.date",
        "--hidden-import=apscheduler.triggers.interval",
        "--hidden-import=apscheduler.triggers.cron",
        "--hidden-import=chardet",
        "--hidden-import=dateutil",
        "--clean",  # 清理临时文件
        "main.py"  # 主程序入口
    ]
    
    print("\n🔨 PyInstaller命令:")
    print(" ".join(pyinstaller_args))
    
    print("\n📋 构建步骤:")
    print("1. 确保在Windows环境中")
    print("2. 安装所有依赖: pip install -r requirements.txt")
    print("3. 安装PyInstaller: pip install pyinstaller")
    print("4. 准备图标文件: icon.ico (可选)")
    print("5. 运行此脚本: python build_exe_windows.py")
    print("6. EXE文件将在 dist/ 目录中生成")
    
    print("\n💡 提示:")
    print("- 单文件模式(--onefile)会生成单个EXE文件，但启动较慢")
    print("- 如果不需要单文件，可以移除--onefile参数")
    print("- 窗口模式(--windowed)会隐藏控制台窗口")
    print("- 如果需要调试，可以移除--windowed参数")
    
    print("\n🎯 预期输出:")
    print("- dist/WindowsTaskScheduler.exe (单文件)")
    print("- 或 dist/WindowsTaskScheduler/ 目录 (多文件)")
    
    return True

def create_installer_script():
    """创建安装程序脚本（NSIS示例）"""
    print("\n📦 创建安装程序脚本...")
    
    nsis_script = """; Windows定时任务管理器 - NSIS安装脚本
; 需要NSIS (Nullsoft Scriptable Install System)

; 基本设置
!define APP_NAME "Windows定时任务管理器"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "十三香 🦞✨"
!define APP_WEB_SITE "https://example.com"
!define APP_EXE "WindowsTaskScheduler.exe"

; 压缩设置
SetCompressor lzma

; 现代UI设置
!include "MUI2.nsh"

; 安装程序属性
Name "${APP_NAME}"
OutFile "WindowsTaskScheduler_Setup.exe"
InstallDir "$PROGRAMFILES\\${APP_NAME}"
InstallDirRegKey HKLM "Software\\${APP_NAME}" "Install_Dir"
RequestExecutionLevel admin

; 界面设置
!define MUI_ABORTWARNING
!define MUI_ICON "icon.ico"
!define MUI_UNICON "icon.ico"

; 页面
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; 语言
!insertmacro MUI_LANGUAGE "SimpChinese"

; 安装部分
Section "主程序"
  SectionIn RO
  
  ; 设置输出目录
  SetOutPath $INSTDIR
  
  ; 复制文件
  File "dist\\WindowsTaskScheduler.exe"
  File "README.md"
  File "LICENSE.txt"
  
  ; 创建开始菜单快捷方式
  CreateDirectory "$SMPROGRAMS\\${APP_NAME}"
  CreateShortcut "$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk" "$INSTDIR\\${APP_EXE}"
  CreateShortcut "$SMPROGRAMS\\${APP_NAME}\\卸载.lnk" "$INSTDIR\\uninstall.exe"
  
  ; 创建桌面快捷方式
  CreateShortcut "$DESKTOP\\${APP_NAME}.lnk" "$INSTDIR\\${APP_EXE}"
  
  ; 写入注册表信息
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "UninstallString" '"$INSTDIR\\uninstall.exe"'
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "Publisher" "${APP_PUBLISHER}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "URLInfoAbout" "${APP_WEB_SITE}"
  
  ; 写入卸载程序
  WriteUninstaller "$INSTDIR\\uninstall.exe"
SectionEnd

; 卸载部分
Section "Uninstall"
  ; 删除文件
  Delete "$INSTDIR\\${APP_EXE}"
  Delete "$INSTDIR\\README.md"
  Delete "$INSTDIR\\LICENSE.txt"
  Delete "$INSTDIR\\uninstall.exe"
  
  ; 删除目录
  RMDir "$INSTDIR"
  
  ; 删除开始菜单快捷方式
  Delete "$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk"
  Delete "$SMPROGRAMS\\${APP_NAME}\\卸载.lnk"
  RMDir "$SMPROGRAMS\\${APP_NAME}"
  
  ; 删除桌面快捷方式
  Delete "$DESKTOP\\${APP_NAME}.lnk"
  
  ; 删除注册表信息
  DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}"
  DeleteRegKey HKLM "Software\\${APP_NAME}"
SectionEnd
"""
    
    script_path = Path(__file__).parent / "installer.nsi"
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(nsis_script)
    
    print(f"✅ 安装脚本已创建: {script_path}")
    print("\n📋 使用NSIS编译安装脚本:")
    print("1. 下载并安装NSIS: https://nsis.sourceforge.io/Download")
    print("2. 右键点击 installer.nsi -> 'Compile NSIS Script'")
    print("3. 安装程序将在当前目录生成")
    
    return script_path

if __name__ == "__main__":
    print("Windows定时任务管理器 - 打包工具")
    print("=" * 60)
    
    # 检查环境
    build_exe_windows()
    
    # 创建安装脚本
    create_installer_script()
    
    print("\n" + "=" * 60)
    print("📦 打包工具准备完成！")
    print("=" * 60)
    print("✅ EXE打包脚本已准备")
    print("✅ NSIS安装脚本已创建")
    print("\n🎯 下一步:")
    print("1. 在Windows环境中运行此脚本")
    print("2. 使用PyInstaller生成EXE文件")
    print("3. 使用NSIS创建安装程序")
    print("4. 测试安装和运行")
    print("=" * 60)