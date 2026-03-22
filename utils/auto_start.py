"""
开机自启动管理工具
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class AutoStartManager:
    """开机自启动管理器"""
    
    def __init__(self, app_name: str = "WindowsTaskScheduler"):
        self.app_name = app_name
        self.is_windows = sys.platform == 'win32'
        self.is_mac = sys.platform == 'darwin'
        self.is_linux = sys.platform.startswith('linux')
        
        # 获取应用路径
        self.app_path = self._get_app_path()
    
    def _get_app_path(self) -> Optional[str]:
        """获取应用路径"""
        if getattr(sys, 'frozen', False):
            # 打包后的exe
            return os.path.abspath(sys.executable)
        else:
            # 开发环境
            script_path = sys.argv[0]
            if script_path and os.path.exists(script_path):
                return os.path.abspath(script_path)
        
        logger.warning("无法确定应用路径")
        return None
    
    def is_enabled(self) -> bool:
        """检查是否已启用开机自启动"""
        if self.is_windows:
            return self._is_windows_enabled()
        elif self.is_mac:
            return self._is_mac_enabled()
        elif self.is_linux:
            return self._is_linux_enabled()
        
        logger.warning(f"不支持的操作系统: {sys.platform}")
        return False
    
    def enable(self) -> bool:
        """启用开机自启动"""
        if not self.app_path:
            logger.error("无法启用开机自启动：应用路径未知")
            return False
        
        if self.is_windows:
            return self._enable_windows()
        elif self.is_mac:
            return self._enable_mac()
        elif self.is_linux:
            return self._enable_linux()
        
        logger.warning(f"不支持的操作系统: {sys.platform}")
        return False
    
    def disable(self) -> bool:
        """禁用开机自启动"""
        if self.is_windows:
            return self._disable_windows()
        elif self.is_mac:
            return self._disable_mac()
        elif self.is_linux:
            return self._disable_linux()
        
        logger.warning(f"不支持的操作系统: {sys.platform}")
        return False
    
    # ========== Windows实现 ==========
    
    def _is_windows_enabled(self) -> bool:
        """检查Windows开机自启动是否已启用"""
        try:
            import winreg
            
            key = winreg.HKEY_CURRENT_USER
            subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            with winreg.OpenKey(key, subkey, 0, winreg.KEY_READ) as reg_key:
                try:
                    value, _ = winreg.QueryValueEx(reg_key, self.app_name)
                    return value == self.app_path
                except FileNotFoundError:
                    return False
        except ImportError:
            logger.warning("winreg模块不可用，无法检查Windows开机自启动")
            return False
        except Exception as e:
            logger.error(f"检查Windows开机自启动失败: {e}")
            return False
    
    def _enable_windows(self) -> bool:
        """启用Windows开机自启动"""
        try:
            import winreg
            
            key = winreg.HKEY_CURRENT_USER
            subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            with winreg.OpenKey(key, subkey, 0, winreg.KEY_WRITE) as reg_key:
                winreg.SetValueEx(reg_key, self.app_name, 0, winreg.REG_SZ, self.app_path)
                logger.info(f"已启用Windows开机自启动: {self.app_path}")
                return True
        except ImportError:
            logger.error("winreg模块不可用，无法启用Windows开机自启动")
            return False
        except PermissionError:
            logger.error("权限不足，无法写入注册表")
            return False
        except Exception as e:
            logger.error(f"启用Windows开机自启动失败: {e}")
            return False
    
    def _disable_windows(self) -> bool:
        """禁用Windows开机自启动"""
        try:
            import winreg
            
            key = winreg.HKEY_CURRENT_USER
            subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            with winreg.OpenKey(key, subkey, 0, winreg.KEY_WRITE) as reg_key:
                try:
                    winreg.DeleteValue(reg_key, self.app_name)
                    logger.info("已禁用Windows开机自启动")
                    return True
                except FileNotFoundError:
                    # 值不存在，说明已经禁用了
                    return True
        except ImportError:
            logger.error("winreg模块不可用，无法禁用Windows开机自启动")
            return False
        except PermissionError:
            logger.error("权限不足，无法修改注册表")
            return False
        except Exception as e:
            logger.error(f"禁用Windows开机自启动失败: {e}")
            return False
    
    # ========== macOS实现 ==========
    
    def _is_mac_enabled(self) -> bool:
        """检查macOS开机自启动是否已启用"""
        launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
        plist_file = launch_agents_dir / f"com.{self.app_name.lower()}.plist"
        
        return plist_file.exists()
    
    def _enable_mac(self) -> bool:
        """启用macOS开机自启动"""
        try:
            launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
            launch_agents_dir.mkdir(parents=True, exist_ok=True)
            
            plist_file = launch_agents_dir / f"com.{self.app_name.lower()}.plist"
            
            plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.{self.app_name.lower()}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{self.app_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>'''
            
            plist_file.write_text(plist_content, encoding='utf-8')
            logger.info(f"已启用macOS开机自启动: {plist_file}")
            return True
        except Exception as e:
            logger.error(f"启用macOS开机自启动失败: {e}")
            return False
    
    def _disable_mac(self) -> bool:
        """禁用macOS开机自启动"""
        try:
            launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
            plist_file = launch_agents_dir / f"com.{self.app_name.lower()}.plist"
            
            if plist_file.exists():
                plist_file.unlink()
                logger.info("已禁用macOS开机自启动")
            
            return True
        except Exception as e:
            logger.error(f"禁用macOS开机自启动失败: {e}")
            return False
    
    # ========== Linux实现 ==========
    
    def _is_linux_enabled(self) -> bool:
        """检查Linux开机自启动是否已启用"""
        autostart_dir = Path.home() / ".config" / "autostart"
        desktop_file = autostart_dir / f"{self.app_name.lower()}.desktop"
        
        return desktop_file.exists()
    
    def _enable_linux(self) -> bool:
        """启用Linux开机自启动"""
        try:
            autostart_dir = Path.home() / ".config" / "autostart"
            autostart_dir.mkdir(parents=True, exist_ok=True)
            
            desktop_file = autostart_dir / f"{self.app_name.lower()}.desktop"
            
            desktop_content = f'''[Desktop Entry]
Type=Application
Name={self.app_name}
Exec={self.app_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Comment=Windows定时任务管理器
'''
            
            desktop_file.write_text(desktop_content, encoding='utf-8')
            logger.info(f"已启用Linux开机自启动: {desktop_file}")
            return True
        except Exception as e:
            logger.error(f"启用Linux开机自启动失败: {e}")
            return False
    
    def _disable_linux(self) -> bool:
        """禁用Linux开机自启动"""
        try:
            autostart_dir = Path.home() / ".config" / "autostart"
            desktop_file = autostart_dir / f"{self.app_name.lower()}.desktop"
            
            if desktop_file.exists():
                desktop_file.unlink()
                logger.info("已禁用Linux开机自启动")
            
            return True
        except Exception as e:
            logger.error(f"禁用Linux开机自启动失败: {e}")
            return False
    
    # ========== 工具方法 ==========
    
    def toggle(self) -> bool:
        """切换开机自启动状态"""
        if self.is_enabled():
            return self.disable()
        else:
            return self.enable()
    
    def get_status_text(self) -> str:
        """获取状态文本"""
        if self.is_enabled():
            return "已启用开机自启动"
        else:
            return "未启用开机自启动"


# 单例实例
_auto_start_manager = None

def get_auto_start_manager() -> AutoStartManager:
    """获取AutoStartManager单例"""
    global _auto_start_manager
    if _auto_start_manager is None:
        _auto_start_manager = AutoStartManager()
    return _auto_start_manager


if __name__ == '__main__':
    # 测试代码
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    manager = AutoStartManager()
    
    print(f"应用路径: {manager.app_path}")
    print(f"当前状态: {manager.get_status_text()}")
    
    # 测试切换
    print("\n测试切换开机自启动...")
    if manager.toggle():
        print(f"切换成功，新状态: {manager.get_status_text()}")
    else:
        print("切换失败")
    
    # 切换回来
    print("\n切换回原状态...")
    if manager.toggle():
        print(f"切换成功，新状态: {manager.get_status_text()}")
    else:
        print("切换失败")