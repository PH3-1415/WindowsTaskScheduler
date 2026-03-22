"""
数据库管理器
"""

import os
import sqlite3
import threading
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

from .models import Task, TaskLog, DefaultScript, AppConfig


class DatabaseManager:
    """数据库管理器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        # 在测试环境中，允许创建新实例
        if os.environ.get('TEST_MODE') == '1':
            return super().__new__(cls)
        
        # 在生产环境中，使用单例模式
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.db_path: Optional[str] = None
            self.conn: Optional[sqlite3.Connection] = None
            self._init_done = False
            self.logger = logging.getLogger(__name__)
    
    def initialize(self, db_path: str = None):
        """初始化数据库"""
        # 在测试环境中，允许重新初始化
        if self._init_done and os.environ.get('TEST_MODE') != '1':
            return
        
        if db_path is None:
            # 默认使用用户数据目录
            app_data_dir = self._get_app_data_dir()
            self.db_path = str(Path(app_data_dir) / 'tasks.db')
        else:
            self.db_path = db_path
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # 连接数据库
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # 创建表
        self._create_tables()
        
        # 更新表结构（如果表已存在但缺少列）
        self._update_table_schema()
        
        self._init_done = True
    
    def _get_app_data_dir(self) -> str:
        """获取应用数据目录"""
        # Windows: %APPDATA%\WindowsTaskScheduler
        if os.name == 'nt':
            app_data = os.getenv('APPDATA')
            if app_data:
                return os.path.join(app_data, 'WindowsTaskScheduler')
        
        # Linux/macOS: ~/.config/WindowsTaskScheduler
        home = os.path.expanduser('~')
        return os.path.join(home, '.config', 'WindowsTaskScheduler')
    
    def _create_tables(self):
        """创建数据库表"""
        cursor = self.conn.cursor()
        
        # tasks表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                command TEXT NOT NULL,
                working_dir TEXT,
                schedule_type TEXT NOT NULL,
                schedule_config TEXT NOT NULL,
                condition TEXT,
                enabled BOOLEAN DEFAULT 1,
                priority INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # task_logs表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                output TEXT,
                exit_code INTEGER,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                error_message TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_logs_task_id ON task_logs(task_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_logs_start_time ON task_logs(start_time)')
        
        # default_scripts表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS default_scripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                script_content TEXT NOT NULL,
                output_config TEXT,
                last_run TIMESTAMP,
                last_output TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # app_config表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_config (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def _update_table_schema(self):
        """更新表结构（如果表已存在但缺少列）"""
        cursor = self.conn.cursor()
        
        # 检查default_scripts表是否有所有必要的列
        columns_to_check = [
            ('script_content', 'TEXT NOT NULL DEFAULT \'\''),
            ('output_config', 'TEXT DEFAULT \'{}\''),
            ('last_run', 'TIMESTAMP'),
            ('last_output', 'TEXT DEFAULT \'\''),
            ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
        ]
        
        for column_name, column_type in columns_to_check:
            try:
                cursor.execute(f"SELECT {column_name} FROM default_scripts LIMIT 1")
            except sqlite3.OperationalError:
                # 表存在但没有该列，添加它
                try:
                    cursor.execute(f"ALTER TABLE default_scripts ADD COLUMN {column_name} {column_type}")
                    self.logger.info(f"已添加{column_name}列到default_scripts表")
                except sqlite3.OperationalError as e:
                    self.logger.warning(f"无法添加{column_name}列: {e}")
        
        self.conn.commit()
    
    # ========== 任务管理 ==========
    
    def add_task(self, task: Task) -> int:
        """添加任务"""
        cursor = self.conn.cursor()
        data = task.to_dict()
        data.pop('id', None)  # 移除id，让数据库自动生成
        
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        
        cursor.execute(
            f'INSERT INTO tasks ({columns}) VALUES ({placeholders})',
            list(data.values())
        )
        
        self.conn.commit()
        return cursor.lastrowid
    
    def update_task(self, task: Task) -> bool:
        """更新任务"""
        if task.id is None:
            return False
        
        cursor = self.conn.cursor()
        data = task.to_dict()
        data['updated_at'] = datetime.now().isoformat()
        
        # 移除id，因为它是WHERE条件
        task_id = data.pop('id')
        
        set_clause = ', '.join([f'{key} = ?' for key in data.keys()])
        
        cursor.execute(
            f'UPDATE tasks SET {set_clause} WHERE id = ?',
            list(data.values()) + [task_id]
        )
        
        self.conn.commit()
        return cursor.rowcount > 0
    
    def delete_task(self, task_id: int) -> bool:
        """删除任务"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_task(self, task_id: int) -> Optional[Task]:
        """获取任务"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        
        if row:
            return Task.from_dict(dict(row))
        return None
    
    def get_all_tasks(self, enabled_only: bool = False) -> List[Task]:
        """获取所有任务"""
        cursor = self.conn.cursor()
        
        if enabled_only:
            cursor.execute('SELECT * FROM tasks WHERE enabled = 1 ORDER BY priority DESC, created_at')
        else:
            cursor.execute('SELECT * FROM tasks ORDER BY priority DESC, created_at')
        
        rows = cursor.fetchall()
        return [Task.from_dict(dict(row)) for row in rows]
    
    # ========== 任务日志管理 ==========
    
    def add_task_log(self, log: TaskLog) -> int:
        """添加任务日志"""
        cursor = self.conn.cursor()
        data = log.to_dict()
        data.pop('id', None)
        
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        
        cursor.execute(
            f'INSERT INTO task_logs ({columns}) VALUES ({placeholders})',
            list(data.values())
        )
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_task_logs(self, task_id: int, limit: int = 100) -> List[TaskLog]:
        """获取任务日志"""
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT * FROM task_logs WHERE task_id = ? ORDER BY start_time DESC LIMIT ?',
            (task_id, limit)
        )
        
        rows = cursor.fetchall()
        return [TaskLog.from_dict(dict(row)) for row in rows]
    
    def cleanup_old_logs(self, days: int = 90) -> int:
        """清理旧日志（保留指定天数），返回删除的记录数"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor = self.conn.cursor()
        cursor.execute(
            'DELETE FROM task_logs WHERE start_time < ?',
            (cutoff_date.isoformat(),)
        )
        
        deleted_count = cursor.rowcount
        self.conn.commit()
        return deleted_count
    
    # ========== 默认脚本管理 ==========
    
    def add_default_script(self, script: DefaultScript) -> int:
        """添加默认脚本"""
        cursor = self.conn.cursor()
        data = script.to_dict()
        data.pop('id', None)
        
        # 检查表中有哪些列
        cursor.execute("PRAGMA table_info(default_scripts)")
        table_info = cursor.fetchall()
        available_columns = [col[1] for col in table_info]  # 列名在索引1
        
        # 过滤数据，只包含表中存在的列
        filtered_data = {}
        for key, value in data.items():
            # 处理列名映射：script_content -> content
            if key == 'script_content' and 'content' in available_columns and 'script_content' not in available_columns:
                filtered_data['content'] = value
            elif key in available_columns:
                filtered_data[key] = value
        
        if not filtered_data:
            raise ValueError("没有可用的列来插入数据")
        
        columns = ', '.join(filtered_data.keys())
        placeholders = ', '.join(['?'] * len(filtered_data))
        
        cursor.execute(
            f'INSERT INTO default_scripts ({columns}) VALUES ({placeholders})',
            list(filtered_data.values())
        )
        
        self.conn.commit()
        return cursor.lastrowid
    
    def update_default_script(self, script: DefaultScript) -> bool:
        """更新默认脚本"""
        if script.id is None:
            return False
        
        cursor = self.conn.cursor()
        data = script.to_dict()
        
        # 移除id
        script_id = data.pop('id')
        
        set_clause = ', '.join([f'{key} = ?' for key in data.keys()])
        
        cursor.execute(
            f'UPDATE default_scripts SET {set_clause} WHERE id = ?',
            list(data.values()) + [script_id]
        )
        
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_default_script(self, script_id: int) -> Optional[DefaultScript]:
        """获取默认脚本"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM default_scripts WHERE id = ?', (script_id,))
        row = cursor.fetchone()
        
        if row:
            return DefaultScript.from_dict(dict(row))
        return None
    
    def get_all_default_scripts(self) -> List[DefaultScript]:
        """获取所有默认脚本"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM default_scripts ORDER BY created_at')
        
        rows = cursor.fetchall()
        return [DefaultScript.from_dict(dict(row)) for row in rows]
    
    def delete_default_script(self, script_id: int) -> bool:
        """删除默认脚本"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM default_scripts WHERE id = ?', (script_id,))
        
        self.conn.commit()
        return cursor.rowcount > 0
    
    # 为测试兼容性添加别名
    def get_default_scripts(self) -> List[DefaultScript]:
        """获取所有默认脚本（get_all_default_scripts的别名）"""
        return self.get_all_default_scripts()
    
    # ========== 应用配置管理 ==========
    
    def set_config(self, key: str, value: Dict[str, Any]) -> bool:
        """设置配置，返回是否成功"""
        try:
            cursor = self.conn.cursor()
            
            # 先删除再插入（简化逻辑）
            cursor.execute('DELETE FROM app_config WHERE key = ?', (key,))
            
            config = AppConfig(key=key, value=value)
            data = config.to_dict()
            
            cursor.execute(
                'INSERT INTO app_config (key, value, updated_at) VALUES (?, ?, ?)',
                (data['key'], data['value'], data['updated_at'])
            )
            
            self.conn.commit()
            return True
        except Exception:
            return False
    
    def get_config(self, key: str, default: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """获取配置"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT value FROM app_config WHERE key = ?', (key,))
        row = cursor.fetchone()
        
        if row and row['value']:
            try:
                return json.loads(row['value'])
            except json.JSONDecodeError:
                # 如果JSON解析失败，返回默认值
                return default if default is not None else {}
        
        # 如果没有找到配置，返回None
        return None
    
    # ========== 工具方法 ==========
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __del__(self):
        self.close()