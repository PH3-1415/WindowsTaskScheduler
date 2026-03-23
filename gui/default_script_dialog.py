"""
默认脚本管理对话框 - 编辑和管理默认脚本
"""

import json
import logging
import os
from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QTextEdit, QLineEdit, QComboBox, QSpinBox,
    QCheckBox, QPushButton, QLabel, QGroupBox,
    QMessageBox, QFileDialog, QTabWidget, QWidget,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QIcon, QTextCursor, QColor

from database.models import DefaultScript
from database.db_manager import DatabaseManager
from core.default_script import DefaultScriptManager
from gui.styles.colors import COLORS


class DefaultScriptDialog(QDialog):
    """默认脚本管理对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化组件
        self.db = DatabaseManager()
        self.script_manager = DefaultScriptManager()
        self.current_script: Optional[DefaultScript] = None
        
        # 设置窗口属性
        self.setWindowTitle("默认脚本管理")
        self.setMinimumSize(800, 600)
        self.setModal(True)
        
        # 初始化UI
        self._init_ui()
        
        # 应用样式
        self._apply_styles()
        
        # 加载脚本列表
        self._load_script_list()
        
        # 启动定时器
        self._start_timers()
    
    def _init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 脚本列表标签页
        self.list_tab = self._create_list_tab()
        self.tab_widget.addTab(self.list_tab, "脚本列表")
        
        # 脚本编辑标签页
        self.edit_tab = self._create_edit_tab()
        self.tab_widget.addTab(self.edit_tab, "脚本编辑")
        
        # 执行结果标签页
        self.result_tab = self._create_result_tab()
        self.tab_widget.addTab(self.result_tab, "执行结果")
        
        # 添加到主布局
        main_layout.addWidget(self.tab_widget)
        
        # 按钮栏
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 运行按钮
        self.run_button = QPushButton("运行脚本")
        self.run_button.setIcon(QIcon("resources/icons/play.png"))
        self.run_button.clicked.connect(self._run_script)
        self.run_button.setEnabled(False)
        
        # 保存按钮
        self.save_button = QPushButton("保存")
        self.save_button.setIcon(QIcon("resources/icons/save.png"))
        self.save_button.clicked.connect(self._save_script)
        self.save_button.setEnabled(False)
        
        # 新建按钮
        self.new_button = QPushButton("新建")
        self.new_button.setIcon(QIcon("resources/icons/add.png"))
        self.new_button.clicked.connect(self._new_script)
        
        # 删除按钮
        self.delete_button = QPushButton("删除")
        self.delete_button.setIcon(QIcon("resources/icons/delete.png"))
        self.delete_button.clicked.connect(self._delete_script)
        self.delete_button.setEnabled(False)
        
        # 关闭按钮
        self.close_button = QPushButton("关闭")
        self.close_button.setIcon(QIcon("resources/icons/close.png"))
        self.close_button.clicked.connect(self.reject)
        
        # 添加到按钮布局
        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.new_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.close_button)
        
        # 添加到主布局
        main_layout.addLayout(button_layout)
    
    def _create_list_tab(self) -> QWidget:
        """创建脚本列表标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 脚本列表表格
        self.script_table = QTableWidget()
        self.script_table.setColumnCount(6)
        self.script_table.setHorizontalHeaderLabels([
            "ID", "名称", "描述", "最后执行", "状态", "启用"
        ])
        
        # 设置表格属性
        self.script_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.script_table.setSelectionMode(QTableWidget.SingleSelection)
        self.script_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.script_table.horizontalHeader().setStretchLastSection(True)
        self.script_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.script_table.verticalHeader().setVisible(False)
        
        # 连接选择信号
        self.script_table.itemSelectionChanged.connect(self._on_script_selected)
        
        # 添加到布局
        layout.addWidget(QLabel("默认脚本列表（每天00:00自动执行）"))
        layout.addWidget(self.script_table)
        
        # 状态信息
        self.list_status_label = QLabel("就绪")
        self.list_status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.list_status_label)
        
        return tab
    
    def _create_edit_tab(self) -> QWidget:
        """创建脚本编辑标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 基本信息组
        info_group = QGroupBox("脚本信息")
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(10)
        
        # 脚本名称
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("输入脚本名称")
        info_layout.addRow("脚本名称:", self.name_edit)
        
        # 脚本描述
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("输入脚本描述")
        info_layout.addRow("脚本描述:", self.desc_edit)
        
        # 启用状态
        self.enabled_check = QCheckBox("启用脚本")
        self.enabled_check.setChecked(True)
        info_layout.addRow(self.enabled_check)
        
        # 脚本内容组
        content_group = QGroupBox("脚本内容")
        content_layout = QVBoxLayout(content_group)
        
        # 脚本编辑器
        self.script_edit = QTextEdit()
        self.script_edit.setPlaceholderText("输入Python脚本代码...")
        self.script_edit.setFont(QFont("Consolas", 10))
        content_layout.addWidget(self.script_edit)
        
        # 脚本示例
        example_button = QPushButton("查看示例")
        example_button.clicked.connect(self._show_example)
        content_layout.addWidget(example_button)
        
        # 添加到布局
        layout.addWidget(info_group)
        layout.addWidget(content_group)
        layout.addStretch()
        
        return tab
    
    def _create_result_tab(self) -> QWidget:
        """创建执行结果标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 执行结果组
        result_group = QGroupBox("执行结果")
        result_layout = QVBoxLayout(result_group)
        
        # 结果输出
        self.result_output = QTextEdit()
        self.result_output.setReadOnly(True)
        self.result_output.setFont(QFont("Consolas", 9))
        self.result_output.setPlaceholderText("脚本执行结果将显示在这里...")
        result_layout.addWidget(self.result_output)
        
        # 结果信息
        self.result_info_label = QLabel("未执行")
        self.result_info_label.setAlignment(Qt.AlignCenter)
        result_layout.addWidget(self.result_info_label)
        
        # 配置输出组
        config_group = QGroupBox("配置输出")
        config_layout = QVBoxLayout(config_group)
        
        # 配置输出预览
        self.config_preview = QTextEdit()
        self.config_preview.setReadOnly(True)
        self.config_preview.setFont(QFont("Consolas", 9))
        self.config_preview.setMaximumHeight(150)
        self.config_preview.setPlaceholderText("配置输出预览...")
        config_layout.addWidget(self.config_preview)
        
        # 配置路径
        config_path_layout = QHBoxLayout()
        config_path_layout.addWidget(QLabel("配置文件路径:"))
        
        self.config_path_label = QLabel("未设置")
        self.config_path_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        config_path_layout.addWidget(self.config_path_label)
        config_path_layout.addStretch()
        
        config_layout.addLayout(config_path_layout)
        
        # 添加到布局
        layout.addWidget(result_group)
        layout.addWidget(config_group)
        layout.addStretch()
        
        return tab
    
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
                
                QLineEdit, QTextEdit, QComboBox, QSpinBox {{
                    background-color: {COLORS['background_card']};
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border_light']};
                    border-radius: 4px;
                    padding: 6px;
                    font-size: 9pt;
                }}
                
                QLineEdit:focus, QTextEdit:focus {{
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
                
                QTableWidget {{
                    background-color: {COLORS['background_card']};
                    border: 1px solid {COLORS['border_light']};
                    border-radius: 4px;
                    font-size: 9pt;
                }}
                
                QTableWidget::item {{
                    padding: 4px;
                }}
                
                QTableWidget::item:selected {{
                    background-color: {COLORS['selection']};
                }}
                
                QHeaderView::section {{
                    background-color: {COLORS['background_secondary']};
                    padding: 4px;
                    border: none;
                    font-weight: bold;
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
    
    def _start_timers(self):
        """启动定时器"""
        # 状态更新定时器
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(1000)
    
    def _update_status(self):
        """更新状态"""
        # 更新脚本列表状态
        scripts = self.db.get_default_scripts()
        enabled_count = sum(1 for s in scripts if s.enabled)
        self.list_status_label.setText(f"共 {len(scripts)} 个脚本，{enabled_count} 个启用")
    
    def _load_script_list(self):
        """加载脚本列表"""
        try:
            scripts = self.db.get_default_scripts()
            
            # 清空表格
            self.script_table.setRowCount(0)
            
            for script in scripts:
                row = self.script_table.rowCount()
                self.script_table.insertRow(row)
                
                # ID
                id_item = QTableWidgetItem(str(script.id))
                id_item.setData(Qt.UserRole, script.id)
                self.script_table.setItem(row, 0, id_item)
                
                # 名称
                name_item = QTableWidgetItem(script.name)
                self.script_table.setItem(row, 1, name_item)
                
                # 描述
                desc_item = QTableWidgetItem(script.description or "")
                self.script_table.setItem(row, 2, desc_item)
                
                # 最后执行时间
                last_exec = script.last_executed_at
                if last_exec:
                    last_exec_text = last_exec.strftime('%Y-%m-%d %H:%M')
                else:
                    last_exec_text = "从未执行"
                last_exec_item = QTableWidgetItem(last_exec_text)
                self.script_table.setItem(row, 3, last_exec_item)
                
                # 状态
                status_item = QTableWidgetItem("正常" if script.last_status == 'success' else "失败")
                if script.last_status == 'success':
                    status_item.setForeground(QColor(COLORS['status_success']))
                elif script.last_status == 'failed':
                    status_item.setForeground(QColor(COLORS['status_error']))
                self.script_table.setItem(row, 4, status_item)
                
                # 启用状态
                enabled_item = QTableWidgetItem("是" if script.enabled else "否")
                self.script_table.setItem(row, 5, enabled_item)
            
            # 调整列宽
            self.script_table.resizeColumnsToContents()
            
        except Exception as e:
            logging.error(f"加载脚本列表失败: {e}")
            QMessageBox.warning(self, "加载失败", f"加载脚本列表失败:\n\n{str(e)}")
    
    def _on_script_selected(self):
        """脚本选中事件"""
        selected_items = self.script_table.selectedItems()
        if not selected_items:
            self.current_script = None
            self._clear_edit_form()
            self._update_button_states()
            return
        
        # 获取选中的脚本ID
        first_item = selected_items[0]
        script_id = first_item.data(Qt.UserRole)
        
        try:
            # 加载脚本详情
            script = self.db.get_default_script(script_id)
            if script:
                self.current_script = script
                self._load_script_to_form(script)
                self._load_script_results(script)
                self._update_button_states()
                
                # 切换到编辑标签页
                self.tab_widget.setCurrentIndex(1)
        
        except Exception as e:
            logging.error(f"加载脚本详情失败: {e}")
            QMessageBox.warning(self, "加载失败", f"加载脚本详情失败:\n\n{str(e)}")
    
    def _clear_edit_form(self):
        """清空编辑表单"""
        self.name_edit.clear()
        self.desc_edit.clear()
        self.script_edit.clear()
        self.enabled_check.setChecked(True)
        
        self.result_output.clear()
        self.result_info_label.setText("未执行")
        self.config_preview.clear()
        self.config_path_label.setText("未设置")
    
    def _load_script_to_form(self, script: DefaultScript):
        """加载脚本到表单"""
        self.name_edit.setText(script.name)
        self.desc_edit.setText(script.description or "")
        self.script_edit.setPlainText(script.content or "")
        self.enabled_check.setChecked(script.enabled)
    
    def _load_script_results(self, script: DefaultScript):
        """加载脚本执行结果"""
        try:
            # 加载执行结果
            if script.last_output:
                self.result_output.setPlainText(script.last_output)
            
            # 更新结果信息
            if script.last_executed_at:
                status_text = "成功" if script.last_status == 'success' else "失败"
                time_text = script.last_executed_at.strftime('%Y-%m-%d %H:%M:%S')
                self.result_info_label.setText(f"最后执行: {time_text} ({status_text})")
            else:
                self.result_info_label.setText("从未执行")
            
            # 加载配置输出预览
            config_output = self.script_manager.get_config_output()
            if config_output:
                config_str = json.dumps(config_output, ensure_ascii=False, indent=2)
                self.config_preview.setPlainText(config_str)
            
            # 显示配置文件路径
            config_path = self.script_manager.get_config_file_path()
            if config_path and os.path.exists(config_path):
                self.config_path_label.setText(config_path)
                self.config_path_label.setToolTip(config_path)
            
        except Exception as e:
            logging.error(f"加载脚本结果失败: {e}")
    
    def _update_button_states(self):
        """更新按钮状态"""
        has_selection = self.current_script is not None
        
        self.run_button.setEnabled(has_selection)
        self.save_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
    
    def _run_script(self):
        """运行脚本"""
        if not self.current_script:
            return
        
        try:
            # 运行脚本
            success, output = self.script_manager.execute_script(self.current_script)
            
            # 显示结果
            self.result_output.setPlainText(output)
            
            # 更新结果信息
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            status_text = "成功" if success else "失败"
            self.result_info_label.setText(f"执行完成: {current_time} ({status_text})")
            
            # 重新加载脚本列表
            self._load_script_list()
            
            # 显示成功消息
            if success:
                QMessageBox.information(self, "执行成功", "脚本执行成功")
            else:
                QMessageBox.warning(self, "执行失败", "脚本执行失败，请检查脚本内容")
            
        except Exception as e:
            logging.error(f"运行脚本失败: {e}")
            QMessageBox.critical(self, "执行错误", f"运行脚本失败:\n\n{str(e)}")
    
    def _save_script(self):
        """保存脚本"""
        if not self.current_script:
            return
        
        try:
            # 验证输入
            name = self.name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "输入错误", "脚本名称不能为空")
                return
            
            content = self.script_edit.toPlainText().strip()
            if not content:
                QMessageBox.warning(self, "输入错误", "脚本内容不能为空")
                return
            
            # 更新脚本
            self.current_script.name = name
            self.current_script.description = self.desc_edit.text().strip()
            self.current_script.content = content
            self.current_script.enabled = self.enabled_check.isChecked()
            self.current_script.updated_at = datetime.now()
            
            # 保存到数据库
            self.db.update_default_script(self.current_script)
            
            # 重新加载脚本列表
            self._load_script_list()
            
            # 显示成功消息
            QMessageBox.information(self, "保存成功", "脚本已保存成功")
            
        except Exception as e:
            logging.error(f"保存脚本失败: {e}")
            QMessageBox.critical(self, "保存错误", f"保存脚本失败:\n\n{str(e)}")
    
    def _new_script(self):
        """新建脚本"""
        try:
            # 创建新脚本
            new_script = DefaultScript(
                name="新脚本",
                description="",
                content="# 在这里编写你的Python脚本\n# 脚本输出将保存到配置文件中",
                enabled=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # 保存到数据库
            script_id = self.db.add_default_script(new_script)
            new_script.id = script_id
            
            # 设置为当前脚本
            self.current_script = new_script
            
            # 加载到表单
            self._load_script_to_form(new_script)
            
            # 更新按钮状态
            self._update_button_states()
            
            # 切换到编辑标签页
            self.tab_widget.setCurrentIndex(1)
            
            # 显示消息
            QMessageBox.information(self, "新建成功", "新脚本已创建，请编辑脚本内容")
            
        except Exception as e:
            logging.error(f"新建脚本失败: {e}")
            QMessageBox.critical(self, "新建错误", f"新建脚本失败:\n\n{str(e)}")
    
    def _delete_script(self):
        """删除脚本"""
        if not self.current_script:
            return
        
        try:
            # 确认对话框
            reply = QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除脚本 '{self.current_script.name}' 吗？\n\n此操作不可撤销。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 删除脚本
                self.db.delete_default_script(self.current_script.id)
                
                # 清空表单
                self.current_script = None
                self._clear_edit_form()
                self._update_button_states()
                
                # 重新加载脚本列表
                self._load_script_list()
                
                # 显示成功消息
                QMessageBox.information(self, "删除成功", "脚本已删除成功")
                
                # 切换回列表标签页
                self.tab_widget.setCurrentIndex(0)
        
        except Exception as e:
            logging.error(f"删除脚本失败: {e}")
            QMessageBox.critical(self, "删除错误", f"删除脚本失败:\n\n{str(e)}")
    
    def _show_example(self):
        """显示脚本示例"""
        example_code = '''# 默认脚本示例
# 这个脚本每天00:00自动执行，输出保存到配置文件
# 其他任务可以通过条件表达式引用这些配置值

import json
import datetime

# 1. 获取当前日期和时间
now = datetime.datetime.now()
current_date = now.strftime("%Y-%m-%d")
current_time = now.strftime("%H:%M:%S")
weekday = now.strftime("%A")  # Monday, Tuesday, etc.

# 2. 计算一些有用的值
# 例如：判断是否是工作日
is_weekday = now.weekday() < 5  # 0-4是周一到周五

# 3. 调用外部API或处理数据
# 例如：获取天气信息（示例）
weather_data = {
    "temperature": 25,
    "condition": "sunny",
    "humidity": 60
}

# 4. 构建配置输出
config_output = {
    "date": current_date,
    "time": current_time,
    "weekday": weekday,
    "is_weekday": is_weekday,
    "weather": weather_data,
    "last_updated": now.isoformat()
}

# 5. 输出配置
# 脚本的输出会自动保存到配置文件
print(json.dumps(config_output, ensure_ascii=False, indent=2))'''
        
        # 创建示例对话框
        example_dialog = QDialog(self)
        example_dialog.setWindowTitle("脚本示例")
        example_dialog.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(example_dialog)
        
        # 说明标签
        info_label = QLabel("这是一个默认脚本的示例，脚本输出将保存到配置文件，其他任务可以通过条件表达式引用这些值。")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 代码编辑器
        example_edit = QTextEdit()
        example_edit.setPlainText(example_code)
        example_edit.setFont(QFont("Consolas", 10))
        example_edit.setReadOnly(True)
        layout.addWidget(example_edit)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        copy_button = QPushButton("复制到剪贴板")
        copy_button.clicked.connect(lambda: self._copy_to_clipboard(example_code))
        
        close_button = QPushButton("关闭")
        close_button.clicked.connect(example_dialog.reject)
        
        button_layout.addWidget(copy_button)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        # 显示对话框
        example_dialog.exec()
    
    def _copy_to_clipboard(self, text: str):
        """复制文本到剪贴板"""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        
        QMessageBox.information(self, "复制成功", "代码已复制到剪贴板")
    
    def accept(self):
        """接受对话框"""
        # 检查是否有未保存的更改
        if self.current_script:
            reply = QMessageBox.question(
                self,
                "确认关闭",
                "脚本内容已更改，确定要关闭吗？\n\n未保存的更改将丢失。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
        
        super().accept()
    
    def reject(self):
        """拒绝对话框"""
        self.accept()
    
    # ========== 公共接口 ==========
    
    def get_script_count(self) -> int:
        """获取脚本数量"""
        try:
            scripts = self.db.get_default_scripts()
            return len(scripts)
        except:
            return 0
    
    def get_enabled_script_count(self) -> int:
        """获取启用脚本数量"""
        try:
            scripts = self.db.get_default_scripts()
            enabled_count = sum(1 for s in scripts if s.enabled)
            return enabled_count
        except:
            return 0
    
    def refresh_script_list(self):
        """刷新脚本列表"""
        self._load_script_list()
    
    def run_all_scripts(self):
        """运行所有启用脚本"""
        try:
            scripts = self.db.get_default_scripts()
            enabled_scripts = [s for s in scripts if s.enabled]
            
            if not enabled_scripts:
                QMessageBox.information(self, "提示", "没有启用的脚本")
                return
            
            # 运行所有脚本
            for script in enabled_scripts:
                try:
                    self.script_manager.execute_script(script)
                except Exception as e:
                    logging.error(f"运行脚本失败 {script.name}: {e}")
            
            # 重新加载列表
            self._load_script_list()
            
            QMessageBox.information(self, "执行完成", f"已运行 {len(enabled_scripts)} 个脚本")
            
        except Exception as e:
            logging.error(f"运行所有脚本失败: {e}")
            QMessageBox.critical(self, "执行错误", f"运行所有脚本失败:\n\n{str(e)}")