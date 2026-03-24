# -*- coding: utf-8 -*-
"""
图标助手 - 提供统一的图标获取接口
使用 PySide6 内置图标作为默认方案，避免资源文件缺失问题
"""

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QStyle, QApplication


def get_standard_icon(icon_type: str) -> QIcon:
    """
    获取系统标准图标
    
    Args:
        icon_type: 图标类型，支持：
            - 'app' / 'window' - 应用/窗口图标
            - 'add' / 'new' - 添加/新建
            - 'edit' - 编辑
            - 'delete' / 'remove' - 删除
            - 'save' - 保存
            - 'cancel' / 'close' - 取消/关闭
            - 'ok' / 'apply' / 'check' - 确认/应用
            - 'play' / 'run' / 'start' - 运行/开始
            - 'pause' / 'stop' - 暂停/停止
            - 'clear' / 'trash' - 清除
            - 'settings' / 'config' - 设置
            - 'info' - 信息
            - 'warning' - 警告
            - 'error' / 'critical' - 错误
            - 'question' - 问题
            - 'folder' / 'directory' - 文件夹
            - 'file' - 文件
            - 'refresh' / 'reload' - 刷新
            - 'search' / 'find' - 搜索
            - 'copy' - 复制
            - 'paste' - 粘贴
            - 'cut' - 剪切
            - 'undo' - 撤销
            - 'redo' - 重做
            - 'up' - 向上
            - 'down' - 向下
            - 'left' - 向左
            - 'right' - 向右
            - 'home' - 主页
            - 'back' - 返回
            - 'forward' - 前进
            - 'media' - 媒体
            - 'network' - 网络
            - 'computer' - 计算机
            - 'user' - 用户
            - 'time' / 'clock' - 时间/时钟
            - 'calendar' - 日历
            - 'mail' - 邮件
            - 'print' - 打印
            - 'help' - 帮助
    
    Returns:
        QIcon 对象
    """
    style = QApplication.style()
    
    # 图标映射表
    icon_map = {
        # 应用和窗口
        'app': QStyle.SP_ComputerIcon,
        'window': QStyle.SP_ComputerIcon,
        
        # 添加/新建
        'add': QStyle.SP_FileDialogNewFolder,
        'new': QStyle.SP_FileDialogNewFolder,
        
        # 编辑
        'edit': QStyle.SP_FileDialogDetailedView,
        
        # 删除
        'delete': QStyle.SP_TrashIcon,
        'remove': QStyle.SP_TrashIcon,
        
        # 保存
        'save': QStyle.SP_DialogSaveButton,
        
        # 取消/关闭
        'cancel': QStyle.SP_DialogCancelButton,
        'close': QStyle.SP_DialogCloseButton,
        
        # 确认/应用
        'ok': QStyle.SP_DialogOkButton,
        'apply': QStyle.SP_DialogApplyButton,
        'check': QStyle.SP_DialogApplyButton,
        
        # 运行/开始
        'play': QStyle.SP_MediaPlay,
        'run': QStyle.SP_MediaPlay,
        'start': QStyle.SP_MediaPlay,
        
        # 暂停/停止
        'pause': QStyle.SP_MediaPause,
        'stop': QStyle.SP_MediaStop,
        
        # 清除
        'clear': QStyle.SP_LineEditClearButton,
        'trash': QStyle.SP_TrashIcon,
        
        # 设置
        'settings': QStyle.SP_FileDialogDetailedView,
        'config': QStyle.SP_FileDialogDetailedView,
        
        # 消息类型
        'info': QStyle.SP_MessageBoxInformation,
        'warning': QStyle.SP_MessageBoxWarning,
        'error': QStyle.SP_MessageBoxCritical,
        'critical': QStyle.SP_MessageBoxCritical,
        'question': QStyle.SP_MessageBoxQuestion,
        
        # 文件和文件夹
        'folder': QStyle.SP_DirIcon,
        'directory': QStyle.SP_DirIcon,
        'file': QStyle.SP_FileIcon,
        
        # 导航
        'refresh': QStyle.SP_BrowserReload,
        'reload': QStyle.SP_BrowserReload,
        'search': QStyle.SP_FileDialogContentsView,
        'find': QStyle.SP_FileDialogContentsView,
        
        # 编辑操作
        'copy': QStyle.SP_FileDialogDetailedView,
        'paste': QStyle.SP_FileDialogDetailedView,
        'cut': QStyle.SP_FileDialogDetailedView,
        'undo': QStyle.SP_FileDialogDetailedView,
        'redo': QStyle.SP_FileDialogDetailedView,
        
        # 方向
        'up': QStyle.SP_ArrowUp,
        'down': QStyle.SP_ArrowDown,
        'left': QStyle.SP_ArrowLeft,
        'right': QStyle.SP_ArrowRight,
        
        # 浏览
        'home': QStyle.SP_DirHomeIcon,
        'back': QStyle.SP_ArrowBack,
        'forward': QStyle.SP_ArrowForward,
        
        # 其他
        'media': QStyle.SP_MediaPlay,
        'network': QStyle.SP_DirLinkIcon,
        'computer': QStyle.SP_ComputerIcon,
        'user': QStyle.SP_FileIcon,
        'time': QStyle.SP_MediaSeekForward,
        'clock': QStyle.SP_MediaSeekForward,
        'calendar': QStyle.SP_FileIcon,
        'mail': QStyle.SP_FileIcon,
        'print': QStyle.SP_FileIcon,
        'help': QStyle.SP_MessageBoxQuestion,
    }
    
    # 获取标准图标像素图
    if icon_type.lower() in icon_map:
        return style.standardIcon(icon_map[icon_type.lower()])
    
    # 默认返回一个空图标
    return QIcon()


def get_icon(icon_name: str, fallback: str = None) -> QIcon:
    """
    获取图标（优先使用自定义图标，回退到系统图标）
    
    Args:
        icon_name: 图标文件名或图标类型
        fallback: 回退的图标类型（用于 get_standard_icon）
        
    Returns:
        QIcon 对象
    """
    from utils.resource_helper import get_icon_path, resource_exists
    
    # 尝试加载自定义图标文件
    if resource_exists(f"icons/{icon_name}"):
        icon_path = get_icon_path(icon_name)
        icon = QIcon(icon_path)
        if not icon.isNull():
            return icon
    
    # 使用系统标准图标作为回退
    if fallback:
        return get_standard_icon(fallback)
    
    # 尝试将 icon_name 作为图标类型
    return get_standard_icon(icon_name)


def get_app_icon() -> QIcon:
    """获取应用图标"""
    return get_standard_icon('app')


def get_tray_icon() -> QIcon:
    """获取系统托盘图标"""
    return get_standard_icon('clock')
