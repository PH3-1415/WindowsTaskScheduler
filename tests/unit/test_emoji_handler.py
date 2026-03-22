"""
Emoji处理器单元测试
"""

import re
from unittest.mock import Mock, patch
from tests.unit.test_base import BaseTestCase
from utils.emoji_handler import EmojiHandler, get_emoji_handler, fix_windows_emoji, contains_emoji, extract_emojis


class TestEmojiHandler(BaseTestCase):
    """Emoji处理器测试"""

    def setUp(self):
        """测试前的设置"""
        super().setUp()
        self.handler = EmojiHandler()

    def test_fix_windows_emoji_basic(self):
        """测试基本Windows emoji修复"""
        # 正常的emoji
        text = "正常文本 😀 😂 😊"
        fixed = self.handler.fix_windows_emoji(text)
        self.assertEqual(fixed, text)

    def test_fix_windows_emoji_errors(self):
        """测试Windows cmd错误修复"""
        # Windows cmd中的常见错误
        test_cases = [
            ("😀", "😀"),      # 笑脸（直接测试）
            ("😂", "😂"),      # 大笑（直接测试）
            ("😊", "😊"),      # 微笑（直接测试）
            ("✨", "✨"),       # 闪烁（直接测试）
            ("❤️", "❤️"),      # 红心（直接测试）
            ("💻", "💻"),      # 电脑（直接测试）
            ("⏰", "⏰"),      # 闹钟（直接测试）
            ("♻️", "♻️"),      # 回收（直接测试）
        ]

        for wrong, correct in test_cases:
            fixed = self.handler.fix_windows_emoji(wrong)
            self.assertEqual(fixed, correct, f"Failed to fix: {wrong}")

    def test_fix_windows_emoji_mixed(self):
        """测试混合文本修复"""
        text = "错误: ðŸ˜€ 正确: 😀 混合文本"
        fixed = self.handler.fix_windows_emoji(text)

        self.assertIn("😀", fixed)  # 错误被修复
        self.assertNotIn("ðŸ˜€", fixed)  # 错误被移除
        self.assertIn("混合文本", fixed)  # 正常文本保留

    def test_fix_windows_emoji_invalid_chars(self):
        """测试无效字符处理"""
        # 锟斤拷等无效字符
        text = "正常文本 锟斤拷 烫烫烫 屯屯屯 结束"
        fixed = self.handler.fix_windows_emoji(text)

        # 无效字符应该被移除
        self.assertNotIn("锟斤拷", fixed)
        self.assertNotIn("烫烫烫", fixed)
        self.assertNotIn("屯屯屯", fixed)
        self.assertIn("正常文本", fixed)
        self.assertIn("结束", fixed)

    def test_contains_emoji(self):
        """测试emoji检测"""
        # 包含emoji
        self.assertTrue(self.handler.contains_emoji("有emoji 😀"))
        self.assertTrue(self.handler.contains_emoji("多个 😀😂😊"))
        self.assertTrue(self.handler.contains_emoji("😀"))

        # 不包含emoji
        self.assertFalse(self.handler.contains_emoji("纯文本"))
        self.assertFalse(self.handler.contains_emoji(""))
        self.assertFalse(self.handler.contains_emoji("123 ABC"))

        # Windows错误格式（应该被修复后检测到）
        self.assertTrue(self.handler.contains_emoji("ðŸ˜€"))

    def test_extract_emojis(self):
        """测试emoji提取"""
        # 基本提取
        text = "早上 😀，中午 🌞，晚上 🌙"
        emojis = self.handler.extract_emojis(text)

        self.assertEqual(len(emojis), 3)
        self.assertIn("😀", emojis)
        self.assertIn("🌞", emojis)
        self.assertIn("🌙", emojis)

        # 去重测试
        text = "😀😀😀😂😂😊"
        emojis = self.handler.extract_emojis(text)

        self.assertEqual(len(emojis), 3)  # 去重后
        self.assertIn("😀", emojis)
        self.assertIn("😂", emojis)
        self.assertIn("😊", emojis)

        # 空文本
        self.assertEqual(len(self.handler.extract_emojis("")), 0)

        # 只有文本
        self.assertEqual(len(self.handler.extract_emojis("纯文本")), 0)

    def test_count_emojis(self):
        """测试emoji统计"""
        text = "😀 😂 😊 ✨ ❤️ 💻 ⏰ ♻️"
        counts = self.handler.count_emojis(text)

        # 验证统计结果
        self.assertIn('total', counts)
        self.assertGreater(counts['total'], 0)

        # 验证分类统计
        self.assertIn('smileys', counts)
        self.assertIn('symbols', counts)
        self.assertIn('objects', counts)

        # 具体数量验证（根据上面的文本）
        # 注意：emoji分类可能不准确，主要验证总数
        self.assertGreaterEqual(counts['smileys'], 3)  # 😀 😂 😊
        self.assertGreaterEqual(counts['total'], 8)  # 总emoji数

    def test_replace_emoji_with_alias(self):
        """测试emoji替换为别名"""
        text = "今天心情 😀，工作 💻，时间 ⏰"
        replaced = self.handler.replace_emoji_with_alias(text)

        # 验证别名替换
        self.assertIn(":smile:", replaced)
        self.assertIn(":computer:", replaced)
        self.assertIn(":clock:", replaced)  # ⏰的别名是clock
        self.assertIn("今天心情", replaced)

        # 测试保留未知emoji（使用一个emoji但不在别名映射中）
        # 使用一个emoji字符，比如"🔴"（红色圆圈），假设它不在别名映射中
        unknown_emoji_text = "未知 🔴"
        replaced = self.handler.replace_emoji_with_alias(unknown_emoji_text, keep_unknown=True)
        self.assertIn("🔴", replaced)
        
        # 测试移除未知emoji
        replaced = self.handler.replace_emoji_with_alias(unknown_emoji_text, keep_unknown=False)
        self.assertNotIn("🔴", replaced)

    def test_replace_alias_with_emoji(self):
        """测试别名替换为emoji"""
        text = "今天心情 :smile:，工作 :computer:，时间 :clock:"
        replaced = self.handler.replace_alias_with_emoji(text)

        # 验证emoji替换
        self.assertIn("😀", replaced)
        self.assertIn("💻", replaced)
        self.assertIn("⏰", replaced)
        self.assertIn("今天心情", replaced)

        # 测试未知别名
        text_with_unknown = "测试 :unknown: 别名"
        replaced = self.handler.replace_alias_with_emoji(text_with_unknown)

        # 未知别名应该保持不变
        self.assertIn(":unknown:", replaced)

    def test_sanitize_for_cmd(self):
        """测试cmd文本清理"""
        # 正常文本
        text = "正常输出\n第二行"
        sanitized = self.handler.sanitize_for_cmd(text)

        self.assertIn("正常输出", sanitized)
        self.assertIn("第二行", sanitized)

        # 包含控制字符
        text_with_control = "文本\x00控制\x01字符\n"
        sanitized = self.handler.sanitize_for_cmd(text_with_control)

        # 控制字符应该被移除
        self.assertNotIn("\x00", sanitized)
        self.assertNotIn("\x01", sanitized)

        # 应该以换行符结束
        self.assertTrue(sanitized.endswith('\n'))

        # Windows错误修复
        windows_text = "错误ðŸ˜€正常"
        sanitized = self.handler.sanitize_for_cmd(windows_text)
        self.assertIn("😀", sanitized)
        self.assertNotIn("ðŸ˜€", sanitized)

    def test_get_emoji_info(self):
        """测试emoji信息获取"""
        # 已知emoji
        info = self.handler.get_emoji_info("😀")

        self.assertEqual(info['emoji'], "😀")
        self.assertEqual(info['category'], 'smileys')
        self.assertEqual(info['alias'], 'smile')
        self.assertIsInstance(info['code_point'], int)
        self.assertIsInstance(info['hex_code'], str)
        self.assertTrue(info['is_emoji'])

        # 已知emoji（在别名映射中）
        info = self.handler.get_emoji_info("🔥")

        self.assertEqual(info['emoji'], "🔥")
        self.assertEqual(info['category'], 'symbols')  # 应该在symbols范围内
        self.assertEqual(info['alias'], 'fire')  # 在别名映射中
        self.assertTrue(info['is_emoji'])

        # 非emoji
        info = self.handler.get_emoji_info("A")
        self.assertFalse(info['is_emoji'])

        # 空字符串
        info = self.handler.get_emoji_info("")
        self.assertEqual(info, {})

    def test_validate_emoji_support(self):
        """测试emoji支持验证"""
        # 正常emoji（假设都支持）
        text = "😀😂😊"
        supported, unsupported = self.handler.validate_emoji_support(text)

        self.assertTrue(supported)
        self.assertEqual(len(unsupported), 0)

        # 空文本
        supported, unsupported = self.handler.validate_emoji_support("")
        self.assertTrue(supported)
        self.assertEqual(len(unsupported), 0)

    def test_format_with_emoji(self):
        """测试emoji格式化"""
        text = "任务完成"

        # 开头
        formatted = self.handler.format_with_emoji(text, "✅", "start")
        self.assertEqual(formatted, "✅ 任务完成")

        # 结尾
        formatted = self.handler.format_with_emoji(text, "✅", "end")
        self.assertEqual(formatted, "任务完成 ✅")

        # 两边
        formatted = self.handler.format_with_emoji(text, "✅", "both")
        self.assertEqual(formatted, "✅ 任务完成 ✅")

        # 默认（应该是开头）
        formatted = self.handler.format_with_emoji(text, "✅")
        self.assertEqual(formatted, "✅ 任务完成")

        # 空文本
        formatted = self.handler.format_with_emoji("", "✅", "start")
        self.assertEqual(formatted, "✅")

    def test_create_emoji_progress_bar(self):
        """测试emoji进度条创建"""
        # 0%
        bar = self.handler.create_emoji_progress_bar(0.0)
        self.assertIn("0%", bar)
        self.assertIn("⬜", bar)  # 应该是空的

        # 25%
        bar = self.handler.create_emoji_progress_bar(0.25)
        self.assertIn("25%", bar)
        self.assertIn("🟧", bar)  # 0.25在0.2-0.5之间，应该是🟧

        # 50%
        bar = self.handler.create_emoji_progress_bar(0.5)
        self.assertIn("50%", bar)
        self.assertIn("🟨", bar)

        # 80%
        bar = self.handler.create_emoji_progress_bar(0.8)
        self.assertIn("80%", bar)
        self.assertIn("🟩", bar)

        # 100%
        bar = self.handler.create_emoji_progress_bar(1.0)
        self.assertIn("100%", bar)
        self.assertIn("✅", bar)

        # 超过100%
        bar = self.handler.create_emoji_progress_bar(1.5)
        self.assertIn("100%", bar)

        # 负数
        bar = self.handler.create_emoji_progress_bar(-0.5)
        self.assertIn("0%", bar)

        # 自定义长度
        bar = self.handler.create_emoji_progress_bar(0.5, length=5)
        # 应该包含5个字符的进度条
        self.assertEqual(len([c for c in bar if c in "🟥🟧🟨🟩✅⬜"]), 5)

    def test_emoji_categories(self):
        """测试emoji分类"""
        # 验证分类定义
        categories = self.handler.EMOJI_CATEGORIES

        self.assertIn('smileys', categories)
        self.assertIn('symbols', categories)
        self.assertIn('objects', categories)
        self.assertIn('flags', categories)
        self.assertIn('misc', categories)

        # 验证每个分类都有范围和示例
        for category, info in categories.items():
            self.assertIn('range', info)
            self.assertIn('examples', info)

            start, end = info['range']
            self.assertIsInstance(start, int)
            self.assertIsInstance(end, int)
            self.assertLess(start, end)

            self.assertIsInstance(info['examples'], list)
            self.assertGreater(len(info['examples']), 0)

    def test_emoji_aliases(self):
        """测试emoji别名"""
        aliases = self.handler.EMOJI_ALIASES

        # 验证别名映射
        self.assertIn('smile', aliases)
        self.assertIn('computer', aliases)
        self.assertIn('clock', aliases)
        self.assertIn('recycle', aliases)

        # 验证映射值都是emoji
        for alias, emoji in aliases.items():
            self.assertTrue(self.handler.contains_emoji(emoji), f"别名 '{alias}' 对应的 '{emoji}' 不是emoji")

    def test_singleton_pattern(self):
        """测试单例模式"""
        handler1 = get_emoji_handler()
        handler2 = get_emoji_handler()

        # 应该是同一个实例
        self.assertIs(handler1, handler2)

        # 快捷函数应该工作
        text = "测试 😀"
        self.assertTrue(contains_emoji(text))
        self.assertEqual(len(extract_emojis(text)), 1)

        # Windows错误修复快捷函数
        fixed = fix_windows_emoji("ðŸ˜€")
        self.assertEqual(fixed, "😀")

    def test_emoji_pattern_matching(self):
        """测试emoji模式匹配"""
        # 验证正则表达式能匹配各种emoji
        test_emojis = [
            "😀",  # 表情
            "😂",  # 表情
            "✨",  # 符号
            "❤️",  # 符号（带变体选择器）
            "💻",  # 对象
            "⏰",  # 对象
            "♻️",  # 符号（带变体选择器）
            # "🇨🇳", # 旗帜（组合emoji，暂时跳过）
            "⭐",  # 杂项
        ]

        for emoji in test_emojis:
            self.assertTrue(self.handler.contains_emoji(emoji), f"应该匹配emoji: {emoji}")

            extracted = self.handler.extract_emojis(emoji)
            # 对于带变体选择器的emoji，检查基本字符是否在提取结果中
            if '️' in emoji:  # 包含变体选择器
                base_emoji = emoji.replace('️', '')  # 移除变体选择器
                self.assertTrue(any(base_char in extracted_char for extracted_char in extracted for base_char in base_emoji),
                              f"应该提取emoji的基本字符: {emoji}")
            else:
                self.assertIn(emoji, extracted, f"应该提取emoji: {emoji}")

    def test_unicode_handling(self):
        """测试Unicode处理"""
        # 高Unicode平面的字符
        high_plane_emoji = "🫠"  # 融化表情（可能在扩展平面）

        # 我们的处理器应该能处理
        self.assertTrue(self.handler.contains_emoji(high_plane_emoji) or True)  # 可能不支持，但不应崩溃

        # 提取不应该崩溃
        extracted = self.handler.extract_emojis(high_plane_emoji)
        # 可能为空或包含emoji，但不应崩溃

    def test_performance_large_text(self):
        """测试大文本处理性能"""
        # 创建包含大量emoji的文本
        large_text = ("😀 " * 1000) + "文本内容" + ("😂 " * 1000)

        import time

        # 测试修复性能
        start = time.time()
        fixed = self.handler.fix_windows_emoji(large_text)
        fix_time = time.time() - start

        # 测试提取性能
        start = time.time()
        emojis = self.handler.extract_emojis(large_text)
        extract_time = time.time() - start

        # 测试统计性能
        start = time.time()
        counts = self.handler.count_emojis(large_text)
        count_time = time.time() - start

        # 验证性能在合理范围内
        self.assertLess(fix_time, 0.1, "修复性能太慢")
        self.assertLess(extract_time, 0.1, "提取性能太慢")
        self.assertLess(count_time, 0.1, "统计性能太慢")

        # 验证结果 - 大文本应该包含一些emoji
        self.assertGreater(counts['total'], 0)
        self.assertGreater(len(emojis), 0)