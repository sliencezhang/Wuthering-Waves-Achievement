import os
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QPainterPath

from core.config import config


class CircularAvatar(QLabel):
    """圆形头像标签"""
    def __init__(self, parent=None, size=60):
        super().__init__(parent)
        self.avatar_size = size
        self.setFixedSize(self.avatar_size, self.avatar_size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 默认头像路径
        self.default_avatar = self.get_default_avatar_path()
        self.current_avatar = self.default_avatar
        
        # 边框样式
        self.border_width = 3
        self.border_color = QColor("#4a90e2")
        
        # 应用主题
        self.apply_theme()
        
        self.update_avatar()
    
    def get_default_avatar_path(self):
        """获取默认头像路径"""
        from core.config import get_resource_path
        profiles_dir = get_resource_path("resources/profile")
        
        if profiles_dir.exists():
            # 优先使用"男漂泊者.png"作为默认头像
            default_avatar = profiles_dir / "男漂泊者.png"
            if default_avatar.exists():
                return str(default_avatar)
            
            # 如果没有找到，使用第一个png文件
            png_files = list(profiles_dir.glob("*.png"))
            if png_files:
                return str(png_files[0])
        
        # 如果没有找到，返回空路径（将显示默认图标）
        return ""

    def paintEvent(self, event):
        """重绘事件，绘制圆形头像"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制圆形边框
        pen = QPen(self.border_color)
        pen.setWidth(self.border_width)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(self.border_width // 2, self.border_width // 2,
                            self.width() - self.border_width, self.height() - self.border_width)

        # 创建圆形遮罩区域 - 使用 QPainterPath
        path = QPainterPath()
        path.addEllipse(self.border_width, self.border_width,
                        self.width() - 2 * self.border_width,
                        self.height() - 2 * self.border_width)

        # 设置裁剪路径
        painter.setClipPath(path)

        # 绘制头像图片
        if self.pixmap() and not self.pixmap().isNull():
            pixmap = self.pixmap().scaled(
                self.width() - 2 * self.border_width,
                self.height() - 2 * self.border_width,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )

            # 计算居中位置
            x = (self.width() - pixmap.width()) // 2
            y = (self.height() - pixmap.height()) // 2

            painter.drawPixmap(x, y, pixmap)

        painter.end()
    
    def update_avatar(self, avatar_path=None):
        """更新头像"""
        # 优先使用传入的头像路径
        if avatar_path and os.path.exists(avatar_path):
            self.current_avatar = avatar_path
        else:
            # 如果没有传入头像，尝试从配置中获取当前用户头像
            from core.config import config
            current_avatar = config.get_current_user_avatar()
            if current_avatar and os.path.exists(current_avatar):
                self.current_avatar = current_avatar
            else:
                # 使用默认头像
                self.current_avatar = self.default_avatar
        
        # 加载图片
        if self.current_avatar and os.path.exists(self.current_avatar):
            pixmap = QPixmap(self.current_avatar)
            self.setPixmap(pixmap)
        else:
            # 如果没有图片，清空
            self.clear()
        
        self.update()
    
    def apply_theme(self, theme=None):
        """应用主题"""
        if theme is None:
            theme = config.theme
            
        # 深色主题使用月亮蓝色，浅色主题使用太阳金黄色
        if theme == "dark":
            self.border_color = QColor("#64b5f6")  # 月亮蓝色
        else:
            self.border_color = QColor("#ffc107")  # 太阳金黄色
            
        self.update()