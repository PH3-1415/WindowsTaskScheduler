"""
主窗口 - 应用的主要界面
"""

import logging
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QStatusBar, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QCloseEvent, QIcon

from gui.task_list_widget import TaskListWidget
from gui.output_widget import OutputWidget
from config import ConfigManager
from database.db_manager import DatabaseManager
from core.scheduler import TaskScheduler


class MainWindow(QMainWindow):
    """主窗口"""
    
    # 信号定义
    task_added = Signal(dict)      # 任务添加信号
    task_updated = Signal(dict)    # 任务更新信号
    task_deleted = Signal(int)     # 任务删除信号
    task_run_now = Signal(int)     # 立即运行任务信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化组件
        self.config = ConfigManager()
        self.db = DatabaseManager()
        self.scheduler: Optional[TaskScheduler] = None
        
        # 初始化状态
        self._initialized = False
        
        # 设置窗口属性
        self.setWindowTitle("Windows定时任务管理器")
        self.setMinimumSize(800, 500)
        
        # 设置图标
        self._setup_icon()
        
        # 初始化UI
        self._init_ui()
        
        # 初始化数据
        self._init_data()
        
        # 启动定时器
        self._start_timers()
        
        # 标记初始化完成
        self._initialized = True
        
        # 连接信号
        self._connect_signals()
    
    def _setup_icon(self):
        """设置图标"""
        try:
            from utils.icon_helper import get_app_icon
            icon = get_app_icon()
            self.setWindowIcon(icon)
        except Exception:
            pass
    
    def _init_ui(self):
        """初始化UI"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 创建任务列表部件
        self.task_list_widget = TaskListWidget(self)
        
        # 创建输出部件
        self.output_widget = OutputWidget(self)
        
        # 添加部件到分割器
        splitter.addWidget(self.task_list_widget)
        splitter.addWidget(self.output_widget)
        
        # 设置分割器比例
        splitter.setSizes([400, 400])
        
        # 添加到主布局
        main_layout.addWidget(splitter)
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 设置初始状态
        self.status_bar.showMessage("就绪")
        
        # 应用样式
        self._apply_styles()
    
    def _init_data(self):
        """初始化数据"""
        try:
            # 初始化数据库
            self.db.initialize()
            
            # 创建任务调度器
            self.scheduler = TaskScheduler()
            
            # 设置回调函数
            self.scheduler.on_task_started = self._on_task_started
            self.scheduler.on_task_completed = self._on_task_completed
            self.scheduler.on_task_failed = self._on_task_failed
            self.scheduler.on_output = self._on_task_output
            
            # 启动调度器
            self.scheduler.start()
            
            # 加载任务到UI
            self._load_tasks_to_ui()
            
            logging.info("主窗口数据初始化完成")
            
        except Exception as e:
            logging.error(f"主窗口数据初始化失败: {e}")
            QMessageBox.critical(
                self,
                "初始化失败",
                f"数据初始化失败:\n\n{str(e)}"
            )
    
    def _load_tasks_to_ui(self):
        """加载任务到UI"""
        if not self.scheduler:
            return
        
        try:
            tasks = self.db.get_all_tasks()
            self.task_list_widget.load_tasks(tasks)
        except Exception as e:
            logging.error(f"加载任务到UI失败: {e}")
    
    def _start_timers(self):
        """启动定时器"""
        # 状态更新定时器
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(1000)  # 1秒更新一次
    
    def _apply_styles(self):
        """应用样式"""
        try:
            from gui.styles.colors import COLORS
            
            # 设置窗口样式
            self.setStyleSheet(f"""
                QMainWindow {{
                    background-color: {COLORS['background_primary']};
                }}
                
                QSplitter::handle {{
                    background-color: {COLORS['border_light']};
                    width: 1px;
                }}
                
                QSplitter::handle:hover {{
                    background-color: {COLORS['border_medium']};
                }}
                
                QStatusBar {{
                    background-color: {COLORS['background_secondary']};
                    color: {COLORS['text_primary']};
                    border-top: 1px solid {COLORS['border_light']};
                    font-size: 9pt;
                }}
                
                QStatusBar::item {{
                    border: none;
                }}
            """)
        except Exception as e:
            logging.warning(f"应用样式失败: {e}")
    
    def _connect_signals(self):
        """连接信号"""
        # 任务列表信号
        self.task_list_widget.task_added.connect(self._on_task_added)
        self.task_list_widget.task_edited.connect(self._on_task_edited)
        self.task_list_widget.task_deleted.connect(self._on_task_deleted)
        self.task_list_widget.task_run_now.connect(self._on_task_run_now)
        self.task_list_widget.task_paused.connect(self._on_task_paused)
        self.task_list_widget.task_resumed.connect(self._on_task_resumed)
        
        # 输出部件信号
        self.output_widget.cleared.connect(self._on_output_cleared)
    
    def _update_status(self):
        """更新状态栏"""
        if not self._initialized:
            return
        
        try:
            status_parts = []
            
            # 获取任务状态
            if self.scheduler:
                running_tasks = self.scheduler.get_running_tasks()
                queued_tasks = self.scheduler.get_queued_tasks()
                
                if running_tasks:
                    status_parts.append(f"运行中: {len(running_tasks)}")
                
                if queued_tasks:
                    status_parts.append(f"队列中: {len(queued_tasks)}")
            
            # 添加就绪状态
            if not status_parts:
                status_parts.append("就绪")
            
            # 更新状态栏
            status_text = " | ".join(status_parts)
            self.status_bar.showMessage(status_text)
            
        except Exception as e:
            logging.error(f"更新状态失败: {e}")
    
    # ========== 任务回调处理 ==========
    
    def _on_task_started(self, task_id: int, task_name: str):
        """任务开始回调"""
        logging.info(f"任务开始: {task_name} (ID: {task_id})")
        
        # 更新UI
        self.task_list_widget.update_task_status(task_id, 'running')
        
        # 清空输出区域
        self.output_widget.clear()
        
        # 显示任务开始信息
        self.output_widget.append_output(f"开始执行任务: {task_name}\n")
    
    def _on_task_completed(self, task_id: int, task_name: str, status: str, output: str):
        """任务完成回调"""
        logging.info(f"任务完成: {task_name}, 状态: {status}")
        
        # 更新UI
        self.task_list_widget.update_task_status(task_id, status)
        
        # 显示任务完成信息
        if status == 'success':
            self.output_widget.append_output(f"\n✅ 任务执行成功: {task_name}\n")
        else:
            self.output_widget.append_output(f"\n❌ 任务执行失败: {task_name}\n")
        
        # 显示输出摘要
        if output:
            lines = output.strip().split('\n')
            if lines:
                last_line = lines[-1]
                if len(last_line) > 100:
                    last_line = last_line[:100] + "..."
                self.output_widget.append_output(f"最后输出: {last_line}\n")
    
    def _on_task_failed(self, task_id: int, error: str):
        """任务失败回调"""
        logging.error(f"任务失败: {task_id}, 错误: {error}")
        
        # 更新UI
        self.task_list_widget.update_task_status(task_id, 'failed')
        
        # 显示错误信息
        self.output_widget.append_output(f"\n❌ 任务执行失败: {error}\n")
    
    def _on_task_output(self, output: str):
        """任务输出回调"""
        self.output_widget.append_output(output)
    
    # ========== UI事件处理 ==========    
    def _on_task_added(self, task_data: dict):
        """处理任务添加"""
        try:
            from database.models import Task
            
            # 创建任务对象
            task = Task.from_dict(task_data)
            
            # 添加到数据库
            task_id = self.db.add_task(task)
            
            # 添加到调度器
            if self.scheduler:
                self.scheduler.add_task(task)
            
            # 刷新UI
            self._load_tasks_to_ui()
            
            logging.info(f"任务添加成功: {task.name}")
            
        except Exception as e:
            logging.error(f"添加任务失败: {e}")
            QMessageBox.critical(self, "错误", f"添加任务失败:\\n\\n{str(e)}")
    
    def _on_task_edited(self, task_data: dict):
        """处理任务编辑"""
        try:
            from database.models import Task
            
            # 创建任务对象
            task = Task.from_dict(task_data)
            
            # 更新数据库
            self.db.update_task(task)
            
            # 更新调度器
            if self.scheduler:
                self.scheduler.update_task(task)
            
            # 刷新UI
            self._load_tasks_to_ui()
            
            logging.info(f"任务更新成功: {task.name}")
            
        except Exception as e:
            logging.error(f"更新任务失败: {e}")
            QMessageBox.critical(self, "错误", f"更新任务失败:\\n\\n{str(e)}")
    
    def _on_task_deleted(self, task_id: int):
        """处理任务删除"""
        try:
            # 从数据库删除
            self.db.delete_task(task_id)
            
            # 从调度器删除
            if self.scheduler:
                self.scheduler.remove_task(task_id)
            
            # 刷新UI
            self._load_tasks_to_ui()
            
            logging.info(f"任务删除成功: ID={task_id}")
            
        except Exception as e:
            logging.error(f"删除任务失败: {e}")
            QMessageBox.critical(self, "错误", f"删除任务失败:\\n\\n{str(e)}")
    
    def _on_task_run_now(self, task_id: int):
        """处理立即运行任务"""
        try:
            if self.scheduler:
                self.scheduler.run_task_now(task_id)
                logging.info(f"任务立即执行: ID={task_id}")
        except Exception as e:
            logging.error(f"立即执行任务失败: {e}")
            QMessageBox.critical(self, "错误", f"立即执行任务失败:\\n\\n{str(e)}")
    
    def _on_task_paused(self, task_id: int):
        """处理任务暂停"""
        try:
            if self.scheduler:
                self.scheduler.pause_task(task_id)
                self.task_list_widget.update_task_status(task_id, 'paused')
                logging.info(f"任务暂停: ID={task_id}")
        except Exception as e:
            logging.error(f"暂停任务失败: {e}")
    
    def _on_task_resumed(self, task_id: int):
        """处理任务恢复"""
        try:
            if self.scheduler:
                self.scheduler.resume_task(task_id)
                self.task_list_widget.update_task_status(task_id, 'enabled')
                logging.info(f"任务恢复: ID={task_id}")
        except Exception as e:
            logging.error(f"恢复任务失败: {e}")
    
    def _on_output_cleared(self):
        """处理输出清除"""
        logging.info("输出已清除")
    
    def closeEvent(self, event):
        """关闭事件"""
        # 停止调度器
        if self.scheduler:
            self.scheduler.stop()
        
        # 关闭数据库
        if self.db:
            self.db.close()
        
        event.accept()