"""
测试运行器 - 运行所有测试并生成报告
"""

import sys
import os
import time
from pathlib import Path


def run_all_tests():
    """运行所有测试"""
    print("🧪 运行所有测试...")
    
    test_results = {}
    
    # 添加项目根目录到Python路径
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # 运行数据库测试
    print("\n" + "=" * 60)
    print("🗄️  运行数据库管理器测试")
    print("=" * 60)
    
    try:
        import unittest
        from tests.unit.test_db_manager import TestDatabaseManager
        
        suite = unittest.TestLoader().loadTestsFromTestCase(TestDatabaseManager)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        test_results['database'] = {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success': result.wasSuccessful()
        }
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        test_results['database'] = {'error': str(e)}
    
    # 运行编码助手测试
    print("\n" + "=" * 60)
    print("🔤 运行编码助手测试")
    print("=" * 60)
    
    try:
        from tests.unit.test_encoding_helper_fixed import TestEncodingHelper
        
        suite = unittest.TestLoader().loadTestsFromTestCase(TestEncodingHelper)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        test_results['encoding'] = {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success': result.wasSuccessful()
        }
    except Exception as e:
        print(f"❌ 编码助手测试失败: {e}")
        test_results['encoding'] = {'error': str(e)}
    
    # 运行emoji处理器测试
    print("\n" + "=" * 60)
    print("😀 运行Emoji处理器测试")
    print("=" * 60)
    
    try:
        from tests.unit.test_emoji_handler import TestEmojiHandler
        
        suite = unittest.TestLoader().loadTestsFromTestCase(TestEmojiHandler)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        test_results['emoji'] = {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success': result.wasSuccessful()
        }
    except Exception as e:
        print(f"❌ Emoji处理器测试失败: {e}")
        test_results['emoji'] = {'error': str(e)}
    
    return test_results


def generate_test_report(test_results):
    """生成测试报告"""
    print("\n" + "=" * 60)
    print("📊 测试报告")
    print("=" * 60)
    
    total_tests = 0
    total_failures = 0
    total_errors = 0
    all_success = True
    
    for module, results in test_results.items():
        if 'error' in results:
            print(f"{module.upper():15} ❌ 错误: {results['error']}")
            all_success = False
            continue
        
        tests_run = results['tests_run']
        failures = results['failures']
        errors = results['errors']
        success = results['success']
        
        total_tests += tests_run
        total_failures += failures
        total_errors += errors
        
        status = "✅ 通过" if success else "❌ 失败"
        
        print(f"{module.upper():15} {status}")
        print(f"              测试数: {tests_run}")
        print(f"              失败数: {failures}")
        print(f"              错误数: {errors}")
    
    print("\n" + "=" * 60)
    print("📈 总体统计")
    print("=" * 60)
    
    print(f"总测试数: {total_tests}")
    print(f"总失败数: {total_failures}")
    print(f"总错误数: {total_errors}")
    
    success_rate = (total_tests - total_failures - total_errors) / total_tests * 100 if total_tests > 0 else 0
    print(f"成功率: {success_rate:.1f}%")
    
    if all_success and total_failures == 0 and total_errors == 0:
        print("\n🎉 所有测试通过！")
        return True
    else:
        print("\n⚠️  部分测试失败，需要修复")
        return False


def run_performance_analysis():
    """运行性能分析"""
    print("\n" + "=" * 60)
    print("⚡ 运行性能分析")
    print("=" * 60)
    
    try:
        from tools.performance_analyzer import PerformanceAnalyzer
        
        analyzer = PerformanceAnalyzer()
        
        # 运行编码性能分析
        print("🔤 分析编码处理性能...")
        encoding_metrics = analyzer.analyze_encoding_performance()
        
        # 生成优化建议
        print("💡 生成优化建议...")
        suggestions = analyzer.generate_optimization_suggestions()
        
        # 生成报告
        print("📄 生成性能报告...")
        report = analyzer.generate_report()
        
        # 打印关键指标
        print("\n📊 关键性能指标:")
        if 'encoding' in analyzer.metrics:
            for key, value in analyzer.metrics['encoding'].items():
                if 'bytes' in key:
                    print(f"  {key}: {value:.6f}秒")
        
        if suggestions:
            print("\n💡 关键优化建议:")
            for suggestion in suggestions[:3]:  # 只显示前3个
                print(f"  [{suggestion['priority']}] {suggestion['issue']}")
        
        return True
    except Exception as e:
        print(f"❌ 性能分析失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 Windows定时任务管理器 - 测试与性能分析")
    print("=" * 60)
    
    start_time = time.time()
    
    # 运行所有测试
    test_results = run_all_tests()
    
    # 生成测试报告
    tests_passed = generate_test_report(test_results)
    
    # 运行性能分析
    if tests_passed:
        print("\n" + "=" * 60)
        print("🔧 测试通过，开始性能优化...")
        print("=" * 60)
        
        performance_ok = run_performance_analysis()
    else:
        print("\n⚠️  测试失败，跳过性能分析")
        performance_ok = False
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print("\n" + "=" * 60)
    print("📋 执行总结")
    print("=" * 60)
    
    print(f"总执行时间: {total_time:.2f}秒")
    print(f"测试结果: {'✅ 通过' if tests_passed else '❌ 失败'}")
    print(f"性能分析: {'✅ 完成' if performance_ok else '⚠️  跳过/失败'}")
    
    if tests_passed and performance_ok:
        print("\n🎉 测试和性能分析完成！")
        print("🚀 项目已准备好进入下一阶段")
        return 0
    else:
        print("\n⚠️  需要修复问题后再继续")
        return 1


if __name__ == '__main__':
    sys.exit(main())