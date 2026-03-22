"""
配置管理模块
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from database.db_manager import DatabaseManager


class ConfigManager:
    """配置管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.db = DatabaseManager()
            self.db.initialize()
            self._load_default_config()
    
    def _load_default_config(self):
        """加载默认配置"""
        default_config = {
            'app': {
                'version': '1.0.0',
                'first_run': True,
                'last_run': datetime.now().isoformat(),
                'auto_start': True,
                'minimize_to_tray': True,
                'language': 'zh_CN'
            },
            'ui': {
                'window_width': 900,
                'window_height': 600,
                'window_x': -1,  # -1表示居中
                'window_y': -1,
                'theme': 'light',  # light, dark
                'font_size': 9,
                'show_system_tray': True
            },
            'scheduler': {
                'max_concurrent_tasks': 1,  # 串行执行
                'retry_count': 3,
                'retry_delay': 5,  # 秒
                'cleanup_logs_days': 90,
                'default_script_run_time': '00:00'
            },
            'output': {
                'max_output_lines': 1000,
                'auto_scroll': True,
                'show_timestamps': True,
                'encoding': 'auto'  # auto, utf-8, gbk, etc.
            },
            'paths': {
                'config_dir': self._get_config_dir(),
                'log_dir': self._get_log_dir(),
                'temp_dir': self._get_temp_dir()
            }
        }
        
        # 保存默认配置
        for key, value in default_config.items():
            if not self.db.get_config(key):
                self.db.set_config(key, value)
    
    def _get_config_dir(self) -> str:
        """获取配置目录"""
        # 使用数据库管理器中的相同逻辑
        db = DatabaseManager()
        return os.path.dirname(db._get_app_data_dir())
    
    def _get_log_dir(self) -> str:
        """获取日志目录"""
        config_dir = self._get_config_dir()
        return os.path.join(config_dir, 'logs')
    
    def _get_temp_dir(self) -> str:
        """获取临时目录"""
        config_dir = self._get_config_dir()
        return os.path.join(config_dir, 'temp')
    
    # ========== 配置访问方法 ==========
    
    def get(self, section: str, key: str = None, default: Any = None) -> Any:
        """获取配置值"""
        config = self.db.get_config(section, {})
        
        if key is None:
            return config
        
        # 支持嵌套键，如 'ui.window_width'
        if '.' in key:
            keys = key.split('.')
            value = config
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            return value
        else:
            return config.get(key, default)
    
    def set(self, section: str, key: str, value: Any):
        """设置配置值"""
        config = self.db.get_config(section, {})
        
        # 支持嵌套键
        if '.' in key:
            keys = key.split('.')
            current = config
            
            # 遍历到最后一个键的父级
            for k in keys[:-1]:
                if k not in current or not isinstance(current[k], dict):
                    current[k] = {}
                current = current[k]
            
            # 设置值
            current[keys[-1]] = value
        else:
            config[key] = value
        
        self.db.set_config(section, config)
    
    def update(self, section: str, updates: Dict[str, Any]):
        """批量更新配置"""
        config = self.db.get_config(section, {})
        config.update(updates)
        self.db.set_config(section, config)
    
    # ========== 具体配置访问器 ==========
    
    @property
    def app_version(self) -> str:
        return self.get('app', 'version', '1.0.0')
    
    @property
    def is_first_run(self) -> bool:
        return self.get('app', 'first_run', True)
    
    @is_first_run.setter
    def is_first_run(self, value: bool):
        self.set('app', 'first_run', value)
    
    @property
    def auto_start(self) -> bool:
        return self.get('app', 'auto_start', True)
    
    @auto_start.setter
    def auto_start(self, value: bool):
        self.set('app', 'auto_start', value)
    
    @property
    def minimize_to_tray(self) -> bool:
        return self.get('app', 'minimize_to_tray', True)
    
    @minimize_to_tray.setter
    def minimize_to_tray(self, value: bool):
        self.set('app', 'minimize_to_tray', value)
    
    @property
    def window_size(self) -> tuple:
        return (
            self.get('ui', 'window_width', 900),
            self.get('ui', 'window_height', 600)
        )
    
    @window_size.setter
    def window_size(self, size: tuple):
        width, height = size
        self.set('ui', 'window_width', width)
        self.set('ui', 'window_height', height)
    
    @property
    def window_position(self) -> tuple:
        return (
            self.get('ui', 'window_x', -1),
            self.get('ui', 'window_y', -1)
        )
    
    @window_position.setter
    def window_position(self, pos: tuple):
        x, y = pos
        self.set('ui', 'window_x', x)
        self.set('ui', 'window_y', y)
    
    @property
    def theme(self) -> str:
        return self.get('ui', 'theme', 'light')
    
    @theme.setter
    def theme(self, value: str):
        self.set('ui', 'theme', value)
    
    @property
    def max_concurrent_tasks(self) -> int:
        return self.get('scheduler', 'max_concurrent_tasks', 1)
    
    @property
    def retry_count(self) -> int:
        return self.get('scheduler', 'retry_count', 3)
    
    @property
    def retry_delay(self) -> int:
        return self.get('scheduler', 'retry_delay', 5)
    
    @property
    def cleanup_logs_days(self) -> int:
        return self.get('scheduler', 'cleanup_logs_days', 90)
    
    @property
    def default_script_run_time(self) -> str:
        return self.get('scheduler', 'default_script_run_time', '00:00')
    
    @property
    def max_output_lines(self) -> int:
        return self.get('output', 'max_output_lines', 1000)
    
    @property
    def auto_scroll(self) -> bool:
        return self.get('output', 'auto_scroll', True)
    
    @property
    def show_timestamps(self) -> bool:
        return self.get('output', 'show_timestamps', True)
    
    @property
    def encoding(self) -> str:
        return self.get('output', 'encoding', 'auto')
    
    @encoding.setter
    def encoding(self, value: str):
        self.set('output', 'encoding', value)
    
    # ========== 工具方法 ==========
    
    def save_window_state(self, window):
        """保存窗口状态"""
        geometry = window.geometry()
        self.window_position = (geometry.x(), geometry.y())
        self.window_size = (geometry.width(), geometry.height())
    
    def mark_run_complete(self):
        """标记运行完成"""
        self.set('app', 'last_run', datetime.now().isoformat())
        if self.is_first_run:
            self.is_first_run = False
    
    def get_config_dir(self) -> str:
        """获取配置目录路径"""
        return self.get('paths', 'config_dir')
    
    def get_log_dir(self) -> str:
        """获取日志目录路径"""
        log_dir = self.get('paths', 'log_dir')
        os.makedirs(log_dir, exist_ok=True)
        return log_dir
    
    def get_temp_dir(self) -> str:
        """获取临时目录路径"""
        temp_dir = self.get('paths', 'temp_dir')
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于调试）"""
        sections = ['app', 'ui', 'scheduler', 'output', 'paths']
        result = {}
        
        for section in sections:
            result[section] = self.db.get_config(section, {})
        
        return result