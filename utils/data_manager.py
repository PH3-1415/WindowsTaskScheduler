"""
数据管理器 - 任务配置的导入导出和备份恢复
"""

import json
import logging
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import sqlite3

from ..database.models import Task, TaskLog, DefaultScript, AppConfig
from ..database.db_manager import DatabaseManager
from ..config import ConfigManager


class DataManager:
    """数据管理器"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.config = ConfigManager()
        self.logger = logging.getLogger(__name__)
    
    def export_tasks(self, filepath: str, include_logs: bool = False) -> bool:
        """导出任务配置"""
        try:
            # 获取所有任务
            tasks = self.db.get_all_tasks()
            
            # 构建导出数据
            export_data = {
                'version': '1.0',
                'export_time': datetime.now().isoformat(),
                'app_name': 'Windows定时任务管理器',
                'tasks': []
            }
            
            for task in tasks:
                task_dict = task.to_dict()
                
                # 如果包含日志，获取任务日志
                if include_logs:
                    logs = self.db.get_task_logs(task.id, limit=100)
                    task_dict['logs'] = [log.to_dict() for log in logs]
                
                export_data['tasks'].append(task_dict)
            
            # 写入文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"已导出 {len(tasks)} 个任务到: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出任务失败: {e}")
            return False
    
    def import_tasks(self, filepath: str, mode: str = 'merge') -> Dict[str, Any]:
        """导入任务配置"""
        result = {
            'total': 0,
            'imported': 0,
            'skipped': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            # 读取文件
            with open(filepath, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # 验证数据格式
            if 'tasks' not in import_data:
                result['errors'].append("文件格式错误：缺少tasks字段")
                return result
            
            tasks_data = import_data['tasks']
            result['total'] = len(tasks_data)
            
            # 获取现有任务（用于去重）
            existing_tasks = self.db.get_all_tasks()
            existing_names = {task.name for task in existing_tasks}
            existing_ids = {task.id for task in existing_tasks}
            
            for task_data in tasks_data:
                try:
                    # 验证任务数据
                    if 'name' not in task_data or 'command' not in task_data:
                        result['warnings'].append(f"跳过无效任务数据: {task_data}")
                        result['skipped'] += 1
                        continue
                    
                    task_name = task_data['name']
                    
                    # 检查是否已存在
                    if mode == 'skip_existing' and task_name in existing_names:
                        result['warnings'].append(f"跳过已存在的任务: {task_name}")
                        result['skipped'] += 1
                        continue
                    
                    # 创建任务对象
                    task = Task.from_dict(task_data)
                    
                    # 如果是更新模式且任务已存在
                    if mode == 'update' and task_name in existing_names:
                        # 查找现有任务ID
                        existing_task = next((t for t in existing_tasks if t.name == task_name), None)
                        if existing_task:
                            task.id = existing_task.id
                            self.db.update_task(task)
                            result['imported'] += 1
                            self.logger.info(f"更新任务: {task_name}")
                        else:
                            self.db.add_task(task)
                            result['imported'] += 1
                            self.logger.info(f"导入新任务: {task_name}")
                    
                    # 如果是合并模式
                    elif mode == 'merge':
                        if task_name in existing_names:
                            # 重命名以避免冲突
                            counter = 1
                            new_name = f"{task_name}_导入{counter}"
                            while new_name in existing_names:
                                counter += 1
                                new_name = f"{task_name}_导入{counter}"
                            
                            task.name = new_name
                            result['warnings'].append(f"重命名重复任务: {task_name} -> {new_name}")
                        
                        self.db.add_task(task)
                        result['imported'] += 1
                        self.logger.info(f"导入任务: {task.name}")
                    
                    # 替换模式（先删除所有现有任务）
                    elif mode == 'replace':
                        # 在替换模式下，我们会在导入所有任务后删除现有任务
                        pass
                    
                    else:
                        # 默认添加模式
                        self.db.add_task(task)
                        result['imported'] += 1
                        self.logger.info(f"导入任务: {task_name}")
                
                except Exception as e:
                    error_msg = f"导入任务失败 '{task_data.get('name', '未知')}': {str(e)}"
                    result['errors'].append(error_msg)
                    result['skipped'] += 1
                    self.logger.error(error_msg)
            
            # 如果是替换模式，删除所有现有任务
            if mode == 'replace':
                for task in existing_tasks:
                    self.db.delete_task(task.id)
                self.logger.info(f"已删除 {len(existing_tasks)} 个现有任务")
            
            self.logger.info(f"导入完成: 总计{result['total']}, 成功{result['imported']}, 跳过{result['skipped']}")
            return result
            
        except Exception as e:
            error_msg = f"导入任务文件失败: {str(e)}"
            result['errors'].append(error_msg)
            self.logger.error(error_msg)
            return result
    
    def backup_all_data(self, backup_dir: str) -> str:
        """备份所有数据"""
        try:
            # 创建备份目录
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"task_scheduler_backup_{timestamp}"
            backup_path = os.path.join(backup_dir, backup_name)
            os.makedirs(backup_path, exist_ok=True)
            
            # 备份数据库
            db_path = self.db.get_db_path()
            if os.path.exists(db_path):
                backup_db_path = os.path.join(backup_path, 'database.db')
                shutil.copy2(db_path, backup_db_path)
            
            # 备份配置文件
            config_file = self.config.get_config_file_path()
            if os.path.exists(config_file):
                backup_config_path = os.path.join(backup_path, 'config.json')
                shutil.copy2(config_file, backup_config_path)
            
            # 备份日志目录
            log_dir = self.config.get('log_path', '')
            if log_dir and os.path.exists(log_dir):
                backup_log_path = os.path.join(backup_path, 'logs')
                shutil.copytree(log_dir, backup_log_path, dirs_exist_ok=True)
            
            # 创建备份信息文件
            backup_info = {
                'backup_time': datetime.now().isoformat(),
                'app_version': '1.0.0',
                'backup_type': 'full',
                'files': {
                    'database': os.path.exists(db_path),
                    'config': os.path.exists(config_file),
                    'logs': log_dir and os.path.exists(log_dir)
                }
            }
            
            info_file = os.path.join(backup_path, 'backup_info.json')
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, ensure_ascii=False, indent=2)
            
            # 压缩备份
            zip_path = f"{backup_path}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(backup_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, backup_path)
                        zipf.write(file_path, arcname)
            
            # 删除临时目录
            shutil.rmtree(backup_path)
            
            self.logger.info(f"数据备份完成: {zip_path}")
            return zip_path
            
        except Exception as e:
            self.logger.error(f"数据备份失败: {e}")
            raise
    
    def restore_backup(self, backup_file: str) -> bool:
        """从备份恢复数据"""
        try:
            # 验证备份文件
            if not os.path.exists(backup_file):
                self.logger.error(f"备份文件不存在: {backup_file}")
                return False
            
            # 创建临时目录
            import tempfile
            temp_dir = tempfile.mkdtemp()
            
            try:
                # 解压备份文件
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                # 读取备份信息
                info_file = os.path.join(temp_dir, 'backup_info.json')
                if not os.path.exists(info_file):
                    self.logger.error("备份信息文件不存在")
                    return False
                
                with open(info_file, 'r', encoding='utf-8') as f:
                    backup_info = json.load(f)
                
                # 恢复数据库
                backup_db = os.path.join(temp_dir, 'database.db')
                if os.path.exists(backup_db):
                    # 关闭现有数据库连接
                    self.db.close()
                    
                    # 备份当前数据库
                    current_db = self.db.get_db_path()
                    if os.path.exists(current_db):
                        backup_current = f"{current_db}.backup"
                        shutil.copy2(current_db, backup_current)
                    
                    # 恢复数据库
                    shutil.copy2(backup_db, current_db)
                    
                    # 重新初始化数据库
                    self.db.initialize()
                    self.logger.info("数据库恢复完成")
                
                # 恢复配置文件
                backup_config = os.path.join(temp_dir, 'config.json')
                if os.path.exists(backup_config):
                    current_config = self.config.get_config_file_path()
                    shutil.copy2(backup_config, current_config)
                    self.config.reload()
                    self.logger.info("配置文件恢复完成")
                
                # 恢复日志
                backup_logs = os.path.join(temp_dir, 'logs')
                if os.path.exists(backup_logs):
                    log_dir = self.config.get('log_path', '')
                    if log_dir:
                        if os.path.exists(log_dir):
                            shutil.rmtree(log_dir)
                        shutil.copytree(backup_logs, log_dir)
                        self.logger.info("日志文件恢复完成")
                
                self.logger.info("数据恢复完成")
                return True
                
            finally:
                # 清理临时目录
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            self.logger.error(f"数据恢复失败: {e}")
            return False
    
    def export_to_csv(self, filepath: str) -> bool:
        """导出任务到CSV文件"""
        try:
            tasks = self.db.get_all_tasks()
            
            # CSV头部
            csv_lines = []
            csv_lines.append("任务ID,任务名称,任务描述,执行命令,调度类型,调度配置,执行条件,是否启用,创建时间,更新时间")
            
            for task in tasks:
                # 转义CSV特殊字符
                def escape_csv(value):
                    if value is None:
                        return ""
                    value_str = str(value)
                    if ',' in value_str or '"' in value_str or '\n' in value_str:
                        return f'"{value_str.replace('"', '""')}"'
                    return value_str
                
                # 构建行数据
                row = [
                    task.id,
                    escape_csv(task.name),
                    escape_csv(task.description),
                    escape_csv(task.command),
                    task.schedule_type,
                    escape_csv(json.dumps(task.schedule_config, ensure_ascii=False)),
                    escape_csv(task.condition),
                    "是" if task.enabled else "否",
                    task.created_at.isoformat() if task.created_at else "",
                    task.updated_at.isoformat() if task.updated_at else ""
                ]
                
                csv_lines.append(','.join(map(str, row)))
            
            # 写入文件
            with open(filepath, 'w', encoding='utf-8-sig') as f:  # utf-8-sig for Excel compatibility
                f.write('\n'.join(csv_lines))
            
            self.logger.info(f"已导出 {len(tasks)} 个任务到CSV: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出CSV失败: {e}")
            return False
    
    def import_from_csv(self, filepath: str) -> Dict[str, Any]:
        """从CSV文件导入任务"""
        result = {
            'total': 0,
            'imported': 0,
            'skipped': 0,
            'errors': []
        }
        
        try:
            import csv
            
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    result['total'] += 1
                    
                    try:
                        # 解析行数据
                        task_data = {
                            'name': row.get('任务名称', '').strip(),
                            'description': row.get('任务描述', '').strip(),
                            'command': row.get('执行命令', '').strip(),
                            'schedule_type': row.get('调度类型', 'daily').strip(),
                            'condition': row.get('执行条件', '').strip(),
                            'enabled': row.get('是否启用', '是').strip().lower() in ['是', 'true', 'yes', '1']
                        }
                        
                        # 解析调度配置
                        schedule_config_str = row.get('调度配置', '{}')
                        try:
                            task_data['schedule_config'] = json.loads(schedule_config_str)
                        except:
                            task_data['schedule_config'] = {}
                        
                        # 验证必要字段
                        if not task_data['name'] or not task_data['command']:
                            result['errors'].append(f"第{result['total']}行: 缺少必要字段")
                            result['skipped'] += 1
                            continue
                        
                        # 创建任务
                        task = Task.from_dict(task_data)
                        self.db.add_task(task)
                        result['imported'] += 1
                        
                    except Exception as e:
                        error_msg = f"第{result['total']}行导入失败: {str(e)}"
                        result['errors'].append(error_msg)
                        result['skipped'] += 1
                        self.logger.error(error_msg)
            
            self.logger.info(f"CSV导入完成: 总计{result['total']}, 成功{result['imported']}, 跳过{result['skipped']}")
            return result
            
        except Exception as e:
            error_msg = f"导入CSV文件失败: {str(e)}"
            result['errors'].append(error_msg)
            self.logger.error(error_msg)
            return result
    
    def get_data_stats(self) -> Dict[str, Any]:
        """获取数据统计"""
        try:
            tasks = self.db.get_all_tasks()
            logs = self.db.get_all_logs(limit=1000)
            
            # 按状态统计任务
            enabled_count = sum(1 for task in tasks if task.enabled)
            disabled_count = len(tasks) - enabled_count
            
            # 按类型统计
            type_stats = {}
            for task in tasks:
                task_type = task.schedule_type
                type_stats[task_type] = type_stats.get(task_type, 0) + 1
            
            # 日志统计
            log_stats = {
                'total': len(logs),
                'success': sum(1 for log in logs if log.status == 'success'),
                'failed': sum(1 for log in logs if log.status == 'failed'),
                'running': sum(1 for log in logs if log.status == 'running'),
                'recent_24h': 0  # 需要根据时间计算
            }
            
            # 计算24小时内的日志
            twenty_four_hours_ago = datetime.now().timestamp() - 24 * 3600
            for log in logs:
                if log.created_at and log.created_at.timestamp() > twenty_four_hours_ago:
                    log_stats['recent_24h'] += 1
            
            stats = {
                'tasks': {
                    'total': len(tasks),
                    'enabled': enabled_count,
                    'disabled': disabled_count,
                    'by_type': type_stats
                },
                'logs': log_stats,
                'database': {
                    'path': self.db.get_db_path(),
                    'size': os.path.getsize(self.db.get_db_path()) if os.path.exists(self.db.get_db_path()) else 0
                },
                'last_backup': self._get_last_backup_time()
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"获取数据统计失败: {e}")
            return {}
    
    def _get_last_backup_time(self) -> Optional[str]:
        """获取最后备份时间"""
        try:
            backup_dir = self.config.get('backup_dir', '')
            if not backup_dir or not os.path.exists(backup_dir):
                return None
            
            backup_files = list(Path(backup_dir).glob('*.zip'))
            if not backup_files:
                return None
            
            # 获取最新的备份文件
            latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
            mtime = datetime.fromtimestamp(latest_backup.stat().st_mtime)
            return mtime.strftime('%Y-%m-%d %H:%M:%S')
            
        except:
            return None
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, int]:
        """清理旧数据"""
        result = {
            'logs_deleted': 0,
            'backups_deleted': 0,
            'errors': []
        }
        
        try:
            # 清理旧日志
            cutoff_date = datetime.now().timestamp() - days_to_keep * 24 * 3600
            
            # 获取所有日志
            all_logs = self.db.get_all_logs(limit=10000)  # 限制数量避免内存问题
            
            for log in all_logs:
                if log.created_at and log.created_at.timestamp() < cutoff_date:
                    try:
                        self.db.delete_log(log.id)
                        result['logs_deleted'] += 1
                    except Exception as e:
                        result['errors'].append(f"删除日志 {log.id} 失败: {str(e)}")
            
            # 清理旧备份
            backup_dir = self.config.get('backup_dir', '')
            if backup_dir and os.path.exists(backup_dir):
                for backup_file in Path(backup_dir).glob('*.zip'):
                    if backup_file.stat().st_mtime < cutoff_date:
                        try:
                            backup_file.unlink()
                            result['backups_deleted'] += 1
                        except Exception as e:
                            result['errors'].append(f"删除备份 {backup_file.name} 失败: {str(e)}")
            
            self.logger.info(f"数据清理完成: 删除{result['logs_deleted']}条日志, {result['backups_deleted']}个备份")
            return result
            
        except Exception as e:
            error_msg = f"数据清理失败: {str(e)}"
            result['errors'].append(error_msg)
            self.logger.error(error_msg)
            return result
    
    def validate_data_integrity(self) -> Dict[str, Any]:
        """验证数据完整性"""
        result = {
            'valid': True,
            'issues': [],
            'warnings': [],
            'stats': {}
        }
        
        try:
            # 检查数据库连接
            try:
                self.db.execute_query("SELECT 1")
                result['stats']['db_connection'] = '正常'
            except Exception as e:
                result['valid'] = False
                result['issues'].append(f"数据库连接失败: {str(e)}")
                return result
            
            # 检查表结构
            tables = ['tasks', 'task_logs', 'default_scripts', 'app_config']
            for table in tables:
                try:
                    self.db.execute_query(f"SELECT COUNT(*) FROM {table}")
                    result['stats'][f'table_{table}'] = '存在'
                except Exception as e:
                    result['valid'] = False
                    result['issues'].append(f"表 {table} 不存在或损坏: {str(e)}")
            
            # 检查任务数据
            tasks = self.db.get_all_tasks()
            result['stats']['total_tasks'] = len(tasks)
            
            for task in tasks:
                # 检查必要字段
                if not task.name or not task.command:
                    result['warnings'].append(f"任务 {task.id} 缺少必要字段")
                
                # 检查调度配置
                try:
                    json.dumps(task.schedule_config)
                except:
                    result['issues'].append(f"任务 {task.id} 调度配置格式错误")
                
                # 检查命令长度
                if len(task.command) > 10000:
                    result['warnings'].append(f"任务 {task.id} 命令过长 ({len(task.command)}字符)")
            
            # 检查日志数据
            logs = self.db.get_all_logs(limit=100)
            result['stats']['recent_logs'] = len(logs)
            
            # 检查配置文件
            config_file = self.config.get_config_file_path()
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        json.load(f)
                    result['stats']['config_file'] = '正常'
                except Exception as e:
                    result['warnings'].append(f"配置文件格式错误: {str(e)}")
            else:
                result['warnings'].append("配置文件不存在")
            
            self.logger.info(f"数据完整性检查完成: {'通过' if result['valid'] else '失败'}")
            return result
            
        except Exception as e:
            result['valid'] = False
            result['issues'].append(f"完整性检查失败: {str(e)}")
            self.logger.error(f"数据完整性检查失败: {e}")
            return result
    
    def repair_database(self) -> Dict[str, Any]:
        """修复数据库"""
        result = {
            'repaired': False,
            'actions': [],
            'errors': []
        }
        
        try:
            # 备份当前数据库
            db_path = self.db.get_db_path()
            if os.path.exists(db_path):
                backup_path = f"{db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(db_path, backup_path)
                result['actions'].append(f"创建数据库备份: {backup_path}")
            
            # 关闭现有连接
            self.db.close()
            
            # 尝试重新初始化数据库
            self.db.initialize()
            
            # 验证修复结果
            integrity_check = self.validate_data_integrity()
            
            if integrity_check['valid']:
                result['repaired'] = True
                result['actions'].append("数据库修复成功")
            else:
                result['errors'].extend(integrity_check['issues'])
                result['errors'].append("数据库修复失败")
            
            self.logger.info(f"数据库修复完成: {'成功' if result['repaired'] else '失败'}")
            return result
            
        except Exception as e:
            result['errors'].append(f"数据库修复失败: {str(e)}")
            self.logger.error(f"数据库修复失败: {e}")
            return result
    
    def migrate_data(self, old_version: str, new_version: str) -> bool:
        """数据迁移"""
        try:
            self.logger.info(f"开始数据迁移: {old_version} -> {new_version}")
            
            # 这里可以根据版本号实现具体的迁移逻辑
            # 例如：添加新字段、修改表结构等
            
            if old_version == '1.0.0' and new_version == '1.1.0':
                # 示例：添加新字段
                self.db.execute_query("""
                    ALTER TABLE tasks ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 0
                """)
                self.logger.info("添加priority字段")
            
            # 更新数据库版本
            self.db.execute_query("""
                INSERT OR REPLACE INTO app_config (key, value) 
                VALUES ('db_version', ?)
            """, (new_version,))
            
            self.logger.info(f"数据迁移完成: {old_version} -> {new_version}")
            return True
            
        except Exception as e:
            self.logger.error(f"数据迁移失败: {e}")
            return False


# 全局数据管理器实例
_data_manager: Optional[DataManager] = None


def get_data_manager() -> DataManager:
    """获取全局数据管理器"""
    global _data_manager
    
    if _data_manager is None:
        _data_manager = DataManager()
    
    return _data_manager


# 快捷函数
def export_tasks(filepath: str, include_logs: bool = False) -> bool:
    """导出任务（快捷方式）"""
    return get_data_manager().export_tasks(filepath, include_logs)


def import_tasks(filepath: str, mode: str = 'merge') -> Dict[str, Any]:
    """导入任务（快捷方式）"""
    return get_data_manager().import_tasks(filepath, mode)


def backup_all_data(backup_dir: str) -> str:
    """备份所有数据（快捷方式）"""
    return get_data_manager().backup_all_data(backup_dir)


def restore_backup(backup_file: str) -> bool:
    """从备份恢复（快捷方式）"""
    return get_data_manager().restore_backup(backup_file)