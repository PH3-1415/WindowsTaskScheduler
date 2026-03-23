"""
任务列表组件 - 显示和管理任务列表
"""

import logging
from typing import List, Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QMenu, QMessageBox, QInputDialog, QLineEdit
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QIcon, QAction, QColor

from database.models import Task
from database.db_manager import DatabaseManager
from gui.styles.colors import COLORS


class TaskListWidget(QWidget):
    """任务列表组件"""
    
    # 信号定义
    task_added = Signal(dict)      # 任务添加信号
    task_edited = Signal(dict)    # 任务编辑信号
    task_deleted = Signal(int)     # 任务删除信号
    task_run_now = Signal(int)     # 立即运行任务信号
    task_paused = Signal(int)      # 任务暂停信号
    task_resumed = Signal(int)     # 任务恢复信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化组件
        self.db = DatabaseManager()
        self.tasks: List[Task] = []
        
        # 初始化UI
        self._init_ui()
        
        # 应用样式
        self._apply_styles()
        
        # 启动定时器
        self._start_timers()
    
    def _init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 标题
        title_label = QLabel("任务列表")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        
        # 按钮栏
        button_layout = QHBoxLayout()
        
        # 添加任务按钮
        self.add_button = QPushButton("添加任务")
        self.add_button.setIcon(QIcon("resources/icons/add.png"))
        self.add_button.clicked.connect(self._on_add_task)
        
        # 编辑按钮
        self.edit_button = QPushButton("编辑")
        self.edit_button.setIcon(QIcon("resources/icons/edit.png"))
        self.edit_button.clicked.connect(self._on_edit_task)
        self.edit_button.setEnabled(False)
        
        # 删除按钮
        self.delete_button = QPushButton("删除")
        self.delete_button.setIcon(QIcon("resources/icons/delete.png"))
        self.delete_button.clicked.connect(self._on_delete_task)
        self.delete_button.setEnabled(False)
        
        # 运行按钮
        self.run_button = QPushButton("立即运行")
        self.run_button.setIcon(QIcon("resources/icons/play.png"))
        self.run_button.clicked.connect(self._on_run_task_now)
        self.run_button.setEnabled(False)
        
        # 暂停/恢复按钮
        self.pause_button = QPushButton("暂停")
        self.pause_button.setIcon(QIcon("resources/icons/pause.png"))
        self.pause_button.clicked.connect(self._on_pause_task)
        self.pause_button.setEnabled(False)
        
        # 添加到按钮布局
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addStretch()
        
        # 任务列表
        self.task_list = QListWidget()
        self.task_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.task_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.task_list.customContextMenuRequested.connect(self._show_context_menu)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # 添加到主布局
        main_layout.addWidget(title_label)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.task_list)
        main_layout.addWidget(self.status_label)
    
    def _apply_styles(self):
        """应用样式"""
        try:
            self.setStyleSheet(f"""
                QWidget {{
                    background-color: {COLORS['background_primary']};
                    color: {COLORS['text_primary']};
                }}
                
                QLabel {{
                    color: {COLORS['text_primary']};
                    font-size: 9pt;
                }}
                
                QListWidget {{
                    background-color: {COLORS['background_card']};
                    border: 1px solid {COLORS['border_light']};
                    border-radius: 4px;
                    font-size: 9pt;
                }}
                
                QListWidget::item {{
                    border-bottom: 1px solid {COLORS['border_light']};
                    padding: 8px;
                }}
                
                QListWidget::item:selected {{
                    background-color: {COLORS['selection']};
                }}
                
                QListWidget::item:hover {{
                    background-color: {COLORS['background_hover']};
                }}
                
                QPushButton {{
                    background-color: {COLORS['button_normal']};
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border_medium']};
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-size: 9pt;
                    min-width: 80px;
                }}
                
                QPushButton:hover {{
                    background-color: {COLORS['button_hover']};
                }}
                
                QPushButton:pressed {{
                    background-color: {COLORS['button_pressed']};
                }}
                
                QPushButton:disabled {{
                    background-color: {COLORS['button_disabled']};
                    color: {COLORS['text_disabled']};
                }}
            """)
        except Exception as e:
            logging.warning(f"应用样式失败: {e}")
    
    def _start_timers(self):
        """启动定时器"""
        # 状态更新定时器
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(1000)  # 1秒更新一次
    
    def _update_status(self):
        """更新状态"""
        total_tasks = len(self.tasks)
        enabled_tasks = sum(1 for task in self.tasks if task.enabled)
        running_tasks = sum(1 for task in self.tasks if hasattr(task, 'is_running') and task.is_running)
        
        status_text = f"任务: {enabled_tasks}/{total_tasks}"
        if running_tasks > 0:
            status_text += f" (运行中: {running_tasks})"
        
        self.status_label.setText(status_text)
    
    def _on_selection_changed(self):
        """选中项改变"""
        selected_items = self.task_list.selectedItems()
        has_selection = len(selected_items) > 0
        
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        self.run_button.setEnabled(has_selection)
        self.pause_button.setEnabled(has_selection)
        
        if has_selection:
            item = selected_items[0]
            task_id = item.data(Qt.UserRole)
            task = self._get_task_by_id(task_id)
            
            if task:
                if task.enabled:
                    self.pause_button.setText("暂停")
                    self.pause_button.setIcon(QIcon("resources/icons/pause.png"))
                else:
                    self.pause_button.setText("恢复")
                    self.pause_button.setIcon(QIcon("resources/icons/play.png"))
    
    def _show_context_menu(self, position):
        """显示上下文菜单"""
        item = self.task_list.itemAt(position)
        if not item:
            return
        
        task_id = item.data(Qt.UserRole)
        task = self._get_task_by_id(task_id)
        if not task:
            return
        
        # 创建菜单
        menu = QMenu(self)
        
        # 运行任务
        run_action = QAction("立即运行", self)
        run_action.triggered.connect(lambda: self._on_run_task_now())
        menu.addAction(run_action)
        
        # 暂停/恢复
        if task.enabled:
            pause_action = QAction("暂停", self)
            pause_action.triggered.connect(lambda: self._on_pause_task())
        else:
            resume_action = QAction("恢复", self)
            resume_action.triggered.connect(lambda: self._on_resume_task())
        menu.addAction(pause_action if task.enabled else resume_action)
        
        menu.addSeparator()
        
        # 编辑
        edit_action = QAction("编辑", self)
        edit_action.triggered.connect(lambda: self._on_edit_task())
        menu.addAction(edit_action)
        
        # 删除
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self._on_delete_task())
        menu.addAction(delete_action)
        
        # 显示菜单
        menu.exec_(self.task_list.mapToGlobal(position))
    
    def _get_task_by_id(self, task_id: int) -> Optional[Task]:
        """根据ID获取任务"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    # ========== 按钮事件处理 ==========    
    def _on_add_task(self):
        """添加任务"""
        from gui.task_edit_dialog import TaskEditDialog
        
        dialog = TaskEditDialog(self)
        if dialog.exec():
            task_data = dialog.get_task_data()
            self.task_added.emit(task_data)
    
    def _on_edit_task(self):
        """编辑任务"""
        selected_items = self.task_list.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        task_id = item.data(Qt.UserRole)
        task = self._get_task_by_id(task_id)
        if not task:
            return
        
        from gui.task_edit_dialog import TaskEditDialog
        
        dialog = TaskEditDialog(self, task)
        if dialog.exec():
            task_data = dialog.get_task_data()
            self.task_edited.emit(task_data)
    
    def _on_delete_task(self):
        """删除任务"""
        selected_items = self.task_list.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        task_id = item.data(Qt.UserRole)
        task = self._get_task_by_id(task_id)
        if not task:
            return
        
        # 确认对话框
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除任务 '{task.name}' 吗？\n\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.task_deleted.emit(task_id)
    
    def _on_run_task_now(self):
        """立即运行任务"""
        selected_items = self.task_list.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        task_id = item.data(Qt.UserRole)
        
        self.task_run_now.emit(task_id)
    
    def _on_pause_task(self):
        """暂停任务"""
        selected_items = self.task_list.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        task_id = item.data(Qt.UserRole)
        
        self.task_paused.emit(task_id)
    
    def _on_resume_task(self):
        """恢复任务"""
        selected_items = self.task_list.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        task_id = item.data(Qt.UserRole)
        
        self.task_resumed.emit(task_id)
    
    # ========== 公共接口 ==========    
    def load_tasks(self, tasks: List[Task]):
        """加载任务列表"""
        self.tasks = tasks
        self.task_list.clear()
        
        for task in tasks:
            self._add_task_item(task)
    
    def add_task(self, task: Task):
        """添加单个任务"""
        self.tasks.append(task)
        self._add_task_item(task)
    
    def update_task(self, task: Task):
        """更新任务"""
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            if item.data(Qt.UserRole) == task.id:
                self._update_task_item(item, task)
                break
        
        # 更新内存中的任务列表
        for i, t in enumerate(self.tasks):
            if t.id == task.id:
                self.tasks[i] = task
                break
    
    def delete_task(self, task_id: int):
        """删除任务"""
        # 从列表中删除
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            if item.data(Qt.UserRole) == task_id:
                self.task_list.takeItem(i)
                break
        
        # 从内存中删除
        self.tasks = [t for t in self.tasks if t.id != task_id]
    
    def update_task_status(self, task_id: int, status: str):
        """更新任务状态"""
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            if item.data(Qt.UserRole) == task_id:
                task = self._get_task_by_id(task_id)
                if task:
                    # 更新任务状态（这里可以根据需要扩展）
                    self._update_task_item(item, task)
                    self._update_status_color(item, status)
                break
    
    def _add_task_item(self, task: Task):
        """添加任务项到列表"""
        item = QListWidgetItem()
        item.setData(Qt.UserRole, task.id)
        
        # 设置显示文本
        self._update_task_item(item, task)
        
        # 添加状态颜色
        self._update_status_color(item, 'waiting' if task.enabled else 'disabled')
        
        self.task_list.addItem(item)
    
    def _update_task_item(self, item: QListWidgetItem, task: Task):
        """更新任务项显示"""
        # 构建显示文本
        status_icon = self._get_status_icon(task)
        time_text = self._get_schedule_time_text(task)
        
        text = f"{status_icon} {task.name} [{time_text}]"
        if task.description:
            text += f"\n  {task.description}"
        
        item.setText(text)
        item.setData(Qt.UserRole, task.id)
    
    def _update_status_color(self, item: QListWidgetItem, status: str):
        """更新状态颜色"""
        color = COLORS.get(f'status_{status}', COLORS['status_waiting'])
        
        # 创建一个新的字体对象
        font = item.font()
        font.setPointSize(9)
        
        # 设置前景色（文本颜色）
        item.setForeground(QColor(color))
    
    def _get_status_icon(self, task: Task) -> str:
        """获取状态图标"""
        if not task.enabled:
            return "⏸"  # 暂停
            
        # 这里可以根据任务的实际运行状态返回不同的图标
        # 例如：运行中、等待、成功、失败等
        
        return "○"  # 默认等待状态
    
    def _get_schedule_time_text(self, task: Task) -> str:
        """获取调度时间文本"""
        config = task.schedule_config
        
        if task.schedule_type == 'daily':
            hour = config.get('hour', 0)
            minute = config.get('minute', 0)
            return f"{hour:02d}:{minute:02d}"
        
        elif task.schedule_type == 'weekly':
            days = config.get('days', [])
            hour = config.get('hour', 0)
            minute = config.get('minute', 0)
            
            day_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
            day_text = ' '.join(day_names[d] for d in days if 0 <= d < 7)
            
            return f"{day_text} {hour:02d}:{minute:02d}"
        
        elif task.schedule_type == 'monthly':
            day = config.get('day', 1)
            hour = config.get('hour', 0)
            minute = config.get('minute', 0)
            
            return f"每月{day}日 {hour:02d}:{minute:02d}"
        
        return "未知"