"""
编码助手单元测试
"""

import unittest
from unittest.mock import Mock, patch
from tests.unit.test_base import BaseTestCase
from utils.encoding_helper import EncodingHelper


class TestEncodingHelper(BaseTestCase):
    """编码助手测试"""
    
    def test_detect_encoding_utf8(self):
        """测试UTF-8编码检测"""
        # UTF-8文本
        text = "Hello, 世界! 🌍"
        utf8_bytes = text.encode('utf-8')
        
        encoding, confidence = EncodingHelper.detect_encoding(utf8_bytes)
        
        # 验证检测结果
        self.assertIsNotNone(encoding)
        self.assertIsNotNone(confidence)
        self.assertGreater(confidence, 0.5)
        
        # 通常是UTF-8或ascii
        self.assertIn(encoding.lower(), ['utf-8', 'ascii', 'utf-8-sig'])
    
    def test_detect_encoding_gbk(self):
        """测试GBK编码检测"""
        # GBK文本（中文）
        text = "你好，世界！"
        gbk_bytes = text.encode('gbk')
        
        encoding, confidence = EncodingHelper.detect_encoding(gbk_bytes)
        
        # 验证检测结果
        self.assertIsNotNone(encoding)
        self.assertIsNotNone(confidence)
        self.assertGreater(confidence, 0.5)
        
        # 可能是GBK或GB2312
        self.assertIn(encoding.lower(), ['gbk', 'gb2312', 'gb18030'])
    
    def test_detect_encoding_empty(self):
        """测试空数据检测"""
        encoding, confidence = EncodingHelper.detect_encoding(b'')
        
        self.assertIsNone(encoding)
        self.assertEqual(confidence, 0.0)
    
    def test_decode_with_fallback_utf8(self):
        """测试UTF-8解码"""
        text = "测试文本 with emoji 😀"
        utf8_bytes = text.encode('utf-8')
        
        decoded = EncodingHelper.decode_with_fallback(utf8_bytes)
        
        self.assertEqual(decoded, text)
    
    def test_decode_with_fallback_gbk(self):
        """测试GBK解码"""
        text = "中文测试"
        gbk_bytes = text.encode('gbk')
        
        decoded = EncodingHelper.decode_with_fallback(gbk_bytes)
        
        self.assertEqual(decoded, text)
    
    def test_decode_with_fallback_preferred_encoding(self):
        """测试优先编码解码"""
        text = "优先编码测试"
        utf8_bytes = text.encode('utf-8')
        
        # 指定优先编码
        decoded = EncodingHelper.decode_with_fallback(utf8_bytes, preferred_encoding='utf-8')
        
        self.assertEqual(decoded, text)
    
    def test_decode_with_fallback_invalid_encoding(self):
        """测试无效优先编码"""
        text = "测试文本"
        utf8_bytes = text.encode('utf-8')
        
        # 指定无效的优先编码
        decoded = EncodingHelper.decode_with_fallback(utf8_bytes, preferred_encoding='invalid-encoding')
        
        # 应该仍然能正确解码
        self.assertEqual(decoded, text)
    
    def test_decode_with_fallback_corrupted_data(self):
        """测试损坏数据解码"""
        # 创建损坏的UTF-8数据
        corrupted_bytes = b'\xff\xfe\x00' + "部分文本".encode('utf-8')
        
        decoded = EncodingHelper.decode_with_fallback(corrupted_bytes)
        
        # 应该能解码，可能有替换字符
        self.assertIsInstance(decoded, str)
        self.assertGreater(len(decoded), 0)
    
    def test_fix_emoji_encoding(self):
        """测试emoji编码修复"""
        # 测试正常的emoji
        text = "正常emoji 😀😂😊"
        fixed = EncodingHelper.fix_emoji_encoding(text)
        
        self.assertEqual(fixed, text)
        
        # 测试Windows cmd错误
        windows_error = "错误显示 ðŸ˜€ðŸ˜‚"
        fixed = EncodingHelper.fix_emoji_encoding(windows_error)
        
        # 应该修复为正确的emoji
        self.assertIn("😀", fixed)
        self.assertIn("😂", fixed)
    
    def test_contains_emoji(self):
        """测试emoji检测"""
        # 包含emoji的文本
        text_with_emoji = "Hello 😀 World"
        self.assertTrue(EncodingHelper.contains_emoji(text_with_emoji))
        
        # 不包含emoji的文本
        text_without_emoji = "Hello World"
        self.assertFalse(EncodingHelper.contains_emoji(text_without_emoji))
        
        # 空文本
        self.assertFalse(EncodingHelper.contains_emoji(""))
        
        # 只有emoji
        self.assertTrue(EncodingHelper.contains_emoji("😀😂😊"))
    
    def test_extract_emojis(self):
        """测试emoji提取"""
        # 混合文本
        text = "早上好 😀，今天天气不错 🌞，心情很好 😊！"
        emojis = EncodingHelper.extract_emojis(text)
        
        # 验证提取结果
        self.assertEqual(len(emojis), 3)
        self.assertIn("😀", emojis)
        self.assertIn("🌞", emojis)
        self.assertIn("😊", emojis)
        
        # 没有emoji的文本
        no_emojis = EncodingHelper.extract_emojis("纯文本")
        self.assertEqual(len(no_emojis), 0)
        
        # 重复emoji
        repeated = "😀😀😀😂😂"
        emojis = EncodingHelper.extract_emojis(repeated)
        self.assertEqual(len(emojis), 2)  # 去重后
        self.assertIn("😀", emojis)
        self.assertIn("😂", emojis)
    
    def test_normalize_line_endings(self):
        """测试行尾符标准化"""
        # Windows行尾
        windows_text = "第一行\r\n第二行\r\n第三行"
        normalized = EncodingHelper.normalize_line_endings(windows_text)
        
        self.assertEqual(normalized, "第一行\n第二行\n第三行")
        
        # Mac行尾
        mac_text = "第一行\r第二行\r第三行"
        normalized = EncodingHelper.normalize_line_endings(mac_text)
        
        self.assertEqual(normalized, "第一行\n第二行\n第三行")
        
        # 混合行尾
        mixed_text = "第一行\r\n第二行\r第三行\n第四行"
        normalized = EncodingHelper.normalize_line_endings(mixed_text)
        
        self.assertEqual(normalized, "第一行\n第二行\n第三行\n第四行")
    
    def test_sanitize_output(self):
        """测试输出清理"""
        # 正常文本
        text = "正常输出\n第二行"
        sanitized = EncodingHelper.sanitize_output(text)
        
        self.assertEqual(sanitized, "正常输出\n第二行")
        
        # 包含控制字符
        text_with_control = "正常\x00控制\x01字符"
        sanitized = EncodingHelper.sanitize_output(text_with_control)
        
        # 控制字符应该被移除或处理
        self.assertNotIn("\x00", sanitized)
        self.assertNotIn("\x01", sanitized)
        
        # 超长文本截断
        long_text = "A" * 15000
        sanitized = EncodingHelper.sanitize_output(long_text, max_length=1000)
        
        self.assertLessEqual(len(sanitized), 1100)  # 加上截断提示
        self.assertIn("...[输出被截断]", sanitized)
    
    def test_get_system_default_encoding(self):
        """测试获取系统默认编码"""
        encoding = EncodingHelper.get_system_default_encoding()
        
        # 应该是有效的编码名称
        self.assertIsInstance(encoding, str)
        self.assertGreater(len(encoding), 0)
        
        # 验证编码是否被支持
        self.assertTrue(EncodingHelper.is_encoding_supported(encoding))
    
    def test_is_encoding_supported(self):
        """测试编码支持检查"""
        # 支持的编码
        self.assertTrue(EncodingHelper.is_encoding_supported('utf-8'))
        self.assertTrue(EncodingHelper.is_encoding_supported('gbk'))
        self.assertTrue(EncodingHelper.is_encoding_supported('ascii'))
        
        # 不支持的编码
        self.assertFalse(EncodingHelper.is_encoding_supported('invalid-encoding'))
        self.assertFalse(EncodingHelper.is_encoding_supported(''))
    
    def test_convert_encoding(self):
        """测试编码转换"""
        # UTF-8转GBK
        text = "中文测试"
        utf8_bytes = text.encode('utf-8')
        
        # 先解码为字符串
        decoded = utf8_bytes.decode('utf-8')
        
        # 转换编码
        converted = EncodingHelper.convert_encoding(decoded, 'utf-8', 'gbk')
        
        # 转换后的文本应该相同
        self.assertEqual(converted, text)
        
        # 无效编码转换
        invalid_result = EncodingHelper.convert_encoding(text, 'invalid-from', 'invalid-to')
        
        # 应该返回原始文本
        self.assertEqual(invalid_result, text)
    
    def test_encode_safe(self):
        """测试安全编码"""
        text = "安全编码测试 😀"
        
        # UTF-8编码
        utf8_bytes = EncodingHelper.encode_safe(text, 'utf-8')
        self.assertIsInstance(utf8_bytes, bytes)
        self.assertGreater(len(utf8_bytes), 0)
        
        # 解码验证
        decoded = utf8_bytes.decode('utf-8')
        self.assertEqual(decoded, text)
        
        # 无效编码
        invalid_bytes = EncodingHelper.encode_safe(text, 'invalid-encoding')
        
        # 应该返回字节数据（可能是UTF-8回退）
        self.assertIsInstance(invalid_bytes, bytes)
        
        # 空文本
        empty_bytes = EncodingHelper.encode_safe('', 'utf-8')
        self.assertEqual(empty_bytes, b'')
    
    def test_emoji_progress_integration(self):
        """测试emoji进度条集成"""
        # 这个测试验证emoji处理与其他功能的集成
        text = "任务进度: 50%"
        
        # 添加emoji
        emoji_text = "✅ " + text
        fixed = EncodingHelper.fix_emoji_encoding(emoji_text)
        
        self.assertIn("✅", fixed)
        self.assertIn("任务进度", fixed)
    
    def test_windows_cmd_compatibility(self):
        """测试Windows cmd兼容性"""
        # Windows cmd可能输出的文本
        cmd_output = "C:\\Users\\Test> echo Hello\r\nHello\r\nC:\\Users\\Test>"
        
        sanitized = EncodingHelper.sanitize_output(cmd_output)
        
        # 应该处理行尾符
        self.assertNotIn("\r\n", sanitized)  # 应该被标准化为\n
        self.assertIn("echo Hello", sanitized)
    
    def test_mixed_encoding_detection(self):
        """测试混合编码检测"""
        # 创建混合编码的数据（模拟实际场景）
        part1 = "中文部分".encode('gbk')
        part2 = " and English part".encode('utf-8')
        
        # 注意：实际中不会这样混合，但测试解码器的鲁棒性
        mixed_bytes = part1 + part2
        
        decoded = EncodingHelper.decode_with_fallback(mixed_bytes)
        
        # 应该能解码，可能有乱码但不会崩溃
        self.assertIsInstance(decoded, str)
        self.assertGreater(len(decoded), 0)
    
    def test_encoding_helper_singleton_behavior(self):
        """测试编码助手的单例行为（静态方法）"""
        # 所有方法都是静态的，应该可以直接调用
        result1 = EncodingHelper.detect_encoding(b'test')
        result2 = EncodingHelper.detect_encoding(b'test')
        
        # 相同输入应该得到相同输出
        self.assertEqual(result1, result2)
    
    @patch('utils.encoding_helper.chardet.detect')
    def test_detect_encoding_chardet_error(self, mock_detect):
        """测试chardet检测错误"""
        # 模拟chardet抛出异常
        mock_detect.side_effect = Exception("chardet error")
        
        encoding, confidence = EncodingHelper.detect_encoding(b'test data')
        
        # 应该优雅地处理错误
        self.assertIsNone(encoding)
        self.assertEqual(confidence, 0.0)
    
    def test_performance_large_data(self):
        """测试大数据处理性能"""
        # 创建大量数据
        large_text = "测试数据 " * 10000  # 约100KB
        
        # 编码
        large_bytes = large_text.encode('utf-8')
        
        # 解码（应该能快速完成）
        import time
        start_time = time.time()
        
        decoded = EncodingHelper.decode_with_fallback(large_bytes)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 验证性能（应该在合理时间内完成）
        self.assertLess(duration, 1.0)  # 1秒内完成
        self.assertEqual(len(decoded), len(large_text))