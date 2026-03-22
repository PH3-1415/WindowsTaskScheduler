"""
日期时间工具
"""

import re
from datetime import datetime, time, timedelta
from typing import Optional, Tuple, List, Dict, Any
from dateutil import parser as date_parser


class DateUtils:
    """日期时间工具类"""
    
    @staticmethod
    def parse_time(time_str: str) -> Optional[time]:
        """
        解析时间字符串
        
        Args:
            time_str: 时间字符串，如 "08:30", "14:00", "22:15"
            
        Returns:
            time对象或None
        """
        if not time_str:
            return None
        
        # 移除空格
        time_str = time_str.strip()
        
        # 尝试多种格式
        formats = [
            '%H:%M',      # 08:30
            '%H:%M:%S',   # 08:30:00
            '%I:%M %p',   # 08:30 AM
            '%I:%M:%S %p' # 08:30:00 AM
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt).time()
            except ValueError:
                continue
        
        # 如果标准格式都失败，尝试dateutil
        try:
            dt = date_parser.parse(time_str)
            return dt.time()
        except:
            return None
    
    @staticmethod
    def format_time(t: time) -> str:
        """
        格式化时间为字符串
        
        Args:
            t: time对象
            
        Returns:
            格式化的时间字符串，如 "08:30"
        """
        return t.strftime('%H:%M')
    
    @staticmethod
    def parse_schedule_config(config_str: str) -> Dict[str, Any]:
        """
        解析调度配置字符串
        
        Args:
            config_str: JSON格式的配置字符串
            
        Returns:
            解析后的配置字典
        """
        import json
        
        if not config_str:
            return {}
        
        try:
            return json.loads(config_str)
        except json.JSONDecodeError:
            return {}
    
    @staticmethod
    def create_daily_schedule(hour: int, minute: int) -> Dict[str, Any]:
        """
        创建每日调度配置
        
        Args:
            hour: 小时 (0-23)
            minute: 分钟 (0-59)
            
        Returns:
            调度配置字典
        """
        return {
            'type': 'daily',
            'hour': hour,
            'minute': minute
        }
    
    @staticmethod
    def create_weekly_schedule(
        days_of_week: List[int],  # 0=周一, 6=周日
        hour: int,
        minute: int
    ) -> Dict[str, Any]:
        """
        创建每周调度配置
        
        Args:
            days_of_week: 星期几列表
            hour: 小时
            minute: 分钟
            
        Returns:
            调度配置字典
        """
        return {
            'type': 'weekly',
            'days': days_of_week,
            'hour': hour,
            'minute': minute
        }
    
    @staticmethod
    def create_monthly_schedule(
        day_of_month: int,  # 1-31
        hour: int,
        minute: int
    ) -> Dict[str, Any]:
        """
        创建每月调度配置
        
        Args:
            day_of_month: 月中的第几天
            hour: 小时
            minute: 分钟
            
        Returns:
            调度配置字典
        """
        return {
            'type': 'monthly',
            'day': day_of_month,
            'hour': hour,
            'minute': minute
        }
    
    @staticmethod
    def is_workday(date: datetime = None) -> bool:
        """
        判断是否为工作日（周一至周五）
        
        Args:
            date: 日期，默认为今天
            
        Returns:
            是否为工作日
        """
        if date is None:
            date = datetime.now()
        
        # 周一=0, 周日=6
        weekday = date.weekday()
        return weekday < 5  # 周一到周五为工作日
    
    @staticmethod
    def get_next_run_time(
        schedule_type: str,
        schedule_config: Dict[str, Any],
        last_run: datetime = None
    ) -> Optional[datetime]:
        """
        计算下一次运行时间
        
        Args:
            schedule_type: 调度类型
            schedule_config: 调度配置
            last_run: 上次运行时间
            
        Returns:
            下一次运行时间
        """
        if last_run is None:
            last_run = datetime.now()
        
        now = datetime.now()
        
        if schedule_type == 'daily':
            hour = schedule_config.get('hour', 0)
            minute = schedule_config.get('minute', 0)
            
            # 创建今天的运行时间
            next_run = datetime(
                now.year, now.month, now.day,
                hour, minute, 0
            )
            
            # 如果今天的时间已过，则设置为明天
            if next_run < now:
                next_run += timedelta(days=1)
            
            return next_run
        
        elif schedule_type == 'weekly':
            days = schedule_config.get('days', [])
            hour = schedule_config.get('hour', 0)
            minute = schedule_config.get('minute', 0)
            
            if not days:
                return None
            
            # 找到下一个符合条件的日期
            current_weekday = now.weekday()  # 周一=0, 周日=6
            
            for days_ahead in range(1, 8):  # 检查未来7天
                next_date = now + timedelta(days=days_ahead)
                next_weekday = next_date.weekday()
                
                if next_weekday in days:
                    next_run = datetime(
                        next_date.year, next_date.month, next_date.day,
                        hour, minute, 0
                    )
                    return next_run
            
            return None
        
        elif schedule_type == 'monthly':
            day = schedule_config.get('day', 1)
            hour = schedule_config.get('hour', 0)
            minute = schedule_config.get('minute', 0)
            
            # 创建这个月的运行时间
            try:
                next_run = datetime(
                    now.year, now.month, day,
                    hour, minute, 0
                )
            except ValueError:
                # 如果日期无效（如2月30日），则使用当月最后一天
                import calendar
                last_day = calendar.monthrange(now.year, now.month)[1]
                day = min(day, last_day)
                next_run = datetime(
                    now.year, now.month, day,
                    hour, minute, 0
                )
            
            # 如果这个月的时间已过，则设置为下个月
            if next_run < now:
                # 计算下个月
                if now.month == 12:
                    next_year = now.year + 1
                    next_month = 1
                else:
                    next_year = now.year
                    next_month = now.month + 1
                
                try:
                    next_run = datetime(
                        next_year, next_month, day,
                        hour, minute, 0
                    )
                except ValueError:
                    # 调整到下个月的有效日期
                    import calendar
                    last_day = calendar.monthrange(next_year, next_month)[1]
                    day = min(day, last_day)
                    next_run = datetime(
                        next_year, next_month, day,
                        hour, minute, 0
                    )
            
            return next_run
        
        return None
    
    @staticmethod
    def format_next_run_time(next_run: datetime) -> str:
        """
        格式化下一次运行时间
        
        Args:
            next_run: 下一次运行时间
            
        Returns:
            格式化的字符串
        """
        if not next_run:
            return "无计划"
        
        now = datetime.now()
        delta = next_run - now
        
        if delta.days < 0:
            return "已过时"
        elif delta.days == 0:
            if delta.seconds < 60:
                return f"{delta.seconds}秒后"
            elif delta.seconds < 3600:
                return f"{delta.seconds // 60}分钟后"
            else:
                return f"{delta.seconds // 3600}小时后"
        elif delta.days == 1:
            return "明天 " + next_run.strftime("%H:%M")
        elif delta.days < 7:
            return f"{delta.days}天后"
        else:
            return next_run.strftime("%Y-%m-%d %H:%M")
    
    @staticmethod
    def validate_time_range(start_time: str, end_time: str) -> Tuple[bool, str]:
        """
        验证时间范围
        
        Args:
            start_time: 开始时间字符串
            end_time: 结束时间字符串
            
        Returns:
            (是否有效, 错误信息)
        """
        start = DateUtils.parse_time(start_time)
        end = DateUtils.parse_time(end_time)
        
        if not start:
            return False, "开始时间格式无效"
        
        if not end:
            return False, "结束时间格式无效"
        
        if start >= end:
            return False, "开始时间必须早于结束时间"
        
        return True, ""
    
    @staticmethod
    def get_time_delta_display(delta: timedelta) -> str:
        """
        获取时间间隔的显示文本
        
        Args:
            delta: 时间间隔
            
        Returns:
            显示文本
        """
        total_seconds = int(delta.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds}秒"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes}分{seconds}秒"
        elif total_seconds < 86400:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}小时{minutes}分"
        else:
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            return f"{days}天{hours}小时"