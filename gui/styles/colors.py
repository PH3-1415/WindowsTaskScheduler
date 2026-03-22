"""
奶茶色系颜色定义
"""

# 主色调 - 奶茶色系
COLORS = {
    # 背景色
    'background_primary': '#F5F1E8',    # 浅米白 - 主背景
    'background_secondary': '#E8DFD5',  # 浅奶茶色 - 侧边栏背景
    'background_tertiary': '#D4B996',   # 奶茶棕 - 按钮背景
    'background_card': '#FFFFFF',       # 白色 - 卡片背景
    'background_hover': '#C2A57C',      # 深奶茶棕 - 悬停背景
    
    # 文字色
    'text_primary': '#5D4037',          # 深棕色 - 主要文字
    'text_secondary': '#8D6E63',        # 中棕色 - 次要文字
    'text_tertiary': '#BCAAA4',         # 浅棕色 - 辅助文字
    'text_light': '#FFFFFF',            # 白色 - 浅色背景文字
    'text_disabled': '#BDBDBD',         # 浅灰色 - 禁用文字
    
    # 状态色
    'status_success': '#81C784',        # 浅绿色 - 成功
    'status_error': '#E57373',          # 浅红色 - 失败
    'status_running': '#64B5F6',        # 浅蓝色 - 运行中
    'status_waiting': '#BDBDBD',        # 浅灰色 - 等待
    'status_paused': '#FFB74D',         # 浅橙色 - 暂停
    'status_disabled': '#E0E0E0',       # 更浅灰色 - 禁用
    
    # 边框色
    'border_light': '#D7CCC8',          # 浅边框
    'border_medium': '#BCAAA4',         # 中边框
    'border_dark': '#8D6E63',           # 深边框
    
    # 交互色
    'button_normal': '#D4B996',         # 按钮正常状态
    'button_hover': '#C2A57C',          # 按钮悬停状态
    'button_pressed': '#B39D72',        # 按钮按下状态
    'button_disabled': '#E0E0E0',       # 按钮禁用状态
    
    'link_normal': '#5D4037',           # 链接正常状态
    'link_hover': '#8D6E63',            # 链接悬停状态
    'link_visited': '#6D4C41',          # 链接访问过状态
    
    # 特殊元素
    'selection': 'rgba(212, 185, 150, 0.3)',  # 选择背景（半透明奶茶色）
    'focus_ring': '#D4B996',                   # 焦点环
    'shadow': 'rgba(93, 64, 55, 0.1)',         # 阴影
}


def get_color(name: str, default: str = '#000000') -> str:
    """获取颜色值"""
    return COLORS.get(name, default)


def rgba(color_name: str, alpha: float = 1.0) -> str:
    """获取带透明度的颜色"""
    color = get_color(color_name)
    if color.startswith('#'):
        # 将十六进制颜色转换为RGBA
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        return f'rgba({r}, {g}, {b}, {alpha})'
    elif color.startswith('rgba'):
        # 已经是RGBA格式，只修改alpha
        parts = color[5:-1].split(',')
        if len(parts) >= 3:
            return f'rgba({parts[0]}, {parts[1]}, {parts[2]}, {alpha})'
    
    return color


def get_status_color(status: str) -> str:
    """根据状态获取颜色"""
    status_map = {
        'success': 'status_success',
        'failed': 'status_error',
        'running': 'status_running',
        'waiting': 'status_waiting',
        'paused': 'status_paused',
        'disabled': 'status_disabled',
    }
    return get_color(status_map.get(status, 'status_waiting'))


def get_button_color(state: str = 'normal') -> str:
    """根据按钮状态获取颜色"""
    state_map = {
        'normal': 'button_normal',
        'hover': 'button_hover',
        'pressed': 'button_pressed',
        'disabled': 'button_disabled',
    }
    return get_color(state_map.get(state, 'button_normal'))


# QSS样式片段
QSS_COLOR_SNIPPETS = {
    'background_primary': f"background-color: {COLORS['background_primary']};",
    'background_secondary': f"background-color: {COLORS['background_secondary']};",
    'text_primary': f"color: {COLORS['text_primary']};",
    'border_light': f"border: 1px solid {COLORS['border_light']};",
}


def generate_qss_color_variables() -> str:
    """生成QSS颜色变量定义"""
    variables = []
    for name, color in COLORS.items():
        if not name.startswith('rgba'):
            variable_name = name.replace('_', '-')
            variables.append(f'    --{variable_name}: {color};')
    
    return '\n'.join(variables)


if __name__ == '__main__':
    # 测试颜色输出
    print("奶茶色系颜色定义:")
    for name, color in COLORS.items():
        print(f"{name:20}: {color}")
    
    print("\nQSS变量:")
    print(generate_qss_color_variables())