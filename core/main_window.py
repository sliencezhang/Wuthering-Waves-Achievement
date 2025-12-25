import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QTabWidget, QDialog)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap

from core.config import config
from core.signal_bus import signal_bus

from core.styles import get_main_window_style, ColorPalette
from core.widgets import BackgroundWidget, load_background_image
from core.circular_avatar import CircularAvatar
from core.avatar_selector import AvatarSelector


class TemplateMainWindow(QMainWindow):
    """模板主窗口"""
    
    def __init__(self):
        super().__init__()
        
        # 设置无边框窗口
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        # 设置窗口透明以显示圆角
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 设置窗口图标
        from core.styles import get_icon
        self.setWindowIcon(get_icon("logo"))
        
        # 加载背景图片
        self.background_pixmap = load_background_image(config.theme)

        # 设置现代UI样式
        self.setup_modern_ui()
        self.init_ui()

        # 应用滚动条样式
        from core.styles import get_scrollbar_style
        self.setStyleSheet(self.styleSheet() + get_scrollbar_style(config.theme))
        
        
        # 连接数据共享信号
        self.setup_data_sharing()
        
        # 启动时检查更新（后台进行）
        self.setup_update_check()

    def setup_modern_ui(self):
        """设置现代化UI样式"""
        self.setStyleSheet(get_main_window_style(config.theme))

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("鸣潮成就管理器")
        self.setGeometry(100, 100, 1200, 800)

        # 创建带背景图片的中心widget
        central_widget = BackgroundWidget(self.background_pixmap, config.theme)
        self.setCentralWidget(central_widget)

        # 主布局（垂直，包含标题栏和内容）
        main_container_layout = QVBoxLayout(central_widget)
        main_container_layout.setContentsMargins(0, 0, 0, 0)
        main_container_layout.setSpacing(0)
        
        # 添加自定义标题栏（主窗口显示主题切换按钮）
        from core.custom_title_bar import CustomTitleBar
        self.title_bar = CustomTitleBar(self, show_theme_toggle=True)
        main_container_layout.addWidget(self.title_bar)
        
        # 内容区域
        content_widget = QWidget()
        main_container_layout.addWidget(content_widget)
        
        main_layout = QHBoxLayout(content_widget)

        # 左侧栏
        left_widget = QWidget()
        left_widget.setMinimumWidth(250)
        left_widget.setMaximumWidth(250)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetNoConstraint)

        # 头像和设置区域
        avatar_widget = QWidget()
        avatar_layout = QVBoxLayout(avatar_widget)
        avatar_layout.setContentsMargins(10, 10, 10, 10)
        avatar_layout.setSpacing(8)
        avatar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 头像
        self.avatar_label = CircularAvatar(size=100)
        self.avatar_label.setCursor(Qt.CursorShape.PointingHandCursor)
        avatar_layout.addWidget(self.avatar_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 昵称标签
        self.nickname_label = QLabel("")
        self.nickname_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.update_nickname_style()
        avatar_layout.addWidget(self.nickname_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        left_layout.addWidget(avatar_widget)
        
        # 创建头像选择器窗口但不显示
        self.avatar_selector = AvatarSelector()
        self.setup_avatar_signals()
        
        left_layout.addStretch()
        
        main_layout.addWidget(left_widget)

        # 右侧操作区域
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # 创建标签页
        self.tab_widget = QTabWidget()

        # 添加成就管理标签页
        from core.manage_tab import ManageTab
        self.manage_tab = ManageTab()
        self.tab_widget.addTab(self.manage_tab, "🏆 成就管理")

        # 添加统计信息标签页
        from core.statistics_tab import StatisticsTab
        self.statistics_tab = StatisticsTab()
        self.tab_widget.addTab(self.statistics_tab, "📈 统计图表")
        
        # 添加数据爬取标签页
        from core.crawl_tab import CrawlTab
        self.crawl_tab = CrawlTab()
        self.tab_widget.addTab(self.crawl_tab, "📊 数据爬取")

        # 应用滚动条样式到标签页
        from core.styles import get_scrollbar_style
        self.tab_widget.setStyleSheet(self.tab_widget.styleSheet() + get_scrollbar_style(config.theme))

        right_layout.addWidget(self.tab_widget)

        # 创建角色立绘标签，固定在左下角（背景层级）
        self.character_portrait_label = QLabel(central_widget)
        self.character_portrait_label.setFixedSize(500, 500)
        self.character_portrait_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # 降低层级，让其他组件显示在上方
        self.character_portrait_label.lower()
        # 使用定时器在窗口显示后更新位置
        QTimer.singleShot(0, self.position_character_portrait)
        
        # 从配置加载当前用户的角色立绘
        character_name = config.get_current_user_character_name()
        self.update_character_portrait(character_name)
        
        main_layout.addWidget(right_widget)
        
        # 确保角色立绘在最底层
        self.character_portrait_label.lower()

        # 连接信号
        signal_bus.settings_changed.connect(self.on_settings_saved)
        signal_bus.theme_changed.connect(self.apply_theme)
        signal_bus.category_config_updated.connect(self.on_category_config_updated)
        
        # 初始化头像和昵称显示
        self.update_nickname_display()
        self.update_avatar_display()
    
    def position_character_portrait(self):
        """定位角色立绘到左下角"""
        # 获取标题栏高度
        title_bar_height = self.title_bar.height() if hasattr(self, 'title_bar') else 0
        # 定位到左下角（考虑标题栏高度）
        x = -100  # 向左偏移100px，部分超出窗口
        y = self.height() - 500 - 20  # 距离底部20px
        self.character_portrait_label.move(x, y)
        # 确保图片始终在最底层
        self.character_portrait_label.lower()
    
    def resizeEvent(self, event):
        """窗口大小改变时重新定位角色立绘"""
        super().resizeEvent(event)
        if hasattr(self, 'character_portrait_label'):
            self.position_character_portrait()



    def setup_avatar_signals(self):
            """设置头像相关信号"""
            self.avatar_label.mousePressEvent = self.on_avatar_clicked
            # 连接头像选择器的信号
            self.avatar_selector.avatar_selected.connect(self.on_avatar_selected)
            # 监听用户切换信号
            signal_bus.user_switched.connect(self.on_user_switched)
            # 初始化昵称和头像显示
            self.update_nickname_display()
            self.update_avatar_display()    
    def on_user_switched(self, username):
        """用户切换时的处理"""
        self.update_nickname_display()
        self.update_avatar_display()
        character_name = config.get_current_user_character_name()
        print(f"[DEBUG] 用户切换: {username}, 角色名: {character_name}")
        self.update_character_portrait(character_name)
    
    def update_nickname_display(self):
        """更新昵称显示"""
        current_user = config.get_current_user()
        users = config.get_users()
        current_data = users.get(current_user, {})
        
        if isinstance(current_data, dict):
            nickname = current_data.get('nickname', current_user)
        else:
            nickname = current_user
            
        self.nickname_label.setText(nickname)
        self.update_nickname_style()
    
    def update_nickname_style(self):
        """更新昵称样式"""
        colors = ColorPalette.Dark if config.theme == "dark" else ColorPalette.Light
        text_color = colors.TEXT_PRIMARY
        self.nickname_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {text_color}; margin-left: 10px;")
    
    def update_avatar_display(self):
        """更新头像显示"""
        avatar_path = config.get_current_user_avatar()
        print(f"[DEBUG] 更新头像显示: {avatar_path}")
        if avatar_path:
            print(f"[DEBUG] 找到头像文件: {os.path.exists(avatar_path)}")
            self.avatar_label.update_avatar(avatar_path)
        else:
            print("[DEBUG] 没有找到用户头像，使用默认头像")
    
    def on_avatar_clicked(self, event):
        """头像点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 显示头像选择器
            self.avatar_selector.show()
            # 将选择器窗口置于主窗口中央
            self.avatar_selector.move(
                self.geometry().center() - self.avatar_selector.rect().center()
            )
    
    def on_avatar_selected(self, avatar_path, avatar_name):
        """处理头像选择信号"""
        print(f"[DEBUG] 收到头像选择信号: {avatar_path} - {avatar_name}")
        # 更新头像
        self.avatar_label.update_avatar(avatar_path)
        
        # 更新角色立绘
        self.update_character_portrait(avatar_name)
        
        # 保存到当前用户的头像配置
        current_user = config.get_current_user()
        print(f"[DEBUG] 当前用户: {current_user}")
        config.set_user_avatar(current_user, avatar_path)
        config.set_user_character_name(current_user, avatar_name)
        print(f"[DEBUG] 头像已保存到配置: {config.get_current_user_avatar()}")
        print(f"[DEBUG] 角色名已保存到配置: {avatar_name}")
        
        # 发送日志消息
        signal_bus.log_message.emit("INFO", f"已选择头像: {avatar_name}", {})
    
    def update_character_portrait(self, character_name):
        """更新角色立绘"""
        from core.config import get_resource_path
        
        # 尝试查找角色立绘文件（支持 png 和 webp 格式）
        characters_dir = get_resource_path("resources/characters")
        portrait_path = None
        
        if characters_dir.exists():
            # 优先尝试 webp 格式
            webp_path = characters_dir / f"{character_name}.webp"
            png_path = characters_dir / f"{character_name}.png"
            
            if webp_path.exists():
                portrait_path = webp_path
            elif png_path.exists():
                portrait_path = png_path
        
        # 加载并显示图片
        if portrait_path and portrait_path.exists():
            portrait_pixmap = QPixmap(str(portrait_path))
            if not portrait_pixmap.isNull():
                # 设置图片大小为500x500，保持宽高比
                scaled_pixmap = portrait_pixmap.scaled(
                    500, 500,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.character_portrait_label.setPixmap(scaled_pixmap)
                print(f"[DEBUG] 已更新角色立绘: {character_name}")
            else:
                print(f"[WARNING] 无法加载角色立绘: {portrait_path}")
                self.character_portrait_label.clear()
        else:
            print(f"[WARNING] 未找到角色立绘: {character_name}")
            self.character_portrait_label.clear()

    def on_settings_saved(self, settings):
        """设置保存回调"""
        signal_bus.log_message.emit("SUCCESS", "设置已保存", {})
        # 更新主题和背景图片
        self.apply_theme()

    def apply_theme(self):
        """应用主题到所有组件"""
        
        # 更新背景图片
        self.background_pixmap = load_background_image(config.theme)
        central = self.centralWidget()
        if isinstance(central, BackgroundWidget):
            central.set_background(self.background_pixmap, config.theme)
        
        # 更新自定义标题栏主题
        if hasattr(self, 'title_bar'):
            self.title_bar.update_theme()
        
        self.setStyleSheet(get_main_window_style(config.theme))
        
        # 更新头像边框颜色
        if hasattr(self, 'avatar_label'):
            self.avatar_label.apply_theme(config.theme)
        
        # 更新昵称样式
        if hasattr(self, 'nickname_label'):
            self.update_nickname_style()
        
        # 数据爬取标签页
        if hasattr(self, 'crawl_tab'):
            if hasattr(self.crawl_tab, 'apply_theme'):
                self.crawl_tab.apply_theme(config.theme)
        
        # 成就管理标签页
        if hasattr(self, 'manage_tab'):
            if hasattr(self.manage_tab, 'apply_theme'):
                self.manage_tab.apply_theme(config.theme)
        
        for i in range(self.findChildren(QWidget).__len__()):
            widget = self.findChildren(QWidget)[i]
            if hasattr(widget, 'apply_theme'):
                widget.apply_theme(config.theme)

    def setup_data_sharing(self):
            """设置数据共享机制"""
            # 监听爬虫完成信号
            if hasattr(self, 'crawl_tab'):
                # 连接爬虫完成信号到管理标签页
                from PySide6.QtCore import QTimer
                # 使用定时器延迟连接，确保组件已完全初始化
                QTimer.singleShot(100, self._connect_crawler_signal)
    
    def _connect_crawler_signal(self):
        """连接爬虫信号"""
        # 爬虫完成后不需要切换标签页，所以不需要连接信号
        pass
    
    def setup_update_check(self):
        """设置更新检查"""
        # 连接更新检查信号
        signal_bus.update_available.connect(self.on_update_available)
        
        # 启动后台更新检查
        from core.update import check_for_updates_background
        check_for_updates_background()
    
    def on_update_available(self, update_info):
        """处理可用更新"""
        from core.update_dialog import UpdateDialog
        
        # 创建自定义更新对话框
        dialog = UpdateDialog(self, update_info)
        
        # 显示对话框并等待用户响应
        if dialog.exec() == QDialog.Accepted:
            # 用户点击了确认，密码已复制，链接已打开
            pass
    
    def on_category_config_updated(self):
        """处理分类配置更新"""
        # 重新加载成就管理标签页的数据
        if hasattr(self, 'manage_tab') and hasattr(self.manage_tab, 'load_local_data'):
            self.manage_tab.load_local_data()
            print("[INFO] 成就管理数据已重新加载")

    def closeEvent(self, event):
            """窗口关闭事件"""
            event.accept()
