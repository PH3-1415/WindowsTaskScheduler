#!/usr/bin/env python3
"""
Windows定时任务管理器 - 主程序入口
"""

import sys
import os
import traceback
from pathlib import Path


def setup_path():
    """设置Python路径（兼容 PyInstaller 打包）"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后，使用 _MEIPASS
        base_path = Path(sys._MEIPASS)
    else:
        # 开发环境，使用脚本所在目录
        base_path = Path(__file__).parent.resolve()
    
    # 确保项目根目录在 Python 路径中
    if str(base_path) not in sys.path:
        sys.path.insert(0, str(base_path))
    
    return base_path


# 在任何其他导入之前设置路径
PROJECT_ROOT = setup_path()

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from app import TaskSchedulerApp
from config import ConfigManager
from utils.logger import get_logger


def setup_high_dpi():
    """设置高DPI支持"""
    # 在创建QApplication之前设置
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


def handle_exception(exc_type, exc_value, exc_traceback):
    """全局异常处理"""
    # 忽略键盘中断
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger = get_logger(__name__)
    logger.error("未捕获的异常:", exc_info=(exc_type, exc_value, exc_traceback))
    
    # 显示错误对话框
    try:
        from PySide6.QtWidgets import QMessageBox
        error_msg = f"发生未处理的异常:\n\n{exc_type.__name__}: {exc_value}"
        QMessageBox.critical(None, "程序错误", error_msg)
    except:
        pass


def check_single_instance():
    """检查是否已有实例运行"""
    # Windows下可以使用命名互斥体
    if sys.platform == 'win32':
        try:
            import win32event
            import win32api
            import winerror
            
            mutex_name = "WindowsTaskScheduler_Mutex"
            mutex = win32event.CreateMutex(None, False, mutex_name)
            last_error = win32api.GetLastError()
            
            if last_error == winerror.ERROR_ALREADY_EXISTS:
                # 已有实例运行
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    None, 
                    "程序已运行",
                    "Windows定时任务管理器已经在运行中。\n\n"
                    "请检查系统托盘图标。"
                )
                return False
        except ImportError:
            # 如果没有win32api，跳过单实例检查
            pass
    
    return True


def main():
    """主函数"""
    # 设置异常处理
    sys.excepthook = handle_exception
    
    # 检查单实例
    if not check_single_instance():
        sys.exit(0)
    
    # 设置高DPI
    setup_high_dpi()
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("Windows定时任务管理器")
    app.setOrganizationName("十三香工作室")
    app.setApplicationVersion("1.0.0")
    
    # 设置字体（在Windows上使用系统字体）
    if sys.platform == 'win32':
        font = QFont("Microsoft YaHei UI", 9)
        app.setFont(font)
    
    # 创建主窗口
    try:
        window = TaskSchedulerApp()
        
        # 显示窗口
        window.show()
        
        # 运行应用
        exit_code = app.exec()
        
        # 清理资源
        window.cleanup()
        
        sys.exit(exit_code)
        
    except Exception as e:
        # 启动失败
        logger = get_logger(__name__)
        logger.error("程序启动失败:", exc_info=True)
        
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(
            None,
            "启动失败",
            f"程序启动失败:\n\n{str(e)}\n\n"
            "请检查日志文件获取详细信息。"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()