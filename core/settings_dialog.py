from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                               QWidget, QLabel, QLineEdit, QPushButton,
                               QDialogButtonBox, QFileDialog, QGroupBox, QCheckBox, QTableWidget,
                               QTableWidgetItem, QComboBox)
from PySide6.QtCore import Qt

from core.config import config
from core.signal_bus import signal_bus
from core.styles import (get_dialog_style, get_settings_desc_style, get_button_style)
from core.custom_message_box import CustomMessageBox
from core.widgets import BackgroundWidget, load_background_image


class TemplateSettingsDialog(QDialog):
    """模板设置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("设置")
        self.setModal(True)
        self.setFixedSize(850, 600)
        
        # 设置无边框窗口和透明背景以实现圆角
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setStyleSheet(get_dialog_style(config.theme))

        # 背景图片初始化
        self.background_pixmap = None
        self._load_background_image()

        self._init_ui()
        self._load_current_settings()

    def _init_ui(self):
        """初始化UI"""
        # 创建主布局（透明）
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建容器（用于绘制背景）
        self.container_widget = BackgroundWidget(self.background_pixmap, config.theme)
        self.container_widget.setObjectName("dialogContainer")
        container_layout = QVBoxLayout(self.container_widget)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        main_layout.addWidget(self.container_widget)
        
        # 添加自定义标题栏（默认不显示主题切换按钮）
        from core.custom_title_bar import CustomTitleBar
        self.title_bar = CustomTitleBar(self, show_theme_toggle=False)
        container_layout.addWidget(self.title_bar)
        
        # 内容区域
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        container_layout.addWidget(content_widget)

        # 创建标签页
        self.tab_widget = QTabWidget()

        # 添加标签页
        tabs = [
            ("👤 用户管理", self._create_user_tab),
            ("🎨 外观设置", self._create_appearance_tab),
            ("📂 分类管理", self._create_category_tab)
        ]

        for name, creator in tabs:
            self.tab_widget.addTab(creator(), name)

        layout.addWidget(self.tab_widget)

        # 按钮区域
        button_box = self._create_button_box()
        layout.addWidget(button_box)

        self.setLayout(main_layout)

    def _create_button_box(self):
        """创建按钮区域"""
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )

        save_btn = button_box.button(QDialogButtonBox.StandardButton.Save)
        cancel_btn = button_box.button(QDialogButtonBox.StandardButton.Cancel)

        save_btn.setText("保存")
        cancel_btn.setText("取消")
        cancel_btn.setStyleSheet(get_button_style(config.theme))

        button_box.accepted.connect(self._save_settings)
        button_box.rejected.connect(self.reject)

        return button_box

    def _create_appearance_tab(self) -> QWidget:
        """创建外观设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 背景图片设置组
        bg_group = QGroupBox("背景图片设置")
        bg_layout = QVBoxLayout(bg_group)

        # 是否使用背景图片
        use_bg_layout = QHBoxLayout()
        self.use_background_checkbox = QCheckBox("使用背景图片")
        self.use_background_checkbox.setChecked(config.use_background)
        self.use_background_checkbox.setToolTip("关闭后将使用纯色背景")
        use_bg_layout.addWidget(self.use_background_checkbox)
        use_bg_layout.addStretch()
        bg_layout.addLayout(use_bg_layout)

        # 浅色模式背景图片
        light_bg_layout = QHBoxLayout()
        light_bg_layout.addWidget(QLabel("浅色背景:"))
        self.custom_bg_light_edit = QLineEdit()
        self.custom_bg_light_edit.setPlaceholderText("留空使用默认背景...")
        self.custom_bg_light_edit.setText(config.custom_background_light)
        self.custom_bg_light_edit.setReadOnly(True)
        light_bg_layout.addWidget(self.custom_bg_light_edit)

        select_light_btn = QPushButton("📁 选择")
        select_light_btn.clicked.connect(lambda: self._select_background_image("light"))
        light_bg_layout.addWidget(select_light_btn)

        clear_light_btn = QPushButton("🗑️")
        clear_light_btn.setStyleSheet(get_button_style(config.theme))
        clear_light_btn.clicked.connect(lambda: self.custom_bg_light_edit.clear())
        light_bg_layout.addWidget(clear_light_btn)

        bg_layout.addLayout(light_bg_layout)

        # 深色模式背景图片
        dark_bg_layout = QHBoxLayout()
        dark_bg_layout.addWidget(QLabel("深色背景:"))
        self.custom_bg_dark_edit = QLineEdit()
        self.custom_bg_dark_edit.setPlaceholderText("留空使用默认背景...")
        self.custom_bg_dark_edit.setText(config.custom_background_dark)
        self.custom_bg_dark_edit.setReadOnly(True)
        dark_bg_layout.addWidget(self.custom_bg_dark_edit)

        select_dark_btn = QPushButton("📁 选择")
        select_dark_btn.clicked.connect(lambda: self._select_background_image("dark"))
        dark_bg_layout.addWidget(select_dark_btn)

        clear_dark_btn = QPushButton("🗑️")
        clear_dark_btn.setStyleSheet(get_button_style(config.theme))
        clear_dark_btn.clicked.connect(lambda: self.custom_bg_dark_edit.clear())
        dark_bg_layout.addWidget(clear_dark_btn)

        bg_layout.addLayout(dark_bg_layout)

        # 背景图片说明
        bg_help = QLabel(
            "背景图片说明：\n"
            "• 关闭背景图片后将使用纯色背景\n"
            "• 可以分别为浅色和深色模式设置不同的背景图片\n"
            "• 支持 PNG、JPG、JPEG 格式\n"
            "• 留空则使用内置的默认背景图片"
        )
        bg_help.setStyleSheet(get_settings_desc_style(config.theme))
        bg_help.setWordWrap(True)
        bg_layout.addWidget(bg_help)

        layout.addWidget(bg_group)
        layout.addStretch()

        return widget

    def _create_help_tab(self) -> QWidget:
        """创建帮助标签页"""
        from PySide6.QtWidgets import QScrollArea
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        from core.styles import get_scroll_area_style
        scroll_area.setStyleSheet(get_scroll_area_style(config.theme))
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("QWidget { background: transparent; }")
        scroll_layout = QVBoxLayout(scroll_content)

        help_group = QGroupBox("使用指南")
        help_group.setStyleSheet("QGroupBox { background: transparent; }")
        help_layout = QVBoxLayout(help_group)

        help_text = QLabel(
            "<h3>鸣潮成就管理器 - 使用帮助</h3>"
            "<p><b>1. 通用认证信息设置</b></p>"
            "<p style='margin-left: 20px;'>在使用爬虫功能前，需要先在<b>爬虫</b>标签页中设置通用认证信息（devcode 和 token）。"
            "这些信息用于访问库街区Wiki API获取成就数据。</p>"
            
            "<p><b>2. 旧数据迁移指南</b></p>"
            "<p style='margin-left: 20px;'>如果您之前使用HTML版本的成就管理工具：<br>"
            "① 在旧版本中使用<b>导出JSON</b>功能导出您的成就数据<br>"
            "② 在本应用的<b>成就管理</b>标签页中点击<b>导入JSON</b>按钮<br>"
            "③ 选择导出的JSON文件即可恢复您的成就进度</p>"
            
            "<p><b>3. 数据版本说明</b></p>"
            "<p style='margin-left: 20px;'>当前应用内置了<b>1.0-2.8版本</b>的完整成就数据，共 764 条。<br>"
            "<span style='color: #e74c3c;'><b>⚠️ 重要提示：</b></span>不建议使用爬虫功能爬取旧版本数据覆盖现有数据，"
            "因为库街区Wiki的源数据存在以下问题：<br>"
            "• &nbsp;&nbsp;&nbsp;多了一条不存在的成就：要用声骸打败声骸<br>"
            "• 少了几条实际存在的成就：人形定风珠、战迹如新、大斩龙屠、失色的深红、江湖路远、凭一口气，点一盏灯<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;为荣耀倾注的花雨、他们都叫我残像收割机、无欲无求的我很难理解<br>"
            "建议仅在新版本发布后使用爬虫功能更新数据。</p>"
            
            "<p><b>4. 爬虫使用说明</b></p>"
            "<p style='margin-left: 20px;'>爬虫功能<b>仅支持单个版本</b>的数据爬取。<br>"
            "使用步骤：<br>"
            "① 在爬虫标签页设置通用认证信息<br>"
            "② 选择要爬取的版本（如：2.9）<br>"
            "③ 点击开始爬取按钮<br>"
            "④ 等待爬取完成后保存数据<br><br>"
            "<b>缓存机制：</b><br>"
            "• 首次爬取时会将网页数据保存到本地缓存（resources/achievement_cache.json）<br>"
            "• 下次爬取时会优先使用本地缓存，无需重新请求网络<br>"
            "• 点击<b>清除缓存</b>按钮可删除本地缓存文件，下次爬取将重新获取最新数据<br>"
            "• 点击<b>打开WIKI</b>按钮可在浏览器中查看库街区Wiki成就页面</p>"
            
            "<p><b>5. 状态列操作说明</b></p>"
            "<p style='margin-left: 20px;'>在成就管理标签页的表格中：<br>"
            "• <b>单击</b>状态列：在<span style='color: #27ae60;'>已完成</span>和<span style='color: #95a5a6;'>未完成</span>之间切换<br>"
            "• <b>长按</b>状态列（按住1秒）：切换为<span style='color: #e67e22;'>暂不可获取</span>状态<br>"
            "• 再次单击可恢复为未完成状态</p>"
            
            "<p><b>6. 资源获取方式</b></p>"
            "<p style='margin-left: 20px;'>如需添加更多角色头像和肖像图资源：</p>"
            "<p style='margin-left: 40px;'><b>头像图片：</b><br>"
            "① 访问 <a href='https://wiki.kurobbs.com/mc/catalogue/list?fid=1099&sid=1363' style='color: #3498db; text-decoration: underline;'>库街区Wiki-角色头像页面</a><br>"
            "② 直接拖动每个角色的头像图片到 <code>resources\\profile</code> 文件夹<br>"
            "③ 将图片重命名为角色名（如：今汐.png）<br>"
            "<p style='margin-left: 20px;'><span style='color: #3498db;'><b>💡 提示：</b></span>"
            "在主窗口点击头像切换头像，会自动更新同角色肖像图。</p>"
            "<p style='margin-left: 40px;'><b>角色肖像图：</b><br>"
            "① 访问 <a href='https://wiki.kurobbs.com/mc/catalogue/list?fid=1099&sid=1105' style='color: #3498db; text-decoration: underline;'>库街区Wiki-角色列表页面</a><br>"
            "② 点击每个角色进入详情页<br>"
            "③ 拖动角色的全身肖像图到 <code>resources\\characters</code> 文件夹<br>"
            "④ 将图片重命名为角色名（如：今汐.webp）<br>"
            "<p style='margin-left: 20px;'><span style='color: #3498db;'><b>💡 提示：</b></span>"
            "头像和肖像图的文件名必须与角色名完全一致，这样切换头像时才能自动联动显示对应的肖像图。<s>缄默</s></p>"
        )
        help_text.setWordWrap(True)
        help_text.setTextFormat(Qt.TextFormat.RichText)
        help_text.setOpenExternalLinks(True)
        help_text.setStyleSheet("QLabel a { color: #3498db; text-decoration: underline; }")
        help_layout.addWidget(help_text)

        scroll_layout.addWidget(help_group)
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        return widget

    def _select_background_image(self, theme_mode):
        """选择背景图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"选择{'浅色' if theme_mode == 'light' else '深色'}模式背景图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg)"
        )
        
        if file_path:
            if theme_mode == "light":
                self.custom_bg_light_edit.setText(file_path)
            else:
                self.custom_bg_dark_edit.setText(file_path)

    def _load_current_settings(self):
        """加载当前设置"""
        # 外观设置
        self.use_background_checkbox.setChecked(config.use_background)
        self.custom_bg_light_edit.setText(config.custom_background_light)
        self.custom_bg_dark_edit.setText(config.custom_background_dark)
        
        # 通用认证设置
        self.devcode_edit.setText(config.devcode)
        self.token_edit.setText(config.token)

    def _save_settings(self):
        """保存设置"""
        # 保存外观设置
        config.use_background = self.use_background_checkbox.isChecked()
        config.custom_background_light = self.custom_bg_light_edit.text()
        config.custom_background_dark = self.custom_bg_dark_edit.text()
        
        # 保存通用认证设置
        config.devcode = self.devcode_edit.text().strip()
        config.token = self.token_edit.text().strip()
        
        # 保存分类配置
        self._save_category_config_silent()
        
        # 保存到配置文件
        config.save_to_settings()
        
        # 发射设置变更信号（包含所有设置）
        signal_bus.settings_changed.emit({
            'use_background': config.use_background,
            'custom_background_light': config.custom_background_light,
            'custom_background_dark': config.custom_background_dark,
            'devcode': config.devcode,
            'token': config.token,
            'theme': config.theme
        })
        
        # CustomMessageBox.information(self, "成功", "设置已保存")
        self.accept()

    def _create_user_tab(self):
        """创建用户管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 添加获取认证信息的提示
        help_label = QLabel(
            "📖 <b>如何获取认证信息：</b><br>"
            "1. 访问库街区Wiki首页：<a href='https://wiki.kurobbs.com/mc/home' style='color: #0078d4;'>https://wiki.kurobbs.com/mc/home</a><br>"
            "2. 登录后，按 <b>F12</b> 打开开发者工具（Developer Tools）<br>"
            "3. 刷新页面（F5 或 Ctrl+R）<br>"
            "4. 切换到 <b>网络</b>（Network）标签<br>"
            "5. 在请求列表中找到名称为 <b>getUserBons</b> 的请求<br>"
            "6. 点击该请求，在右侧查看 <b>请求标头</b>（Request Headers）<br>"
            "7. 找到 <b>Devcode</b> 和 <b>Token</b> 字段，复制其值到下方输入框"
        )
        help_label.setWordWrap(True)
        help_label.setOpenExternalLinks(True)  # 允许点击链接
        help_label.setStyleSheet(get_settings_desc_style(config.theme))
        layout.addWidget(help_label)

        # 通用认证设置
        auth_group = QGroupBox("通用认证设置")
        auth_layout = QVBoxLayout(auth_group)

        # DevCode输入
        devcode_layout = QHBoxLayout()
        devcode_layout.addWidget(QLabel("DevCode:"))
        self.devcode_edit = QLineEdit()
        self.devcode_edit.setPlaceholderText("输入DevCode")
        self.devcode_edit.setText(config.devcode)
        self.devcode_edit.setEchoMode(QLineEdit.EchoMode.Password)  # 密文显示
        devcode_layout.addWidget(self.devcode_edit)
        auth_layout.addLayout(devcode_layout)

        # Token输入
        token_layout = QHBoxLayout()
        token_layout.addWidget(QLabel("Token:"))
        self.token_edit = QLineEdit()
        self.token_edit.setPlaceholderText("输入Token")
        self.token_edit.setText(config.token)
        self.token_edit.setEchoMode(QLineEdit.EchoMode.Password)  # 密文显示
        token_layout.addWidget(self.token_edit)
        auth_layout.addLayout(token_layout)

        layout.addWidget(auth_group)

        # 当前用户信息
        current_group = QGroupBox("当前用户")
        current_layout = QVBoxLayout(current_group)

        self.current_user_label = QLabel(f"当前用户: {config.get_current_user() or '未设置'}")
        current_layout.addWidget(self.current_user_label)

        layout.addWidget(current_group)

        # 创建水平布局：左侧添加用户，右侧用户列表
        user_main_layout = QHBoxLayout()
        
        # 左侧：添加用户
        add_group = QGroupBox("添加用户")
        add_layout = QVBoxLayout(add_group)

        # 昵称输入
        nickname_layout = QHBoxLayout()
        nickname_layout.addWidget(QLabel("昵称:"))
        self.nickname_edit = QLineEdit()
        self.nickname_edit.setPlaceholderText("输入昵称")
        nickname_layout.addWidget(self.nickname_edit)
        add_layout.addLayout(nickname_layout)

        # UID输入
        uid_layout = QHBoxLayout()
        uid_layout.addWidget(QLabel("UID:"))
        self.uid_edit = QLineEdit()
        self.uid_edit.setPlaceholderText("输入UID")
        uid_layout.addWidget(self.uid_edit)
        add_layout.addLayout(uid_layout)

        # 添加按钮
        self.add_user_btn = QPushButton("添加用户")
        self.add_user_btn.clicked.connect(self._add_user)
        add_layout.addWidget(self.add_user_btn)
        
        add_layout.addStretch()
        user_main_layout.addWidget(add_group, 1)  # 左侧占1份

        # 右侧：用户列表
        list_group = QGroupBox("用户列表")
        list_layout = QVBoxLayout(list_group)

        from PySide6.QtWidgets import QTableWidget
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(4)
        self.user_table.setHorizontalHeaderLabels(["昵称", "UID", "切换", "删除"])
        self.user_table.horizontalHeader().setStretchLastSection(True)
        self.user_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.user_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)  # 禁止选择
        self.user_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # 去掉焦点框
        self.user_table.setShowGrid(True)  # 显示网格线
        
        # 应用滚动条样式
        from core.styles import get_scrollbar_style
        self.user_table.setStyleSheet(self.user_table.styleSheet() + get_scrollbar_style(config.theme))
        
        # 设置列宽
        self.user_table.setColumnWidth(0, 120)  # 昵称
        self.user_table.setColumnWidth(1, 120)  # UID
        self.user_table.setColumnWidth(2, 60)   # 切换
        self.user_table.setColumnWidth(3, 60)   # 删除
        
        # 监听单元格点击事件
        self.user_table.cellClicked.connect(self._on_cell_clicked)
        # 监听单元格编辑完成事件
        self.user_table.itemChanged.connect(self._on_nickname_changed)
        
        self._refresh_user_list()
        
        list_layout.addWidget(self.user_table)
        user_main_layout.addWidget(list_group, 2)  # 右侧占2份
        
        layout.addLayout(user_main_layout)
        layout.addStretch()
        return widget

    def _refresh_user_list(self):
        """刷新用户列表"""
        from PySide6.QtWidgets import QTableWidgetItem
        from PySide6.QtGui import QColor
        from PySide6.QtCore import Qt
        
        # 暂时断开信号，避免刷新时触发编辑事件
        self.user_table.itemChanged.disconnect(self._on_nickname_changed)
        
        # 清除表格
        self.user_table.setRowCount(0)
        
        # 添加用户数据
        users = config.get_users()
        current_user = config.get_current_user()
        
        for row, (username, user_data) in enumerate(users.items()):
            self.user_table.insertRow(row)
            
            # 显示昵称和UID
            nickname = user_data.get('nickname', username) if isinstance(user_data, dict) else username
            uid = user_data.get('uid', '') if isinstance(user_data, dict) else ''
            
            # 昵称列（可编辑）
            nickname_item = QTableWidgetItem(nickname)
            nickname_item.setData(Qt.ItemDataRole.UserRole, username)  # 保存username用于后续操作
            if username == current_user:
                nickname_item.setForeground(QColor(0, 120, 212))  # 蓝色
                font = nickname_item.font()
                font.setBold(True)
                nickname_item.setFont(font)
            self.user_table.setItem(row, 0, nickname_item)
            
            # UID列（不可编辑）
            uid_item = QTableWidgetItem(uid)
            uid_item.setFlags(uid_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.user_table.setItem(row, 1, uid_item)
            
            # 切换列（文字）
            if username != current_user:
                switch_item = QTableWidgetItem("切换")
                switch_item.setForeground(QColor(0, 120, 212))  # 蓝色
                switch_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                switch_item.setFlags(switch_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                switch_item.setData(Qt.ItemDataRole.UserRole, username)
                self.user_table.setItem(row, 2, switch_item)
            else:
                empty_item = QTableWidgetItem("")
                empty_item.setFlags(empty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.user_table.setItem(row, 2, empty_item)
            
            # 删除列（文字）
            delete_item = QTableWidgetItem("删除")
            delete_item.setForeground(QColor(220, 53, 69))  # 红色
            delete_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            delete_item.setFlags(delete_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            delete_item.setData(Qt.ItemDataRole.UserRole, username)
            self.user_table.setItem(row, 3, delete_item)
        
        # 重新连接信号
        self.user_table.itemChanged.connect(self._on_nickname_changed)

    def _add_user(self):
        """添加用户"""
        nickname = self.nickname_edit.text().strip()
        uid = self.uid_edit.text().strip()
        
        if not nickname:
            CustomMessageBox.warning(self, "警告", "请输入昵称")
            return
        
        if not uid:
            CustomMessageBox.warning(self, "警告", "请输入UID")
            return
        
        # 检查UID是否已存在
        users = config.get_users()
        for user_data in users.values():
            if user_data.get('uid', '') == uid:
                CustomMessageBox.warning(self, "警告", "UID已存在")
                return
        
        # 添加用户（昵称作为键，包含UID信息）
        user_data = {'nickname': nickname, 'uid': uid}
        config.add_user(nickname, user_data)
        
        # 清空输入框
        self.nickname_edit.clear()
        self.uid_edit.clear()
        
        # 更新当前用户标签
        current_user = config.get_current_user()
        current_data = users.get(current_user, {})
        current_nickname = current_data.get('nickname', current_user)
        self.current_user_label.setText(f"当前用户: {current_nickname}")
        
        # 刷新用户列表
        self._refresh_user_list()
        
        CustomMessageBox.information(self, "成功", f"用户 {nickname} 添加成功")

    def _switch_to_user(self, username):
        """切换到指定用户"""
        if config.switch_user(username):
            # 更新当前用户标签
            self.current_user_label.setText(f"当前用户: {config.get_current_user()}")
            
            # 刷新用户列表
            self._refresh_user_list()
            
            # 发射用户切换信号
            signal_bus.user_switched.emit(username)
        else:
            CustomMessageBox.warning(self, "警告", "切换用户失败")

    def _on_cell_clicked(self, row, column):
        """处理单元格点击事件"""
        from PySide6.QtCore import Qt
        
        if column == 2:  # 切换列
            item = self.user_table.item(row, column)
            if item and item.text() == "切换":
                username = item.data(Qt.ItemDataRole.UserRole)
                self._switch_to_user(username)
        elif column == 3:  # 删除列
            item = self.user_table.item(row, column)
            if item and item.text() == "删除":
                username = item.data(Qt.ItemDataRole.UserRole)
                self._delete_user(username)
    
    def _on_nickname_changed(self, item):
        """昵称编辑完成"""
        if item.column() == 0:  # 昵称列
            from PySide6.QtCore import Qt
            username = item.data(Qt.ItemDataRole.UserRole)
            new_nickname = item.text().strip()
            
            if not new_nickname:
                CustomMessageBox.warning(self, "警告", "昵称不能为空")
                self._refresh_user_list()
                return
            
            # 更新用户昵称
            if username in config.users:
                if isinstance(config.users[username], dict):
                    config.users[username]['nickname'] = new_nickname
                else:
                    config.users[username] = {'nickname': new_nickname, 'uid': ''}
                
                # 保存配置
                config.save_config()
                
                # 刷新用户列表
                self._refresh_user_list()
                
                # 如果是当前用户，更新显示
                if username == config.get_current_user():
                    self.current_user_label.setText(f"当前用户: {new_nickname}")
    
    def _delete_user(self, username):
        """删除用户"""
        reply = CustomMessageBox.question(
            self, "确认", f"确定要删除用户 {username} 吗？", 
            ("是", "否")
        )
        
        if reply == CustomMessageBox.Yes:
            # 从用户列表中删除
            if username in config.users:
                del config.users[username]
                
                # 如果删除的是当前用户，清空当前用户
                if username == config.get_current_user():
                    config.current_user = ""
                    self.current_user_label.setText("当前用户: 未设置")
                
                # 保存配置
                config.save_config()
                
                # 刷新用户列表
                self._refresh_user_list()
                
                CustomMessageBox.information(self, "成功", f"用户 {username} 已删除")
    
    def _create_category_tab(self):
        """创建分类管理标签页"""
        from core.config import config
        category_config = config.load_category_config()
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 说明文字
        info_label = QLabel("管理成就分类配置，用于智能编号分配")
        info_label.setStyleSheet(get_settings_desc_style(config.theme))
        layout.addWidget(info_label)
        
        # 创建左右布局容器
        categories_layout = QHBoxLayout()
        
        # 第一分类管理（左侧）
        first_group = QGroupBox("第一分类")
        first_layout = QVBoxLayout(first_group)
        
        # 第一分类表格
        self.first_category_table = QTableWidget()
        self.first_category_table.setColumnCount(2)
        self.first_category_table.setHorizontalHeaderLabels(["分类名称", "排序"])
        self.first_category_table.horizontalHeader().setStretchLastSection(True)
        
        # 应用滚动条样式
        from core.styles import get_scrollbar_style
        self.first_category_table.setStyleSheet(self.first_category_table.styleSheet() + get_scrollbar_style(config.theme))
        
        # 填充第一分类数据
        first_categories = category_config.get("first_categories", {})
        self.first_category_table.setRowCount(len(first_categories))
        for i, (name, order) in enumerate(first_categories.items()):
            self.first_category_table.setItem(i, 0, QTableWidgetItem(name))
            self.first_category_table.setItem(i, 1, QTableWidgetItem(str(order)))
        
        # 设置表格最小高度
        self.first_category_table.setMinimumHeight(400)
        first_layout.addWidget(self.first_category_table)
        
        # 第一分类按钮
        first_btn_layout = QHBoxLayout()
        first_btn_layout.addStretch()  # 左侧弹性空间
        add_first_btn = QPushButton("添加")
        add_first_btn.setFixedWidth(80)  # 4字宽度
        add_first_btn.clicked.connect(self._add_first_category_row)
        delete_first_btn = QPushButton("删除")
        delete_first_btn.setFixedWidth(80)  # 4字宽度
        delete_first_btn.clicked.connect(self._delete_first_category)
        first_btn_layout.addWidget(add_first_btn)
        first_btn_layout.addWidget(delete_first_btn)
        first_btn_layout.addStretch()  # 右侧弹性空间
        first_layout.addLayout(first_btn_layout)
        
        categories_layout.addWidget(first_group)
        
        # 第二分类管理（右侧）
        second_group = QGroupBox("第二分类")
        second_layout = QVBoxLayout(second_group)
        
        # 第一分类选择器
        first_selector_layout = QHBoxLayout()
        first_selector_layout.addWidget(QLabel("选择第一分类:"))
        self.first_category_combo = QComboBox()
        self.first_category_combo.addItems(list(first_categories.keys()))
        self.first_category_combo.currentTextChanged.connect(self._load_second_categories)
        first_selector_layout.addWidget(self.first_category_combo)
        first_selector_layout.addStretch()
        second_layout.addLayout(first_selector_layout)
        
        # 第二分类表格
        self.second_category_table = QTableWidget()
        self.second_category_table.setColumnCount(2)
        self.second_category_table.setHorizontalHeaderLabels(["分类名称", "后缀"])
        # 设置列宽：分类名称列占70%，后缀列占30%
        header = self.second_category_table.horizontalHeader()
        header.setStretchLastSection(False)  # 不自动拉伸最后一列
        self.second_category_table.setColumnWidth(0, 300)  # 分类名称列宽
        self.second_category_table.setColumnWidth(1, 100)  # 后缀列宽
        
        # 应用滚动条样式
        from core.styles import get_scrollbar_style
        self.second_category_table.setStyleSheet(self.second_category_table.styleSheet() + get_scrollbar_style(config.theme))
        
        # 设置表格最小高度
        self.second_category_table.setMinimumHeight(400)
        second_layout.addWidget(self.second_category_table)
        
        # 第二分类按钮
        second_btn_layout = QHBoxLayout()
        second_btn_layout.addStretch()  # 左侧弹性空间
        add_second_btn = QPushButton("添加")
        add_second_btn.setFixedWidth(80)  # 4字宽度
        add_second_btn.clicked.connect(self._add_second_category_row)
        delete_second_btn = QPushButton("删除")
        delete_second_btn.setFixedWidth(80)  # 4字宽度
        delete_second_btn.clicked.connect(self._delete_second_category)
        second_btn_layout.addWidget(add_second_btn)
        second_btn_layout.addWidget(delete_second_btn)
        second_btn_layout.addStretch()  # 右侧弹性空间
        second_layout.addLayout(second_btn_layout)
        
        categories_layout.addWidget(second_group)
        
        # 设置左右比例：第一分类占1/3，第二分类占2/3
        categories_layout.setStretch(0, 1)  # 第一分类占1份
        categories_layout.setStretch(1, 2)  # 第二分类占2份
        
        layout.addLayout(categories_layout)
        layout.addStretch()  # 添加弹性空间
        
        # 初始化第二分类缓存
        self._second_categories_cache = category_config.get("second_categories", {}).copy()
        
        # 初始加载第二分类
        if first_categories:
            self._load_second_categories()
        
        return widget
    
    def _add_first_category_row(self):
        """在第一分类表格中添加空白行"""
        row = self.first_category_table.rowCount()
        self.first_category_table.insertRow(row)
        
        # 智能计算下一个排序号
        next_order = self._get_next_first_category_order()
        
        # 添加可编辑的项目
        name_item = QTableWidgetItem("")
        name_item.setFlags(name_item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.first_category_table.setItem(row, 0, name_item)
        
        order_item = QTableWidgetItem(str(next_order))
        order_item.setFlags(order_item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.first_category_table.setItem(row, 1, order_item)
        
        # 自动选中新行的第一个单元格
        self.first_category_table.setCurrentCell(row, 0)
        self.first_category_table.editItem(name_item)
    
    def _delete_first_category(self):
        """删除第一分类"""
        from core.custom_message_box import CustomMessageBox
        
        current_row = self.first_category_table.currentRow()
        if current_row >= 0:
            name = self.first_category_table.item(current_row, 0).text()
            reply = CustomMessageBox.question(self, "确认删除", f"确定要删除分类 '{name}' 吗？")
            if reply == CustomMessageBox.Yes:
                self.first_category_table.removeRow(current_row)
                
                # 从下拉框中移除
                index = self.first_category_combo.findText(name)
                if index >= 0:
                    self.first_category_combo.removeItem(index)
    
    def _add_second_category_row(self):
        """在第二分类表格中添加空白行"""
        row = self.second_category_table.rowCount()
        self.second_category_table.insertRow(row)
        
        # 智能计算下一个后缀
        next_suffix = self._get_next_second_category_suffix()
        
        # 添加可编辑的项目
        name_item = QTableWidgetItem("")
        name_item.setFlags(name_item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.second_category_table.setItem(row, 0, name_item)
        
        suffix_item = QTableWidgetItem(str(next_suffix))
        suffix_item.setFlags(suffix_item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.second_category_table.setItem(row, 1, suffix_item)
        
        # 自动选中新行的第一个单元格
        self.second_category_table.setCurrentCell(row, 0)
        self.second_category_table.editItem(name_item)
    
    def _delete_second_category(self):
        """删除第二分类"""
        from core.custom_message_box import CustomMessageBox
        
        current_row = self.second_category_table.currentRow()
        if current_row >= 0:
            name = self.second_category_table.item(current_row, 0).text()
            reply = CustomMessageBox.question(self, "确认删除", f"确定要删除分类 '{name}' 吗？")
            if reply == CustomMessageBox.Yes:
                self.second_category_table.removeRow(current_row)
    
    def _load_second_categories(self):
        """加载指定第一分类的第二分类"""
        from core.config import config
        
        # 先保存当前正在编辑的第二分类数据到缓存
        if hasattr(self, '_last_first_category') and self._last_first_category:
            self._save_current_second_categories_to_cache(self._last_first_category)
        
        # 加载新的第二分类数据
        first_category = self.first_category_combo.currentText()
        self._last_first_category = first_category
        
        # 优先从缓存加载，如果缓存中没有则从配置文件加载
        if not hasattr(self, '_second_categories_cache'):
            self._second_categories_cache = {}
        
        if first_category in self._second_categories_cache:
            second_categories = self._second_categories_cache[first_category]
        else:
            category_config = config.load_category_config()
            second_categories = category_config.get("second_categories", {}).get(first_category, {})
            self._second_categories_cache[first_category] = second_categories.copy()
        
        # 清空表格并加载数据
        self.second_category_table.setRowCount(len(second_categories))
        for i, (name, suffix) in enumerate(second_categories.items()):
            self.second_category_table.setItem(i, 0, QTableWidgetItem(name))
            self.second_category_table.setItem(i, 1, QTableWidgetItem(suffix))
    
    def _save_current_second_categories_to_cache(self, first_category):
        """保存当前第二分类数据到缓存"""
        if not hasattr(self, '_second_categories_cache'):
            self._second_categories_cache = {}
        
        second_cats = {}
        for row in range(self.second_category_table.rowCount()):
            name_item = self.second_category_table.item(row, 0)
            suffix_item = self.second_category_table.item(row, 1)
            
            if name_item and suffix_item:
                name = name_item.text().strip()
                suffix = suffix_item.text().strip()
                
                if name and suffix:
                    second_cats[name] = suffix
        
        self._second_categories_cache[first_category] = second_cats
    
    def _save_category_config_silent(self):
        """静默保存分类配置（不显示提示框）"""
        from core.config import config
        
        # 先保存当前正在编辑的第二分类数据到缓存
        current_first = self.first_category_combo.currentText()
        self._save_current_second_categories_to_cache(current_first)
        
        # 直接使用缓存中的数据
        all_second_categories = {}
        if hasattr(self, '_second_categories_cache'):
            all_second_categories = self._second_categories_cache.copy()
        else:
            # 如果缓存不存在，从配置文件加载
            category_config = config.load_category_config()
            all_second_categories = category_config.get("second_categories", {})
        
        # 收集第一分类数据
        first_categories = {}
        for row in range(self.first_category_table.rowCount()):
            name_item = self.first_category_table.item(row, 0)
            order_item = self.first_category_table.item(row, 1)
            
            if name_item and order_item:
                name = name_item.text().strip()
                order = order_item.text().strip()
                
                if name and order:
                    try:
                        first_categories[name] = int(order)
                    except ValueError:
                        print(f"[WARNING] 分类 '{name}' 的排序必须是数字，跳过")
                        continue
        
        # 保存配置
        updated_config = {
            "first_categories": first_categories,
            "second_categories": all_second_categories
        }
        
        config.save_category_config(updated_config)
    
    def _save_category_config(self):
        """保存分类配置（显示提示框）"""
        from core.config import config
        from core.custom_message_box import CustomMessageBox
        
        # 收集第一分类数据（过滤空白行）
        first_categories = {}
        for row in range(self.first_category_table.rowCount()):
            name_item = self.first_category_table.item(row, 0)
            order_item = self.first_category_table.item(row, 1)
            
            if name_item and order_item:
                name = name_item.text().strip()
                order = order_item.text().strip()
                
                if name and order:  # 只保存非空行
                    try:
                        first_categories[name] = int(order)
                    except ValueError:
                        CustomMessageBox.warning(self, "错误", f"分类 '{name}' 的排序必须是数字")
                        return
        
        # 先保存当前正在编辑的第二分类数据到缓存
        current_first = self.first_category_combo.currentText()
        self._save_current_second_categories_to_cache(current_first)
        
        # 使用缓存中的所有第二分类数据
        all_second_categories = {}
        if hasattr(self, '_second_categories_cache'):
            all_second_categories = self._second_categories_cache.copy()
        else:
            # 如果缓存不存在，从配置文件加载
            category_config = config.load_category_config()
            all_second_categories = category_config.get("second_categories", {})
        
        # 保存配置
        updated_config = {
            "first_categories": first_categories,
            "second_categories": all_second_categories
        }
        
        if config.save_category_config(updated_config):
            CustomMessageBox.information(self, "成功", "分类配置已保存")
            # 更新下拉框
            self._refresh_first_category_combo()
        else:
            CustomMessageBox.warning(self, "错误", "保存分类配置失败")
    
    def _refresh_first_category_combo(self):
        """刷新第一分类下拉框"""
        current_text = self.first_category_combo.currentText()
        self.first_category_combo.clear()
        
        for row in range(self.first_category_table.rowCount()):
            name_item = self.first_category_table.item(row, 0)
            if name_item:
                name = name_item.text().strip()
                if name:
                    self.first_category_combo.addItem(name)
        
        # 恢复之前的选择
        index = self.first_category_combo.findText(current_text)
        if index >= 0:
            self.first_category_combo.setCurrentIndex(index)
    
    def _get_next_first_category_order(self):
        """获取下一个第一分类排序号"""
        existing_orders = set()
        for row in range(self.first_category_table.rowCount()):
            order_item = self.first_category_table.item(row, 1)
            if order_item:
                try:
                    order = int(order_item.text().strip())
                    existing_orders.add(order)
                except ValueError:
                    pass
        
        # 找到最小的未使用排序号，从1开始
        next_order = 1
        while next_order in existing_orders:
            next_order += 1
        
        return next_order
    
    def _get_next_second_category_suffix(self):
        """获取下一个第二分类后缀"""
        existing_suffixes = set()
        for row in range(self.second_category_table.rowCount()):
            suffix_item = self.second_category_table.item(row, 1)
            if suffix_item:
                try:
                    suffix = int(suffix_item.text().strip())
                    existing_suffixes.add(suffix)
                except ValueError:
                    pass
        
        # 找到最小的未使用后缀，从10开始，每次递增10
        next_suffix = 10
        while next_suffix in existing_suffixes:
            next_suffix += 10
        
        return next_suffix

    def _load_background_image(self):
        """加载背景图片"""
        self.background_pixmap = load_background_image(config.theme)