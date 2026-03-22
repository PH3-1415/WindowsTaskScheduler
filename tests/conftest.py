"""
Pytest配置和共享fixtures
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_db_path():
    """临时数据库路径"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    yield db_path
    
    # 清理临时文件
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def temp_config_dir():
    """临时配置目录"""
    temp_dir = tempfile.mkdtemp(prefix='task_scheduler_test_')
    
    yield temp_dir
    
    # 清理临时目录
    import shutil
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def sample_task_data():
    """示例任务数据"""
    return {
        'name': '测试任务',
        'description': '这是一个测试任务',
        'command': 'echo "Hello, World!"',
        'working_dir': None,
        'schedule_type': 'daily',
        'schedule_config': '{"time": "12:00"}',
        'condition': None,
        'enabled': True,
        'priority': 0
    }


@pytest.fixture
def sample_script_data():
    """示例脚本数据"""
    return {
        'name': '测试脚本',
        'description': '这是一个测试脚本',
        'content': 'print("Hello from default script")',
        'enabled': True
    }


@pytest.fixture
def mock_datetime():
    """模拟datetime"""
    from unittest.mock import Mock
    from datetime import datetime
    
    mock_dt = Mock(spec=datetime)
    mock_dt.now.return_value = datetime(2026, 3, 22, 12, 0, 0)
    mock_dt.strftime = datetime.strftime
    
    return mock_dt


@pytest.fixture
def mock_subprocess():
    """模拟subprocess"""
    from unittest.mock import Mock, MagicMock
    
    mock_process = Mock()
    mock_process.returncode = 0
    mock_process.stdout = MagicMock()
    mock_process.stdout.readline.side_effect = [
        b'Line 1\n',
        b'Line 2\n',
        b''  # 空字符串表示结束
    ]
    mock_process.poll.return_value = 0
    
    return mock_process