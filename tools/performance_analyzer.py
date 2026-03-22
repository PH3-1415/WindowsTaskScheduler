"""
性能分析工具 - 分析代码性能并进行优化
"""

import time
import cProfile
import pstats
import io
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any
import psutil
import threading


class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        self.results = {}
        self.metrics = {}
        self.optimizations = []
    
    def analyze_function(self, func, *args, **kwargs) -> Dict[str, Any]:
        """分析函数性能"""
        print(f"🔍 分析函数: {func.__name__}")
        
        # 预热
        for _ in range(3):
            func(*args, **kwargs)
        
        # 测量执行时间
        start_time = time.perf_counter()
        
        # 使用cProfile进行详细分析
        profiler = cProfile.Profile()
        profiler.enable()
        
        result = func(*args, **kwargs)
        
        profiler.disable()
        
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        
        # 分析性能数据
        s = io.StringIO()
        stats = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        stats.print_stats(20)  # 显示前20个最耗时的函数
        
        profile_output = s.getvalue()
        
        # 收集指标
        metrics = {
            'execution_time': execution_time,
            'function_name': func.__name__,
            'profile_data': profile_output,
            'memory_usage': self._get_memory_usage(),
            'cpu_usage': self._get_cpu_usage(),
            'call_count': stats.total_calls,
            'total_time': stats.total_tt,
        }
        
        self.results[func.__name__] = metrics
        
        print(f"⏱️  执行时间: {execution_time:.4f}秒")
        print(f"🧠 内存使用: {metrics['memory_usage']:.2f} MB")
        print(f"⚡ CPU使用: {metrics['cpu_usage']:.1f}%")
        
        return metrics
    
    def analyze_module(self, module_name: str) -> Dict[str, Any]:
        """分析模块性能"""
        print(f"📦 分析模块: {module_name}")
        
        try:
            module = __import__(module_name)
        except ImportError:
            print(f"❌ 无法导入模块: {module_name}")
            return {}
        
        # 分析模块中的所有函数
        functions = []
        for name in dir(module):
            obj = getattr(module, name)
            if callable(obj) and not name.startswith('_'):
                functions.append((name, obj))
        
        print(f"🔍 发现 {len(functions)} 个函数")
        
        module_metrics = {
            'module_name': module_name,
            'function_count': len(functions),
            'functions': {}
        }
        
        # 分析每个函数（限制数量）
        for i, (func_name, func) in enumerate(functions[:10]):  # 只分析前10个
            if i >= 5:  # 只详细分析前5个
                break
            
            try:
                # 创建简单的测试参数
                test_args = self._create_test_args(func)
                
                # 分析函数
                metrics = self.analyze_function(func, *test_args)
                module_metrics['functions'][func_name] = metrics
            except Exception as e:
                print(f"⚠️  分析函数 {func_name} 失败: {e}")
        
        return module_metrics
    
    def analyze_database_operations(self, db_manager) -> Dict[str, Any]:
        """分析数据库操作性能"""
        print("🗄️  分析数据库操作性能...")
        
        metrics = {}
        
        # 测试添加任务
        start_time = time.perf_counter()
        
        # 创建测试任务
        from database.models import Task
        import json
        
        test_task = Task(
            name='性能测试任务',
            description='用于性能测试',
            command='echo "Performance Test"',
            schedule_type='daily',
            schedule_config=json.dumps({'time': '12:00'}),
            enabled=True,
            priority=0
        )
        
        task_id = db_manager.add_task(test_task)
        
        end_time = time.perf_counter()
        add_time = end_time - start_time
        
        metrics['add_task'] = add_time
        
        print(f"📝 添加任务耗时: {add_time:.4f}秒")
        
        # 测试获取任务
        start_time = time.perf_counter()
        task = db_manager.get_task(task_id)
        end_time = time.perf_counter()
        get_time = end_time - start_time
        
        metrics['get_task'] = get_time
        
        print(f"🔍 获取任务耗时: {get_time:.4f}秒")
        
        # 测试获取所有任务
        start_time = time.perf_counter()
        tasks = db_manager.get_all_tasks()
        end_time = time.perf_counter()
        get_all_time = end_time - start_time
        
        metrics['get_all_tasks'] = get_all_time
        
        print(f"📋 获取所有任务耗时: {get_all_time:.4f}秒")
        
        # 测试更新任务
        start_time = time.perf_counter()
        task.name = '更新后的任务'
        success = db_manager.update_task(task)
        end_time = time.perf_counter()
        update_time = end_time - start_time
        
        metrics['update_task'] = update_time
        
        print(f"🔄 更新任务耗时: {update_time:.4f}秒")
        
        # 测试删除任务
        start_time = time.perf_counter()
        success = db_manager.delete_task(task_id)
        end_time = time.perf_counter()
        delete_time = end_time - start_time
        
        metrics['delete_task'] = delete_time
        
        print(f"🗑️  删除任务耗时: {delete_time:.4f}秒")
        
        # 批量操作测试
        start_time = time.perf_counter()
        
        task_ids = []
        for i in range(10):
            task = Task(
                name=f'批量任务{i}',
                description=f'批量测试{i}',
                command=f'echo "Batch {i}"',
                schedule_type='daily',
                schedule_config=json.dumps({'time': f'{i+9}:00'}),
                enabled=True,
                priority=i
            )
            task_id = db_manager.add_task(task)
            task_ids.append(task_id)
        
        end_time = time.perf_counter()
        batch_add_time = end_time - start_time
        
        metrics['batch_add_10_tasks'] = batch_add_time
        
        print(f"📦 批量添加10个任务耗时: {batch_add_time:.4f}秒")
        
        # 清理批量任务
        for task_id in task_ids:
            db_manager.delete_task(task_id)
        
        self.metrics['database'] = metrics
        
        return metrics
    
    def analyze_encoding_performance(self) -> Dict[str, Any]:
        """分析编码处理性能"""
        print("🔤 分析编码处理性能...")
        
        from utils.encoding_helper import EncodingHelper
        
        metrics = {}
        
        # 测试不同大小的数据
        test_sizes = [100, 1000, 10000, 100000]  # 字节
        
        for size in test_sizes:
            # 生成测试数据
            test_data = 'A' * size
            encoded_data = test_data.encode('utf-8')
            
            # 测试解码性能
            start_time = time.perf_counter()
            
            for _ in range(100):  # 多次执行取平均值
                EncodingHelper.decode_with_fallback(encoded_data)
            
            end_time = time.perf_counter()
            avg_time = (end_time - start_time) / 100
            
            metrics[f'decode_{size}_bytes'] = avg_time
            
            print(f"📊 {size}字节数据解码平均耗时: {avg_time:.6f}秒")
        
        # 测试emoji处理
        test_text = "Hello 😀 World 🌍 Test " * 100
        
        start_time = time.perf_counter()
        
        for _ in range(100):
            EncodingHelper.fix_emoji_encoding(test_text)
            EncodingHelper.contains_emoji(test_text)
        
        end_time = time.perf_counter()
        avg_time = (end_time - start_time) / 100
        
        metrics['emoji_processing'] = avg_time
        
        print(f"😀 Emoji处理平均耗时: {avg_time:.6f}秒")
        
        self.metrics['encoding'] = metrics
        
        return metrics
    
    def analyze_gui_performance(self) -> Dict[str, Any]:
        """分析GUI性能"""
        print("🖥️  分析GUI性能...")
        
        metrics = {}
        
        # 这里可以添加GUI性能测试
        # 由于GUI测试需要Qt环境，这里只做框架
        
        print("⚠️  GUI性能测试需要Qt环境，跳过详细测试")
        
        self.metrics['gui'] = metrics
        
        return metrics
    
    def generate_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """生成优化建议"""
        print("💡 生成优化建议...")
        
        suggestions = []
        
        # 分析数据库性能
        if 'database' in self.metrics:
            db_metrics = self.metrics['database']
            
            # 检查添加任务性能
            if db_metrics.get('add_task', 0) > 0.1:  # 超过100ms
                suggestions.append({
                    'category': '数据库',
                    'issue': '添加任务耗时过长',
                    'suggestion': '考虑使用批量插入或优化索引',
                    'priority': '高'
                })
        
        # 分析编码性能
        if 'encoding' in self.metrics:
            encoding_metrics = self.metrics['encoding']
            
            # 检查大文件解码性能
            if encoding_metrics.get('decode_100000_bytes', 0) > 0.01:  # 超过10ms
                suggestions.append({
                    'category': '编码处理',
                    'issue': '大文件解码性能不佳',
                    'suggestion': '考虑使用流式处理或分块解码',
                    'priority': '中'
                })
        
        # 通用建议
        suggestions.extend([
            {
                'category': '通用',
                'issue': '内存使用监控不足',
                'suggestion': '添加内存使用监控和自动清理机制',
                'priority': '中'
            },
            {
                'category': '通用',
                'issue': '错误处理需要完善',
                'suggestion': '添加更多异常处理和错误日志',
                'priority': '高'
            },
            {
                'category': '性能',
                'issue': '启动时间优化',
                'suggestion': '延迟加载非核心模块',
                'priority': '低'
            }
        ])
        
        self.optimizations = suggestions
        
        return suggestions
    
    def generate_report(self) -> str:
        """生成性能报告"""
        print("📄 生成性能报告...")
        
        report_lines = []
        
        # 报告标题
        report_lines.append("=" * 60)
        report_lines.append("📊 Windows定时任务管理器 - 性能分析报告")
        report_lines.append("=" * 60)
        
        # 总体统计
        report_lines.append("\n📈 总体统计")
        report_lines.append("-" * 40)
        
        total_time = sum(
            metric.get('execution_time', 0) 
            for metrics in self.results.values() 
            for metric in [metrics] if isinstance(metrics, dict)
        )
        
        report_lines.append(f"总测试函数数: {len(self.results)}")
        report_lines.append(f"总执行时间: {total_time:.4f}秒")
        
        # 数据库性能
        if 'database' in self.metrics:
            report_lines.append("\n🗄️  数据库性能")
            report_lines.append("-" * 40)
            
            db_metrics = self.metrics['database']
            for key, value in db_metrics.items():
                report_lines.append(f"{key}: {value:.4f}秒")
        
        # 编码性能
        if 'encoding' in self.metrics:
            report_lines.append("\n🔤 编码处理性能")
            report_lines.append("-" * 40)
            
            encoding_metrics = self.metrics['encoding']
            for key, value in encoding_metrics.items():
                report_lines.append(f"{key}: {value:.6f}秒")
        
        # 优化建议
        if self.optimizations:
            report_lines.append("\n💡 优化建议")
            report_lines.append("-" * 40)
            
            for suggestion in self.optimizations:
                report_lines.append(
                    f"[{suggestion['priority']}] {suggestion['category']}: "
                    f"{suggestion['issue']}"
                )
                report_lines.append(f"  建议: {suggestion['suggestion']}")
        
        # 总结
        report_lines.append("\n" + "=" * 60)
        report_lines.append("🎯 性能分析总结")
        report_lines.append("=" * 60)
        
        # 找出性能瓶颈
        bottlenecks = []
        if 'database' in self.metrics:
            db_metrics = self.metrics['database']
            for key, value in db_metrics.items():
                if value > 0.05:  # 超过50ms
                    bottlenecks.append(f"数据库操作: {key} ({value:.4f}秒)")
        
        if bottlenecks:
            report_lines.append("\n⚠️  发现性能瓶颈:")
            for bottleneck in bottlenecks:
                report_lines.append(f"  • {bottleneck}")
        else:
            report_lines.append("\n✅ 未发现明显性能瓶颈")
        
        # 最终建议
        report_lines.append("\n🚀 推荐优化措施:")
        report_lines.append("  1. 添加数据库连接池")
        report_lines.append("  2. 实现任务执行队列")
        report_lines.append("  3. 添加内存监控和自动清理")
        report_lines.append("  4. 优化GUI渲染性能")
        
        report = "\n".join(report_lines)
        
        # 保存报告到文件
        report_file = Path(__file__).parent.parent / "performance_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📁 报告已保存到: {report_file}")
        
        return report
    
    def _get_memory_usage(self) -> float:
        """获取内存使用情况（MB）"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    def _get_cpu_usage(self) -> float:
        """获取CPU使用率"""
        return psutil.cpu_percent(interval=0.1)
    
    def _create_test_args(self, func) -> tuple:
        """创建测试参数"""
        import inspect
        
        try:
            # 获取函数签名
            sig = inspect.signature(func)
            
            args = []
            for param_name, param in sig.parameters.items():
                # 根据参数类型创建测试值
                if param.annotation == str:
                    args.append("test")
                elif param.annotation == int:
                    args.append(1)
                elif param.annotation == list:
                    args.append([])
                elif param.annotation == dict:
                    args.append({})
                elif param.annotation == bool:
                    args.append(True)
                else:
                    args.append(None)
            
            return tuple(args)
        
        except:
            # 如果无法获取签名，返回空参数
            return ()
    
    def run_full_analysis(self):
        """运行完整性能分析"""
        print("🚀 开始完整性能分析...")
        
        # 分析编码性能
        self.analyze_encoding_performance()
        
        # 分析GUI性能（框架）
        self.analyze_gui_performance()
        
        # 生成优化建议
        self.generate_optimization_suggestions()
        
        # 生成报告
        report = self.generate_report()
        
        print("✅ 性能分析完成！")
        
        return report


def main():
    """主函数"""
    analyzer = PerformanceAnalyzer()
    
    print("=" * 60)
    print("🔧 Windows定时任务管理器 - 性能分析工具")
    print("=" * 60)
    
    # 运行完整分析
    report = analyzer.run_full_analysis()
    
    # 打印报告摘要
    print("\n📋 报告摘要:")
    lines = report.split('\n')
    for line in lines:
        if '秒' in line or '建议' in line or '瓶颈' in line:
            print(f"  {line}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())