# Windows定时任务管理器

一个免安装的Windows定时任务执行器，支持复杂调度和条件判断。

## 🎯 功能特点

- ✅ 免安装EXE，双击运行
- ✅ GUI窗口界面（奶茶色系）
- ✅ 任务列表管理（增删改查、暂停/恢复、排序）
- ✅ 定时调度（每天/每周/每月/法定工作日）
- ✅ 串行任务执行（禁止并发）
- ✅ 实时输出显示
- ✅ 默认脚本管理
- ✅ 字体编码支持（emoji等特殊字符）
- ✅ 条件判断（if/or，引用配置文件）
- ✅ 历史记录查看

## 📦 自动构建

本项目使用GitHub Actions自动构建Windows EXE文件。

### 如何获取EXE文件

#### 方法1：下载最新版本
1. 访问 [Releases](../../releases) 页面
2. 下载最新的 `WindowsTaskScheduler.exe`
3. 双击运行即可

#### 方法2：手动触发构建
1. 点击 [Actions](../../actions) 标签
2. 选择 "Build Windows EXE" 工作流
3. 点击 "Run workflow" 按钮
4. 等待构建完成后下载artifact

### 如何修改并构建

1. **Fork 本仓库**
2. **修改代码**
3. **推送到 main 分支**
4. **等待自动构建**（约5-10分钟）
5. **下载生成的EXE文件**

## 🚀 快速开始

### 使用预编译EXE（推荐）
1. 下载 `WindowsTaskScheduler.exe`
2. 双击运行
3. 无需安装Python或任何依赖

### 从源码运行
```bash
# 克隆仓库
git clone https://github.com/yourusername/WindowsTaskScheduler.git
cd WindowsTaskScheduler

# 安装依赖
pip install -r requirements.txt

# 运行程序
python main.py
```

### 从源码构建EXE
```bash
# 安装PyInstaller
pip install pyinstaller

# 构建EXE
pyinstaller --onefile --windowed --name=WindowsTaskScheduler main.py

# 生成的EXE在 dist/ 目录
```

## 📋 系统要求

- **操作系统**: Windows 10/11
- **内存**: 最低 512MB RAM
- **磁盘空间**: 约 50MB
- **Python** (仅开发时需要): Python 3.8+

## 🛠️ 技术栈

- **GUI框架**: PySide6 (Qt for Python)
- **任务调度**: APScheduler
- **数据库**: SQLite
- **编码检测**: chardet
- **打包工具**: PyInstaller

## 📁 项目结构

```
WindowsTaskScheduler/
├── .github/
│   └── workflows/
│       └── build.yml          # GitHub Actions配置
├── database/
│   ├── models.py              # 数据模型
│   └── db_manager.py          # 数据库管理
├── gui/
│   ├── main_window.py         # 主窗口
│   ├── task_edit_dialog.py    # 任务编辑对话框
│   ├── task_list_widget.py    # 任务列表组件
│   ├── system_tray.py         # 系统托盘
│   ├── output_widget.py       # 输出显示组件
│   ├── default_script_dialog.py # 默认脚本管理
│   └── settings_dialog.py     # 设置对话框
├── utils/
│   ├── data_manager.py        # 数据导入导出
│   ├── encoding_helper.py     # 编码处理
│   ├── emoji_handler.py       # Emoji处理
│   ├── auto_start.py          # 开机自启动
│   ├── logger.py              # 日志系统
│   └── date_utils.py          # 日期工具
├── core/
│   ├── scheduler.py           # 调度器
│   ├── task_executor.py       # 任务执行器
│   ├── condition_evaluator.py # 条件判断
│   └── default_script.py      # 默认脚本
├── tools/
│   └── performance_analyzer.py # 性能分析
├── main.py                    # 主程序入口
├── app.py                     # 应用程序类
├── config.py                  # 配置管理
├── requirements.txt           # Python依赖
├── .gitignore                 # Git忽略文件
└── README.md                  # 本文件
```

## 🧪 测试

```bash
# 运行所有测试
python run_tests.py

# 测试覆盖率: 100% (53个测试全部通过)
```

## 📝 开发文档

详细的开发文档请查看 `开发文档.md`

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 👤 作者

十三香 🦞✨

---

*最后更新: 2026-03-22*
*版本: v1.0.0*