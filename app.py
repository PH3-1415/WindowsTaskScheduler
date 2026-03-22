"""
应用主类
"""

import sys
import logging
from typing import Optional

from PySide6.QtWidgets import QMainWindow, QApplication, QMessageBox
from PySide6.QtCore import QTimer, Qt, QSettings
from PySide6.QtGui import QCloseEvent, QIcon

from config import ConfigManager
from database.db_manager import DatabaseManager
from utils.auto_start import get_auto_start_manager
from gui.main_window import MainWindow


class TaskSchedulerApp(QMainWindow):
    """应用主类"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化组件
        self.config = ConfigManager()
        self.db = DatabaseManager()
        self.auto_start_manager = get_auto_start_manager()
        
        # 初始化状态
        self._initialized = False
        self._shutting_down = False
        
        # 设置窗口属性
        self.setWindowTitle("Windows定时任务管理器")
        self.setMinimumSize(800, 500)
        
        # 应用图标
        self._setup_icon()
        
        # 初始化UI
        self._init_ui()
        
        # 初始化数据
        self._init_data()
        
        # 启动定时器
        self._start_timers()
        
        # 标记初始化完成
        self._initialized = True
        
        # 如果是第一次运行，显示欢迎信息
        if self.config.is_first_run:
            self._show_welcome_message()
    
    def _setup_icon(self):
        """设置应用图标"""
        try:
            # 尝试加载图标文件
            icon_path = "resources/icons/app.ico"
            icon = QIcon(icon_path)
            self.setWindowIcon(icon)
            QApplication.setWindowIcon(icon)
        except:
            # 如果图标文件不存在，使用默认图标
            pass
    
    def _init_ui(self):
        """初始化UI"""
        # 创建主窗口
        self.main_window = MainWindow(self)
        self.setCentralWidget(self.main_window)
        
        # 设置窗口大小和位置
        self._restore_window_state()
        
        # 应用样式
        self._apply_styles()
    
    def _init_data(self):
        """初始化数据"""
        try:
            # 初始化数据库
            self.db.initialize()
            
            # 清理旧日志
            self.db.cleanup_old_logs(self.config.cleanup_logs_days)
            
            # 检查开机自启动设置
            auto_start_enabled = self.config.auto_start
            if auto_start_enabled and not self.auto_start_manager.is_enabled():
                # 自动启用开机自启动
                self.auto_start_manager.enable()
            
            logging.info("应用数据初始化完成")
        except Exception as e:
            logging.error(f"数据初始化失败: {e}")
            QMessageBox.critical(
                self,
                "初始化失败",
                f"应用初始化失败:\n\n{str(e)}\n\n请检查数据目录权限。"
            )
    
    def _start_timers(self):
        """启动定时器"""
        # 状态更新定时器（每秒）
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(1000)  # 1秒
        
        # 日志清理定时器（每天）
        self.cleanup_timer = QTimer(self)
        self.cleanup_timer.timeout.connect(self._cleanup_old_logs)
        self.cleanup_timer.start(24 * 60 * 60 * 1000)  # 24小时
    
    def _restore_window_state(self):
        """恢复窗口状态"""
        width, height = self.config.window_size
        x, y = self.config.window_position
        
        # 设置窗口大小
        self.resize(width, height)
        
        # 设置窗口位置
        if x >= 0 and y >= 0:
            self.move(x, y)
        else:
            # 居中显示
            self.center_window()
    
    def center_window(self):
        """居中显示窗口"""
        screen = QApplication.primaryScreen().geometry()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen.center())
        self.move(window_geometry.topLeft())
    
    def _apply_styles(self):
        """应用样式"""
        try:
            # 加载QSS样式表
            from gui.styles.colors import COLORS
            
            # 设置窗口背景色
            self.setStyleSheet(f"""
                QMainWindow {{
                    background-color: {COLORS['background_primary']};
                }}
                
                QStatusBar {{
                    background-color: {COLORS['background_secondary']};
                    color: {COLORS['text_primary']};
                    border-top: 1px solid {COLORS['border_light']};
                }}
            """)
        except Exception as e:
            logging.warning(f"应用样式失败: {e}")
    
    def _show_welcome_message(self):
        """显示欢迎信息"""
        welcome_msg = """
        <h3>欢迎使用 Windows定时任务管理器！</h3>
        <p>这是一个简单易用的定时任务执行工具，支持：</p>
        <ul>
        <li>免安装，双击即用</li>
        <li>定时执行命令行任务</li>
        <li>条件判断和脚本支持</li>
        <li>7×24小时后台运行</li>
        <li>开机自启动</li>
        </ul>
        <p>点击"添加任务"开始使用，或查看帮助文档了解更多功能。</p>
        """
        
        QMessageBox.information(
            self,
            "欢迎",
            welcome_msg
        )
        
        # 标记已显示欢迎信息
        self.config.is_first_run = False
    
    def _update_status(self):
        """更新状态栏"""
        if not self._initialized or self._shutting_down:
            return
        
        try:
            # 获取任务状态
            tasks = self.db.get_all_tasks(enabled_only=True)
            running_count = sum(1 for task in tasks if hasattr(task, 'is_running') and task.is_running)
            enabled_count = len(tasks)
            
            # 构建状态文本
            status_parts = []
            
            if running_count > 0:
                status_parts.append(f"运行中: {running_count}")
            
            status_parts.append(f"任务: {enabled_count}")
            
            # 添加下一个任务时间
            next_task_time = self._get_next_task_time()
            if next_task_time:
                status_parts.append(f"下一个: {next_task_time}")
            
            # 添加托盘状态
            status_parts.append("托盘: 正常")
            
            # 更新状态栏
            status_text = " | ".join(status_parts)
            self.statusBar().showMessage(status_text)
            
        except Exception as e:
            logging.error(f"更新状态失败: {e}")
    
    def _get_next_task_time(self) -> Optional[str]:
        """获取下一个任务时间"""
        # TODO: 实现获取下一个任务时间
        return None
    
    def _cleanup_old_logs(self):
        """清理旧日志"""
        try:
            days = self.config.cleanup_logs_days
            self.db.cleanup_old_logs(days)
            logging.info(f"已清理{days}天前的日志")
        except Exception as e:
            logging.error(f"清理日志失败: {e}")
    
    # ========== 事件处理 ==========
    
    def closeEvent(self, event: QCloseEvent):
        """关闭事件处理"""
        if self.config.minimize_to_tray:
            # 最小化到托盘，而不是退出
            self.hide()
            event.ignore()
            
            # 显示托盘提示
            if hasattr(self.main_window, 'system_tray'):
                self.main_window.system_tray.showMessage(
                    "程序已最小化",
                    "Windows定时任务管理器已最小化到系统托盘。",
                    QIcon("resources/icons/tray_normal.ico"),
                    3000
                )
        else:
            # 正常退出
            self.cleanup()
            event.accept()
    
    def cleanup(self):
        """清理资源"""
        if self._shutting_down:
            return
        
        self._shutting_down = True
        
        # 停止定时器
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        if hasattr(self, 'cleanup_timer'):
            self.cleanup_timer.stop()
        
        # 保存窗口状态
        self._save_window_state()
        
        # 标记运行完成
        self.config.mark_run_complete()
        
        # 关闭数据库
        if self.db:
            self.db.close()
        
        logging.info("应用清理完成")
    
    def _save_window_state(self):
        """保存窗口状态"""
        if self.isVisible():
            geometry = self.geometry()
            self.config.window_position = (geometry.x(), geometry.y())
            self.config.window_size = (geometry.width(), geometry.height())
    
    # ========== 公共方法 ==========
    
    def show_settings_dialog(self):
        """显示设置对话框"""
        # TODO: 实现设置对话框
        from gui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        if dialog.exec():
            # 设置已保存，重新应用
            self._apply_styles()
            self._update_status()
    
    def add_task(self, task_data: dict):
        """添加任务"""
        # TODO: 实现添加任务
        pass
    
    def edit_task(self, task_id: int):
        """编辑任务"""
        # TODO: 实现编辑任务
        pass
    
    def delete_task(self, task_id: int):
        """删除任务"""
        # TODO: 实现删除任务
        pass
    
    def run_task_now(self, task_id: int):
        """立即运行任务"""
        # TODO: 实现立即运行任务
        pass
    
    def pause_all_tasks(self):
        """暂停所有任务"""
        # TODO: 实现暂停所有任务
        pass
    
    def resume_all_tasks(self):
        """恢复所有任务"""
        # TODO: 实现恢复所有任务
        pass
    
    def show_about_dialog(self):
        """显示关于对话框"""
        about_text = f"""
        <h3>Windows定时任务管理器</h3>
        <p>版本: {self.config.app_version}</p>
        <p>一个简单易用的定时任务执行工具</p>
        <p>功能特点:</p>
        <ul>
        <li>免安装，双击即用</li>
        <li>支持定时执行命令行任务</li>
        <li>条件判断和脚本支持</li>
        <li>7×24小时后台运行</li>
        <li>开机自启动</li>
        <li>奶茶色系界面</li>
        </ul>
        <p>开发: 十三香 🦞✨</p>
        <p>© 2026 十三香工作室</p>
        """
        
        QMessageBox.about(self, "关于", about_text)


if __name__ == "__main__":
    # 直接运行测试
    app = QApplication(sys.argv)
    window = TaskSchedulerApp()
    window.show()
    sys.exit(app.exec())