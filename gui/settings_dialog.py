"""
设置对话框 - 程序设置和配置管理
"""

import logging
import os
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QTabWidget, QWidget, QGroupBox, QLabel,
    QLineEdit, QSpinBox, QCheckBox, QComboBox,
    QPushButton, QFileDialog, QMessageBox,
    QTextEdit, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QIcon

from config import ConfigManager
from utils.auto_start import AutoStartManager
from gui.styles.colors import COLORS
from utils.icon_helper import get_icon


class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化组件
        self.config = ConfigManager()
        self.auto_start = AutoStartManager()
        
        # 设置窗口属性
        self.setWindowTitle("设置")
        self.setMinimumSize(700, 500)
        self.setModal(True)
        
        # 初始化UI
        self._init_ui()
        
        # 应用样式
        self._apply_styles()
        
        # 加载设置
        self._load_settings()
    
    def _init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 常规设置标签页
        self.general_tab = self._create_general_tab()
        self.tab_widget.addTab(self.general_tab, "常规")
        
        # 任务设置标签页
        self.task_tab = self._create_task_tab()
        self.tab_widget.addTab(self.task_tab, "任务")
        
        # 输出设置标签页
        self.output_tab = self._create_output_tab()
        self.tab_widget.addTab(self.output_tab, "输出")
        
        # 高级设置标签页
        self.advanced_tab = self._create_advanced_tab()
        self.tab_widget.addTab(self.advanced_tab, "高级")
        
        # 添加到主布局
        main_layout.addWidget(self.tab_widget)
        
        # 按钮栏
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 保存按钮
        self.save_button = QPushButton("保存")
        self.save_button.setIcon(get_icon('save'))
        self.save_button.clicked.connect(self._on_save)
        
        # 应用按钮
        self.apply_button = QPushButton("应用")
        self.apply_button.setIcon(get_icon('apply'))
        self.apply_button.clicked.connect(self._on_apply)
        
        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setIcon(get_icon('cancel'))
        self.cancel_button.clicked.connect(self.reject)
        
        # 重置按钮
        self.reset_button = QPushButton("重置")
        self.reset_button.setIcon(get_icon('refresh'))
        self.reset_button.clicked.connect(self._on_reset)
        
        # 添加到按钮布局
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.cancel_button)
        
        # 添加到主布局
        main_layout.addLayout(button_layout)
    
    def _create_general_tab(self) -> QWidget:
        """创建常规设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 启动设置组
        startup_group = QGroupBox("启动设置")
        startup_layout = QFormLayout(startup_group)
        startup_layout.setSpacing(10)
        
        # 开机自启动
        self.auto_start_check = QCheckBox("开机自动启动")
        startup_layout.addRow(self.auto_start_check)
        
        # 启动时最小化
        self.start_minimized_check = QCheckBox("启动时最小化到托盘")
        startup_layout.addRow(self.start_minimized_check)
        
        # 启动时恢复上次状态
        self.restore_state_check = QCheckBox("启动时恢复上次状态")
        startup_layout.addRow(self.restore_state_check)
        
        # 界面设置组
        ui_group = QGroupBox("界面设置")
        ui_layout = QFormLayout(ui_group)
        ui_layout.setSpacing(10)
        
        # 主题选择
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["奶茶色系", "深色模式", "浅色模式", "系统主题"])
        ui_layout.addRow("主题:", self.theme_combo)
        
        # 字体大小
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 16)
        self.font_size_spin.setValue(9)
        ui_layout.addRow("字体大小:", self.font_size_spin)
        
        # 语言选择
        self.language_combo = QComboBox()
        self.language_combo.addItems(["中文", "English"])
        ui_layout.addRow("语言:", self.language_combo)
        
        # 添加到标签页布局
        layout.addWidget(startup_group)
        layout.addWidget(ui_group)
        layout.addStretch()
        
        return tab
    
    def _create_task_tab(self) -> QWidget:
        """创建任务设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 默认设置组
        default_group = QGroupBox("默认设置")
        default_layout = QFormLayout(default_group)
        default_layout.setSpacing(10)
        
        # 默认工作目录
        self.default_workdir_edit = QLineEdit()
        self.default_workdir_edit.setPlaceholderText("默认工作目录")
        default_layout.addRow("默认工作目录:", self.default_workdir_edit)
        
        # 浏览按钮
        workdir_layout = QHBoxLayout()
        workdir_layout.addWidget(self.default_workdir_edit)
        
        self.browse_workdir_button = QPushButton("浏览...")
        self.browse_workdir_button.clicked.connect(self._browse_workdir)
        workdir_layout.addWidget(self.browse_workdir_button)
        
        default_layout.addRow("", workdir_layout)
        
        # 默认shell
        self.default_shell_combo = QComboBox()
        self.default_shell_combo.addItems(["cmd", "powershell", "bash"])
        default_layout.addRow("默认Shell:", self.default_shell_combo)
        
        # 执行设置组
        execution_group = QGroupBox("执行设置")
        execution_layout = QFormLayout(execution_group)
        execution_layout.setSpacing(10)
        
        # 任务超时时间
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(0, 3600)
        self.timeout_spin.setValue(300)
        self.timeout_spin.setSuffix(" 秒 (0=无限制)")
        execution_layout.addRow("任务超时:", self.timeout_spin)
        
        # 最大并发任务数
        self.max_concurrent_spin = QSpinBox()
        self.max_concurrent_spin.setRange(1, 10)
        self.max_concurrent_spin.setValue(1)
        execution_layout.addRow("最大并发任务:", self.max_concurrent_spin)
        
        # 任务失败处理
        self.fail_handling_combo = QComboBox()
        self.fail_handling_combo.addItems(["不处理", "发送通知", "记录日志", "自动重试"])
        execution_layout.addRow("失败处理:", self.fail_handling_combo)
        
        # 添加到标签页布局
        layout.addWidget(default_group)
        layout.addWidget(execution_group)
        layout.addStretch()
        
        return tab
    
    def _create_output_tab(self) -> QWidget:
        """创建输出设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 输出显示组
        display_group = QGroupBox("输出显示")
        display_layout = QFormLayout(display_group)
        display_layout.setSpacing(10)
        
        # 最大输出行数
        self.max_lines_spin = QSpinBox()
        self.max_lines_spin.setRange(100, 10000)
        self.max_lines_spin.setValue(1000)
        display_layout.addRow("最大行数:", self.max_lines_spin)
        
        # 自动滚动
        self.auto_scroll_check = QCheckBox("自动滚动到底部")
        self.auto_scroll_check.setChecked(True)
        display_layout.addRow(self.auto_scroll_check)
        
        # 显示时间戳
        self.show_timestamp_check = QCheckBox("显示时间戳")
        self.show_timestamp_check.setChecked(True)
        display_layout.addRow(self.show_timestamp_check)
        
        # 字体设置
        self.font_family_combo = QComboBox()
        self.font_family_combo.addItems(["Consolas", "Courier New", "Monospace", "微软雅黑"])
        display_layout.addRow("字体:", self.font_family_combo)
        
        # 编码设置组
        encoding_group = QGroupBox("编码设置")
        encoding_layout = QFormLayout(encoding_group)
        encoding_layout.setSpacing(10)
        
        # 默认编码
        self.default_encoding_combo = QComboBox()
        self.default_encoding_combo.addItems(["自动检测", "UTF-8", "GBK", "GB2312", "BIG5"])
        encoding_layout.addRow("默认编码:", self.default_encoding_combo)
        
        # 强制编码
        self.force_encoding_check = QCheckBox("强制使用默认编码")
        encoding_layout.addRow(self.force_encoding_check)
        
        # 特殊字符处理
        self.handle_special_chars_check = QCheckBox("处理特殊字符（如emoji）")
        self.handle_special_chars_check.setChecked(True)
        encoding_layout.addRow(self.handle_special_chars_check)
        
        # 添加到标签页布局
        layout.addWidget(display_group)
        layout.addWidget(encoding_group)
        layout.addStretch()
        
        return tab
    
    def _create_advanced_tab(self) -> QWidget:
        """创建高级设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 日志设置组
        log_group = QGroupBox("日志设置")
        log_layout = QFormLayout(log_group)
        log_layout.setSpacing(10)
        
        # 日志级别
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        log_layout.addRow("日志级别:", self.log_level_combo)
        
        # 日志文件大小
        self.log_size_spin = QSpinBox()
        self.log_size_spin.setRange(1, 100)
        self.log_size_spin.setValue(10)
        self.log_size_spin.setSuffix(" MB")
        log_layout.addRow("日志文件大小:", self.log_size_spin)
        
        # 日志保留天数
        self.log_retention_spin = QSpinBox()
        self.log_retention_spin.setRange(1, 365)
        self.log_retention_spin.setValue(90)
        self.log_retention_spin.setSuffix(" 天")
        log_layout.addRow("日志保留:", self.log_retention_spin)
        
        # 日志文件位置
        self.log_path_edit = QLineEdit()
        self.log_path_edit.setPlaceholderText("日志文件路径")
        log_layout.addRow("日志路径:", self.log_path_edit)
        
        # 浏览按钮
        log_path_layout = QHBoxLayout()
        log_path_layout.addWidget(self.log_path_edit)
        
        self.browse_log_button = QPushButton("浏览...")
        self.browse_log_button.clicked.connect(self._browse_log_path)
        log_path_layout.addWidget(self.browse_log_button)
        
        log_layout.addRow("", log_path_layout)
        
        # 网络设置组
        network_group = QGroupBox("网络设置")
        network_layout = QFormLayout(network_group)
        network_layout.setSpacing(10)
        
        # 代理设置
        self.proxy_edit = QLineEdit()
        self.proxy_edit.setPlaceholderText("例如: http://proxy.example.com:8080")
        network_layout.addRow("HTTP代理:", self.proxy_edit)
        
        # 网络超时
        self.network_timeout_spin = QSpinBox()
        self.network_timeout_spin.setRange(5, 300)
        self.network_timeout_spin.setValue(30)
        self.network_timeout_spin.setSuffix(" 秒")
        network_layout.addRow("网络超时:", self.network_timeout_spin)
        
        # 调试设置组
        debug_group = QGroupBox("调试设置")
        debug_layout = QFormLayout(debug_group)
        debug_layout.setSpacing(10)
        
        # 调试模式
        self.debug_mode_check = QCheckBox("启用调试模式")
        debug_layout.addRow(self.debug_mode_check)
        
        # 详细日志
        self.verbose_logging_check = QCheckBox("详细日志记录")
        debug_layout.addRow(self.verbose_logging_check)
        
        # 添加到标签页布局
        layout.addWidget(log_group)
        layout.addWidget(network_group)
        layout.addWidget(debug_group)
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
                
                QLineEdit, QComboBox, QSpinBox, QTextEdit {{
                    background-color: {COLORS['background_card']};
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border_light']};
                    border-radius: 4px;
                    padding: 6px;
                    font-size: 9pt;
                }}
                
                QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
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
    
    def _browse_workdir(self):
        """浏览工作目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择默认工作目录",
            self.default_workdir_edit.text() or os.path.expanduser("~")
        )
        
        if dir_path:
            self.default_workdir_edit.setText(dir_path)
    
    def _browse_log_path(self):
        """浏览日志路径"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择日志目录",
            self.log_path_edit.text() or os.path.expanduser("~")
        )
        
        if dir_path:
            self.log_path_edit.setText(dir_path)
    
    def _load_settings(self):
        """加载设置"""
        try:
            # 常规设置
            self.auto_start_check.setChecked(self.config.get('auto_start', False))
            self.start_minimized_check.setChecked(self.config.get('start_minimized', False))
            self.restore_state_check.setChecked(self.config.get('restore_state', True))
            
            theme = self.config.get('theme', '奶茶色系')
            theme_index = self.theme_combo.findText(theme)
            if theme_index >= 0:
                self.theme_combo.setCurrentIndex(theme_index)
            
            self.font_size_spin.setValue(self.config.get('font_size', 9))
            
            language = self.config.get('language', '中文')
            language_index = self.language_combo.findText(language)
            if language_index >= 0:
                self.language_combo.setCurrentIndex(language_index)
            
            # 任务设置
            self.default_workdir_edit.setText(self.config.get('default_workdir', ''))
            
            shell = self.config.get('default_shell', 'cmd')
            shell_index = self.default_shell_combo.findText(shell)
            if shell_index >= 0:
                self.default_shell_combo.setCurrentIndex(shell_index)
            
            self.timeout_spin.setValue(self.config.get('task_timeout', 300))
            self.max_concurrent_spin.setValue(self.config.get('max_concurrent_tasks', 1))
            
            fail_handling = self.config.get('fail_handling', '不处理')
            fail_index = self.fail_handling_combo.findText(fail_handling)
            if fail_index >= 0:
                self.fail_handling_combo.setCurrentIndex(fail_index)
            
            # 输出设置
            self.max_lines_spin.setValue(self.config.get('max_output_lines', 1000))
            self.auto_scroll_check.setChecked(self.config.get('auto_scroll', True))
            self.show_timestamp_check.setChecked(self.config.get('show_timestamp', True))
            
            font_family = self.config.get('font_family', 'Consolas')
            font_index = self.font_family_combo.findText(font_family)
            if font_index >= 0:
                self.font_family_combo.setCurrentIndex(font_index)
            
            encoding = self.config.get('default_encoding', '自动检测')
            encoding_index = self.default_encoding_combo.findText(encoding)
            if encoding_index >= 0:
                self.default_encoding_combo.setCurrentIndex(encoding_index)
            
            self.force_encoding_check.setChecked(self.config.get('force_encoding', False))
            self.handle_special_chars_check.setChecked(self.config.get('handle_special_chars', True))
            
            # 高级设置
            log_level = self.config.get('log_level', 'INFO')
            log_index = self.log_level_combo.findText(log_level)
            if log_index >= 0:
                self.log_level_combo.setCurrentIndex(log_index)
            
            self.log_size_spin.setValue(self.config.get('log_file_size', 10))
            self.log_retention_spin.setValue(self.config.get('log_retention_days', 90))
            self.log_path_edit.setText(self.config.get('log_path', ''))
            
            self.proxy_edit.setText(self.config.get('proxy', ''))
            self.network_timeout_spin.setValue(self.config.get('network_timeout', 30))
            
            self.debug_mode_check.setChecked(self.config.get('debug_mode', False))
            self.verbose_logging_check.setChecked(self.config.get('verbose_logging', False))
            
        except Exception as e:
            logging.error(f"加载设置失败: {e}")
            QMessageBox.warning(self, "加载失败", f"加载设置失败:\n\n{str(e)}")
    
    def _get_settings(self) -> dict:
        """获取当前设置"""
        settings = {
            # 常规设置
            'auto_start': self.auto_start_check.isChecked(),
            'start_minimized': self.start_minimized_check.isChecked(),
            'restore_state': self.restore_state_check.isChecked(),
            'theme': self.theme_combo.currentText(),
            'font_size': self.font_size_spin.value(),
            'language': self.language_combo.currentText(),
            
            # 任务设置
            'default_workdir': self.default_workdir_edit.text(),
            'default_shell': self.default_shell_combo.currentText(),
            'task_timeout': self.timeout_spin.value(),
            'max_concurrent_tasks': self.max_concurrent_spin.value(),
            'fail_handling': self.fail_handling_combo.currentText(),
            
            # 输出设置
            'max_output_lines': self.max_lines_spin.value(),
            'auto_scroll': self.auto_scroll_check.isChecked(),
            'show_timestamp': self.show_timestamp_check.isChecked(),
            'font_family': self.font_family_combo.currentText(),
            'default_encoding': self.default_encoding_combo.currentText(),
            'force_encoding': self.force_encoding_check.isChecked(),
            'handle_special_chars': self.handle_special_chars_check.isChecked(),
            
            # 高级设置
            'log_level': self.log_level_combo.currentText(),
            'log_file_size': self.log_size_spin.value(),
            'log_retention_days': self.log_retention_spin.value(),
            'log_path': self.log_path_edit.text(),
            'proxy': self.proxy_edit.text(),
            'network_timeout': self.network_timeout_spin.value(),
            'debug_mode': self.debug_mode_check.isChecked(),
            'verbose_logging': self.verbose_logging_check.isChecked()
        }
        
        return settings
    
    def _on_save(self):
        """保存设置"""
        try:
            # 获取当前设置
            settings = self._get_settings()
            
            # 保存到配置文件
            for key, value in settings.items():
                self.config.set(key, value)
            
            # 应用开机自启动
            if settings['auto_start']:
                self.auto_start.enable()
            else:
                self.auto_start.disable()
            
            # 保存成功
            QMessageBox.information(self, "保存成功", "设置已保存成功")
            
            # 关闭对话框
            self.accept()
            
        except Exception as e:
            logging.error(f"保存设置失败: {e}")
            QMessageBox.critical(self, "保存失败", f"保存设置失败:\n\n{str(e)}")
    
    def _on_apply(self):
        """应用设置"""
        try:
            # 获取当前设置
            settings = self._get_settings()
            
            # 保存到配置文件
            for key, value in settings.items():
                self.config.set(key, value)
            
            # 应用开机自启动
            if settings['auto_start']:
                self.auto_start.enable()
            else:
                self.auto_start.disable()
            
            # 应用成功
            QMessageBox.information(self, "应用成功", "设置已应用成功")
            
        except Exception as e:
            logging.error(f"应用设置失败: {e}")
            QMessageBox.critical(self, "应用失败", f"应用设置失败:\n\n{str(e)}")
    
    def _on_reset(self):
        """重置设置"""
        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要重置所有设置为默认值吗？\n\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 重置配置文件
                self.config.reset_to_defaults()
                
                # 重新加载设置
                self._load_settings()
                
                QMessageBox.information(self, "重置成功", "设置已重置为默认值")
                
            except Exception as e:
                logging.error(f"重置设置失败: {e}")
                QMessageBox.critical(self, "重置失败", f"重置设置失败:\n\n{str(e)}")
    
    def accept(self):
        """接受对话框"""
        # 调用父类的accept
        super().accept()
    
    def reject(self):
        """拒绝对话框"""
        # 检查是否有未保存的更改
        current_settings = self._get_settings()
        original_settings = {}
        
        try:
            # 获取原始设置
            original_settings = {
                'auto_start': self.config.get('auto_start', False),
                'start_minimized': self.config.get('start_minimized', False),
                'restore_state': self.config.get('restore_state', True),
                'theme': self.config.get('theme', '奶茶色系'),
                'font_size': self.config.get('font_size', 9),
                'language': self.config.get('language', '中文'),
            }
        except:
            pass
        
        # 比较设置是否改变
        settings_changed = False
        for key in original_settings:
            if key in current_settings and current_settings[key] != original_settings[key]:
                settings_changed = True
                break
        
        if settings_changed:
            reply = QMessageBox.question(
                self,
                "确认取消",
                "设置已更改，确定要取消吗？\n\n所有更改将丢失。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                super().reject()
        else:
            super().reject()
    
    # ========== 公共接口 ==========
    
    def get_settings_summary(self) -> str:
        """获取设置摘要"""
        settings = self._get_settings()
        
        summary = []
        summary.append(f"主题: {settings['theme']}")
        summary.append(f"语言: {settings['language']}")
        summary.append(f"开机自启动: {'是' if settings['auto_start'] else '否'}")
        summary.append(f"最大并发任务: {settings['max_concurrent_tasks']}")
        summary.append(f"任务超时: {settings['task_timeout']}秒")
        summary.append(f"日志级别: {settings['log_level']}")
        
        return "\n".join(summary)
    
    def show_restart_warning(self):
        """显示重启警告"""
        QMessageBox.warning(
            self,
            "需要重启",
            "部分设置需要重启应用程序才能生效。\n\n建议保存设置后重启程序。"
        )