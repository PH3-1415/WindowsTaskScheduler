# GitHub仓库快速设置指南

## 🚀 如何使用GitHub Actions自动构建EXE

### 步骤1：创建GitHub仓库

1. 访问 https://github.com/new
2. 填写仓库信息：
   - Repository name: `WindowsTaskScheduler`
   - Description: `Windows定时任务管理器`
   - 选择 Public 或 Private
   - **不要勾选** "Initialize with README"（我们已经有了）
3. 点击 "Create repository"

### 步骤2：推送代码到GitHub

在本地执行以下命令：

```bash
# 进入项目目录
cd /home/ctyun/.openclaw/workspace/WindowsTaskScheduler

# 初始化Git仓库（如果还没有）
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: Windows Task Scheduler v1.0.0"

# 添加远程仓库（替换为你的用户名）
git remote add origin https://github.com/YOUR_USERNAME/WindowsTaskScheduler.git

# 推送到GitHub
git branch -M main
git push -u origin main
```

### 步骤3：等待自动构建

1. 推送代码后，GitHub Actions会自动开始构建
2. 访问仓库的 "Actions" 标签查看进度
3. 构建完成后（约5-10分钟），会自动创建Release

### 步骤4：下载EXE文件

#### 方法1：从Releases下载
1. 点击仓库的 "Releases" 标签
2. 找到最新的发布版本
3. 下载 `WindowsTaskScheduler.exe`

#### 方法2：从Actions Artifacts下载
1. 点击 "Actions" 标签
2. 选择最新的成功构建
3. 在 "Artifacts" 部分下载 `WindowsTaskScheduler-EXE`

## 🔧 自定义配置

### 修改图标
1. 准备一个 `.ico` 格式的图标文件
2. 命名为 `icon.ico`
3. 放在项目根目录
4. 推送到GitHub，触发重新构建

### 修改版本信息
编辑 `.github/workflows/build.yml` 文件中的版本号和发布说明。

### 修改构建选项
编辑 `.github/workflows/build.yml` 文件中的PyInstaller命令。

## 📋 常见问题

### Q: 构建失败怎么办？
A: 检查 Actions 日志，通常会显示具体的错误信息。常见问题：
- requirements.txt 中有不兼容的包
- Python版本不匹配
- 缺少必要的依赖

### Q: 如何添加更多依赖？
A: 编辑 `requirements.txt` 文件，添加需要的包，然后推送到GitHub。

### Q: 如何修改EXE名称？
A: 编辑 `.github/workflows/build.yml` 文件中的 `--name=WindowsTaskScheduler` 参数。

### Q: 构建需要多长时间？
A: 首次构建约10-15分钟，后续构建约5-10分钟（有缓存）。

## 🎉 完成！

按照以上步骤操作后，你就可以：
- 每次推送代码自动构建EXE
- 自动创建GitHub Release
- 用户直接下载运行，无需安装Python

---

*创建时间: 2026-03-22*
*作者: 十三香 🦞✨*