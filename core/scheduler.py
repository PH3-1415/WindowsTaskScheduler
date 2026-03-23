"""
任务调度器
"""

import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Callable
from queue import Queue, Empty

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

from database.models import Task
from database.db_manager import DatabaseManager
from core.task_executor import TaskExecutor
from core.condition_evaluator import ConditionEvaluator


class TaskScheduler:
    """任务调度器 - 负责任务的定时调度和执行"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db = DatabaseManager()
        
        # 任务执行状态
        self.running_tasks: Dict[int, threading.Thread] = {}  # 正在运行的任务
        self.task_queue = Queue()  # 任务队列（用于串行执行）
        self.is_running = False
        self.current_task_id: Optional[int] = None
        
        # APScheduler实例
        self.scheduler = self._create_scheduler()
        
        # 任务执行器
        self.executor = TaskExecutor()
        
        # 条件评估器
        self.condition_evaluator = ConditionEvaluator()
        
        # 锁
        self._lock = threading.RLock()
        
        # 回调函数
        self.on_task_started: Optional[Callable] = None
        self.on_task_completed: Optional[Callable] = None
        self.on_task_failed: Optional[Callable] = None
        self.on_output: Optional[Callable] = None
    
    def _create_scheduler(self) -> BackgroundScheduler:
        """创建APScheduler实例"""
        # 配置jobstore
        jobstores = {
            'default': SQLAlchemyJobStore(
                url='sqlite:///jobs.db',
                engine_options={'connect_args': {'check_same_thread': False}}
            )
        }
        
        # 配置executor
        executors = {
            'default': ThreadPoolExecutor(1)  # 只使用1个线程，确保串行
        }
        
        # 创建调度器
        scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            timezone='Asia/Shanghai'
        )
        
        return scheduler
    
    def start(self):
        """启动调度器"""
        with self._lock:
            if self.is_running:
                self.logger.warning("调度器已经在运行中")
                return
            
            try:
                # 启动APScheduler
                self.scheduler.start()
                
                # 加载所有启用的任务
                self._load_tasks()
                
                # 启动队列处理器
                self._start_queue_processor()
                
                self.is_running = True
                self.logger.info("任务调度器已启动")
                
            except Exception as e:
                self.logger.error(f"启动调度器失败: {e}")
                raise
    
    def stop(self):
        """停止调度器"""
        with self._lock:
            if not self.is_running:
                return
            
            self.is_running = False
            
            # 停止APScheduler
            if self.scheduler.running:
                self.scheduler.shutdown(wait=False)
            
            # 停止所有运行中的任务
            self._stop_all_tasks()
            
            # 清空队列
            while not self.task_queue.empty():
                try:
                    self.task_queue.get_nowait()
                except Empty:
                    break
            
            self.logger.info("任务调度器已停止")
    
    def _load_tasks(self):
        """加载所有启用的任务"""
        tasks = self.db.get_all_tasks(enabled_only=True)
        
        for task in tasks:
            try:
                self._add_task_to_scheduler(task)
                self.logger.debug(f"已加载任务: {task.name} (ID: {task.id})")
            except Exception as e:
                self.logger.error(f"加载任务失败 {task.name}: {e}")
    
    def _add_task_to_scheduler(self, task: Task):
        """添加任务到调度器"""
        # 创建触发器
        trigger = self._create_trigger(task)
        
        if not trigger:
            self.logger.warning(f"任务 {task.name} 的调度配置无效")
            return
        
        # 添加任务到APScheduler
        self.scheduler.add_job(
            func=self._schedule_task_execution,
            trigger=trigger,
            args=[task.id],
            id=f'task_{task.id}',
            name=task.name,
            replace_existing=True,
            misfire_grace_time=60,  # 允许60秒的误差
            coalesce=True  # 合并多次触发
        )
    
    def _create_trigger(self, task: Task) -> Optional[CronTrigger]:
        """根据任务配置创建触发器"""
        config = task.schedule_config
        
        if task.schedule_type == 'daily':
            # 每天执行
            hour = config.get('hour', 0)
            minute = config.get('minute', 0)
            
            return CronTrigger(
                hour=hour,
                minute=minute,
                timezone='Asia/Shanghai'
            )
        
        elif task.schedule_type == 'weekly':
            # 每周执行
            days = config.get('days', [])
            hour = config.get('hour', 0)
            minute = config.get('minute', 0)
            
            if not days:
                return None
            
            # 转换星期几（APScheduler: 0=周日, 1=周一, ..., 6=周六）
            # 我们的约定：0=周一, 6=周日
            aps_days = [(d + 1) % 7 for d in days]  # 转换为APScheduler格式
            
            return CronTrigger(
                day_of_week=','.join(str(d) for d in aps_days),
                hour=hour,
                minute=minute,
                timezone='Asia/Shanghai'
            )
        
        elif task.schedule_type == 'monthly':
            # 每月执行
            day = config.get('day', 1)
            hour = config.get('hour', 0)
            minute = config.get('minute', 0)
            
            return CronTrigger(
                day=day,
                hour=hour,
                minute=minute,
                timezone='Asia/Shanghai'
            )
        
        return None
    
    def _schedule_task_execution(self, task_id: int):
        """调度任务执行（由APScheduler调用）"""
        with self._lock:
            # 检查是否有任务正在运行
            if self.current_task_id is not None:
                # 有任务正在运行，加入队列
                self.task_queue.put(task_id)
                self.logger.info(f"任务 {task_id} 已加入队列（当前有任务运行中）")
            else:
                # 立即执行
                self._execute_task(task_id)
    
    def _start_queue_processor(self):
        """启动队列处理器"""
        def process_queue():
            while self.is_running:
                try:
                    # 等待队列中的任务
                    task_id = self.task_queue.get(timeout=1)
                    
                    with self._lock:
                        if self.current_task_id is None:
                            # 没有任务运行，执行队列中的任务
                            self._execute_task(task_id)
                        else:
                            # 还有任务在运行，重新放回队列
                            self.task_queue.put(task_id)
                            time.sleep(0.1)  # 短暂等待
                    
                except Empty:
                    # 队列为空，继续等待
                    continue
                except Exception as e:
                    self.logger.error(f"队列处理器错误: {e}")
                    time.sleep(1)
        
        # 启动队列处理线程
        queue_thread = threading.Thread(target=process_queue, daemon=True)
        queue_thread.start()
    
    def _execute_task(self, task_id: int):
        """执行任务"""
        try:
            # 获取任务信息
            task = self.db.get_task(task_id)
            if not task or not task.enabled:
                self.logger.warning(f"任务 {task_id} 不存在或已禁用")
                return
            
            # 检查执行条件
            if task.condition:
                if not self.condition_evaluator.evaluate(task.condition):
                    self.logger.info(f"任务 {task.name} 条件不满足，跳过执行")
                    return
            
            # 标记任务开始
            self.current_task_id = task_id
            self._on_task_started(task)
            
            # 创建任务日志
            log_id = self._create_task_log(task_id, 'running')
            
            # 执行任务
            exit_code, output = self.executor.execute(
                command=task.command,
                working_dir=task.working_dir,
                on_output=self._handle_task_output
            )
            
            # 判断任务状态
            if exit_code == 0:
                status = 'success'
                error_message = ''
            else:
                status = 'failed'
                error_message = f"退出代码: {exit_code}"
            
            # 更新任务日志
            self._update_task_log(log_id, status, output, exit_code, error_message)
            
            # 标记任务完成
            self._on_task_completed(task, status, output)
            
        except Exception as e:
            self.logger.error(f"执行任务 {task_id} 失败: {e}")
            self._on_task_failed(task_id, str(e))
            
        finally:
            # 清理当前任务标记
            self.current_task_id = None
    
    def _create_task_log(self, task_id: int, status: str) -> int:
        """创建任务日志"""
        from database.models import TaskLog
        
        log = TaskLog(
            task_id=task_id,
            status=status,
            start_time=datetime.now()
        )
        
        return self.db.add_task_log(log)
    
    def _update_task_log(self, log_id: int, status: str, output: str, 
                         exit_code: int, error_message: str):
        """更新任务日志"""
        from database.models import TaskLog
        
        log = self.db.get_task_log(log_id)
        if log:
            log.status = status
            log.output = output
            log.exit_code = exit_code
            log.end_time = datetime.now()
            log.error_message = error_message
            
            # TODO: 实现更新日志的方法
            # self.db.update_task_log(log)
    
    def _handle_task_output(self, output: str):
        """处理任务输出"""
        if self.on_output:
            self.on_output(output)
    
    def _on_task_started(self, task: Task):
        """任务开始回调"""
        self.logger.info(f"任务开始执行: {task.name}")
        
        if self.on_task_started:
            self.on_task_started(task.id, task.name)
    
    def _on_task_completed(self, task: Task, status: str, output: str):
        """任务完成回调"""
        self.logger.info(f"任务执行完成: {task.name}, 状态: {status}")
        
        if self.on_task_completed:
            self.on_task_completed(task.id, task.name, status, output)
    
    def _on_task_failed(self, task_id: int, error: str):
        """任务失败回调"""
        self.logger.error(f"任务执行失败: {task_id}, 错误: {error}")
        
        if self.on_task_failed:
            self.on_task_failed(task_id, error)
    
    def _stop_all_tasks(self):
        """停止所有运行中的任务"""
        for task_id, thread in list(self.running_tasks.items()):
            try:
                # 尝试停止线程
                if thread.is_alive():
                    # TODO: 更优雅的停止方式
                    pass
            except:
                pass
        
        self.running_tasks.clear()
    
    # ========== 公共接口 ==========
    
    def add_task(self, task: Task) -> bool:
        """添加新任务"""
        with self._lock:
            try:
                # 保存到数据库
                task_id = self.db.add_task(task)
                task.id = task_id
                
                # 如果任务启用且调度器在运行，添加到调度器
                if task.enabled and self.is_running:
                    self._add_task_to_scheduler(task)
                
                self.logger.info(f"已添加任务: {task.name} (ID: {task_id})")
                return True
                
            except Exception as e:
                self.logger.error(f"添加任务失败: {e}")
                return False
    
    def update_task(self, task: Task) -> bool:
        """更新任务"""
        with self._lock:
            try:
                # 更新数据库
                success = self.db.update_task(task)
                if not success:
                    return False
                
                # 从调度器中移除旧任务
                job_id = f'task_{task.id}'
                if self.scheduler.get_job(job_id):
                    self.scheduler.remove_job(job_id)
                
                # 如果任务启用，重新添加到调度器
                if task.enabled and self.is_running:
                    self._add_task_to_scheduler(task)
                
                self.logger.info(f"已更新任务: {task.name} (ID: {task.id})")
                return True
                
            except Exception as e:
                self.logger.error(f"更新任务失败: {e}")
                return False
    
    def delete_task(self, task_id: int) -> bool:
        """删除任务"""
        with self._lock:
            try:
                # 从调度器中移除
                job_id = f'task_{task_id}'
                if self.scheduler.get_job(job_id):
                    self.scheduler.remove_job(job_id)
                
                # 从数据库中删除
                success = self.db.delete_task(task_id)
                
                if success:
                    self.logger.info(f"已删除任务: {task_id}")
                
                return success
                
            except Exception as e:
                self.logger.error(f"删除任务失败: {e}")
                return False
    
    def pause_task(self, task_id: int) -> bool:
        """暂停任务"""
        with self._lock:
            try:
                # 从调度器中暂停
                job_id = f'task_{task_id}'
                job = self.scheduler.get_job(job_id)
                if job:
                    job.pause()
                
                # 更新数据库
                task = self.db.get_task(task_id)
                if task:
                    task.enabled = False
                    self.db.update_task(task)
                
                self.logger.info(f"已暂停任务: {task_id}")
                return True
                
            except Exception as e:
                self.logger.error(f"暂停任务失败: {e}")
                return False
    
    def resume_task(self, task_id: int) -> bool:
        """恢复任务"""
        with self._lock:
            try:
                # 更新数据库
                task = self.db.get_task(task_id)
                if not task:
                    return False
                
                task.enabled = True
                self.db.update_task(task)
                
                # 重新添加到调度器
                if self.is_running:
                    self._add_task_to_scheduler(task)
                
                self.logger.info(f"已恢复任务: {task_id}")
                return True
                
            except Exception as e:
                self.logger.error(f"恢复任务失败: {e}")
                return False
    
    def run_task_now(self, task_id: int) -> bool:
        """立即运行任务"""
        with self._lock:
            try:
                # 直接执行任务（不经过调度器）
                self._execute_task(task_id)
                return True
            except Exception as e:
                self.logger.error(f"立即运行任务失败: {e}")
                return False
    
    def get_next_run_time(self, task_id: int) -> Optional[datetime]:
        """获取任务下一次运行时间"""
        job_id = f'task_{task_id}'
        job = self.scheduler.get_job(job_id)
        
        if job:
            return job.next_run_time
        
        return None
    
    def get_running_tasks(self) -> List[int]:
        """获取正在运行的任务ID列表"""
        with self._lock:
            return list(self.running_tasks.keys())
    
    def get_queued_tasks(self) -> List[int]:
        """获取队列中的任务ID列表"""
        items = []
        while not self.task_queue.empty():
            try:
                items.append(self.task_queue.get_nowait())
            except Empty:
                break
        
        # 重新放回队列
        for item in items:
            self.task_queue.put(item)
        
        return items