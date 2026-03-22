"""
条件评估器 - 负责评估任务执行条件
"""

import re
import json
import logging
import operator
from typing import Dict, Any, Optional, Callable
from datetime import datetime


class ConditionEvaluator:
    """条件评估器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 运算符映射
        self.operators = {
            '==': operator.eq,
            '!=': operator.ne,
            '<': operator.lt,
            '<=': operator.le,
            '>': operator.gt,
            '>=': operator.ge,
            'in': lambda x, y: x in y,
            'not in': lambda x, y: x not in y,
            'contains': lambda x, y: x in y if isinstance(y, str) else False,
            'starts with': lambda x, y: y.startswith(x) if isinstance(y, str) else False,
            'ends with': lambda x, y: y.endswith(x) if isinstance(y, str) else False,
        }
        
        # 内置变量
        self.builtin_variables = {
            'now': datetime.now,
            'today': lambda: datetime.now().date(),
            'time': lambda: datetime.now().time(),
        }
        
        # 变量提供者
        self.variable_providers: Dict[str, Callable] = {}
        
        # 缓存
        self.variable_cache: Dict[str, Any] = {}
        self.cache_ttl = 60  # 缓存有效期（秒）
    
    def register_variable_provider(self, name: str, provider: Callable):
        """注册变量提供者"""
        self.variable_providers[name] = provider
    
    def set_variable(self, name: str, value: Any):
        """设置变量值"""
        self.variable_cache[name] = {
            'value': value,
            'timestamp': datetime.now()
        }
    
    def get_variable(self, name: str) -> Optional[Any]:
        """获取变量值"""
        # 检查缓存
        if name in self.variable_cache:
            cache_entry = self.variable_cache[name]
            cache_age = (datetime.now() - cache_entry['timestamp']).total_seconds()
            if cache_age < self.cache_ttl:
                return cache_entry['value']
        
        # 检查内置变量
        if name in self.builtin_variables:
            value = self.builtin_variables[name]()
            self.set_variable(name, value)
            return value
        
        # 检查注册的变量提供者
        if name in self.variable_providers:
            try:
                value = self.variable_providers[name]()
                self.set_variable(name, value)
                return value
            except Exception as e:
                self.logger.error(f"获取变量 {name} 失败: {e}")
                return None
        
        # 检查配置文件
        if name.startswith('config.'):
            config_key = name[7:]  # 移除 'config.' 前缀
            value = self._get_config_value(config_key)
            if value is not None:
                self.set_variable(name, value)
            return value
        
        # 检查默认脚本输出
        if name.startswith('script.'):
            script_name = name[7:]  # 移除 'script.' 前缀
            value = self._get_script_output(script_name)
            if value is not None:
                self.set_variable(name, value)
            return value
        
        return None
    
    def _get_config_value(self, key: str) -> Optional[Any]:
        """从配置文件获取值"""
        # TODO: 实现配置读取
        # 这里可以读取JSON配置文件
        try:
            config_path = self._get_config_path()
            if config_path and os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 支持嵌套键，如 'app.version'
                keys = key.split('.')
                value = config
                for k in keys:
                    if isinstance(value, dict) and k in value:
                        value = value[k]
                    else:
                        return None
                
                return value
        except Exception as e:
            self.logger.error(f"读取配置失败: {e}")
        
        return None
    
    def _get_script_output(self, script_name: str) -> Optional[Any]:
        """获取默认脚本输出"""
        # TODO: 实现脚本输出读取
        # 可以从数据库或文件中读取脚本输出
        try:
            # 示例：从数据库读取
            from database.db_manager import DatabaseManager
            db = DatabaseManager()
            
            # 这里假设有一个方法可以获取脚本输出
            # output = db.get_script_output(script_name)
            # return output
            
            return None
            
        except Exception as e:
            self.logger.error(f"获取脚本输出失败: {e}")
        
        return None
    
    def _get_config_path(self) -> Optional[str]:
        """获取配置文件路径"""
        # 这里可以根据实际情况返回配置文件路径
        import os
        from pathlib import Path
        
        # 尝试多个可能的路径
        possible_paths = [
            'config.json',
            'data/config.json',
            os.path.join(os.path.expanduser('~'), '.config', 'WindowsTaskScheduler', 'config.json'),
            os.path.join(os.getenv('APPDATA', ''), 'WindowsTaskScheduler', 'config.json'),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def evaluate(self, condition: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        评估条件表达式
        
        Args:
            condition: 条件字符串，如 "if config.date == '06-01'"
            context: 额外的上下文变量
            
        Returns:
            条件是否满足
        """
        if not condition:
            return True
        
        try:
            # 清理条件字符串
            condition = condition.strip()
            
            # 移除开头的 "if"（如果有）
            if condition.startswith('if '):
                condition = condition[3:].strip()
            
            # 解析条件
            parsed = self._parse_condition(condition)
            
            if not parsed:
                self.logger.warning(f"条件解析失败: {condition}")
                return False
            
            # 获取变量值
            left_value = self._resolve_value(parsed['left'])
            right_value = self._resolve_value(parsed['right'])
            
            # 如果提供了额外的上下文，从中获取变量
            if context:
                for key, value in context.items():
                    self.set_variable(key, value)
            
            # 如果左边是变量名，尝试获取值
            if isinstance(left_value, str) and left_value in self.variable_providers:
                left_value = self.get_variable(left_value)
            
            # 如果右边是变量名，尝试获取值
            if isinstance(right_value, str) and right_value in self.variable_providers:
                right_value = self.get_variable(right_value)
            
            # 执行比较
            operator_func = self.operators.get(parsed['operator'])
            if not operator_func:
                self.logger.warning(f"不支持的运算符: {parsed['operator']}")
                return False
            
            try:
                result = operator_func(left_value, right_value)
                return bool(result)
            except Exception as e:
                self.logger.error(f"执行比较失败: {e}")
                return False
            
        except Exception as e:
            self.logger.error(f"评估条件失败: {condition}, 错误: {e}")
            return False
    
    def _parse_condition(self, condition: str) -> Optional[Dict[str, Any]]:
        """解析条件表达式"""
        # 支持的运算符
        operator_patterns = [
            r'\s+not in\s+',     # not in
            r'\s+in\s+',         # in
            r'\s+starts with\s+', # starts with
            r'\s+ends with\s+',  # ends with
            r'\s+contains\s+',  # contains
            r'==',              # 等于
            r'!=',              # 不等于
            r'<=',              # 小于等于
            r'>=',              # 大于等于
            r'<',               # 小于
            r'>',               # 大于
        ]
        
        for op_pattern in operator_patterns:
            # 使用正则表达式分割
            parts = re.split(f'({op_pattern})', condition, maxsplit=1)
            if len(parts) == 3:
                left, operator, right = parts
                return {
                    'left': left.strip(),
                    'operator': operator.strip(),
                    'right': right.strip()
                }
        
        return None
    
    def _resolve_value(self, value_str: str) -> Any:
        """解析值字符串"""
        if not value_str:
            return value_str
        
        # 去除引号
        value_str = value_str.strip()
        
        # 字符串（带引号）
        if (value_str.startswith("'") and value_str.endswith("'")) or \
           (value_str.startswith('"') and value_str.endswith('"')):
            return value_str[1:-1]
        
        # 数字
        if re.match(r'^-?\d+(\.\d+)?$', value_str):
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        
        # 布尔值
        if value_str.lower() == 'true':
            return True
        if value_str.lower() == 'false':
            return False
        
        # 列表（用方括号表示）
        if value_str.startswith('[') and value_str.endswith(']'):
            try:
                return json.loads(value_str)
            except:
                pass
        
        # 字典（用花括号表示）
        if value_str.startswith('{') and value_str.endswith('}'):
            try:
                return json.loads(value_str)
            except:
                pass
        
        # 变量名
        return value_str
    
    def validate_condition(self, condition: str) -> Tuple[bool, str]:
        """
        验证条件表达式是否有效
        
        Args:
            condition: 条件字符串
            
        Returns:
            (是否有效, 错误信息)
        """
        if not condition:
            return True, ""
        
        try:
            # 移除开头的 "if"
            clean_condition = condition.strip()
            if clean_condition.startswith('if '):
                clean_condition = clean_condition[3:].strip()
            
            # 尝试解析
            parsed = self._parse_condition(clean_condition)
            if not parsed:
                return False, "无法解析条件表达式"
            
            # 检查运算符是否支持
            if parsed['operator'] not in self.operators:
                return False, f"不支持的运算符: {parsed['operator']}"
            
            # 尝试解析左右值
            left_value = self._resolve_value(parsed['left'])
            right_value = self._resolve_value(parsed['right'])
            
            # 检查变量是否存在
            if isinstance(left_value, str) and not self._is_literal(left_value):
                # 变量名，检查是否能获取
                if self.get_variable(left_value) is None:
                    return False, f"变量不存在: {left_value}"
            
            if isinstance(right_value, str) and not self._is_literal(right_value):
                # 变量名，检查是否能获取
                if self.get_variable(right_value) is None:
                    return False, f"变量不存在: {right_value}"
            
            return True, "条件表达式有效"
            
        except Exception as e:
            return False, f"验证条件时发生错误: {str(e)}"
    
    def _is_literal(self, value: str) -> bool:
        """判断是否为字面值（非变量名）"""
        # 数字
        if re.match(r'^-?\d+(\.\d+)?$', value):
            return True
        
        # 布尔值
        if value.lower() in ('true', 'false'):
            return True
        
        # 字符串（带引号）
        if (value.startswith("'") and value.endswith("'")) or \
           (value.startswith('"') and value.endswith('"')):
            return True
        
        # 列表或字典
        if (value.startswith('[') and value.endswith(']')) or \
           (value.startswith('{') and value.endswith('}')):
            return True
        
        return False
    
    # ========== 高级功能 ==========
    
    def evaluate_complex_condition(self, condition: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        评估复杂条件表达式（支持and/or组合）
        
        Args:
            condition: 复杂条件字符串
            context: 额外的上下文变量
            
        Returns:
            条件是否满足
        """
        # 简化实现：先支持单个条件
        # TODO: 实现and/or逻辑组合
        
        # 移除开头的 "if"
        clean_condition = condition.strip()
        if clean_condition.startswith('if '):
            clean_condition = clean_condition[3:].strip()
        
        # 检查是否有and/or
        if ' and ' in clean_condition.lower() or ' or ' in clean_condition.lower():
            self.logger.warning("复杂条件评估暂未完全实现")
            # 简单处理：拆分为多个条件，暂时只评估第一个
            parts = re.split(r'\s+(and|or)\s+', clean_condition, flags=re.IGNORECASE)
            if parts:
                return self.evaluate(parts[0], context)
        
        # 单个条件
        return self.evaluate(condition, context)
    
    def clear_cache(self):
        """清空变量缓存"""
        self.variable_cache.clear()
    
    def get_available_variables(self) -> Dict[str, Any]:
        """获取所有可用变量"""
        variables = {}
        
        # 内置变量
        for name, func in self.builtin_variables.items():
            try:
                variables[name] = func()
            except:
                variables[name] = None
        
        # 注册的变量提供者
        for name, provider in self.variable_providers.items():
            try:
                variables[name] = provider()
            except:
                variables[name] = None
        
        # 缓存中的变量
        for name, cache_entry in self.variable_cache.items():
            variables[name] = cache_entry['value']
        
        return variables