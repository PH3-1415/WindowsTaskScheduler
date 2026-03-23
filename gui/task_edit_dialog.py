"""
任务编辑对话框 - 添加和编辑任务
"""

import json
import logging
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QComboBox, QTimeEdit, QCheckBox,
    QGroupBox, QPushButton, QLabel, QTabWidget, QWidget,
    QSpinBox, QListWidget, QListWidgetItem, QMessageBox,
    QScrollArea, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QTime
from PySide6.QtGui import QFont, QIcon

from database.models import Task
from gui.styles.colors import COLORS


class TaskEditDialog(QDialog):
    """任务编辑对话框"""
    
    def __init__(self, parent=None, task: Optional[Task] = None):
        super().__init__(parent)
        
        # 保存任务引用
        self.task = task
        self.is_edit_mode = task is not None
        
        # 设置窗口属性
        self.setWindowTitle("编辑任务" if self.is_edit_mode else "添加任务")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        # 初始化UI
        self._init_ui()
        
        # 应用样式
        self._apply_styles()
        
        # 如果是编辑模式，加载任务数据
        if self.is_edit_mode:
            self._load_task_data()
    
    def _init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 基本设置标签页
        self.basic_tab = self._create_basic_tab()
        self.tab_widget.addTab(self.basic_tab, "基本设置")
        
        # 调度设置标签页
        self.schedule_tab = self._create_schedule_tab()
        self.tab_widget.addTab(self.schedule_tab, "调度设置")
        
        # 高级设置标签页
        self.advanced_tab = self._create_advanced_tab()
        self.tab_widget.addTab(self.advanced_tab, "高级设置")
        
        # 添加到主布局
        main_layout.addWidget(self.tab_widget)
        
        # 按钮栏
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 确定按钮
        self.ok_button = QPushButton("确定")
        self.ok_button.setIcon(QIcon("resources/icons/ok.png"))
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setDefault(True)
        
        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setIcon(QIcon("resources/icons/cancel.png"))
        self.cancel_button.clicked.connect(self.reject)
        
        # 添加到按钮布局
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        # 添加到主布局
        main_layout.addLayout(button_layout)
    
    def _create_basic_tab(self) -> QWidget:
        """创建基本设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 基本信息组
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout(basic_group)
        basic_layout.setSpacing(10)
        
        # 任务名称
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("请输入任务名称")
        basic_layout.addRow("任务名称:", self.name_edit)
        
        # 任务描述
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(60)
        self.desc_edit.setPlaceholderText("请输入任务描述（可选）")
        basic_layout.addRow("任务描述:", self.desc_edit)
        
        # 执行命令组
        command_group = QGroupBox("执行命令")
        command_layout = QFormLayout(command_group)
        command_layout.setSpacing(10)
        
        # 执行命令
        self.command_edit = QTextEdit()
        self.command_edit.setMaximumHeight(80)
        self.command_edit.setPlaceholderText("例如: python script.py\n或: conda activate env && python script.py")
        command_layout.addRow("命令:", self.command_edit)
        
        # 工作目录
        self.working_dir_edit = QLineEdit()
        self.working_dir_edit.setPlaceholderText("可选，留空使用默认目录")
        command_layout.addRow("工作目录:", self.working_dir_edit)
        
        # 添加到标签页布局
        layout.addWidget(basic_group)
        layout.addWidget(command_group)
        layout.addStretch()
        
        return tab
    
    def _create_schedule_tab(self) -> QWidget:
        """创建调度设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 调度类型组
        type_group = QGroupBox("调度类型")
        type_layout = QVBoxLayout(type_group)
        
        # 调度类型单选按钮
        self.daily_radio = self._create_radio_button("每天执行", True)
        self.weekly_radio = self._create_radio_button("每周执行")
        self.monthly_radio = self._create_radio_button("每月执行")
        
        type_layout.addWidget(self.daily_radio)
        type_layout.addWidget(self.weekly_radio)
        type_layout.addWidget(self.monthly_radio)
        
        # 时间设置组
        time_group = QGroupBox("执行时间")
        time_layout = QFormLayout(time_group)
        time_layout.setSpacing(10)
        
        # 时间选择
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime(8, 30))  # 默认8:30
        time_layout.addRow("执行时间:", self.time_edit)
        
        # 每周设置组（初始隐藏）
        self.weekly_group = QGroupBox("每周设置")
        self.weekly_layout = QGridLayout(self.weekly_group)
        self.weekly_group.setVisible(False)
        
        # 周几复选框
        self.day_checks = []
        days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        
        for i, day in enumerate(days):
            check = QCheckBox(day)
            self.day_checks.append(check)
            row = i // 4
            col = i % 4
            self.weekly_layout.addWidget(check, row, col)
        
        # 每月设置组（初始隐藏）
        self.monthly_group = QGroupBox("每月设置")
        monthly_layout = QFormLayout(self.monthly_group)
        self.monthly_group.setVisible(False)
        
        # 日期选择
        self.day_spin = QSpinBox()
        self.day_spin.setRange(1, 31)
        self.day_spin.setValue(1)
        monthly_layout.addRow("每月第几天:", self.day_spin)
        
        # 连接信号
        self.daily_radio.toggled.connect(lambda: self._on_schedule_type_changed('daily'))
        self.weekly_radio.toggled.connect(lambda: self._on_schedule_type_changed('weekly'))
        self.monthly_radio.toggled.connect(lambda: self._on_schedule_type_changed('monthly'))
        
        # 添加到标签页布局
        layout.addWidget(type_group)
        layout.addWidget(time_group)
        layout.addWidget(self.weekly_group)
        layout.addWidget(self.monthly_group)
        layout.addStretch()
        
        return tab
    
    def _create_advanced_tab(self) -> QWidget:
        """创建高级设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 条件设置组
        condition_group = QGroupBox("执行条件")
        condition_layout = QVBoxLayout(condition_group)
        
        # 条件说明
        condition_label = QLabel("设置任务执行条件（可选）")
        condition_label.setWordWrap(True)
        condition_layout.addWidget(condition_label)
        
        # 条件编辑框
        self.condition_edit = QTextEdit()
        self.condition_edit.setMaximumHeight(80)
        self.condition_edit.setPlaceholderText("例如: if config.date == '06-01'\n或: if script.output == 'success'")
        condition_layout.addWidget(self.condition_edit)
        
        # 条件示例
        example_label = QLabel("示例:\n• if config.key == 'value'\n• if script.name == 'output'\n• if today == 'Monday'")
        example_label.setWordWrap(True)
        example_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 8pt;")
        condition_layout.addWidget(example_label)
        
        # 启用/禁用组
        enable_group = QGroupBox("任务状态")
        enable_layout = QVBoxLayout(enable_group)
        
        # 启用复选框
        self.enable_check = QCheckBox("启用任务")
        self.enable_check.setChecked(True)
        enable_layout.addWidget(self.enable_check)
        
        # 优先级设置
        priority_layout = QHBoxLayout()
        priority_layout.addWidget(QLabel("优先级:"))
        
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(0, 100)
        self.priority_spin.setValue(0)
        self.priority_spin.setToolTip("数字越大优先级越高，用于任务排序")
        priority_layout.addWidget(self.priority_spin)
        priority_layout.addStretch()
        
        enable_layout.addLayout(priority_layout)
        
        # 添加到标签页布局
        layout.addWidget(condition_group)
        layout.addWidget(enable_group)
        layout.addStretch()
        
        return tab
    
    def _create_radio_button(self, text: str, checked: bool = False) -> QPushButton:
        """创建单选按钮（使用QPushButton模拟）"""
        button = QPushButton(text)
        button.setCheckable(True)
        button.setChecked(checked)
        button.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding: 8px;
                border: 1px solid {COLORS['border_light']};
                border-radius: 4px;
            }}
            QPushButton:checked {{
                background-color: {COLORS['button_hover']};
                border: 2px solid {COLORS['border_dark']};
            }}
        """)
        return button
    
    def _apply_styles(self):
        """应用样式"""
        try:
            self.setStyleSheet(f"""
                QDialog {{
                    background-color: {COLORS['background_primary']};
                    color: {COLORS['text_primary']};
                }}
                
                QGroupBox {{
                    font-weight: bold;
                    border: 1px solid {COLORS['border_medium']};
                    border-radius: 6px;
                    margin-top: 10px;
                    padding-top: 10px;
                }}
                
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }}
                
                QLabel {{
                    color: {COLORS['text_primary']};
                    font-size: 9pt;
                }}
                
                QLineEdit, QTextEdit, QComboBox, QTimeEdit, QSpinBox {{
                    background-color: {COLORS['background_card']};
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border_light']};
                    border-radius: 4px;
                    padding: 6px;
                    font-size: 9pt;
                }}
                
                QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QTimeEdit:focus {{
                    border: 2px solid {COLORS['border_dark']};
                }}
                
                QPushButton {{
                    background-color: {COLORS['button_normal']};
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border_medium']};
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-size: 9pt;
                    min-width: 80px;
                }}
                
                QPushButton:hover {{
                    background-color: {COLORS['button_hover']};
                }}
                
                QPushButton:pressed {{
                    background-color: {COLORS['button_pressed']};
                }}
                
                QCheckBox {{
                    color: {COLORS['text_primary']};
                    font-size: 9pt;
                }}
                
                QTabWidget::pane {{
                    border: 1px solid {COLORS['border_light']};
                    border-radius: 4px;
                }}
                
                QTabBar::tab {{
                    background-color: {COLORS['background_secondary']};
                    color: {COLORS['text_primary']};
                    padding: 8px 16px;
                    margin-right: 2px;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                }}
                
                QTabBar::tab:selected {{
                    background-color: {COLORS['background_primary']};
                    border-bottom: 2px solid {COLORS['button_normal']};
                }}
                
                QTabBar::tab:hover {{
                    background-color: {COLORS['button_hover']};
                }}
            """)
        except Exception as e:
            logging.warning(f"应用样式失败: {e}")
    
    def _on_schedule_type_changed(self, schedule_type: str):
        """调度类型改变"""
        # 显示/隐藏相关设置组
        self.weekly_group.setVisible(schedule_type == 'weekly')
        self.monthly_group.setVisible(schedule_type == 'monthly')
    
    def _load_task_data(self):
        """加载任务数据"""
        if not self.task:
            return
        
        try:
            # 基本信息
            self.name_edit.setText(self.task.name)
            self.desc_edit.setPlainText(self.task.description)
            self.command_edit.setPlainText(self.task.command)
            self.working_dir_edit.setText(self.task.working_dir or "")
            
            # 调度设置
            config = self.task.schedule_config
            
            if self.task.schedule_type == 'daily':
                self.daily_radio.setChecked(True)
            elif self.task.schedule_type == 'weekly':
                self.weekly_radio.setChecked(True)
                # 设置周几选择
                days = config.get('days', [])
                for i, check in enumerate(self.day_checks):
                    check.setChecked(i in days)
            elif self.task.schedule_type == 'monthly':
                self.monthly_radio.setChecked(True)
                self.day_spin.setValue(config.get('day', 1))
            
            # 设置时间
            hour = config.get('hour', 8)
            minute = config.get('minute', 30)
            self.time_edit.setTime(QTime(hour, minute))
            
            # 高级设置
            self.condition_edit.setPlainText(self.task.condition or "")
            self.enable_check.setChecked(self.task.enabled)
            self.priority_spin.setValue(self.task.priority)
            
            # 触发调度类型改变事件
            self._on_schedule_type_changed(self.task.schedule_type)
            
        except Exception as e:
            logging.error(f"加载任务数据失败: {e}")
            QMessageBox.warning(self, "加载失败", f"加载任务数据失败:\n\n{str(e)}")
    
    def get_task_data(self) -> dict:
        """获取任务数据"""
        # 基本信息
        task_data = {
            'name': self.name_edit.text().strip(),
            'description': self.desc_edit.toPlainText().strip(),
            'command': self.command_edit.toPlainText().strip(),
            'working_dir': self.working_dir_edit.text().strip(),
            'condition': self.condition_edit.toPlainText().strip(),
            'enabled': self.enable_check.isChecked(),
            'priority': self.priority_spin.value()
        }
        
        # 调度设置
        if self.daily_radio.isChecked():
            task_data['schedule_type'] = 'daily'
            schedule_config = {
                'hour': self.time_edit.time().hour(),
                'minute': self.time_edit.time().minute()
            }
        
        elif self.weekly_radio.isChecked():
            task_data['schedule_type'] = 'weekly'
            # 获取选中的周几
            days = []
            for i, check in enumerate(self.day_checks):
                if check.isChecked():
                    days.append(i)
            
            schedule_config = {
                'days': days,
                'hour': self.time_edit.time().hour(),
                'minute': self.time_edit.time().minute()
            }
        
        elif self.monthly_radio.isChecked():
            task_data['schedule_type'] = 'monthly'
            schedule_config = {
                'day': self.day_spin.value(),
                'hour': self.time_edit.time().hour(),
                'minute': self.time_edit.time().minute()
            }
        
        else:
            # 默认每天
            task_data['schedule_type'] = 'daily'
            schedule_config = {
                'hour': 8,
                'minute': 30
            }
        
        task_data['schedule_config'] = schedule_config
        
        # 如果是编辑模式，添加ID
        if self.is_edit_mode and self.task:
            task_data['id'] = self.task.id
        
        return task_data
    
    def validate_input(self) -> tuple[bool, str]:
        """验证输入"""
        # 检查任务名称
        name = self.name_edit.text().strip()
        if not name:
            return False, "任务名称不能为空"
        
        # 检查命令
        command = self.command_edit.toPlainText().strip()
        if not command:
            return False, "执行命令不能为空"
        
        # 检查调度设置
        if not (self.daily_radio.isChecked() or 
                self.weekly_radio.isChecked() or 
                self.monthly_radio.isChecked()):
            return False, "请选择调度类型"
        
        # 检查每周设置
        if self.weekly_radio.isChecked():
            days_selected = any(check.isChecked() for check in self.day_checks)
            if not days_selected:
                return False, "请至少选择一天"
        
        return True, ""
    
    def accept(self):
        """接受对话框"""
        # 验证输入
        is_valid, error_msg = self.validate_input()
        if not is_valid:
            QMessageBox.warning(self, "输入错误", error_msg)
            return
        
        # 调用父类的accept
        super().accept()
    
    def reject(self):
        """拒绝对话框"""
        # 确认取消
        reply = QMessageBox.question(
            self,
            "确认取消",
            "确定要取消编辑吗？\n\n所有更改将丢失。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            super().reject()
    
    # ========== 工具方法 ==========
    
    def get_schedule_summary(self) -> str:
        """获取调度设置摘要"""
        if self.daily_radio.isChecked():
            time_str = self.time_edit.time().toString("HH:mm")
            return f"每天 {time_str} 执行"
        
        elif self.weekly_radio.isChecked():
            time_str = self.time_edit.time().toString("HH:mm")
            days = []
            day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            for i, check in enumerate(self.day_checks):
                if check.isChecked():
                    days.append(day_names[i])
            
            if days:
                return f"每周 {', '.join(days)} {time_str} 执行"
            else:
                return "每周执行（未选择日期）"
        
        elif self.monthly_radio.isChecked():
            time_str = self.time_edit.time().toString("HH:mm")
            day = self.day_spin.value()
            return f"每月 {day} 日 {time_str} 执行"
        
        return "未设置调度"
    
    def is_condition_enabled(self) -> bool:
        """是否启用了条件"""
        condition = self.condition_edit.toPlainText().strip()
        return bool(condition)
    
    def get_condition_text(self) -> str:
        """获取条件文本"""
        return self.condition_edit.toPlainText().strip()
    
    def set_condition_text(self, text: str):
        """设置条件文本"""
        self.condition_edit.setPlainText(text)
    
    def get_command_preview(self) -> str:
        """获取命令预览"""
        command = self.command_edit.toPlainText().strip()
        
        # 如果是conda命令，添加说明
        if 'conda activate' in command:
            return "Conda环境命令（将自动处理环境激活）"
        
        # 截断长命令
        if len(command) > 100:
            return command[:100] + "..."
        
        return command
    
    def show_command_help(self):
        """显示命令帮助"""
        help_text = """
        <h3>命令格式说明</h3>
        
        <p><b>基本命令:</b></p>
        <ul>
        <li>python script.py - 执行Python脚本</li>
        <li>echo "Hello" - 执行系统命令</li>
        <li>cmd /c "命令" - 执行Windows命令</li>
        </ul>
        
        <p><b>Conda环境:</b></p>
        <ul>
        <li>conda activate myenv && python script.py</li>
        <li>系统会自动处理conda环境激活</li>
        </ul>
        
        <p><b>工作目录:</b></p>
        <ul>
        <li>可以指定工作目录，留空使用默认目录</li>
        <li>支持绝对路径和相对路径</li>
        </ul>
        
        <p><b>注意事项:</b></p>
        <ul>
        <li>命令执行时间过长可能导致程序无响应</li>
        <li>建议为长时间运行的任务设置超时</li>
        <li>输出编码问题会自动处理</li>
        </ul>
        """
        
        QMessageBox.information(self, "命令帮助", help_text)
    
    def show_condition_help(self):
        """显示条件帮助"""
        help_text = """
        <h3>条件表达式说明</h3>
        
        <p><b>基本语法:</b></p>
        <ul>
        <li>if 变量 == 值</li>
        <li>if 变量 != 值</li>
        <li>if 变量 in 列表</li>
        <li>if 变量 contains 文本</li>
        </ul>
        
        <p><b>可用变量:</b></p>
        <ul>
        <li>config.xxx - 配置文件中的值</li>
        <li>script.xxx - 默认脚本的输出</li>
        <li>now - 当前时间</li>
        <li>today - 当前日期</li>
        <li>time - 当前时间</li>
        </ul>
        
        <p><b>示例:</b></p>
        <ul>
        <li>if config.date == "06-01"</li>
        <li>if script.output == "success"</li>
        <li>if today == "Monday"</li>
        <li>if config.enabled == true</li>
        </ul>
        
        <p><b>注意事项:</b></p>
        <ul>
        <li>条件不满足时任务会跳过执行</li>
        <li>条件表达式支持简单的逻辑运算</li>
        <li>变量名区分大小写</li>
        </ul>
        """
        
        QMessageBox.information(self, "条件帮助", help_text)