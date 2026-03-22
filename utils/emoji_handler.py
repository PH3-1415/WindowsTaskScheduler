"""
Emoji处理模块 - 专门处理emoji和特殊字符
"""

import re
import logging
from typing import List, Dict, Optional, Tuple


class EmojiHandler:
    """Emoji处理器"""
    
    # Emoji分类和映射
    EMOJI_CATEGORIES = {
        'smileys': {
            'range': (0x1F600, 0x1F64F),
            'examples': ['😀', '😂', '😊', '😍', '😎']
        },
        'symbols': {
            'range': (0x1F300, 0x1F5FF),  # 杂项符号和象形文字
            'examples': ['✨', '❤️', '⭐', '🎉', '🎈']
        },
        'objects': {
            'range': (0x1F400, 0x1F6FF),  # 扩展范围以包含更多对象
            'examples': ['💻', '📱', '🔑', '📁', '⌚']
        },
        'flags': {
            'range': (0x1F1E0, 0x1F1FF),
            'examples': ['🇨🇳', '🇺🇸', '🇯🇵', '🇰🇷']
        },
        'misc': {
            'range': (0x02000, 0x02BFF),  # 扩展范围以包含更多杂项符号
            'examples': ['✂️', '✏️', '✉️', '✈️', '⏰']
        }
    }
    
    # Windows cmd中的常见错误映射
    WINDOWS_CMD_ERRORS = {
        # UTF-8编码错误
        'ðŸ˜€': '😀',
        'ðŸ˜‚': '😂',
        'ðŸ˜Š': '😊',
        'ðŸ˜': '😍',
        'ðŸ˜Ž': '😎',
        'âœ¨': '✨',
        'â¤ï¸': '❤️',
        'ðŸ’»': '💻',
        'ðŸ”´': '⏰',
        'â™€ï¸': '♻️',
        
        # 问号占位符
        '??': '😀',
        '???': '😂',
        '????': '😊',
        '?????': '😍',
        '??????': '😎',
        
        # 其他常见错误
        '锟斤拷': '',      # 移除无效字符
        '烫烫烫': '',      # 移除调试标记
        '屯屯屯': '',      # 移除调试标记
    }
    
    # 常用emoji别名映射（方便在条件表达式中使用）
    EMOJI_ALIASES = {
        'smile': '😀',
        'laugh': '😂',
        'blush': '😊',
        'heart_eyes': '😍',
        'sunglasses': '😎',
        'sparkles': '✨',
        'heart': '❤️',
        'computer': '💻',
        'clock': '⏰',
        'recycle': '♻️',
        'star': '⭐',
        'fire': '🔥',
        'thumbs_up': '👍',
        'check_mark': '✅',
        'warning': '⚠️',
        'error': '❌',
        'success': '✅',
        'info': 'ℹ️',
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 编译emoji正则表达式
        self._compile_emoji_patterns()
    
    def _compile_emoji_patterns(self):
        """编译emoji正则表达式"""
        # 构建emoji字符范围
        emoji_ranges = []
        for category in self.EMOJI_CATEGORIES.values():
            start, end = category['range']
            # 使用正确的Unicode范围格式
            emoji_ranges.append(f'\\U{start:08X}-\\U{end:08X}')
        
        # 完整的emoji模式
        try:
            emoji_pattern = f'[{"".join(emoji_ranges)}]'
            self.emoji_regex = re.compile(emoji_pattern, flags=re.UNICODE)
        except re.error:
            # 如果正则表达式失败，使用更简单的方法
            # 匹配常见emoji范围
            self.emoji_regex = re.compile(
                r'[\U0001F600-\U0001F64F'  # 表情符号
                r'\U0001F300-\U0001F5FF'  # 杂项符号和象形文字
                r'\U0001F680-\U0001F6FF'  # 交通和地图符号
                r'\U0001F1E0-\U0001F1FF'  # 旗帜（iOS）
                r'\U00002702-\U000027B0'  # 杂项符号
                r'\U000024C2-\U0001F251'  # 封闭字符
                r']', 
                flags=re.UNICODE
            )
        
        # Windows cmd错误模式
        self.windows_errors_regex = re.compile(
            '|'.join(re.escape(key) for key in self.WINDOWS_CMD_ERRORS.keys())
        )
    
    def fix_windows_emoji(self, text: str) -> str:
        """
        修复Windows cmd中的emoji错误
        
        Args:
            text: 输入文本
            
        Returns:
            修复后的文本
        """
        if not text:
            return text
        
        # 简化版：直接替换已知的错误字符串
        for wrong, correct in self.WINDOWS_CMD_ERRORS.items():
            text = text.replace(wrong, correct)
        
        # 移除控制字符（保留emoji）
        # 只移除控制字符（U+0000-U+001F和U+007F-U+009F）
        text = re.sub(r'[\u0000-\u001F\u007F-\u009F]', '', text)
        
        return text
    
    def contains_emoji(self, text: str) -> bool:
        """
        检查文本是否包含emoji
        
        Args:
            text: 输入文本
            
        Returns:
            是否包含emoji
        """
        if not text:
            return False
        
        # 先修复Windows错误
        fixed_text = self.fix_windows_emoji(text)
        
        # 简化版emoji检测：检查常见emoji字符
        # 常见emoji Unicode范围（更全面的列表）
        emoji_ranges = [
            (0x1F600, 0x1F64F),  # 表情符号 (Emoticons)
            (0x1F300, 0x1F5FF),  # 杂项符号和象形文字 (Miscellaneous Symbols and Pictographs)
            (0x1F680, 0x1F6FF),  # 交通和地图符号 (Transport and Map Symbols)
            (0x1F900, 0x1F9FF),  # 补充符号和象形文字 (Supplemental Symbols and Pictographs)
            (0x2600, 0x26FF),    # 杂项符号 (Miscellaneous Symbols)
            (0x2700, 0x27BF),    # 装饰符号 (Dingbats)
            (0x1F000, 0x1F02F),  # 麻将牌 (Mahjong Tiles)
            (0x1F0A0, 0x1F0FF),  # 扑克牌 (Playing Cards)
            (0x1F200, 0x1F2FF),  # 封闭式字母数字补充 (Enclosed Alphanumeric Supplement)
        ]
        
        # 常见单个emoji码点（不在上述范围内的）
        common_emojis = {
            0x2139,  # ℹ️ (信息)
            0x231A, 0x231B, 0x23E9, 0x23EA, 0x23EB, 0x23EC, 0x23F0, 0x23F3,
            0x25FD, 0x25FE, 0x2614, 0x2615, 0x2648, 0x2649, 0x264A, 0x264B,
            0x264C, 0x264D, 0x264E, 0x264F, 0x267F, 0x2693, 0x26A1, 0x26AA,
            0x26AB, 0x26BD, 0x26BE, 0x26C4, 0x26C5, 0x26CE, 0x26D4, 0x26EA,
            0x26F2, 0x26F3, 0x26F5, 0x26FA, 0x26FD, 0x2B05, 0x2B06, 0x2B07,
            0x2B1B, 0x2B1C, 0x2B50, 0x2B55, 0x3030, 0x303D, 0x3297, 0x3299,
        }
        
        for char in fixed_text:
            code = ord(char)
            
            # 检查是否在emoji范围内
            for start, end in emoji_ranges:
                if start <= code <= end:
                    return True
            
            # 检查是否是常见emoji
            if code in common_emojis:
                return True
        
        return False
    
    def extract_emojis(self, text: str) -> List[str]:
        """
        提取文本中的所有emoji
        
        Args:
            text: 输入文本
            
        Returns:
            emoji列表
        """
        if not text:
            return []
        
        # 先修复Windows错误
        fixed_text = self.fix_windows_emoji(text)
        
        # 提取emoji
        emojis = []
        
        # 直接使用contains_emoji的逻辑来提取emoji
        for char in fixed_text:
            if self.contains_emoji(char):
                emojis.append(char)
        
        # 去重并保持顺序
        seen = set()
        unique_emojis = []
        for emoji in emojis:
            if emoji not in seen:
                seen.add(emoji)
                unique_emojis.append(emoji)
        
        return unique_emojis
    
    def count_emojis(self, text: str) -> Dict[str, int]:
        """
        统计emoji数量
        
        Args:
            text: 输入文本
            
        Returns:
            各分类emoji数量统计
        """
        if not text:
            return {}
        
        emojis = self.extract_emojis(text)
        
        # 按分类统计
        counts = {category: 0 for category in self.EMOJI_CATEGORIES}
        counts['total'] = len(emojis)
        
        for emoji in emojis:
            # 获取emoji的Unicode码点
            code_point = ord(emoji[0])  # 只考虑第一个字符（大多数emoji是单字符）
            
            # 查找所属分类
            for category, info in self.EMOJI_CATEGORIES.items():
                start, end = info['range']
                if start <= code_point <= end:
                    counts[category] += 1
                    break
        
        return counts
    
    def replace_emoji_with_alias(self, text: str, keep_unknown: bool = True) -> str:
        """
        用别名替换emoji
        
        Args:
            text: 输入文本
            keep_unknown: 是否保留未知emoji
            
        Returns:
            替换后的文本
        """
        if not text:
            return text
        
        # 创建反向映射（emoji -> 别名）
        emoji_to_alias = {v: k for k, v in self.EMOJI_ALIASES.items()}
        
        # 提取所有emoji
        emojis = self.extract_emojis(text)
        
        # 替换emoji
        result = text
        for emoji in emojis:
            if emoji in emoji_to_alias:
                alias = f":{emoji_to_alias[emoji]}:"
                result = result.replace(emoji, alias)
            elif not keep_unknown:
                # 移除未知emoji
                result = result.replace(emoji, '')
        
        return result
    
    def replace_alias_with_emoji(self, text: str) -> str:
        """
        用emoji替换别名
        
        Args:
            text: 输入文本
            
        Returns:
            替换后的文本
        """
        if not text:
            return text
        
        result = text
        
        # 替换所有别名
        for alias, emoji in self.EMOJI_ALIASES.items():
            pattern = f':{alias}:'
            result = result.replace(pattern, emoji)
        
        return result
    
    def sanitize_for_cmd(self, text: str) -> str:
        """
        为Windows cmd清理文本
        
        Args:
            text: 输入文本
            
        Returns:
            清理后的文本
        """
        if not text:
            return text
        
        # 修复Windows错误
        text = self.fix_windows_emoji(text)
        
        # 移除控制字符（保留换行符和制表符）
        import string
        control_chars = ''.join(
            chr(i) for i in range(32) 
            if chr(i) not in '\n\r\t'
        )
        
        for char in control_chars:
            text = text.replace(char, '')
        
        # 确保文本以换行符结束
        if not text.endswith('\n'):
            text += '\n'
        
        return text
    
    def get_emoji_info(self, emoji: str) -> Dict[str, any]:
        """
        获取emoji信息
        
        Args:
            emoji: emoji字符
            
        Returns:
            emoji信息字典
        """
        if not emoji or len(emoji) == 0:
            return {}
        
        # 获取Unicode码点
        code_point = ord(emoji[0])
        hex_code = f'U+{code_point:04X}'
        
        # 查找分类
        category = 'unknown'
        for cat_name, cat_info in self.EMOJI_CATEGORIES.items():
            start, end = cat_info['range']
            if start <= code_point <= end:
                category = cat_name
                break
        
        # 查找别名
        alias = None
        for alias_name, emoji_char in self.EMOJI_ALIASES.items():
            if emoji_char == emoji:
                alias = alias_name
                break
        
        return {
            'emoji': emoji,
            'code_point': code_point,
            'hex_code': hex_code,
            'category': category,
            'alias': alias,
            'length': len(emoji),
            'is_emoji': self.contains_emoji(emoji)
        }
    
    def validate_emoji_support(self, text: str) -> Tuple[bool, List[str]]:
        """
        验证emoji支持情况
        
        Args:
            text: 输入文本
            
        Returns:
            (是否完全支持, 不支持的emoji列表)
        """
        if not text:
            return True, []
        
        emojis = self.extract_emojis(text)
        unsupported = []
        
        # 这里可以添加特定的检查逻辑
        # 例如，检查某些emoji是否在特定字体中缺失
        
        # 目前假设所有emoji都支持
        # 未来可以添加更复杂的检查
        
        return len(unsupported) == 0, unsupported
    
    def format_with_emoji(self, text: str, emoji: str, position: str = 'start') -> str:
        """
        用emoji格式化文本
        
        Args:
            text: 输入文本
            emoji: emoji字符
            position: 位置 ('start', 'end', 'both')
            
        Returns:
            格式化后的文本
        """
        if not text:
            return emoji if position in ['start', 'end'] else emoji + emoji
        
        if position == 'start':
            return f"{emoji} {text}"
        elif position == 'end':
            return f"{text} {emoji}"
        elif position == 'both':
            return f"{emoji} {text} {emoji}"
        else:
            return text
    
    def create_emoji_progress_bar(self, progress: float, length: int = 10) -> str:
        """
        创建emoji进度条
        
        Args:
            progress: 进度 (0.0-1.0)
            length: 进度条长度
            
        Returns:
            emoji进度条字符串
        """
        # 确保进度在合理范围内
        progress = max(0.0, min(1.0, progress))
        
        # 计算填充数量
        filled = int(progress * length)
        empty = length - filled
        
        # 选择emoji
        if progress >= 1.0:
            # 完成
            bar = '✅' * length
        elif progress >= 0.8:
            # 接近完成
            bar = '🟩' * filled + '⬜' * empty
        elif progress >= 0.5:
            # 进行中
            bar = '🟨' * filled + '⬜' * empty
        elif progress >= 0.2:
            # 刚开始
            bar = '🟧' * filled + '⬜' * empty
        else:
            # 刚开始
            bar = '🟥' * filled + '⬜' * empty
        
        # 添加百分比
        percent = int(progress * 100)
        return f"{bar} {percent}%"


# 全局emoji处理器实例
_emoji_handler: Optional[EmojiHandler] = None


def get_emoji_handler() -> EmojiHandler:
    """获取全局emoji处理器"""
    global _emoji_handler
    
    if _emoji_handler is None:
        _emoji_handler = EmojiHandler()
    
    return _emoji_handler


# 快捷函数
def fix_windows_emoji(text: str) -> str:
    """修复Windows cmd中的emoji错误（快捷方式）"""
    return get_emoji_handler().fix_windows_emoji(text)


def contains_emoji(text: str) -> bool:
    """检查文本是否包含emoji（快捷方式）"""
    return get_emoji_handler().contains_emoji(text)


def extract_emojis(text: str) -> List[str]:
    """提取文本中的所有emoji（快捷方式）"""
    return get_emoji_handler().extract_emojis(text)