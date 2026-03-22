"""
单元测试基类
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path


class BaseTestCase(unittest.TestCase):
    """测试基类"""
    
    @classmethod
    def setUpClass(cls):
        """类级别的设置"""
        # 添加项目根目录到Python路径
        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))
    
    def setUp(self):
        """测试前的设置"""
        # 创建临时工作目录
        self.temp_dir = tempfile.mkdtemp(prefix='test_')
        
        # 设置环境变量
        os.environ['TEST_MODE'] = '1'
        
        # 重置导入的模块（如果需要）
        self._clear_imports()
    
    def tearDown(self):
        """测试后的清理"""
        # 清理临时目录
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
        # 清理环境变量
        if 'TEST_MODE' in os.environ:
            del os.environ['TEST_MODE']
    
    def _clear_imports(self):
        """清除导入的模块"""
        # 这里可以添加需要重新导入的模块
        pass
    
    def assertFileExists(self, filepath):
        """断言文件存在"""
        self.assertTrue(os.path.exists(filepath), f"文件不存在: {filepath}")
    
    def assertFileNotExists(self, filepath):
        """断言文件不存在"""
        self.assertFalse(os.path.exists(filepath), f"文件存在但不应存在: {filepath}")
    
    def assertDirectoryExists(self, dirpath):
        """断言目录存在"""
        self.assertTrue(os.path.isdir(dirpath), f"目录不存在: {dirpath}")
    
    def assertIsValidJson(self, text):
        """断言文本是有效的JSON"""
        import json
        try:
            json.loads(text)
        except json.JSONDecodeError as e:
            self.fail(f"不是有效的JSON: {e}")
    
    def assertIsValidSqlite(self, db_path):
        """断言是有效的SQLite数据库"""
        import sqlite3
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()
            
            self.assertTrue(len(tables) > 0, "数据库中没有表")
        except sqlite3.Error as e:
            self.fail(f"不是有效的SQLite数据库: {e}")
    
    def create_temp_file(self, content: str, suffix: str = '.txt') -> str:
        """创建临时文件"""
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
            f.write(content)
            return f.name
    
    def create_temp_db(self) -> str:
        """创建临时数据库"""
        import sqlite3
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        # 创建基本的表结构
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建tasks表
        cursor.execute('''
            CREATE TABLE tasks (
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
        
        # 创建task_logs表
        cursor.execute('''
            CREATE TABLE task_logs (
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
        
        # 创建default_scripts表
        cursor.execute('''
            CREATE TABLE default_scripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                script_content TEXT NOT NULL,
                output_config TEXT DEFAULT '{}',
                last_run TIMESTAMP,
                last_output TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建app_config表
        cursor.execute('''
            CREATE TABLE app_config (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        return db_path