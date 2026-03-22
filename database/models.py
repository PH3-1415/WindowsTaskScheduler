"""
数据库模型定义
"""

import json
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Any


@dataclass
class Task:
    """任务定义"""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    command: str = ""
    working_dir: str = ""
    schedule_type: str = "daily"  # daily, weekly, monthly
    schedule_config: Dict[str, Any] = field(default_factory=dict)
    condition: str = ""
    enabled: bool = True
    priority: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 处理datetime对象
        for key in ['created_at', 'updated_at']:
            if data[key] and isinstance(data[key], datetime):
                data[key] = data[key].isoformat()
        # 序列化schedule_config
        if data['schedule_config']:
            data['schedule_config'] = json.dumps(data['schedule_config'])
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """从字典创建对象"""
        # 反序列化schedule_config
        if 'schedule_config' in data and data['schedule_config']:
            if isinstance(data['schedule_config'], str):
                data['schedule_config'] = json.loads(data['schedule_config'])
        
        # 处理datetime字符串
        for key in ['created_at', 'updated_at']:
            if key in data and data[key]:
                if isinstance(data[key], str):
                    data[key] = datetime.fromisoformat(data[key].replace('Z', '+00:00'))
        
        return cls(**data)


@dataclass
class TaskLog:
    """任务日志"""
    id: Optional[int] = None
    task_id: int = 0
    status: str = ""  # success, failed, running
    output: str = ""
    exit_code: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 处理datetime对象
        for key in ['start_time', 'end_time']:
            if data[key] and isinstance(data[key], datetime):
                data[key] = data[key].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskLog':
        """从字典创建对象"""
        # 处理datetime字符串
        for key in ['start_time', 'end_time']:
            if key in data and data[key]:
                if isinstance(data[key], str):
                    data[key] = datetime.fromisoformat(data[key].replace('Z', '+00:00'))
        
        return cls(**data)


@dataclass
class DefaultScript:
    """默认脚本"""
    id: Optional[int] = None
    name: str = ""
    script_content: str = ""
    output_config: Dict[str, Any] = field(default_factory=dict)
    last_run: Optional[datetime] = None
    last_output: str = ""
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 处理datetime对象
        for key in ['last_run', 'created_at']:
            if data[key] and isinstance(data[key], datetime):
                data[key] = data[key].isoformat()
        # 序列化output_config
        if 'output_config' in data:
            if data['output_config']:
                data['output_config'] = json.dumps(data['output_config'])
            else:
                data['output_config'] = '{}'  # 空字典序列化为'{}'
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DefaultScript':
        """从字典创建对象"""
        # 反序列化output_config
        if 'output_config' in data and data['output_config']:
            if isinstance(data['output_config'], str):
                data['output_config'] = json.loads(data['output_config'])
        
        # 处理datetime字符串
        for key in ['last_run', 'created_at']:
            if key in data and data[key]:
                if isinstance(data[key], str):
                    data[key] = datetime.fromisoformat(data[key].replace('Z', '+00:00'))
        
        return cls(**data)


@dataclass
class AppConfig:
    """应用配置"""
    key: str = ""
    value: Dict[str, Any] = field(default_factory=dict)
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 处理datetime对象
        if data['updated_at'] and isinstance(data['updated_at'], datetime):
            data['updated_at'] = data['updated_at'].isoformat()
        # 序列化value
        if data['value']:
            data['value'] = json.dumps(data['value'])
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """从字典创建对象"""
        # 反序列化value
        if 'value' in data and data['value']:
            if isinstance(data['value'], str):
                data['value'] = json.loads(data['value'])
        
        # 处理datetime字符串
        if 'updated_at' in data and data['updated_at']:
            if isinstance(data['updated_at'], str):
                data['updated_at'] = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
        
        return cls(**data)