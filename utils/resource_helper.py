# -*- coding: utf-8 -*-
"""
资源加载助手 - 兼容开发环境和PyInstaller打包环境
"""

import sys
import os
from pathlib import Path


def get_base_path() -> Path:
    """
    获取基础路径（兼容 PyInstaller 打包）
    
    开发环境：返回项目根目录
    打包后：返回 sys._MEIPASS（PyInstaller解压目录）
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后
        return Path(sys._MEIPASS)
    else:
        # 开发环境
        return Path(__file__).parent.parent


def get_resource_path(relative_path: str) -> str:
    """
    获取资源文件的绝对路径
    
    Args:
        relative_path: 相对于 resources 目录的路径，如 "icons/app.ico"
        
    Returns:
        资源文件的绝对路径
    """
    base_path = get_base_path()
    resource_path = base_path / "resources" / relative_path
    
    return str(resource_path)


def resource_exists(relative_path: str) -> bool:
    """
    检查资源文件是否存在
    
    Args:
        relative_path: 相对于 resources 目录的路径
        
    Returns:
        文件是否存在
    """
    path = get_resource_path(relative_path)
    return os.path.exists(path)


def get_icon_path(icon_name: str) -> str:
    """
    获取图标路径的便捷方法
    
    Args:
        icon_name: 图标文件名，如 "app.ico" 或 "add.png"
        
    Returns:
        图标文件的绝对路径
    """
    return get_resource_path(f"icons/{icon_name}")
