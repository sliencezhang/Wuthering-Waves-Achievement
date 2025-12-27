# ui/styles.py
"""
统一的样式定义文件
"""
from PySide6.QtGui import QIcon
from core.config import get_resource_path

# 图标资源路径
ICON_PATH = get_resource_path("resources/icons")


# ============================================
# 辅助函数
# ============================================
def _get_rgba_color(r, g, b, opacity):
    """生成rgba颜色字符串的辅助函数

    Args:
        r, g, b: RGB颜色值 (0-255)
        opacity: 透明度 (0-255)

    Returns:
        str: rgba颜色字符串，如 "rgba(255, 255, 255, 200)"
    """
    return f"rgba({r}, {g}, {b}, {opacity})"


class ColorPalette:
    """颜色调色板 - 统一管理所有颜色"""

    # ============================================
    # 透明度配置 - 统一管理所有控件的透明度
    # 数值范围: 0(完全透明) - 255(完全不透明)
    # ============================================
    class Opacity:
        """透明度配置 - 方便统一调整"""
        # 基础控件透明度
        GROUPBOX = 80           # 分组框背景
        TEXT_INPUT = 100        # 文本输入框、表格、列表
        TAB_WIDGET_PANE = 80   # 标签页面板
        TAB_WIDGET_TAB = 80    # 标签页标签
        TAB_SELECTED = 80      # 选中的标签
        TAB_HOVER = 80         # 悬停的标签
        SETTINGS_DESC = 80     # 设置中的提示

        # 表格相关
        TABLE_HEADER = 80      # 表头
        TABLE_SELECTION = 80   # 表格选中项

        # 特殊控件
        COMBOBOX = 80          # 下拉框
        COMBOBOX_VIEW = 200     # 下拉框弹出列表
        
        # 窗口和容器
        MAIN_WINDOW = 80       # 主窗口背景
        DIALOG = 80            # 对话框背景
        STATUSBAR_LIGHT = 230  # 浅色状态栏
        STATUSBAR_DARK = 220   # 深色状态栏
        MESSAGEBOX = 80        # 消息框背景
        
        # 滚动条
        SCROLLBAR = 80         # 滚动条透明度
        
        # 通知和帮助
        HELP_TEXT = 200        # 帮助文本背景

    # 浅色主题颜色
    class Light:
        # 成功色（绿色系）
        SUCCESS, SUCCESS_HOVER, SUCCESS_PRESSED = "#ffc107", "#ffb300", "#ffa000"  # 太阳金黄色系

        # 背景色
        BG_GRAY = "#e9ecef"

        # 文字色
        TEXT_PRIMARY, TEXT_GRAY = "#495057", "#868e96"

        # 边框色
        BORDER = "#dee2e6"

        # 禁用状态
        DISABLED_BG, DISABLED_TEXT = "#adb5bd", "#868e96"

        # 表格色
        TABLE_GRID, TABLE_SELECTION = "#dee2e6", "#e7f5ff"
        TABLE_HEADER = "#f8f9fa"

        # 滚动条颜色
        SCROLLBAR_BG = "#f1f3f4"  # 滚动条背景
        SCROLLBAR_HANDLE = "#c1c1c1"  # 滚动条滑块

        # 特殊组件颜色
        TAB_HOVER = "#f1f3f5"  # Tab悬停背景
        SETTINGS_DESC_BG = "#f5f5f5"  # 设置说明背景
        SETTINGS_DESC_TEXT = "#666"  # 设置说明文字

    # 深色主题颜色
    class Dark:
        # 成功色（绿色系）
        SUCCESS, SUCCESS_HOVER, SUCCESS_PRESSED = "#64b5f6", "#42a5f5", "#2196f3"  # 月亮蓝色系

        # 文字色
        TEXT_PRIMARY, TEXT_GRAY = "#e0e0e0", "#9e9e9e"

        # 边框色
        BORDER = "#424242"

        # 禁用状态
        DISABLED_BG, DISABLED_TEXT = "#424242", "#757575"

        # 表格色
        TABLE_GRID, TABLE_SELECTION = "#424242", "#455a64"
        TABLE_HEADER = "#37474f"

        # 滚动条颜色
        SCROLLBAR_BG = "#424242"  # 滚动条背景
        SCROLLBAR_HANDLE = "#757575"  # 滚动条滑块

        # 特殊组件颜色
        TAB_HOVER = "#455a64"  # Tab悬停背景
        SETTINGS_DESC_BG = "#424242"  # 设置说明背景
        SETTINGS_DESC_TEXT = "#bdbdbd"  # 设置说明文字


class _BaseStylesClass:
    """基础样式类 - 统一的样式定义"""

    @staticmethod
    def get_button_style(theme="light"):
        """生成按钮样式 - 统一使用太阳色/月亮色"""
        colors = ColorPalette.Dark if theme == "dark" else ColorPalette.Light
        
        bg, hover, pressed = colors.SUCCESS, colors.SUCCESS_HOVER, colors.SUCCESS_PRESSED
        text_color = "white" if theme == "dark" else "#8b6914"

        return f"""
        QPushButton {{
            background-color: {bg};
            color: {text_color};
            border: none;
            border-radius: 6px;
            padding: 4px 10px;
            font-weight: bold;
            font-size: 12px;
            min-height: 20px;
        }}
        QPushButton:hover {{
            background-color: {hover};
        }}
        QPushButton:pressed {{
            background-color: {pressed};
        }}
        QPushButton:disabled {{
            background-color: {colors.DISABLED_BG};
            color: {colors.DISABLED_TEXT};
        }}
        """

    @staticmethod
    def get_groupbox_style(theme="light"):
        """生成分组框样式"""
        colors = ColorPalette.Dark if theme == "dark" else ColorPalette.Light
        border_color = colors.BORDER if theme == "dark" else colors.BG_GRAY

        # 使用统一配置的透明度
        opacity = ColorPalette.Opacity.GROUPBOX
        bg_color = _get_rgba_color(50, 50, 50, opacity) if theme == "dark" else _get_rgba_color(255, 255, 255, opacity)

        return f"""
        QGroupBox {{
            font-weight: bold;
            font-size: 13px;
            border: 2px solid {border_color};
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
            background-color: {bg_color};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 8px 0 8px;
            color: {colors.TEXT_PRIMARY};
        }}
        """

    @staticmethod
    def get_tab_widget_style(theme="light"):
        """生成标签页样式"""
        colors = ColorPalette.Dark if theme == "dark" else ColorPalette.Light
        color_style = f"color: {colors.TEXT_PRIMARY};" if theme == "dark" else ""

        # 使用统一配置的透明度
        opacity_pane = ColorPalette.Opacity.TAB_WIDGET_PANE
        opacity_tab = ColorPalette.Opacity.TAB_WIDGET_TAB
        opacity_selected = ColorPalette.Opacity.TAB_SELECTED
        opacity_hover = ColorPalette.Opacity.TAB_HOVER

        if theme == "dark":
            pane_bg = _get_rgba_color(40, 40, 40, opacity_pane)
            tab_bg = _get_rgba_color(60, 60, 60, opacity_tab)
            tab_selected_bg = _get_rgba_color(80, 80, 80, opacity_selected)
            tab_hover_bg = _get_rgba_color(84, 110, 122, opacity_hover)
        else:
            pane_bg = _get_rgba_color(255, 255, 255, opacity_pane)
            tab_bg = _get_rgba_color(230, 230, 230, opacity_tab)
            tab_selected_bg = _get_rgba_color(255, 255, 255, opacity_selected)
            tab_hover_bg = _get_rgba_color(241, 243, 245, opacity_hover)

        return f"""
        QTabWidget::pane {{
            border: 1px solid {colors.BORDER};
            border-radius: 6px;
            background-color: {pane_bg};
            min-height: 30px;
        }}
        QTabBar::tab {{
            background-color: {tab_bg};
            border: 1px solid {colors.BORDER};
            border-bottom: none;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            padding: 12px 16px;
            margin-right: 2px;
            font-weight: 500;
            min-width: 80px;
            min-height: 20px;
            {color_style}
        }}
        QTabBar::tab:selected {{
            background-color: {tab_selected_bg};
            border-bottom: 1px solid {tab_selected_bg};
        }}
        QTabBar::tab:hover {{
            background-color: {tab_hover_bg};
        }}
        """

    @staticmethod
    def get_text_input_style(theme="light"):
        """生成文本输入样式"""
        colors = ColorPalette.Dark if theme == "dark" else ColorPalette.Light
        color_style = f"color: {colors.TEXT_PRIMARY};" if theme == "dark" else ""

        # 使用统一配置的透明度
        opacity_input = ColorPalette.Opacity.TEXT_INPUT
        opacity_header = ColorPalette.Opacity.TABLE_HEADER
        opacity_selection = ColorPalette.Opacity.TABLE_SELECTION

        input_bg = _get_rgba_color(40, 40, 40, opacity_input) if theme == "dark" else _get_rgba_color(255, 255, 255, opacity_input)
        header_bg = _get_rgba_color(55, 71, 79, opacity_header) if theme == "dark" else _get_rgba_color(248, 249, 250, opacity_header)
        selection_bg = _get_rgba_color(69, 90, 100, opacity_selection) if theme == "dark" else _get_rgba_color(231, 245, 255, opacity_selection)

        return f"""
        QTextEdit, QLineEdit, QTableWidget, QListWidget {{
            border: 1px solid {colors.BORDER};
            border-radius: 6px;
            background-color: {input_bg};
            {color_style}
            font-size: 12px;
        }}
        QTableWidget {{
            gridline-color: {colors.TABLE_GRID};
            selection-background-color: {selection_bg};
        }}
        QTableWidget::item {{
            padding: 5px;
        }}
        QListWidget {{
            background-color: {input_bg};
            color: {colors.TEXT_PRIMARY};
        }}
        QListWidget::item:selected {{
            background-color: {selection_bg};
            color: {colors.TEXT_PRIMARY};
        }}
        QHeaderView::section {{
            background-color: {header_bg};
            color: {colors.TEXT_PRIMARY};
            padding: 4px;
            border: 1px solid {colors.BORDER};
        }}
        QTableCornerButton::section {{
            background-color: {header_bg};
            border: 1px solid {colors.BORDER};
        }}
        """

    @staticmethod
    def get_label_style(theme="light", label_type="normal"):
        """生成标签样式"""
        colors = ColorPalette.Dark if theme == "dark" else ColorPalette.Light
        color = colors.TEXT_GRAY if label_type == "gray" else colors.TEXT_PRIMARY

        return f"""
        QLabel {{
            color: {color};
            font-size: 12px;
        }}
        """

    @staticmethod
    def get_combobox_style(theme="light"):
        """生成下拉框样式"""
        colors = ColorPalette.Dark if theme == "dark" else ColorPalette.Light
        color_style = f"color: {colors.TEXT_PRIMARY};" if theme == "dark" else ""

        # 使用统一配置的透明度
        opacity_combo = ColorPalette.Opacity.COMBOBOX
        opacity_view = ColorPalette.Opacity.COMBOBOX_VIEW
        opacity_selection = ColorPalette.Opacity.TAB_HOVER

        bg_color = _get_rgba_color(40, 40, 40, opacity_combo) if theme == "dark" else _get_rgba_color(255, 255, 255, opacity_combo)
        view_bg = _get_rgba_color(43, 43, 43, opacity_view) if theme == "dark" else _get_rgba_color(255, 255, 255, opacity_view)
        selection_bg = _get_rgba_color(69, 90, 100, opacity_selection) if theme == "dark" else _get_rgba_color(231, 245, 255, opacity_selection)

        return f"""
        QComboBox {{
            border: 1px solid {colors.BORDER};
            border-radius: 4px;
            padding: 4px;
            background-color: {bg_color};
            {color_style}
            min-width: 60px;
        }}
        QComboBox::drop-down {{
            border: none;
        }}
        QComboBox QAbstractItemView {{
            border: 1px solid {colors.BORDER};
            background-color: {view_bg};
            color: {colors.TEXT_PRIMARY};
            selection-background-color: {selection_bg};
        }}
        """


# 创建BaseStyles实例供使用
BaseStyles = _BaseStylesClass()


def get_icon(icon_name):
    """获取图标"""
    icon_path = ICON_PATH / f"{icon_name}.ico"
    if icon_path.exists():
        return QIcon(str(icon_path))
    return QIcon()  # 返回空图标

def get_main_window_style(theme="light"):
    """主窗口样式"""
    colors = ColorPalette.Dark if theme == "dark" else ColorPalette.Light

    # 使用统一配置的透明度
    opacity = ColorPalette.Opacity.MAIN_WINDOW
    main_bg = _get_rgba_color(30, 30, 30, opacity) if theme == "dark" else _get_rgba_color(248, 249, 250, opacity)
    # 状态栏使用和BackgroundWidget遮罩层相同的颜色，保持视觉一致
    statusbar_opacity = ColorPalette.Opacity.STATUSBAR_DARK if theme == "dark" else ColorPalette.Opacity.STATUSBAR_LIGHT
    statusbar_bg = _get_rgba_color(0, 0, 0, statusbar_opacity) if theme == "dark" else _get_rgba_color(255, 255, 255, statusbar_opacity)
    messagebox_bg = _get_rgba_color(43, 43, 43, ColorPalette.Opacity.MESSAGEBOX) if theme == "dark" else _get_rgba_color(255, 255, 255, ColorPalette.Opacity.MESSAGEBOX)

    # 获取对应主题的基础样式
    base_styles = (
        BaseStyles.get_groupbox_style(theme) +
        BaseStyles.get_button_style(theme) +
        BaseStyles.get_text_input_style(theme) +
        BaseStyles.get_tab_widget_style(theme) +
        BaseStyles.get_label_style(theme) +
        BaseStyles.get_combobox_style(theme)
    )

    return f"""
    QMainWindow {{
        background-color: transparent;
        font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
    }}
    QMainWindow > QWidget {{
        background-color: {main_bg};
        border: none;
        border-top-left-radius: 15px;
        border-top-right-radius: 15px;
        border-bottom-left-radius: 15px;
        border-bottom-right-radius: 15px;
    }}
    QMainWindow QStatusBar {{
        background-color: {statusbar_bg} !important;
        color: {colors.TEXT_PRIMARY};
        font-size: 11px;
        border: 1px solid {colors.BORDER};
        border-top: none;
        margin-top: -1px;
        border-top-left-radius: 0px !important;
        border-top-right-radius: 0px !important;
        border-bottom-left-radius: 8px !important;
        border-bottom-right-radius: 8px !important;
    }}
    QStatusBar {{
        background-color: {statusbar_bg};
        color: {colors.TEXT_PRIMARY};
        font-size: 11px;
        border-top-left-radius: 0px;
        border-top-right-radius: 0px;
        border-bottom-left-radius: 8px;
        border-bottom-right-radius: 8px;
    }}
    QMessageBox {{
        background-color: {messagebox_bg};
        color: {colors.TEXT_PRIMARY};
    }}
    QMessageBox QLabel {{
        color: {colors.TEXT_PRIMARY};
    }}
    QMessageBox QPushButton {{
        min-width: 60px;
    }}
    """ + base_styles


def get_dialog_style(theme="light"):
    """对话框样式"""
    colors = ColorPalette.Dark if theme == "dark" else ColorPalette.Light

    # 使用统一配置的透明度
    opacity = ColorPalette.Opacity.DIALOG
    dialog_bg = _get_rgba_color(58, 58, 58, opacity) if theme == "dark" else _get_rgba_color(248, 249, 250, opacity)

    # 获取对应主题的基础样式
    base_styles = (
        BaseStyles.get_tab_widget_style(theme) +
        BaseStyles.get_groupbox_style(theme) +
        BaseStyles.get_button_style(theme) +
        BaseStyles.get_text_input_style(theme)
    )

    return f"""
    QDialog {{
        background-color: transparent;
        font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
    }}
    QDialog #dialogContainer {{
        background-color: {dialog_bg};
        border: 1px solid {colors.BORDER};
        border-radius: 8px;
    }}
    """ + base_styles
def get_settings_desc_style(theme="light"):
    """设置说明文本样式"""
    colors = ColorPalette.Dark if theme == "dark" else ColorPalette.Light
    # 使用统一配置的透明度
    opacity = ColorPalette.Opacity.SETTINGS_DESC
    bg_color = _get_rgba_color(66, 66, 66, opacity) if theme == "dark" else _get_rgba_color(245, 245, 245, opacity)
    text_color = colors.SETTINGS_DESC_TEXT
    return f"color: {text_color}; font-size: 12px; background-color: {bg_color}; padding: 10px; border-radius: 5px;"


def get_button_style(theme="light"):
    """按钮样式 - 统一使用太阳色/月亮色"""
    return BaseStyles.get_button_style(theme)


def get_font_gray_style(theme="light"):
    """灰色文字样式"""
    return BaseStyles.get_label_style(theme, "gray")

def get_scrollbar_style(theme="light"):
    """滚动条样式 - 用于表格等控件"""
    opacity = ColorPalette.Opacity.SCROLLBAR
    if theme == "dark":
        bg_color = _get_rgba_color(66, 66, 66, opacity)
        handle_color = _get_rgba_color(158, 158, 158, opacity)
    else:
        bg_color = _get_rgba_color(245, 245, 245, opacity)
        handle_color = _get_rgba_color(193, 193, 193, opacity)
    
    return f"""
    QScrollBar:vertical {{
        background-color: {bg_color};
        width: 12px;
        border-radius: 6px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {handle_color};
        border-radius: 6px;
        min-height: 20px;
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
        width: 0px;
    }}
    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {{
        background: none;
    }}
    QScrollBar:horizontal {{
        background-color: {bg_color};
        height: 12px;
        border-radius: 6px;
        margin: 0px;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {handle_color};
        border-radius: 6px;
        min-width: 20px;
    }}
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0px;
        height: 0px;
    }}
    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {{
        background: none;
    }}
    """


def get_scroll_area_style(theme="light"):
    """滚动区域样式 - 包含滚动区域、内容Widget和滚动条"""
    return f"""
        QScrollArea {{ 
            background-color: transparent; 
            border: none; 
        }}
        QScrollArea QWidget {{ 
            background-color: transparent; 
        }}
    """ + get_scrollbar_style(theme)

def get_label_style(theme="light"):
    return _BaseStylesClass.get_label_style(theme)

def get_notification_style(theme="light"):
    """通知样式 - 使用主题色"""
    colors = ColorPalette.Dark if theme == "dark" else ColorPalette.Light
    bg_color = colors.SUCCESS
    
    return f"""
        QLabel {{
            background-color: {bg_color};
            color: white;
            padding: 12px 20px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: bold;
        }}
    """


def get_help_text_style(theme="light"):
    """帮助文本样式"""
    opacity = ColorPalette.Opacity.HELP_TEXT
    bg_color = _get_rgba_color(43, 43, 43, opacity) if theme == "dark" else _get_rgba_color(255, 255, 255, opacity)
    
    return f"""
        QLabel {{
            background-color: {bg_color};
            padding: 20px;
            border-radius: 8px;
        }}
        QLabel a {{
            color: #3498db;
            text-decoration: underline;
        }}
    """