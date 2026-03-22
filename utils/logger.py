"""
日志管理器 - 统一的日志记录和管理
"""

import logging
import logging.handlers
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

from ..config import ConfigManager


class LogManager:
    """日志管理器"""
    
    def __init__(self):
        self.config = ConfigManager()
        self.loggers: Dict[str, logging.Logger] = {}
        self.handlers: Dict[str, logging.Handler] = {}
        
        # 初始化日志目录
        self._init_log_dir()
        
        # 初始化根日志器
        self._init_root_logger()
    
    def _init_log_dir(self):
        """初始化日志目录"""
        try:
            # 获取日志路径配置
            log_path = self.config.get('log_path', '')
            if not log_path:
                # 默认路径：应用数据目录下的logs文件夹
                app_data_dir = self.config.get_app_data_dir()
                log_path = os.path.join(app_data_dir, 'logs')
            
            # 创建日志目录
            os.makedirs(log_path, exist_ok=True)
            
            # 保存日志路径
            self.log_dir = log_path
            logging.info(f"日志目录: {self.log_dir}")
            
        except Exception as e:
            # 如果配置的路径不可用，使用临时目录
            import tempfile
            self.log_dir = os.path.join(tempfile.gettempdir(), 'WindowsTaskScheduler', 'logs')
            os.makedirs(self.log_dir, exist_ok=True)
            logging.warning(f"使用临时日志目录: {self.log_dir}, 原因: {e}")
    
    def _init_root_logger(self):
        """初始化根日志器"""
        try:
            # 获取日志配置
            log_level_name = self.config.get('log_level', 'INFO')
            log_file_size = self.config.get('log_file_size', 10)  # MB
            log_retention_days = self.config.get('log_retention_days', 90)
            
            # 设置日志级别
            log_level = getattr(logging, log_level_name.upper(), logging.INFO)
            
            # 配置根日志器
            root_logger = logging.getLogger()
            root_logger.setLevel(log_level)
            
            # 清除现有处理器
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
            
            # 创建控制台处理器
            console_handler = self._create_console_handler(log_level)
            root_logger.addHandler(console_handler)
            
            # 创建文件处理器
            file_handler = self._create_file_handler(log_level, log_file_size)
            root_logger.addHandler(file_handler)
            
            # 保存处理器
            self.handlers['console'] = console_handler
            self.handlers['file'] = file_handler
            
            # 清理旧日志文件
            self._cleanup_old_logs(log_retention_days)
            
            logging.info(f"日志系统初始化完成 - 级别: {log_level_name}, 目录: {self.log_dir}")
            
        except Exception as e:
            print(f"日志系统初始化失败: {e}")
            # 使用基本配置作为后备
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
    
    def _create_console_handler(self, log_level: int) -> logging.Handler:
        """创建控制台处理器"""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        return handler
    
    def _create_file_handler(self, log_level: int, max_size_mb: int) -> logging.Handler:
        """创建文件处理器"""
        # 生成日志文件名
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(self.log_dir, f'app_{today}.log')
        
        # 创建轮转文件处理器
        max_bytes = max_size_mb * 1024 * 1024  # 转换为字节
        backup_count = 5  # 保留5个备份文件
        
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        handler.setLevel(log_level)
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        return handler
    
    def _cleanup_old_logs(self, retention_days: int):
        """清理旧日志文件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            for file_path in Path(self.log_dir).glob('*.log*'):
                if file_path.is_file():
                    # 获取文件修改时间
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    if mtime < cutoff_date:
                        try:
                            file_path.unlink()
                            logging.debug(f"删除旧日志文件: {file_path.name}")
                        except Exception as e:
                            logging.warning(f"删除日志文件失败 {file_path.name}: {e}")
                            
        except Exception as e:
            logging.warning(f"清理旧日志失败: {e}")
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志器"""
        if name not in self.loggers:
            logger = logging.getLogger(name)
            self.loggers[name] = logger
        
        return self.loggers[name]
    
    def update_config(self):
        """更新日志配置"""
        try:
            # 重新初始化
            self._init_log_dir()
            
            # 重新配置根日志器
            root_logger = logging.getLogger()
            
            # 更新文件处理器
            if 'file' in self.handlers:
                root_logger.removeHandler(self.handlers['file'])
                self.handlers['file'].close()
            
            # 获取新配置
            log_level_name = self.config.get('log_level', 'INFO')
            log_file_size = self.config.get('log_file_size', 10)
            log_level = getattr(logging, log_level_name.upper(), logging.INFO)
            
            # 创建新的文件处理器
            new_file_handler = self._create_file_handler(log_level, log_file_size)
            root_logger.addHandler(new_file_handler)
            self.handlers['file'] = new_file_handler
            
            # 更新控制台处理器级别
            if 'console' in self.handlers:
                self.handlers['console'].setLevel(log_level)
            
            logging.info(f"日志配置已更新 - 级别: {log_level_name}")
            
        except Exception as e:
            logging.error(f"更新日志配置失败: {e}")
    
    def log_task_start(self, task_id: int, task_name: str):
        """记录任务开始"""
        logger = self.get_logger(f'task.{task_id}')
        logger.info(f"任务开始执行: {task_name}")
    
    def log_task_complete(self, task_id: int, task_name: str, success: bool, duration: float):
        """记录任务完成"""
        logger = self.get_logger(f'task.{task_id}')
        status = "成功" if success else "失败"
        logger.info(f"任务执行{status}: {task_name}, 耗时: {duration:.2f}秒")
    
    def log_task_error(self, task_id: int, task_name: str, error: str):
        """记录任务错误"""
        logger = self.get_logger(f'task.{task_id}')
        logger.error(f"任务执行错误: {task_name}, 错误: {error}")
    
    def log_task_output(self, task_id: int, task_name: str, output: str):
        """记录任务输出"""
        logger = self.get_logger(f'task.output.{task_id}')
        
        # 限制输出长度
        if len(output) > 1000:
            output = output[:1000] + "...[输出过长，已截断]"
        
        logger.debug(f"任务输出 [{task_name}]: {output}")
    
    def log_system_event(self, event_type: str, message: str, **kwargs):
        """记录系统事件"""
        logger = self.get_logger('system')
        
        if event_type == 'startup':
            logger.info(f"应用程序启动: {message}")
        elif event_type == 'shutdown':
            logger.info(f"应用程序关闭: {message}")
        elif event_type == 'error':
            logger.error(f"系统错误: {message}")
        elif event_type == 'warning':
            logger.warning(f"系统警告: {message}")
        else:
            logger.info(f"系统事件 [{event_type}]: {message}")
        
        # 记录额外参数
        if kwargs:
            logger.debug(f"事件详情: {kwargs}")
    
    def log_config_change(self, config_key: str, old_value: Any, new_value: Any):
        """记录配置变更"""
        logger = self.get_logger('config')
        logger.info(f"配置变更: {config_key} = {old_value} -> {new_value}")
    
    def log_user_action(self, action: str, details: str = "", user: str = "system"):
        """记录用户操作"""
        logger = self.get_logger('user')
        logger.info(f"用户操作 [{user}]: {action} - {details}")
    
    def get_log_file_path(self, date: Optional[str] = None) -> str:
        """获取日志文件路径"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        return os.path.join(self.log_dir, f'app_{date}.log')
    
    def get_log_files(self) -> list:
        """获取所有日志文件"""
        try:
            log_files = []
            for file_path in Path(self.log_dir).glob('*.log*'):
                if file_path.is_file():
                    log_files.append({
                        'name': file_path.name,
                        'path': str(file_path),
                        'size': file_path.stat().st_size,
                        'modified': datetime.fromtimestamp(file_path.stat().st_mtime)
                    })
            
            # 按修改时间排序（最新的在前）
            log_files.sort(key=lambda x: x['modified'], reverse=True)
            return log_files
            
        except Exception as e:
            logging.error(f"获取日志文件列表失败: {e}")
            return []
    
    def clear_logs(self, days: Optional[int] = None):
        """清理日志"""
        try:
            if days is None:
                # 清理所有日志文件
                for file_path in Path(self.log_dir).glob('*.log*'):
                    if file_path.is_file():
                        file_path.unlink()
                logging.info("已清理所有日志文件")
            else:
                # 按天数清理
                self._cleanup_old_logs(days)
                logging.info(f"已清理{days}天前的日志文件")
                
        except Exception as e:
            logging.error(f"清理日志失败: {e}")
            raise
    
    def export_logs(self, output_path: str, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """导出日志"""
        try:
            # 解析日期
            if start_date:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                start_dt = datetime.min
            
            if end_date:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            else:
                end_dt = datetime.now()
            
            # 收集符合条件的日志文件
            log_files = []
            for file_path in Path(self.log_dir).glob('*.log*'):
                if file_path.is_file():
                    # 从文件名提取日期
                    file_name = file_path.name
                    if file_name.startswith('app_') and file_name.endswith('.log'):
                        try:
                            date_str = file_name[4:-4]  # 移除'app_'和'.log'
                            file_dt = datetime.strptime(date_str, '%Y-%m-%d')
                            
                            if start_dt <= file_dt <= end_dt:
                                log_files.append(file_path)
                        except:
                            pass
            
            # 合并日志内容
            all_logs = []
            for file_path in sorted(log_files):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        all_logs.append(f"=== {file_path.name} ===\n{content}\n")
                except Exception as e:
                    logging.warning(f"读取日志文件失败 {file_path.name}: {e}")
            
            # 写入输出文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"日志导出时间: {datetime.now()}\n")
                f.write(f"导出范围: {start_date or '最早'} 到 {end_date or '最新'}\n")
                f.write("=" * 50 + "\n\n")
                f.write('\n'.join(all_logs))
            
            logging.info(f"日志已导出到: {output_path}")
            return True
            
        except Exception as e:
            logging.error(f"导出日志失败: {e}")
            return False
    
    def get_log_stats(self) -> Dict[str, Any]:
        """获取日志统计信息"""
        try:
            log_files = self.get_log_files()
            
            stats = {
                'total_files': len(log_files),
                'total_size': sum(f['size'] for f in log_files),
                'latest_file': log_files[0]['name'] if log_files else None,
                'oldest_file': log_files[-1]['name'] if log_files else None,
                'log_dir': self.log_dir,
                'log_level': self.config.get('log_level', 'INFO')
            }
            
            return stats
            
        except Exception as e:
            logging.error(f"获取日志统计失败: {e}")
            return {}
    
    def set_log_level(self, level_name: str):
        """设置日志级别"""
        try:
            level = getattr(logging, level_name.upper(), logging.INFO)
            
            # 更新所有处理器
            for handler in self.handlers.values():
                handler.setLevel(level)
            
            # 更新配置
            self.config.set('log_level', level_name)
            
            logging.info(f"日志级别已设置为: {level_name}")
            
        except Exception as e:
            logging.error(f"设置日志级别失败: {e}")


# 全局日志管理器实例
_log_manager: Optional[LogManager] = None


def get_log_manager() -> LogManager:
    """获取全局日志管理器"""
    global _log_manager
    
    if _log_manager is None:
        _log_manager = LogManager()
    
    return _log_manager


def get_logger(name: str) -> logging.Logger:
    """获取日志器（快捷方式）"""
    return get_log_manager().get_logger(name)