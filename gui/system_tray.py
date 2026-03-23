"""
系统托盘组件 - 管理系统托盘图标和菜单
"""

import logging
from typing import Optional

from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor

from gui.styles.colors import COLORS


class SystemTray(QSystemTrayIcon):
    """系统托盘组件"""
    
    # 信号定义
    show_window = Signal()          # 显示主窗口信号
    hide_window = Signal()          # 隐藏主窗口信号
    pause_all = Signal()            # 暂停所有任务信号
    resume_all = Signal()           # 恢复所有任务信号
    run_default_scripts = Signal()  # 运行默认脚本信号
    show_settings = Signal()        # 显示设置信号
    quit_app = Signal()             # 退出应用信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化状态
        self.is_visible = False
        self.is_running = False
        self.has_error = False
        
        # 初始化图标
        self._init_icons()
        
        # 初始化菜单
        self._init_menu()
        
        # 设置初始图标
        self.setIcon(self.normal_icon)
        self.setToolTip("Windows定时任务管理器\n状态: 就绪")
        
        # 连接信号
        self.activated.connect(self._on_tray_activated)
        
        # 启动动画定时器
        self._start_animation_timer()
    
    def _init_icons(self):
        """初始化图标"""
        # 创建基础图标（⏰ + ♻️）
        self._create_base_icons()
        
        # 正常状态图标（奶茶色）
        self.normal_icon = self._create_colored_icon(COLORS['button_normal'])
        
        # 运行状态图标（蓝色）
        self.running_icon = self._create_colored_icon(COLORS['status_running'])
        
        # 错误状态图标（红色）
        self.error_icon = self._create_colored_icon(COLORS['status_error'])
        
        # 动画图标列表（用于呼吸效果）
        self.animation_icons = []
        self._create_animation_icons()
        
        # 当前动画帧
        self.animation_frame = 0
    
    def _create_base_icons(self):
        """创建基础图标"""
        # 创建闹钟图标（⏰）
        self.clock_pixmap = QPixmap(64, 64)
        self.clock_pixmap.fill(Qt.transparent)
        
        painter = QPainter(self.clock_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制闹钟主体
        painter.setBrush(QColor(COLORS['button_normal']))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(12, 12, 40, 40)
        
        # 绘制闹钟铃铛
        painter.setBrush(QColor(COLORS['text_primary']))
        painter.drawEllipse(8, 8, 8, 8)
        painter.drawEllipse(48, 8, 8, 8)
        
        # 绘制时间指针
        painter.setPen(QColor(COLORS['background_primary']))
        painter.setBrush(QColor(COLORS['background_primary']))
        
        # 时针
        painter.save()
        painter.translate(32, 32)
        painter.rotate(30)  # 指向1点
        painter.drawRect(-2, -20, 4, 20)
        painter.restore()
        
        # 分针
        painter.save()
        painter.translate(32, 32)
        painter.rotate(180)  # 指向6点
        painter.drawRect(-1, -25, 2, 25)
        painter.restore()
        
        painter.end()
        
        # 创建循环图标（♻️）
        self.recycle_pixmap = QPixmap(32, 32)
        self.recycle_pixmap.fill(Qt.transparent)
        
        painter = QPainter(self.recycle_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制循环箭头
        painter.setPen(QColor(COLORS['text_primary']))
        painter.setBrush(Qt.NoBrush)
        painter.setPenWidth(2)
        
        # 绘制三个箭头组成循环
        for i in range(3):
            painter.save()
            painter.translate(16, 16)
            painter.rotate(i * 120)
            
            # 绘制箭头
            path = painter.path()
            path.moveTo(0, -10)
            path.lineTo(8, -2)
            path.lineTo(0, 6)
            path.lineTo(-8, -2)
            path.closeSubpath()
            
            painter.drawPath(path)
            painter.restore()
        
        painter.end()
    
    def _create_colored_icon(self, color: str) -> QIcon:
        """创建彩色图标"""
        # 创建组合图标
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制闹钟（使用指定颜色）
        clock_color = QColor(color)
        painter.setBrush(clock_color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(12, 12, 40, 40)
        
        # 绘制闹钟铃铛
        painter.setBrush(QColor(COLORS['text_primary']))
        painter.drawEllipse(8, 8, 8, 8)
        painter.drawEllipse(48, 8, 8, 8)
        
        # 绘制时间指针
        painter.setPen(QColor(COLORS['background_primary']))
        painter.setBrush(QColor(COLORS['background_primary']))
        
        # 时针
        painter.save()
        painter.translate(32, 32)
        painter.rotate(30)
        painter.drawRect(-2, -20, 4, 20)
        painter.restore()
        
        # 分针
        painter.save()
        painter.translate(32, 32)
        painter.rotate(180)
        painter.drawRect(-1, -25, 2, 25)
        painter.restore()
        
        # 绘制循环图标（叠加在右下角）
        painter.drawPixmap(32, 32, self.recycle_pixmap)
        
        painter.end()
        
        return QIcon(pixmap)
    
    def _create_animation_icons(self):
        """创建动画图标"""
        # 创建呼吸动画效果（透明度变化）
        for i in range(10):
            # 计算透明度（0.3到1.0之间正弦变化）
            alpha = 0.3 + 0.7 * (abs(i - 5) / 5.0)
            
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.transparent)
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 绘制闹钟（带透明度）
            clock_color = QColor(COLORS['status_running'])
            clock_color.setAlphaF(alpha)
            painter.setBrush(clock_color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(12, 12, 40, 40)
            
            # 绘制闹钟铃铛
            painter.setBrush(QColor(COLORS['text_primary']))
            painter.drawEllipse(8, 8, 8, 8)
            painter.drawEllipse(48, 8, 8, 8)
            
            # 绘制时间指针
            painter.setPen(QColor(COLORS['background_primary']))
            painter.setBrush(QColor(COLORS['background_primary']))
            
            # 时针
            painter.save()
            painter.translate(32, 32)
            painter.rotate(30)
            painter.drawRect(-2, -20, 4, 20)
            painter.restore()
            
            # 分针
            painter.save()
            painter.translate(32, 32)
            painter.rotate(180)
            painter.drawRect(-1, -25, 2, 25)
            painter.restore()
            
            # 绘制循环图标
            painter.drawPixmap(32, 32, self.recycle_pixmap)
            
            painter.end()
            
            self.animation_icons.append(QIcon(pixmap))
    
    def _init_menu(self):
        """初始化菜单"""
        self.menu = QMenu()
        
        # 显示/隐藏主窗口
        self.show_action = QAction("显示主窗口", self)
        self.show_action.triggered.connect(self.show_window.emit)
        self.menu.addAction(self.show_action)
        
        self.menu.addSeparator()
        
        # 任务控制
        self.pause_action = QAction("暂停所有任务", self)
        self.pause_action.triggered.connect(self.pause_all.emit)
        self.menu.addAction(self.pause_action)
        
        self.resume_action = QAction("恢复所有任务", self)
        self.resume_action.triggered.connect(self.resume_all.emit)
        self.resume_action.setEnabled(False)
        self.menu.addAction(self.resume_action)
        
        # 运行默认脚本
        self.run_scripts_action = QAction("运行默认脚本", self)
        self.run_scripts_action.triggered.connect(self.run_default_scripts.emit)
        self.menu.addAction(self.run_scripts_action)
        
        self.menu.addSeparator()
        
        # 设置
        self.settings_action = QAction("设置", self)
        self.settings_action.triggered.connect(self.show_settings.emit)
        self.menu.addAction(self.settings_action)
        
        self.menu.addSeparator()
        
        # 退出
        self.quit_action = QAction("退出", self)
        self.quit_action.triggered.connect(self.quit_app.emit)
        self.menu.addAction(self.quit_action)
        
        # 设置菜单
        self.setContextMenu(self.menu)
    
    def _start_animation_timer(self):
        """启动动画定时器"""
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._update_animation)
        self.animation_timer.start(100)  # 100毫秒更新一次
    
    def _update_animation(self):
        """更新动画"""
        if self.is_running and not self.has_error:
            # 运行状态：呼吸动画
            self.animation_frame = (self.animation_frame + 1) % len(self.animation_icons)
            self.setIcon(self.animation_icons[self.animation_frame])
        
        elif self.has_error:
            # 错误状态：闪烁动画
            if self.animation_frame % 2 == 0:
                self.setIcon(self.error_icon)
            else:
                self.setIcon(self.normal_icon)
            self.animation_frame = (self.animation_frame + 1) % 10
    
    def _on_tray_activated(self, reason):
        """托盘图标激活"""
        if reason == QSystemTrayIcon.Trigger:  # 左键单击
            if self.is_visible:
                self.hide_window.emit()
            else:
                self.show_window.emit()
        
        elif reason == QSystemTrayIcon.DoubleClick:  # 双击
            self.show_window.emit()
        
        elif reason == QSystemTrayIcon.Context:  # 右键
            # 菜单会自动显示
            pass
    
    # ========== 公共接口 ==========
    
    def set_running_state(self, is_running: bool):
        """设置运行状态"""
        self.is_running = is_running
        
        if is_running:
            self.setToolTip("Windows定时任务管理器\n状态: 运行中")
            self.pause_action.setEnabled(True)
            self.resume_action.setEnabled(False)
        else:
            self.setToolTip("Windows定时任务管理器\n状态: 就绪")
            self.pause_action.setEnabled(False)
            self.resume_action.setEnabled(True)
            
            # 停止动画，恢复正常图标
            if not self.has_error:
                self.setIcon(self.normal_icon)
    
    def set_error_state(self, has_error: bool, error_message: str = ""):
        """设置错误状态"""
        self.has_error = has_error
        
        if has_error:
            self.setToolTip(f"Windows定时任务管理器\n状态: 错误\n{error_message}")
        else:
            self.setToolTip("Windows定时任务管理器\n状态: 就绪")
            
            # 恢复正常图标
            if not self.is_running:
                self.setIcon(self.normal_icon)
    
    def set_visible_state(self, is_visible: bool):
        """设置可见状态"""
        self.is_visible = is_visible
        
        if is_visible:
            self.show_action.setText("隐藏主窗口")
        else:
            self.show_action.setText("显示主窗口")
    
    def show_notification(self, title: str, message: str, icon_type: QSystemTrayIcon.MessageIcon = None):
        """显示通知"""
        if icon_type is None:
            icon_type = QSystemTrayIcon.Information
        
        self.showMessage(title, message, icon_type, 3000)  # 3秒后自动消失
    
    def show_task_started_notification(self, task_name: str):
        """显示任务开始通知"""
        self.show_notification(
            "任务开始",
            f"任务 '{task_name}' 开始执行",
            QSystemTrayIcon.Information
        )
    
    def show_task_completed_notification(self, task_name: str, success: bool):
        """显示任务完成通知"""
        if success:
            self.show_notification(
                "任务完成",
                f"任务 '{task_name}' 执行成功",
                QSystemTrayIcon.Information
            )
        else:
            self.show_notification(
                "任务失败",
                f"任务 '{task_name}' 执行失败",
                QSystemTrayIcon.Warning
            )
    
    def show_error_notification(self, error_message: str):
        """显示错误通知"""
        self.show_notification(
            "系统错误",
            error_message,
            QSystemTrayIcon.Critical
        )
    
    def update_menu_state(self, has_running_tasks: bool, has_paused_tasks: bool):
        """更新菜单状态"""
        self.pause_action.setEnabled(has_running_tasks)
        self.resume_action.setEnabled(has_paused_tasks)
    
    def set_custom_menu(self, menu: QMenu):
        """设置自定义菜单"""
        self.menu = menu
        self.setContextMenu(menu)
    
    def add_custom_action(self, action: QAction):
        """添加自定义动作"""
        self.menu.addAction(action)
    
    def insert_custom_action(self, action: QAction, before_action: QAction = None):
        """插入自定义动作"""
        if before_action:
            self.menu.insertAction(before_action, action)
        else:
            self.menu.addAction(action)
    
    def remove_custom_action(self, action: QAction):
        """移除自定义动作"""
        self.menu.removeAction(action)
    
    # ========== 工具方法 ==========
    
    def is_system_tray_available(self) -> bool:
        """检查系统托盘是否可用"""
        return self.isSystemTrayAvailable()
    
    def is_system_tray_visible(self) -> bool:
        """检查系统托盘是否可见"""
        return self.isVisible()
    
    def hide_tray(self):
        """隐藏托盘图标"""
        self.hide()
    
    def show_tray(self):
        """显示托盘图标"""
        self.show()
    
    def set_tool_tip(self, tooltip: str):
        """设置工具提示"""
        self.setToolTip(tooltip)
    
    def get_tool_tip(self) -> str:
        """获取工具提示"""
        return self.toolTip()