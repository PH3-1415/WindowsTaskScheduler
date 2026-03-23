"""
输出显示组件 - 显示任务执行输出
"""

import logging
from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QPushButton, QLabel, QScrollBar, QMenu
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import (
    QFont, QTextCursor, QTextCharFormat, QColor, 
    QAction, QIcon, QSyntaxHighlighter, QTextDocument
)

from gui.styles.colors import COLORS
from utils.encoding_helper import EncodingHelper


class OutputWidget(QWidget):
    """输出显示组件"""
    
    # 信号定义
    cleared = Signal()  # 输出清空信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化组件
        self.encoding_helper = EncodingHelper()
        self.current_task_id: Optional[int] = None
        self.current_task_name: Optional[str] = None
        self.output_buffer = []
        self.max_output_lines = 1000
        
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
        
        # 标题栏
        title_layout = QHBoxLayout()
        
        # 标题
        self.title_label = QLabel("任务输出")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        self.title_label.setFont(title_font)
        
        # 清空按钮
        self.clear_button = QPushButton("清空")
        self.clear_button.setIcon(QIcon("resources/icons/clear.png"))
        self.clear_button.clicked.connect(self.clear)
        
        # 自动滚动复选框
        self.auto_scroll_checkbox = QPushButton("自动滚动")
        self.auto_scroll_checkbox.setCheckable(True)
        self.auto_scroll_checkbox.setChecked(True)
        self.auto_scroll_checkbox.clicked.connect(self._toggle_auto_scroll)
        
        # 时间戳复选框
        self.timestamp_checkbox = QPushButton("时间戳")
        self.timestamp_checkbox.setCheckable(True)
        self.timestamp_checkbox.setChecked(True)
        self.timestamp_checkbox.clicked.connect(self._toggle_timestamp)
        
        # 添加到标题栏
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.timestamp_checkbox)
        title_layout.addWidget(self.auto_scroll_checkbox)
        title_layout.addWidget(self.clear_button)
        
        # 输出文本框
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setLineWrapMode(QTextEdit.WidgetWidth)
        self.output_text.setFont(QFont("Consolas", 9))
        self.output_text.setContextMenuPolicy(Qt.CustomContextMenu)
        self.output_text.customContextMenuRequested.connect(self._show_context_menu)
        
        # 状态栏
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # 添加到主布局
        main_layout.addLayout(title_layout)
        main_layout.addWidget(self.output_text)
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
                
                QTextEdit {{
                    background-color: {COLORS['background_card']};
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border_light']};
                    border-radius: 4px;
                    font-family: Consolas, 'Courier New', monospace;
                    font-size: 9pt;
                }}
                
                QPushButton {{
                    background-color: {COLORS['button_normal']};
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border_medium']};
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 9pt;
                    min-width: 60px;
                }}
                
                QPushButton:hover {{
                    background-color: {COLORS['button_hover']};
                }}
                
                QPushButton:pressed {{
                    background-color: {COLORS['button_pressed']};
                }}
                
                QPushButton:checked {{
                    background-color: {COLORS['button_hover']};
                    border: 2px solid {COLORS['border_dark']};
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
        
        # 缓冲区刷新定时器
        self.buffer_timer = QTimer(self)
        self.buffer_timer.timeout.connect(self._flush_buffer)
        self.buffer_timer.start(100)  # 100毫秒刷新一次
    
    def _update_status(self):
        """更新状态"""
        line_count = self.output_text.document().lineCount()
        char_count = len(self.output_text.toPlainText())
        
        status_text = f"行数: {line_count} | 字符: {char_count}"
        
        if self.current_task_name:
            status_text = f"任务: {self.current_task_name} | " + status_text
        
        self.status_label.setText(status_text)
    
    def _flush_buffer(self):
        """刷新输出缓冲区"""
        if not self.output_buffer:
            return
        
        # 获取缓冲区内容
        buffer_content = ''.join(self.output_buffer)
        self.output_buffer.clear()
        
        # 添加到文本框
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(buffer_content)
        
        # 自动滚动到底部
        if self.auto_scroll_checkbox.isChecked():
            self.output_text.ensureCursorVisible()
            scrollbar = self.output_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        
        # 限制行数
        self._limit_output_lines()
    
    def _limit_output_lines(self):
        """限制输出行数"""
        document = self.output_text.document()
        line_count = document.lineCount()
        
        if line_count > self.max_output_lines:
            # 计算要删除的行数
            lines_to_remove = line_count - self.max_output_lines + 100  # 保留一些缓冲
            
            cursor = QTextCursor(document)
            cursor.movePosition(QTextCursor.Start)
            
            # 移动到要删除的行的末尾
            for _ in range(lines_to_remove):
                if not cursor.movePosition(QTextCursor.Down):
                    break
            
            # 删除多余的行
            cursor.movePosition(QTextCursor.Start, QTextCursor.KeepAnchor)
            cursor.removeSelectedText()
    
    def _show_context_menu(self, position):
        """显示上下文菜单"""
        menu = QMenu(self)
        
        # 复制
        copy_action = QAction("复制", self)
        copy_action.triggered.connect(self._copy_selected_text)
        menu.addAction(copy_action)
        
        # 全选
        select_all_action = QAction("全选", self)
        select_all_action.triggered.connect(self._select_all_text)
        menu.addAction(select_all_action)
        
        menu.addSeparator()
        
        # 清空
        clear_action = QAction("清空", self)
        clear_action.triggered.connect(self.clear)
        menu.addAction(clear_action)
        
        menu.addSeparator()
        
        # 查找
        find_action = QAction("查找...", self)
        find_action.triggered.connect(self._show_find_dialog)
        menu.addAction(find_action)
        
        # 显示菜单
        menu.exec_(self.output_text.mapToGlobal(position))
    
    def _copy_selected_text(self):
        """复制选中文本"""
        self.output_text.copy()
    
    def _select_all_text(self):
        """全选文本"""
        self.output_text.selectAll()
    
    def _show_find_dialog(self):
        """显示查找对话框"""
        # TODO: 实现查找功能
        pass
    
    def _toggle_auto_scroll(self):
        """切换自动滚动"""
        is_checked = self.auto_scroll_checkbox.isChecked()
        self.auto_scroll_checkbox.setText("自动滚动" if is_checked else "固定")
    
    def _toggle_timestamp(self):
        """切换时间戳"""
        is_checked = self.timestamp_checkbox.isChecked()
        self.timestamp_checkbox.setText("时间戳" if is_checked else "无时间戳")
    
    # ========== 公共接口 ==========    
    def append_output(self, text: str):
        """追加输出"""
        if not text:
            return
        
        # 清理文本
        cleaned_text = self.encoding_helper.sanitize_output(text)
        
        # 添加时间戳
        if self.timestamp_checkbox.isChecked():
            timestamp = datetime.now().strftime("[%H:%M:%S] ")
            cleaned_text = timestamp + cleaned_text
        
        # 添加到缓冲区
        self.output_buffer.append(cleaned_text)
    
    def clear(self):
        """清空输出"""
        self.output_text.clear()
        self.output_buffer.clear()
        self.current_task_id = None
        self.current_task_name = None
        
        # 发送清空信号
        self.cleared.emit()
        
        logging.debug("输出区域已清空")
    
    def set_current_task(self, task_id: int, task_name: str):
        """设置当前任务"""
        self.current_task_id = task_id
        self.current_task_name = task_name
        self.title_label.setText(f"任务输出: {task_name}")
    
    def highlight_text(self, pattern: str, color: str = COLORS['status_running']):
        """高亮文本"""
        # TODO: 实现文本高亮功能
        pass
    
    def search_text(self, pattern: str) -> bool:
        """搜索文本"""
        # TODO: 实现文本搜索功能
        return False
    
    def save_to_file(self, filepath: str) -> bool:
        """保存到文件"""
        try:
            content = self.output_text.toPlainText()
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logging.info(f"输出已保存到: {filepath}")
            return True
            
        except Exception as e:
            logging.error(f"保存输出失败: {e}")
            return False
    
    def get_output_text(self) -> str:
        """获取输出文本"""
        return self.output_text.toPlainText()
    
    def set_max_lines(self, max_lines: int):
        """设置最大行数"""
        self.max_output_lines = max(100, min(max_lines, 10000))
    
    def is_auto_scroll_enabled(self) -> bool:
        """是否启用自动滚动"""
        return self.auto_scroll_checkbox.isChecked()
    
    def enable_auto_scroll(self, enabled: bool = True):
        """启用/禁用自动滚动"""
        self.auto_scroll_checkbox.setChecked(enabled)
    
    def is_timestamp_enabled(self) -> bool:
        """是否显示时间戳"""
        return self.timestamp_checkbox.isChecked()
    
    def enable_timestamp(self, enabled: bool = True):
        """启用/禁用时间戳"""
        self.timestamp_checkbox.setChecked(enabled)
    
    # ========== 格式处理 ==========    
    def apply_format(self, start_pos: int, end_pos: int, format_dict: dict):
        """应用格式"""
        cursor = self.output_text.textCursor()
        cursor.setPosition(start_pos)
        cursor.setPosition(end_pos, QTextCursor.KeepAnchor)
        
        # 创建格式
        char_format = QTextCharFormat()
        
        if 'color' in format_dict:
            char_format.setForeground(QColor(format_dict['color']))
        
        if 'bold' in format_dict and format_dict['bold']:
            char_format.setFontWeight(QFont.Bold)
        
        if 'italic' in format_dict and format_dict['italic']:
            char_format.setFontItalic(True)
        
        if 'background' in format_dict:
            char_format.setBackground(QColor(format_dict['background']))
        
        # 应用格式
        cursor.mergeCharFormat(char_format)
    
    def clear_formats(self):
        """清除所有格式"""
        cursor = self.output_text.textCursor()
        cursor.select(QTextCursor.Document)
        
        char_format = QTextCharFormat()
        char_format.clearBackground()
        char_format.setForeground(QColor(COLORS['text_primary']))
        char_format.setFontWeight(QFont.Normal)
        char_format.setFontItalic(False)
        
        cursor.mergeCharFormat(char_format)
    
    # ========== 工具方法 ==========    
    def get_line_count(self) -> int:
        """获取行数"""
        return self.output_text.document().lineCount()
    
    def get_char_count(self) -> int:
        """获取字符数"""
        return len(self.output_text.toPlainText())
    
    def scroll_to_top(self):
        """滚动到顶部"""
        scrollbar = self.output_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.minimum())
    
    def scroll_to_bottom(self):
        """滚动到底部"""
        scrollbar = self.output_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def scroll_to_line(self, line_number: int):
        """滚动到指定行"""
        # TODO: 实现滚动到指定行
        pass