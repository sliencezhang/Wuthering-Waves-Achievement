from PySide6.QtWidgets import (QDialog, QVBoxLayout, QScrollArea, QWidget, QGroupBox, 
                               QLabel, QPushButton, QHBoxLayout)
from PySide6.QtCore import Qt

from core.config import config
from core.styles import get_dialog_style, get_scroll_area_style
from core.widgets import BackgroundWidget, load_background_image


class HelpDialog(QDialog):
    """帮助对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("帮助")
        self.setModal(False)  # 改为非模态，允许用户与其他窗口交互
        self.setFixedSize(850, 600)
        
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setStyleSheet(get_dialog_style(config.theme))

        self.background_pixmap = None
        self._load_background_image()

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.container_widget = BackgroundWidget(self.background_pixmap, config.theme)
        self.container_widget.setObjectName("dialogContainer")
        container_layout = QVBoxLayout(self.container_widget)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        main_layout.addWidget(self.container_widget)
        
        from core.custom_title_bar import CustomTitleBar
        self.title_bar = CustomTitleBar(self, show_theme_toggle=False)
        container_layout.addWidget(self.title_bar)
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        container_layout.addWidget(content_widget)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll_area.setStyleSheet(get_scroll_area_style(config.theme))
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("QWidget { background: transparent; }")
        scroll_layout = QVBoxLayout(scroll_content)

        help_group = QGroupBox("使用指南")
        help_group.setStyleSheet("QGroupBox { background: transparent; }")
        help_layout = QVBoxLayout(help_group)

        help_text = QLabel(
            "<h3>鸣潮成就管理器 - 使用帮助</h3>"
            
            "<p><b>🌟 软件使用指南</b></p>"
            "<p style='margin-left: 20px;'><span style='color: #3498db;'><b>💡 简单来说，这个工具是干嘛的？</b></span><br>"
            "这是一个帮你记录和管理《鸣潮》游戏成就进度的工具。你可以用它来：<br>"
            "• ✅ 标记已完成的成就，包括已完成、未完成、已占用(多选一成就)、暂不可获取(永远不会抽的角色的延奏成就或1.2追月节成就等等)<br>"
            "• 📊 查看成就完成进度统计图表<br>"
            "• 👥 支持多个用户，每个用户可以独立记录自己的进度<br>"
            "• ❣️ 美化的软件界面，包含头像、立绘、背景图（使用需在下载页面下载resources.zip并解压，将文件夹(忽略json文件)复制到该软件的resources文件夹内）</p>"
            
            
            "<p><b>1. 通用认证信息设置</b></p>"
            "<p style='margin-left: 20px;'><b>如何获取？</b><br>"
            "① 访问库街区Wiki首页：<a href='https://www.kurobbs.com/' style='color: #3498db; text-decoration: underline;'>https://www.kurobbs.com/</a><br>"
            "② 选择鸣潮并登录后，按 <b>F12</b> 打开开发者工具（Developer Tools）<br>"
            "③ 切换到 <b>网络</b>（Network）标签, 刷新页面（F5 或 Ctrl+R）<br>"
            "④ 在请求列表中找到名称为 <b>getConfig</b> 的请求<br>"
            "⑤ 点击该请求，在右侧切换到标头标签，滚动查看 <b>请求标头</b>（Request Headers）<br>"
            "⑥ 找到 <b>Devcode</b> 和 <b>Token</b> 字段，复制其值到下方输入框<br><br>"
            "<b>如何设置？</b><br>"
            "① 点击程序主界面的<b>设置</b>按钮<br>"
            "② 选择<b>用户管理</b>标签页<br>"
            "③ 将获取的DevCode和Token填入对应输入框<br>"
            "④ 点击<b>保存</b>按钮<br><br>"
            "<span style='color: #3498db;'><b>🔒 安全提示：</b></span><br>"
            "这些信息只保存在你自己的电脑上，不会上传到任何服务器。如果不放心，可以搜索\"QSettings 注册表保存的信息能被远程读取吗\"了解详情。</p>"
            
            "<p><b>2. 数据说明</b></p>"
            "<p style='margin-left: 20px;'><span style='color: #3498db;'><b>📊 内置数据：</b></span><br>"
            "• 程序已经内置了1.0-2.8版本的完整成就数据，共764条<br>"
            "<span style='color: #3498db;'><b>🔄 更新数据：</b></span><br>"
            "• 当游戏更新新版本时，可以通过三种方式获取最新成就数据：<br>"
            "  1. <b>数据爬取-B站UP主</b>：通过b站up主：<b>小白游戏导航</b>的视频按照<b>导出范本</b>的格式自行编辑后，导入Excel，确认覆盖（最快）<br>"
            "  2. <b>数据爬取-打开WIKI</b>：需要设置认证信息，并等待wiki完善新版本成就数据（比较慢，因为需要审核），输入版本号，清除缓存，开始爬取，确认覆盖<br>"
            "  3. <b>数据爬取-下载页面</b>：是我通过b站up主：<b>小白游戏导航</b>的视频按照范本格式整理的，导入Excel，确认覆盖（不保证每次都有）</p>"
            
            "<p><b>3. 状态列操作说明</b></p>"
            "<p style='margin-left: 20px;'>在成就管理标签页的表格中:<br>"
            "• <b>单击</b>状态列：在<span style='color: #27ae60;'>已完成</span>和<span style='color: #95a5a6;'>未完成</span>之间切换<br>"
            "• <b>长按</b>状态列(按住1秒)：切换为<span style='color: #e67e22;'>暂不可获取</span>状态，再次单击恢复为未完成状态<br>"
            "• 多选一成就，点击成就组内任一成就，会将其他成就改为 已占用 状态<br>"
            "• 成就管理-第一分类和第二分类点击后，可更改所属分类</p>"
            
            "<p><b>4. 爬虫使用说明与数据版本管理（进阶功能）</b></p>"
            "<p style='margin-left: 20px;'><span style='color: #e74c3c;'><b>⚠️ 重要提示：</b></span><br>"
            "• 不建议使用爬虫功能爬取旧版本数据覆盖现有数据<br>"
            "• 建议通过点击<b>打开WIKI</b>按钮在网页中确认有新版本数据后再使用爬虫功能<br><br>"
            "<span style='color: #3498db;'><b>🚀 爬虫功能使用步骤：</b></span><br>"
            "爬虫功能<b>仅支持单个版本</b>的数据爬取。<br>"
            "① 在设置-用户管理标签页设置通用认证信息<br>"
            "② 输入要爬取的版本(如：3.0)<br>"
            "③ 点击开始爬取按钮<br>"
            "④ 等待爬取完成后点击<b>确认覆盖</b>保存数据<br><br>"
            "<span style='color: #3498db;'><b>💾 缓存机制：</b></span><br>"
            "• 首次爬取时会将网页数据保存到本地缓存(resources/achievement_cache.json)<br>"
            "• 下次爬取时会优先使用本地缓存，无需重新请求网络<br>"
            "• 点击<b>清除缓存</b>按钮可删除本地缓存文件，下次爬取将重新获取最新数据<br>"
            "• 点击<b>打开WIKI</b>按钮可在浏览器中查看库街区Wiki成就页面是否有新版本成就数据</p>"
            
            "<p><b>5. 设置-分类管理说明</b></p>"
            "• 可以拖动表格行来改变第一分类、第二分类的排序，保持和游戏内排序一致<br>"
            "• 保存设置后会自动重新编码，自动修改所有用户存档数据来适配新排序，不会导致状态数据丢失<br>"
            "• 爬取数据遇到游戏新增的第一二分类时会自动保存在分类配置中，无需手动管理<br>"
            "• 确认覆盖也会自动重新编码所有用户数据来保证数据一致性</p>"
            
            "<p><b>6. 设置-多选一管理说明</b></p>"
            "• 点击添加组，再点击组名称表格中的内容<br>"
            "• 点击添加成就，搜索多选一的成就名称<br>"
            "• 勾选后，点击确定，点击保存<br>"
            "• 在成就管理-获取类型中筛选<b>多选一</b>来管理多选一成就完成状态</p>"
            
            "<p><b>7. 设置-版本管理说明</b></p>"
            "• 仅仅是某一版本成就数据有误时，用来删除当前版本数据的功能，通常可忽略<br>"
            "• 删除时，会自动导出所有用户的当前删除版本的成就数据</p>"
            
            "<p><b>8. 美化资源获取方式</b></p>"
            "<p style='margin-left: 20px;'>如需添加更多角色头像和肖像图资源：</p>"
            "<p style='margin-left: 40px;'><b>头像图片:</b><br>"
            "① 访问 <a href='https://wiki.kurobbs.com/mc/catalogue/list?fid=1099&sid=1363' style='color: #3498db; text-decoration: underline;'>库街区Wiki-角色头像页面</a><br>"
            "② 直接拖动每个角色的头像图片到 <code>resources\\profile</code> 文件夹<br>"
            "③ 将图片重命名为角色名(如：今汐.png)"
            "<p style='margin-left: 20px;'><span style='color: #3498db;'><b>💡 提示：</b></span>"
            "在主窗口点击头像切换头像，会自动更新同角色肖像图。</p>"
            "<p style='margin-left: 40px;'><b>角色肖像图：</b><br>"
            "① 访问 <a href='https://wiki.kurobbs.com/mc/catalogue/list?fid=1099&sid=1105' style='color: #3498db; text-decoration: underline;'>库街区Wiki-角色列表页面</a><br>"
            "② 点击每个角色进入详情页<br>"
            "③ 拖动角色的全身肖像图到 <code>resources\\characters</code> 文件夹<br>"
            "④ 将图片重命名为角色名(如：今汐.webp)"
            "<p style='margin-left: 20px;'><span style='color: #3498db;'><b>💡 提示：</b></span>"
            "头像和肖像图的文件名必须完全一致，这样切换头像时才能自动联动显示对应的肖像图。<s>缄默</s></p>"
            
            "<p style='margin-left: 20px;'><span style='color: #27ae60;'><b>🎉 总结：小白用户使用流程</b></span><br>"
            "1. 打开程序 → 直接开始使用内置的1.0-2.8成就数据<br>"
            "2. 在成就管理页面标记你的完成状态<br>"
            "3. 游戏更新新版本时 → 等待别人整理好的Excel数据（按照范本格式自行整理） → 数据爬取页面 → 导入Excel → 确认覆盖<br>"
            "4. 完全不需要了解JSON，不需要设置认证信息，开箱即用！</p>"
        )
        help_text.setWordWrap(True)
        help_text.setTextFormat(Qt.TextFormat.RichText)
        help_text.setOpenExternalLinks(True)
        
        # 使用统一的帮助文本样式
        from core.styles import get_help_text_style
        help_text.setStyleSheet(get_help_text_style(config.theme))
        help_layout.addWidget(help_text)

        scroll_layout.addWidget(help_group)
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        self.setLayout(main_layout)

    def check_for_updates(self):
        """检查更新"""
        # 获取父窗口（主窗口）
        parent = self.parent()
        if parent and hasattr(parent, 'check_for_updates_manual'):
            parent.check_for_updates_manual()
    
    def _load_background_image(self):
        """加载背景图片"""
        self.background_pixmap = load_background_image(config.theme)
