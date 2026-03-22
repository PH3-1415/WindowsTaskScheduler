"""
默认脚本处理器 - 负责处理每天00:00运行的默认脚本
"""

import os
import tempfile
import subprocess
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path

from database.db_manager import DatabaseManager
from database.models import DefaultScript
from utils.encoding_helper import EncodingHelper


class DefaultScriptProcessor:
    """默认脚本处理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db = DatabaseManager()
        self.encoding_helper = EncodingHelper()
        
        # 执行状态
        self.is_running = False
        self.current_script_id: Optional[int] = None
        self.last_run_time: Optional[datetime] = None
        
        # 定时器
        self.timer: Optional[threading.Timer] = None
        
        # 回调函数
        self.on_script_started = None
        self.on_script_completed = None
        self.on_script_failed = None
    
    def start(self, run_time: str = "00:00"):
        """启动默认脚本处理器"""
        if self.is_running:
            self.logger.warning("默认脚本处理器已经在运行中")
            return
        
        self.is_running = True
        
        # 计算下一次运行时间
        next_run = self._calculate_next_run_time(run_time)
        
        # 启动定时器
        self._schedule_next_run(next_run, run_time)
        
        self.logger.info(f"默认脚本处理器已启动，下次运行时间: {next_run}")
    
    def stop(self):
        """停止默认脚本处理器"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # 取消定时器
        if self.timer:
            self.timer.cancel()
            self.timer = None
        
        self.logger.info("默认脚本处理器已停止")
    
    def _calculate_next_run_time(self, run_time: str) -> datetime:
        """计算下一次运行时间"""
        now = datetime.now()
        
        # 解析运行时间
        try:
            run_hour, run_minute = map(int, run_time.split(':'))
        except:
            run_hour, run_minute = 0, 0
        
        # 创建今天的运行时间
        next_run = datetime(now.year, now.month, now.day, run_hour, run_minute, 0)
        
        # 如果今天的时间已过，则设置为明天
        if next_run <= now:
            next_run += timedelta(days=1)
        
        return next_run
    
    def _schedule_next_run(self, next_run: datetime, run_time: str):
        """调度下一次运行"""
        if not self.is_running:
            return
        
        # 计算延迟（秒）
        delay = (next_run - datetime.now()).total_seconds()
        
        if delay < 0:
            # 时间已过，立即运行
            self._run_all_scripts()
            # 重新计算下一次运行时间
            next_run = self._calculate_next_run_time(run_time)
            delay = (next_run - datetime.now()).total_seconds()
        
        # 创建定时器
        self.timer = threading.Timer(delay, self._on_timer_triggered, args=[run_time])
        self.timer.daemon = True
        self.timer.start()
        
        self.logger.debug(f"已调度下一次运行，延迟: {delay:.0f}秒")
    
    def _on_timer_triggered(self, run_time: str):
        """定时器触发"""
        if not self.is_running:
            return
        
        try:
            # 运行所有脚本
            self._run_all_scripts()
            
            # 记录最后运行时间
            self.last_run_time = datetime.now()
            
            # 调度下一次运行
            next_run = self._calculate_next_run_time(run_time)
            self._schedule_next_run(next_run, run_time)
            
        except Exception as e:
            self.logger.error(f"定时器触发失败: {e}")
            # 即使失败也继续调度
            next_run = self._calculate_next_run_time(run_time)
            self._schedule_next_run(next_run, run_time)
    
    def _run_all_scripts(self):
        """运行所有默认脚本"""
        scripts = self.db.get_all_default_scripts()
        
        if not scripts:
            self.logger.debug("没有默认脚本需要运行")
            return
        
        self.logger.info(f"开始运行 {len(scripts)} 个默认脚本")
        
        for script in scripts:
            try:
                self._run_script(script)
            except Exception as e:
                self.logger.error(f"运行脚本失败 {script.name}: {e}")
                if self.on_script_failed:
                    self.on_script_failed(script.id, script.name, str(e))
    
    def _run_script(self, script: DefaultScript):
        """运行单个脚本"""
        if not script.script_content:
            self.logger.warning(f"脚本 {script.name} 内容为空")
            return
        
        # 标记脚本开始
        self.current_script_id = script.id
        if self.on_script_started:
            self.on_script_started(script.id, script.name)
        
        try:
            # 创建临时文件
            temp_file = self._create_temp_script(script.script_content)
            
            # 执行脚本
            output = self._execute_script(temp_file)
            
            # 保存输出
            self._save_script_output(script, output)
            
            # 更新脚本信息
            script.last_run = datetime.now()
            script.last_output = output
            self.db.update_default_script(script)
            
            # 标记脚本完成
            if self.on_script_completed:
                self.on_script_completed(script.id, script.name, output)
            
            self.logger.info(f"脚本 {script.name} 运行完成")
            
        except Exception as e:
            error_msg = f"运行脚本失败: {str(e)}"
            self.logger.error(f"脚本 {script.name} 运行失败: {e}")
            
            # 保存错误信息
            self._save_script_output(script, error_msg, is_error=True)
            
            if self.on_script_failed:
                self.on_script_failed(script.id, script.name, error_msg)
            
        finally:
            self.current_script_id = None
    
    def _create_temp_script(self, script_content: str) -> str:
        """创建临时脚本文件"""
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="windows_task_scheduler_")
        
        # 创建脚本文件
        script_file = os.path.join(temp_dir, "script.py")
        
        # 添加必要的导入和错误处理
        enhanced_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import traceback

def main():
    try:
        # 用户脚本开始
{self._indent_script(script_content)}
        # 用户脚本结束
        return 0
    except Exception as e:
        print(f"脚本执行错误: {{e}}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
        
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(enhanced_content)
        
        return script_file
    
    def _indent_script(self, script_content: str, indent: str = "        ") -> str:
        """为脚本内容添加缩进"""
        lines = script_content.split('\n')
        indented_lines = []
        
        for line in lines:
            if line.strip():  # 非空行
                indented_lines.append(indent + line)
            else:  # 空行
                indented_lines.append('')
        
        return '\n'.join(indented_lines)
    
    def _execute_script(self, script_file: str) -> str:
        """执行脚本文件"""
        try:
            # 设置环境变量
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8'] = '1'
            
            # 执行脚本
            result = subprocess.run(
                [sys.executable, script_file],
                capture_output=True,
                text=False,  # 使用字节模式，自己处理编码
                encoding=None,  # 不自动解码
                env=env,
                timeout=300  # 5分钟超时
            )
            
            # 解码输出
            stdout = self.encoding_helper.decode_with_fallback(result.stdout)
            stderr = self.encoding_helper.decode_with_fallback(result.stderr)
            
            # 组合输出
            output = ""
            if stdout:
                output += stdout
            if stderr:
                if output:
                    output += "\n"
                output += f"[错误输出]\n{stderr}"
            
            return output
            
        except subprocess.TimeoutExpired:
            return "脚本执行超时（超过5分钟）"
        except Exception as e:
            return f"执行脚本时发生错误: {str(e)}"
        finally:
            # 清理临时文件
            try:
                os.remove(script_file)
                os.rmdir(os.path.dirname(script_file))
            except:
                pass
    
    def _save_script_output(self, script: DefaultScript, output: str, is_error: bool = False):
        """保存脚本输出到配置文件"""
        if not script.output_config:
            return
        
        try:
            config_path = script.output_config.get('path')
            if not config_path:
                return
            
            # 确保目录存在
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # 读取现有配置
            config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    try:
                        config = json.load(f)
                    except json.JSONDecodeError:
                        config = {}
            
            # 更新配置
            output_key = script.output_config.get('key', script.name)
            config[output_key] = {
                'value': output,
                'timestamp': datetime.now().isoformat(),
                'is_error': is_error
            }
            
            # 保存配置
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"脚本输出已保存到: {config_path}")
            
        except Exception as e:
            self.logger.error(f"保存脚本输出失败: {e}")
    
    # ========== 公共接口 ==========
    
    def add_script(self, script: DefaultScript) -> bool:
        """添加默认脚本"""
        try:
            script_id = self.db.add_default_script(script)
            script.id = script_id
            
            self.logger.info(f"已添加默认脚本: {script.name} (ID: {script_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"添加默认脚本失败: {e}")
            return False
    
    def update_script(self, script: DefaultScript) -> bool:
        """更新默认脚本"""
        try:
            success = self.db.update_default_script(script)
            if success:
                self.logger.info(f"已更新默认脚本: {script.name} (ID: {script.id})")
            return success
            
        except Exception as e:
            self.logger.error(f"更新默认脚本失败: {e}")
            return False
    
    def delete_script(self, script_id: int) -> bool:
        """删除默认脚本"""
        try:
            success = self.db.delete_default_script(script_id)
            if success:
                self.logger.info(f"已删除默认脚本: {script_id}")
            return success
            
        except Exception as e:
            self.logger.error(f"删除默认脚本失败: {e}")
            return False
    
    def run_script_now(self, script_id: int) -> bool:
        """立即运行脚本"""
        script = self.db.get_default_script(script_id)
        if not script:
            self.logger.error(f"脚本不存在: {script_id}")
            return False
        
        try:
            self._run_script(script)
            return True
        except Exception as e:
            self.logger.error(f"立即运行脚本失败: {e}")
            return False
    
    def run_all_scripts_now(self) -> bool:
        """立即运行所有脚本"""
        try:
            self._run_all_scripts()
            return True
        except Exception as e:
            self.logger.error(f"立即运行所有脚本失败: {e}")
            return False
    
    def get_script_output(self, script_id: int) -> Optional[str]:
        """获取脚本最后输出"""
        script = self.db.get_default_script(script_id)
        if script:
            return script.last_output
        return None
    
    def get_all_scripts(self) -> List[DefaultScript]:
        """获取所有默认脚本"""
        return self.db.get_all_default_scripts()
    
    def get_next_run_time(self) -> Optional[datetime]:
        """获取下一次运行时间"""
        if self.timer:
            # 计算定时器触发时间
            # 注意：threading.Timer没有直接的方法获取剩余时间
            # 这里返回最后运行时间+24小时作为估计
            if self.last_run_time:
                return self.last_run_time + timedelta(days=1)
        
        return None
    
    def is_script_running(self) -> bool:
        """检查是否有脚本正在运行"""
        return self.current_script_id is not None
    
    def get_running_script_id(self) -> Optional[int]:
        """获取正在运行的脚本ID"""
        return self.current_script_id


# 导入sys模块（用于脚本执行）
import sys