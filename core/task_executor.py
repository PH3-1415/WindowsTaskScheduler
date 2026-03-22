"""
任务执行器 - 负责执行命令行任务
"""

import subprocess
import threading
import time
import logging
import os
import sys
from typing import Optional, Tuple, Callable
from queue import Queue, Empty

from utils.encoding_helper import EncodingHelper


class TaskExecutor:
    """任务执行器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.encoding_helper = EncodingHelper()
        
        # 执行状态
        self.current_process: Optional[subprocess.Popen] = None
        self.is_running = False
        self.output_queue = Queue()
        
        # 锁
        self._lock = threading.RLock()
    
    def execute(self, command: str, working_dir: Optional[str] = None, 
                on_output: Optional[Callable] = None) -> Tuple[int, str]:
        """
        执行命令
        
        Args:
            command: 要执行的命令
            working_dir: 工作目录
            on_output: 输出回调函数
            
        Returns:
            (退出代码, 输出内容)
        """
        with self._lock:
            if self.is_running:
                raise RuntimeError("已有任务正在执行")
            
            self.is_running = True
            self.output_queue = Queue()
            output_lines = []
            
            try:
                # 处理conda环境激活
                processed_command = self._process_conda_command(command)
                
                # 准备执行环境
                env = os.environ.copy()
                
                # 设置编码环境变量
                env['PYTHONIOENCODING'] = 'utf-8'
                env['PYTHONUTF8'] = '1'
                
                # 创建子进程
                self.logger.info(f"执行命令: {processed_command}")
                if working_dir:
                    self.logger.info(f"工作目录: {working_dir}")
                
                # Windows下隐藏控制台窗口
                creationflags = 0
                if sys.platform == 'win32':
                    creationflags = subprocess.CREATE_NO_WINDOW
                
                self.current_process = subprocess.Popen(
                    processed_command,
                    shell=True,
                    cwd=working_dir,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    bufsize=1,
                    universal_newlines=False,  # 使用字节模式，自己处理编码
                    creationflags=creationflags
                )
                
                # 启动输出读取线程
                output_thread = threading.Thread(
                    target=self._read_output,
                    args=(self.current_process.stdout,),
                    daemon=True
                )
                output_thread.start()
                
                # 处理输出
                while True:
                    try:
                        # 从队列获取输出
                        output_chunk = self.output_queue.get(timeout=0.1)
                        
                        # 解码输出
                        decoded_output = self.encoding_helper.decode_with_fallback(output_chunk)
                        
                        # 保存到列表
                        output_lines.append(decoded_output)
                        
                        # 调用回调函数
                        if on_output:
                            on_output(decoded_output)
                            
                    except Empty:
                        # 检查进程是否结束
                        if self.current_process.poll() is not None:
                            # 进程已结束，读取剩余输出
                            while not self.output_queue.empty():
                                try:
                                    output_chunk = self.output_queue.get_nowait()
                                    decoded_output = self.encoding_helper.decode_with_fallback(output_chunk)
                                    output_lines.append(decoded_output)
                                    if on_output:
                                        on_output(decoded_output)
                                except Empty:
                                    break
                            break
                        
                        # 进程还在运行，继续等待
                        continue
                
                # 等待进程结束
                exit_code = self.current_process.wait()
                
                # 构建完整输出
                full_output = ''.join(output_lines)
                
                self.logger.info(f"命令执行完成，退出代码: {exit_code}")
                return exit_code, full_output
                
            except Exception as e:
                self.logger.error(f"执行命令失败: {e}")
                error_output = f"执行失败: {str(e)}"
                if on_output:
                    on_output(error_output)
                return 1, error_output
                
            finally:
                self.current_process = None
                self.is_running = False
    
    def _process_conda_command(self, command: str) -> str:
        """
        处理conda环境激活命令
        
        Args:
            command: 原始命令
            
        Returns:
            处理后的命令
        """
        if 'conda activate' in command:
            # 解析conda环境
            env_name = self._extract_conda_env(command)
            if env_name:
                # 构建conda激活命令
                conda_path = self._find_conda_path()
                if conda_path:
                    # 使用conda run命令
                    base_cmd = command.replace(f'conda activate {env_name}', '').strip()
                    return f'"{conda_path}" run -n {env_name} {base_cmd}'
                else:
                    # 使用传统的激活方式
                    activate_cmd = self._get_conda_activate_cmd(env_name)
                    return f'{activate_cmd} && {command}'
        
        return command
    
    def _extract_conda_env(self, command: str) -> Optional[str]:
        """从命令中提取conda环境名"""
        import re
        
        # 匹配 conda activate <env_name>
        pattern = r'conda\s+activate\s+(\S+)'
        match = re.search(pattern, command)
        
        if match:
            return match.group(1)
        
        return None
    
    def _find_conda_path(self) -> Optional[str]:
        """查找conda可执行文件路径"""
        # 常见conda路径
        possible_paths = [
            'conda',
            'C:\\ProgramData\\Anaconda3\\Scripts\\conda.exe',
            'C:\\ProgramData\\Miniconda3\\Scripts\\conda.exe',
            'C:\\Users\\*\\Anaconda3\\Scripts\\conda.exe',
            'C:\\Users\\*\\Miniconda3\\Scripts\\conda.exe',
            '/opt/anaconda3/bin/conda',
            '/opt/miniconda3/bin/conda',
            '~/anaconda3/bin/conda',
            '~/miniconda3/bin/conda',
        ]
        
        import shutil
        
        for path in possible_paths:
            # 处理通配符
            if '*' in path or '~' in path:
                import glob
                expanded_paths = glob.glob(os.path.expanduser(path))
                for expanded_path in expanded_paths:
                    if os.path.exists(expanded_path):
                        return expanded_path
            else:
                # 直接查找
                found_path = shutil.which(path)
                if found_path:
                    return found_path
        
        return None
    
    def _get_conda_activate_cmd(self, env_name: str) -> str:
        """获取conda激活命令"""
        if sys.platform == 'win32':
            # Windows
            return f'call conda activate {env_name}'
        else:
            # Linux/macOS
            return f'eval "$(conda shell.bash hook)" && conda activate {env_name}'
    
    def _read_output(self, pipe):
        """读取进程输出（在独立线程中运行）"""
        try:
            while True:
                # 读取输出
                chunk = pipe.read1(4096) if hasattr(pipe, 'read1') else pipe.read(4096)
                if not chunk:
                    break
                
                # 放入队列
                self.output_queue.put(chunk)
                
        except Exception as e:
            self.logger.debug(f"读取输出时发生错误: {e}")
        finally:
            try:
                pipe.close()
            except:
                pass
    
    def stop(self):
        """停止当前执行的任务"""
        with self._lock:
            if self.current_process and self.is_running:
                try:
                    # 尝试优雅终止
                    self.current_process.terminate()
                    
                    # 等待一段时间
                    for _ in range(10):  # 最多等待1秒
                        if self.current_process.poll() is not None:
                            break
                        time.sleep(0.1)
                    
                    # 如果还在运行，强制终止
                    if self.current_process.poll() is None:
                        self.current_process.kill()
                        self.current_process.wait()
                    
                    self.logger.info("已停止当前任务")
                    
                except Exception as e:
                    self.logger.error(f"停止任务失败: {e}")
                
                finally:
                    self.current_process = None
                    self.is_running = False
    
    def is_executing(self) -> bool:
        """检查是否正在执行任务"""
        return self.is_running
    
    def get_current_command(self) -> Optional[str]:
        """获取当前正在执行的命令"""
        if self.current_process:
            return self.current_process.args
        return None
    
    # ========== 工具方法 ==========
    
    def test_command(self, command: str, working_dir: Optional[str] = None, 
                    timeout: int = 10) -> Tuple[bool, str]:
        """
        测试命令是否可执行
        
        Args:
            command: 要测试的命令
            working_dir: 工作目录
            timeout: 超时时间（秒）
            
        Returns:
            (是否成功, 输出或错误信息)
        """
        try:
            # 简单测试：执行 echo 命令
            test_cmd = 'echo "Test command"' if sys.platform != 'win32' else 'echo "Test command"'
            
            process = subprocess.Popen(
                test_cmd,
                shell=True,
                cwd=working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                if process.returncode == 0:
                    return True, "命令测试成功"
                else:
                    return False, f"命令测试失败: {stderr}"
            except subprocess.TimeoutExpired:
                process.kill()
                return False, "命令测试超时"
                
        except Exception as e:
            return False, f"命令测试异常: {str(e)}"
    
    def validate_command(self, command: str) -> Tuple[bool, str]:
        """
        验证命令格式
        
        Args:
            command: 要验证的命令
            
        Returns:
            (是否有效, 错误信息)
        """
        if not command or not command.strip():
            return False, "命令不能为空"
        
        # 检查命令长度
        if len(command) > 10000:
            return False, "命令过长"
        
        # 检查危险命令（简单过滤）
        dangerous_patterns = [
            'format',  # 格式化命令
            'del ',    # 删除命令
            'rm ',     # 删除命令
            'shutdown', # 关机命令
            'taskkill', # 终止进程
        ]
        
        cmd_lower = command.lower()
        for pattern in dangerous_patterns:
            if pattern in cmd_lower:
                return False, f"命令包含潜在危险操作: {pattern}"
        
        return True, "命令格式有效"