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
        self.setModal(True)
        self.setFixedSize(850, 600)
        
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
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
            "<p><b>1. 通用认证信息设置</b></p>"
            "<p style='margin-left: 20px;'>在使用数据爬取功能前,需要先在设置<b>用户管理</b>标签页中设置通用认证信息(DevCode 和 Token)。<br>"
            "这些信息用于访问库街区Wiki 获取成就数据<br>"
            "数据通过 <b>PySide6</b>（本程序的GUI依赖）的 <b>QSettings</b> 模块保存在本地注册表中<br>"
            "<b>HKEY_CURRENT_USER/Software/WutheringWavesAchievement/AuthData</b><br>"
            "不放心可AI搜索<b>QSettings 注册表保存的信息能被远程读取吗</b></p>"
            
            "<p><b>2. 旧数据迁移指南</b></p>"
            "<p style='margin-left: 20px;'>如果您之前使用<b>鸣潮成就爬取官方wiki并自带本地网页管理.zip</b>的成就管理工具：<br>"
            "① 在<b>鸣潮成就.html</b>使用<b>导出JSON</b>功能导出您的成就数据<br>"
            "② 在本应用的<b>成就管理</b>标签页中点击<b>导入JSON</b>按钮<br>"
            "③ 选择导出的JSON文件即可恢复您的成就进度</p>"
            
            "<p><b>3. 数据版本说明</b></p>"
            "<p style='margin-left: 20px;'>当前内置了<b>1.0-2.8版本</b>的完整成就数据,共 764 条。<br>"
            "<span style='color: #e74c3c;'><b>⚠️ 重要提示: </b></span>不建议使用爬虫功能爬取旧版本数据覆盖现有数据，"
            "因为库街区Wiki的源数据存在以下问题：<br>"
            "• 多了一条本不存在的成就：要用声骸打败声骸<br>"
            "• 少了几条实际存在的成就：人形定风珠、战迹如新、大斩龙屠、失色的深红、江湖路远、凭一口气,点一盏灯<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;为荣耀倾注的花雨、他们都叫我残像收割机、无欲无求的我很难理解<br>"
            "建议通过点击<b>打开WIKI</b>按钮在网页中确认有新版本数据后再点击<b>清除缓存</b>，然后使用爬虫功能更新数据。</p>"
            
            "<p><b>4. 设置-分类管理说明</b></p>"
            "• 可以拖动表格行来改变第一分类、第二分类的排序，保持和游戏内排序一致<br>"
            "• 保存设置后会自动重新编码，自动修改所有用户存档数据来适配新排序，不会导致状态数据丢失<br>"
            "• 爬取数据遇到游戏新增的第一二分类时会自动保存在分类配置中，无需手动管理<br>"
            "• 确认覆盖也会自动重新编码所有用户数据来保证数据一致性</p>"
            
            "<p><b>5. 状态列操作说明</b></p>"
            "<p style='margin-left: 20px;'>在成就管理标签页的表格中:<br>"
            "• <b>单击</b>状态列：在<span style='color: #27ae60;'>已完成</span>和<span style='color: #95a5a6;'>未完成</span>之间切换<br>"
            "• <b>长按</b>状态列(按住1秒)：切换为<span style='color: #e67e22;'>暂不可获取</span>状态<br>"
            "• 再次单击可恢复为未完成状态</p>"
            
            "<p><b>6. 爬虫使用说明</b></p>"
            "<p style='margin-left: 20px;'>爬虫功能<b>仅支持单个版本</b>的数据爬取。<br>"
            "使用步骤：<br>"
            "① 在设置-用户管理标签页设置通用认证信息<br>"
            "② 输入要爬取的版本(如：2.9)<br>"
            "③ 点击开始爬取按钮<br>"
            "④ 等待爬取完成后点击<b>确认覆盖</b>保存数据<br><br>"
            "<b>缓存机制：</b><br>"
            "• 首次爬取时会将网页数据保存到本地缓存(resources/achievement_cache.json)<br>"
            "• 下次爬取时会优先使用本地缓存，无需重新请求网络<br>"
            "• 点击<b>清除缓存</b>按钮可删除本地缓存文件，下次爬取将重新获取最新数据<br>"
            "• 点击<b>打开WIKI</b>按钮可在浏览器中查看库街区Wiki成就页面是否有新版本成就数据</p>"
            
            
            
            "<p><b>7. 资源获取方式</b></p>"
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
