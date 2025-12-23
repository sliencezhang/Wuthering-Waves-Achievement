"""
统计信息标签页
"""

import os
import math
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QComboBox, QGroupBox, QCheckBox, QGridLayout)
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QColor, QFont, QFontMetrics

from core.signal_bus import SignalBus
from core.config import Config
from core.styles import get_button_style


class ChartColors:
    """图表颜色常量"""
    COLORS = [
        QColor(52, 152, 219),   # 蓝色
        QColor(46, 204, 113),   # 绿色
        QColor(231, 76, 60),    # 红色
        QColor(241, 196, 15),   # 黄色
        QColor(155, 89, 182),   # 紫色
        QColor(230, 126, 34),   # 橙色
        QColor(149, 165, 166),  # 灰色
    ]
    
    @staticmethod
    def get_theme_colors(theme):
        """获取主题颜色配置"""
        if theme == "light":
            return ChartColors.COLORS, QColor(0, 0, 0), QColor(0, 0, 0, 0)
        return ChartColors.COLORS, QColor(255, 255, 255), QColor(0, 0, 0, 0)


class ChartDimensions:
    """图表尺寸常量"""
    MIN_BAR_WIDTH = 40
    MAX_BAR_WIDTH = 100
    BAR_SPACING = 15
    HOVER_OFFSET = 10
    PIE_SIZE_RATIO = 0.8


class TooltipWidget(QWidget):
    """悬浮提示框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        self.subtitle_label = QLabel()
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.subtitle_label)
        
        self.hide()
    
    def show_tooltip(self, pos, title, subtitle=""):
        """显示提示框"""
        self.title_label.setText(title)
        if subtitle:
            self.subtitle_label.setText(subtitle)
            self.subtitle_label.show()
        else:
            self.subtitle_label.hide()
        
        # 调整大小
        self.adjustSize()
        
        # 确保在屏幕范围内显示
        screen = self.screen().availableGeometry()
        x = pos.x()
        y = pos.y() - self.height() - 10
        if x + self.width() > screen.right():
            x = screen.right() - self.width()
        if y < screen.top():
            y = pos.y() + 10
        
        self.move(x, y)
        self.show()
    
    def paintEvent(self, event):
        """绘制半透明背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制半透明圆角背景
        rect = self.rect()
        painter.setBrush(QColor(40, 40, 40, 120))
        painter.setPen(QColor(60, 60, 60, 180))
        painter.drawRoundedRect(rect, 6, 6)


class SimpleChartWidget(QWidget):
    """简单图表组件"""
    def __init__(self, chart_type="pie", parent=None):
        super().__init__(parent)
        self.chart_type = chart_type
        self.data = {}
        self.hover_index = -1
        self.config = Config()
        self.theme = self.config.theme
        
        # 获取主题颜色
        self.colors, self.text_color, self.bg_color = ChartColors.get_theme_colors(self.theme)
        
        self.setMinimumSize(300, 300)
        self.setMouseTracking(True)
    
    def set_data(self, data):
        """设置图表数据"""
        self.data = data
        self.update()
    
    def _find_tooltip_parent(self):
        """查找包含tooltip的父级"""
        parent = self.parent()
        while parent and not hasattr(parent, 'tooltip'):
            parent = parent.parent()
        return parent if hasattr(parent, 'tooltip') else None
    
    def _handle_horizontal_bar_hover(self, event):
        """处理水平条形图的hover"""
        rect = self.rect()
        padding = 20
        label_width = 60
        chart_rect = rect.adjusted(label_width + padding, padding, -padding, -padding)
        
        # 获取数据并排序（按值降序）
        sorted_items = sorted(self.data.items(), key=lambda x: x[1], reverse=True)
        
        # 限制显示最多10个版本
        max_display = 10
        if len(sorted_items) > max_display:
            sorted_items = sorted_items[:max_display]
            # 添加"其他"项
            other_count = sum(self.data.values()) - sum(item[1] for item in sorted_items)
            if other_count > 0:
                sorted_items.append(("其他", other_count))
        
        bar_height = min(30, (chart_rect.height() - (len(sorted_items) - 1) * 5) / len(sorted_items))
        
        for i, (label, value) in enumerate(sorted_items):
            y = chart_rect.top() + i * (bar_height + 5)
            bar_bottom = y + bar_height
            # 检查鼠标是否在当前条形内（考虑条形间的5像素间距）
            if y <= event.pos().y() <= bar_bottom and event.pos().y() < y + bar_height + 5:
                if self.hover_index != i:
                    self.hover_index = i
                    self.update()
                # 显示提示框
                global_pos = self.mapToGlobal(event.pos())
                parent = self._find_tooltip_parent()
                if parent:
                    parent.tooltip.show_tooltip(global_pos, f"{label}", f"成就数量: {value}")
                return
        else:
            if self.hover_index != -1:
                self.hover_index = -1
                self.update()
            parent = self._find_tooltip_parent()
            if parent:
                parent.tooltip.hide()
    
    def _handle_bar_hover(self, event):
        """处理柱状图的hover"""
        rect = self.rect()
        label_height = 70
        padding = 40
        chart_rect = rect.adjusted(padding, padding, -padding, -(padding + label_height))
        
        # 获取数据
        labels = list(self.data.keys())
        if not labels:
            return
        
        # 计算最大值（总数）
        max_value = max([data['total'] for data in self.data.values()]) if self.data else 1
        
        # 动态计算柱宽
        min_bar_width = ChartDimensions.MIN_BAR_WIDTH
        max_bar_width = ChartDimensions.MAX_BAR_WIDTH
        spacing = ChartDimensions.BAR_SPACING
        
        # 根据柱子数量计算合适的宽度
        if len(labels) <= 5:
            target_width = (chart_rect.width() - (len(labels) - 1) * spacing) / len(labels)
            bar_width = min(target_width, max_bar_width)
        elif len(labels) <= 10:
            bar_width = (chart_rect.width() - (len(labels) - 1) * spacing) / len(labels)
            bar_width = max(min(bar_width, 80), min_bar_width)
        else:
            bar_width = min_bar_width
        
        # 计算所有柱子的总宽度
        total_bars_width = len(labels) * bar_width + (len(labels) - 1) * spacing
        
        # 计算起始x坐标，使柱状图居中
        start_x = chart_rect.left() + (chart_rect.width() - total_bars_width) // 2
        
        # 检查每个柱子
        for i, label in enumerate(labels):
            x = start_x + i * (bar_width + spacing)
            # 检查鼠标是否在当前柱子内
            if x <= event.pos().x() <= x + bar_width:
                if chart_rect.top() <= event.pos().y() <= chart_rect.bottom():
                    if self.hover_index != i:
                        self.hover_index = i
                        self.update()
                    # 显示提示框
                    total = self.data[label]['total']
                    completed = self.data[label]['completed']
                    percentage = int(completed * 100 / total) if total > 0 else 0
                    global_pos = self.mapToGlobal(event.pos())
                    parent = self._find_tooltip_parent()
                    if parent:
                        parent.tooltip.show_tooltip(global_pos, f"{label}", f"完成度: {completed}/{total} ({percentage}%)")
                    return
        else:
            if self.hover_index != -1:
                self.hover_index = -1
                self.update()
            parent = self._find_tooltip_parent()
            if parent:
                parent.tooltip.hide()
    
    def _handle_pie_hover(self, event):
        """处理饼图的hover"""
        rect = self.rect()
        pie_width = rect.width() * 0.6
        padding = 20
        
        # 饼图区域
        max_pie_size = min(pie_width - padding * 2, rect.height() - padding * 2)
        pie_size = int(max_pie_size * ChartDimensions.PIE_SIZE_RATIO)
        pie_x = rect.left() + padding + (max_pie_size - pie_size) // 2
        pie_y = rect.top() + (rect.height() - pie_size) // 2
        chart_rect = QRect(pie_x, pie_y, pie_size, pie_size)
        
        # 计算鼠标相对于饼图中心的位置
        center_x = chart_rect.center().x()
        center_y = chart_rect.center().y()
        dx = event.pos().x() - center_x
        dy = event.pos().y() - center_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # 检查鼠标是否在饼图内
        if distance <= pie_size / 2:
            # 计算角度
            angle = math.degrees(math.atan2(-dy, dx))  # 负dy因为y轴向下
            if angle < 0:
                angle += 360
            
            # 计算总和
            total = sum(self.data.values())
            if total > 0:
                # 查找鼠标在哪个扇形内
                start_angle = 0
                for i, (label, value) in enumerate(self.data.items()):
                    span_angle = int(360 * value / total) if total > 0 else 0
                    if span_angle == 0:
                        span_angle = 1
                    
                    end_angle = start_angle + span_angle
                    # 检查角度是否在当前扇形内
                    if start_angle <= angle < end_angle:
                        if self.hover_index != i:
                            self.hover_index = i
                            self.update()
                        # 显示提示框
                        percentage = int(value * 100 / total) if total > 0 else 0
                        global_pos = self.mapToGlobal(event.pos())
                        parent = self._find_tooltip_parent()
                        if parent:
                            parent.tooltip.show_tooltip(global_pos, f"{label}", f"占比: {percentage}%")
                        return
                    start_angle = end_angle
        else:
            if self.hover_index != -1:
                self.hover_index = -1
                self.update()
            parent = self._find_tooltip_parent()
            if parent:
                parent.tooltip.hide()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.chart_type == "horizontal_bar" and self.data:
            self._handle_horizontal_bar_hover(event)
        elif self.chart_type == "bar" and self.data:
            self._handle_bar_hover(event)
        elif self.chart_type == "pie" and self.data:
            self._handle_pie_hover(event)
        else:
            if self.hover_index != -1:
                self.hover_index = -1
                self.update()
            parent = self._find_tooltip_parent()
            if parent:
                parent.tooltip.hide()
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        if self.hover_index != -1:
            self.hover_index = -1
            self.update()
        # 隐藏提示框
        parent = self._find_tooltip_parent()
        if parent:
            parent.tooltip.hide()
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.chart_type == "pie":
            self.draw_pie(painter, self.rect())
        elif self.chart_type == "bar":
            self.draw_bar(painter, self.rect())
        elif self.chart_type == "horizontal_bar":
            self.draw_horizontal_bar(painter, self.rect())
    
    def draw_pie(self, painter, rect):
        """绘制饼图"""
        if not self.data:
            return
        
        # 计算绘图区域 - 左侧饼图，右侧图例
        pie_width = rect.width() * 0.6
        legend_width = rect.width() * 0.35
        padding = 20
        
        # 饼图区域 - 调整饼图大小为80%
        max_pie_size = min(pie_width - padding * 2, rect.height() - padding * 2)
        pie_size = int(max_pie_size * ChartDimensions.PIE_SIZE_RATIO)
        pie_x = rect.left() + padding + (max_pie_size - pie_size) // 2
        pie_y = rect.top() + (rect.height() - pie_size) // 2
        chart_rect = QRect(pie_x, pie_y, pie_size, pie_size)
        
        # 图例区域
        legend_x = pie_x + pie_size + padding
        legend_y = rect.top() + padding
        legend_width = rect.right() - legend_x - padding
        legend_height = rect.height() - padding * 2
        
        # 计算总和
        total = sum(self.data.values())
        if total == 0:
            return
        
        # 绘制饼图
        start_angle = 0
        for i, (label, value) in enumerate(self.data.items()):
            # 计算角度
            span_angle = int(360 * value / total) if total > 0 else 0
            
            # 如果值为0，绘制一个极小的扇形以显示该分类
            if span_angle == 0:
                span_angle = 1
            
            # 判断是否是hover状态
            is_hover = (self.hover_index == i)
            
            if is_hover:
                # 计算中心角度
                center_angle = start_angle + span_angle / 2
                
                # 计算偏移量（向外移动）
                offset_x = int(ChartDimensions.HOVER_OFFSET * math.cos(math.radians(center_angle)))
                offset_y = int(-ChartDimensions.HOVER_OFFSET * math.sin(math.radians(center_angle)))
                hover_rect = chart_rect.adjusted(offset_x, offset_y, offset_x, offset_y)
                
                # 绘制hover阴影
                shadow_rect = hover_rect.adjusted(3, 3, 3, 3)
                painter.setBrush(QColor(0, 0, 0, 60))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawPie(shadow_rect, start_angle * 16, span_angle * 16)
                
                # 绘制hover扇形（更亮的颜色）
                hover_color = QColor(
                    min(255, self.colors[i % len(self.colors)].red() + 30),
                    min(255, self.colors[i % len(self.colors)].green() + 30),
                    min(255, self.colors[i % len(self.colors)].blue() + 30)
                )
                painter.setBrush(hover_color)
                painter.setPen(QColor(255, 255, 255, 150))
                painter.drawPie(hover_rect, start_angle * 16, span_angle * 16)
            else:
                # 绘制普通阴影
                shadow_rect = chart_rect.adjusted(2, 2, 2, 2)
                painter.setBrush(QColor(0, 0, 0, 50))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawPie(shadow_rect, start_angle * 16, span_angle * 16)
                
                # 绘制普通扇形
                painter.setBrush(self.colors[i % len(self.colors)])
                painter.setPen(QColor(255, 255, 255, 100))
                painter.drawPie(chart_rect, start_angle * 16, span_angle * 16)
            start_angle += span_angle
        
        # 绘制图例 - 按指定顺序：未完成、已完成、暂不可获取
        order = ['未完成', '已完成', '暂不可获取']
        ordered_data = []
        for key in order:
            if key in self.data:
                ordered_data.append((key, self.data[key]))
        
        legend_item_height = 25
        legend_y_start = legend_y + (legend_height - len(ordered_data) * legend_item_height) // 2
        
        # 计算最宽的标签
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)
        fm = QFontMetrics(font)
        max_label_width = max(fm.horizontalAdvance(label) for label, _ in ordered_data)
        label_width = max(max_label_width, 60)
        
        # 冒号宽度和间距
        colon_width = fm.horizontalAdvance(":")
        
        for i, (label, value) in enumerate(ordered_data):
            # 图例项位置
            item_y = legend_y_start + i * legend_item_height
            
            # 绘制颜色方块
            color_rect = QRect(legend_x, item_y + 5, 15, 15)
            painter.fillRect(color_rect, self.colors[i % len(self.colors)])
            
            # 绘制标签文字（固定宽度，居中）
            painter.setPen(self.text_color)
            label_rect = QRect(legend_x + 25, item_y, label_width, legend_item_height)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, label)
            
            # 绘制冒号
            colon_x = legend_x + 25 + label_width
            colon_rect = QRect(colon_x, item_y, colon_width, legend_item_height)
            painter.drawText(colon_rect, Qt.AlignmentFlag.AlignCenter, ":")
            
            # 绘制数值（剩余空间）
            percentage = int(value * 100 / total) if total > 0 else 0
            text = f"{value} ({percentage}%)"
            value_x = colon_x + colon_width + 5
            value_width = legend_x + legend_width - value_x - 5
            value_rect = QRect(value_x, item_y, value_width, legend_item_height)
            painter.drawText(value_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)
    
    def draw_bar(self, painter, rect):
        """绘制堆叠柱状图"""
        if not self.data:
            return
        
        # 计算绘图区域，给底部标签留适当空间
        label_height = 70
        padding = 40
        chart_rect = rect.adjusted(padding, padding, -padding, -(padding + label_height))
        
        # 获取数据
        labels = list(self.data.keys())
        if not labels:
            return
        
        # 计算最大值（总数）
        max_value = max([data['total'] for data in self.data.values()]) if self.data else 1
        
        # 动态计算柱宽
        min_bar_width = ChartDimensions.MIN_BAR_WIDTH
        max_bar_width = ChartDimensions.MAX_BAR_WIDTH
        spacing = ChartDimensions.BAR_SPACING
        
        # 根据柱子数量计算合适的宽度
        if len(labels) <= 5:
            target_width = (chart_rect.width() - (len(labels) - 1) * spacing) / len(labels)
            bar_width = min(target_width, max_bar_width)
        elif len(labels) <= 10:
            bar_width = (chart_rect.width() - (len(labels) - 1) * spacing) / len(labels)
            bar_width = max(min(bar_width, 80), min_bar_width)
        else:
            bar_width = min_bar_width
        
        # 计算所有柱子的总宽度
        total_bars_width = len(labels) * bar_width + (len(labels) - 1) * spacing
        
        # 计算起始x坐标，使柱状图居中
        start_x = chart_rect.left() + (chart_rect.width() - total_bars_width) // 2
        
        # 文字颜色
        if self.theme == "light":
            text_color = QColor(0, 0, 0)
        else:
            text_color = QColor(255, 255, 255)
        
        # 绘制柱形
        for i, (label, data) in enumerate(self.data.items()):
            x = start_x + i * (bar_width + spacing)
            total = data['total']
            completed = data['completed']
            
            # 获取该分类的颜色
            base_color = self.colors[i % len(self.colors)]
            
            # 计算高度
            total_height = (total / max_value) * chart_rect.height()
            completed_height = (completed / max_value) * chart_rect.height()
            
            # 判断是否是hover状态
            is_hover = (self.hover_index == i)
            
            # 如果hover，调整宽度和位置
            if is_hover:
                hover_x = x - 3
                hover_width = bar_width + 6
                hover_total_height = total_height + 5
                hover_completed_height = completed_height + 5
            else:
                hover_x = x
                hover_width = bar_width
                hover_total_height = total_height
                hover_completed_height = completed_height
            
            # 绘制总数柱形（底层）
            if is_hover:
                total_color = QColor(
                    min(255, int(base_color.red() * 0.6) + 20),
                    min(255, int(base_color.green() * 0.6) + 20),
                    min(255, int(base_color.blue() * 0.6) + 20),
                    200
                )
            else:
                total_color = QColor(
                    int(base_color.red() * 0.6),
                    int(base_color.green() * 0.6),
                    int(base_color.blue() * 0.6),
                    200
                )
            total_y = chart_rect.bottom() - hover_total_height
            
            # 绘制阴影
            if is_hover:
                shadow_rect = QRect(hover_x + 2, total_y + 2, hover_width, hover_total_height)
                painter.fillRect(shadow_rect, QColor(0, 0, 0, 40))
            else:
                shadow_rect = QRect(x + 2, total_y + 2, bar_width, total_height)
                painter.fillRect(shadow_rect, QColor(0, 0, 0, 30))
            
            # 绘制柱形主体
            painter.fillRect(hover_x, total_y, hover_width, hover_total_height, total_color)
            
            # 添加渐变效果
            if is_hover:
                gradient_rect = QRect(hover_x + 1, total_y + 1, hover_width - 2, hover_total_height - 2)
            else:
                gradient_rect = QRect(x + 1, total_y + 1, bar_width - 2, total_height - 2)
            gradient_color = QColor(
                int(base_color.red() * 0.7),
                int(base_color.green() * 0.7),
                int(base_color.blue() * 0.7),
                100
            )
            painter.fillRect(gradient_rect, gradient_color)
            
            # 绘制完成数柱形（上层）
            if completed > 0:
                if is_hover:
                    completed_color = QColor(
                        min(255, int(base_color.red() * 0.9) + 20),
                        min(255, int(base_color.green() * 0.9) + 20),
                        min(255, int(base_color.blue() * 0.9) + 20),
                        180
                    )
                else:
                    completed_color = QColor(
                        int(base_color.red() * 0.9),
                        int(base_color.green() * 0.9),
                        int(base_color.blue() * 0.9),
                        180
                    )
                completed_y = chart_rect.bottom() - hover_completed_height
                
                # 添加发光效果
                if is_hover:
                    glow_rect = QRect(hover_x - 1, completed_y - 1, hover_width + 2, hover_completed_height + 2)
                    glow_color = QColor(
                        int(base_color.red()),
                        int(base_color.green()),
                        int(base_color.blue()),
                        70
                    )
                else:
                    glow_rect = QRect(x - 1, completed_y - 1, bar_width + 2, completed_height + 2)
                    glow_color = QColor(
                        int(base_color.red()),
                        int(base_color.green()),
                        int(base_color.blue()),
                        50
                    )
                painter.fillRect(glow_rect, glow_color)
                
                # 绘制完成数柱形主体
                painter.fillRect(hover_x, completed_y, hover_width, hover_completed_height, completed_color)
                
                # 添加高光效果
                top_highlight_height = 4 if is_hover else 3
                right_highlight_width = 3
                # 顶部高光
                if is_hover:
                    top_highlight_rect = QRect(hover_x + right_highlight_width + 2, completed_y + 2, 
                                             hover_width - right_highlight_width - 4, top_highlight_height)
                else:
                    top_highlight_rect = QRect(x + right_highlight_width + 2, completed_y + 2, 
                                             bar_width - right_highlight_width - 4, top_highlight_height)
                top_highlight_color = QColor(255, 255, 255, 100 if is_hover else 80)
                painter.fillRect(top_highlight_rect, top_highlight_color)
                
                # 右侧高光
                if is_hover:
                    right_highlight_rect = QRect(hover_x + hover_width - right_highlight_width, 
                                               completed_y + top_highlight_height + 2,
                                               right_highlight_width, hover_completed_height - top_highlight_height - 4)
                else:
                    right_highlight_rect = QRect(x + bar_width - right_highlight_width, 
                                               completed_y + top_highlight_height + 2,
                                               right_highlight_width, completed_height - top_highlight_height - 4)
                right_highlight_color = QColor(255, 255, 255, 60 if is_hover else 40)
                painter.fillRect(right_highlight_rect, right_highlight_color)
                
                # 右上角高光（hover时）
                if is_hover:
                    corner_size = 6
                    corner_highlight_rect = QRect(hover_x + hover_width - right_highlight_width - corner_size - 2,
                                               completed_y + 2, corner_size, corner_size)
                    corner_highlight_color = QColor(255, 255, 255, 120)
                    painter.fillRect(corner_highlight_rect, corner_highlight_color)
            
            # 绘制总数（在柱子上方）
            painter.setPen(text_color)
            painter.drawText(x, total_y - 20, bar_width, 20,
                           Qt.AlignmentFlag.AlignCenter, str(total))
            
            # 绘制完成数（在柱子内部底部）
            if completed > 0:
                if self.theme == "light":
                    painter.setPen(QColor(0, 0, 0))
                else:
                    painter.setPen(QColor(255, 255, 255))
                painter.drawText(x + 2, chart_rect.bottom() - 5, bar_width - 4, 20,
                               Qt.AlignmentFlag.AlignCenter, str(completed))
            
            # 绘制标签（在柱子下方）
            painter.setPen(text_color)
            label_rect = QRect(x, chart_rect.bottom() + 5, bar_width, label_height - 10)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop, label)
    
    def draw_horizontal_bar(self, painter, rect):
        """绘制水平条形图"""
        if not self.data:
            return
        
        # 计算绘图区域，给标签留更多空间
        label_width = 60
        padding = 20
        chart_rect = rect.adjusted(label_width + padding, padding, -padding, -padding)
        
        # 获取数据并排序（按值降序）
        sorted_items = sorted(self.data.items(), key=lambda x: x[1], reverse=True)
        
        # 限制显示最多10个版本
        max_display = 10
        if len(sorted_items) > max_display:
            sorted_items = sorted_items[:max_display]
            # 添加"其他"项
            other_count = sum(self.data.values()) - sum(item[1] for item in sorted_items)
            if other_count > 0:
                sorted_items.append(("其他", other_count))
        
        labels = [item[0] for item in sorted_items]
        values = [item[1] for item in sorted_items]
        
        if not labels:
            return
        
        # 计算最大值
        max_value = max(values) if values and max(values) > 0 else 1
        
        # 计算条形高度和间距
        bar_height = min(30, (chart_rect.height() - (len(labels) - 1) * 5) / len(labels))
        
        # 绘制条形
        for i, (label, value) in enumerate(zip(labels, values)):
            y = chart_rect.top() + i * (bar_height + 5)
            bar_width = (value / max_value) * chart_rect.width() if max_value > 0 else 0
            
            # 判断是否是hover状态
            is_hover = (self.hover_index == i)
            
            if is_hover:
                # 如果hover，只调整高度
                hover_y = y - 2
                hover_height = bar_height + 4

                # 绘制hover阴影
                shadow_rect = QRect(chart_rect.left() + 2, hover_y + 2, bar_width, hover_height)
                painter.fillRect(shadow_rect, QColor(0, 0, 0, 40))

                # 使用更亮的颜色，保持相同宽度
                hover_color = QColor(
                    min(255, self.colors[i % len(self.colors)].red() + 20),
                    min(255, self.colors[i % len(self.colors)].green() + 20),
                    min(255, self.colors[i % len(self.colors)].blue() + 20)
                )
                painter.fillRect(chart_rect.left(), hover_y, bar_width, hover_height, hover_color)

                # 添加内部高光（无边框）
                inner_highlight = QRect(chart_rect.left() + 2, hover_y + 2, bar_width - 4, hover_height // 3)
                inner_highlight_color = QColor(255, 255, 255, 30)
                painter.fillRect(inner_highlight, inner_highlight_color)
            else:
                # 绘制阴影
                shadow_rect = QRect(chart_rect.left() + 2, y + 2, bar_width, bar_height)
                painter.fillRect(shadow_rect, QColor(0, 0, 0, 30))

                # 绘制圆角矩形条形
                painter.fillRect(chart_rect.left(), y, bar_width, bar_height, self.colors[i % len(self.colors)])

                # 添加高光效果
                highlight_rect = QRect(chart_rect.left() + 2, y + 2, bar_width - 4, bar_height // 3)
                highlight_color = QColor(255, 255, 255, 40)
                painter.fillRect(highlight_rect, highlight_color)
            
            # 绘制标签（左侧外部显示版本号，垂直居中）
            if self.theme == "light":
                painter.setPen(QColor(0, 0, 0))
            else:
                painter.setPen(QColor(255, 255, 255))
            label_y = y - 2 if self.hover_index == i else y
            painter.drawText(padding, label_y, label_width, bar_height + 4,
                           Qt.AlignmentFlag.AlignCenter, label)
            
            # 绘制数值（条内右侧显示数量）
            painter.setPen(QColor(255, 255, 255))
            value_y = y - 2 if self.hover_index == i else y
            painter.drawText(chart_rect.left() + bar_width - 45, value_y, 40, bar_height + 4,
                           Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter, str(value))


class StatisticsTab(QWidget):
    """统计信息标签页"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statistics_tab")
        self.config = Config()
        self.signal_bus = SignalBus()
        self.current_user = self.config.current_user
        self.base_achievements = []
        self.user_progress = {}
        self.merged_achievements = []
        
        # 创建提示框
        self.tooltip = TooltipWidget(self)
        
        self.init_ui()
        
        # 监听用户切换信号
        self.signal_bus.user_switched.connect(self.on_user_switched)
        self.signal_bus.theme_changed.connect(self.on_theme_changed)
        
        # 直接加载数据
        self.load_data()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 控制区域
        control_group = QGroupBox("筛选条件")
        control_main_layout = QVBoxLayout(control_group)
        
        # 第一行筛选
        filter_layout1 = QHBoxLayout()
        
        # 用户选择
        user_label = QLabel("用户:")
        user_label.setFixedWidth(50)
        user_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        filter_layout1.addWidget(user_label)
        
        self.user_combo = QComboBox()
        self.user_combo.currentTextChanged.connect(self.on_user_changed)
        self.user_combo.setFixedWidth(120)
        filter_layout1.addWidget(self.user_combo)
        
        # 第一分类筛选
        first_category_label = QLabel("第一分类:")
        first_category_label.setFixedWidth(70)
        first_category_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        filter_layout1.addWidget(first_category_label)
        
        self.first_category_filter = QComboBox()
        self.first_category_filter.addItem("全部")
        self.first_category_filter.setFixedWidth(120)
        self.first_category_filter.currentTextChanged.connect(self.on_first_category_changed)
        filter_layout1.addWidget(self.first_category_filter)
        
        # 第二分类筛选
        second_category_label = QLabel("第二分类:")
        second_category_label.setFixedWidth(70)
        second_category_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        filter_layout1.addWidget(second_category_label)
        
        self.second_category_filter = QComboBox()
        self.second_category_filter.addItem("全部")
        self.second_category_filter.setFixedWidth(120)
        self.second_category_filter.currentTextChanged.connect(self.update_statistics)
        filter_layout1.addWidget(self.second_category_filter)
        
        # 版本筛选
        version_label = QLabel("版本:")
        version_label.setFixedWidth(50)
        version_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        filter_layout1.addWidget(version_label)
        
        self.version_filter = QComboBox()
        self.version_filter.addItem("全部")
        self.version_filter.setFixedWidth(100)
        self.version_filter.currentTextChanged.connect(self.update_statistics)
        filter_layout1.addWidget(self.version_filter)
        
        filter_layout1.addStretch()
        
        # 刷新按钮
        self.refresh_btn = QPushButton("刷新统计")
        self.refresh_btn.clicked.connect(self.load_data)
        self.refresh_btn.setFixedWidth(100)
        filter_layout1.addWidget(self.refresh_btn)
        
        control_main_layout.addLayout(filter_layout1)
        
        layout.addWidget(control_group)
        
        # 统计概览
        stats_group = QGroupBox("统计概览")
        stats_layout = QHBoxLayout(stats_group)
        stats_layout.addStretch()
        
        # 总成就数
        self.total_label = QLabel("总成就数: 0")
        self.total_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        stats_layout.addWidget(self.total_label)
        stats_layout.addSpacing(80)
        
        # 已完成
        self.completed_label = QLabel("已完成: 0")
        self.completed_label.setStyleSheet("color: #27ae60; font-size: 16px; font-weight: bold;")
        stats_layout.addWidget(self.completed_label)
        stats_layout.addSpacing(80)
        
        # 完成率
        self.completion_rate_label = QLabel("完成率: 0%")
        self.completion_rate_label.setStyleSheet("color: #3498db; font-size: 16px; font-weight: bold;")
        stats_layout.addWidget(self.completion_rate_label)
        stats_layout.addSpacing(80)
        
        # 暂不可获取
        self.unavailable_label = QLabel("暂不可获取: 0")
        self.unavailable_label.setStyleSheet("color: #e67e22; font-size: 16px; font-weight: bold;")
        stats_layout.addWidget(self.unavailable_label)
        stats_layout.addStretch()
        
        layout.addWidget(stats_group)
        
        # 图表区域
        charts_layout = QGridLayout()
        charts_layout.setSpacing(10)
        charts_layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. 完成状态饼图
        self.pie_chart = SimpleChartWidget("pie")
        self.pie_chart.setMinimumSize(250, 250)
        charts_layout.addWidget(self.pie_chart, 0, 0)
        
        # 2. 分类完成情况柱状图
        self.bar_chart = SimpleChartWidget("bar")
        self.bar_chart.setMinimumSize(600, 350)
        charts_layout.addWidget(self.bar_chart, 0, 1)
        
        # 3. 版本分布图
        self.version_chart = SimpleChartWidget("horizontal_bar")
        self.version_chart.setMinimumSize(800, 200)
        charts_layout.addWidget(self.version_chart, 1, 0, 1, 2)
        
        layout.addLayout(charts_layout)
        
        # 应用按钮样式
        self.refresh_btn.setStyleSheet(get_button_style(self.config.theme))
        
        self.setLayout(layout)
    
    def _extract_major_version(self, version):
        """提取大版本号"""
        if version == '未知':
            return '未知'
        parts = version.split('.')
        if len(parts) >= 2:
            return f"{parts[0]}.0"
        return version
    
    def load_data(self):
        """加载数据"""
        try:
            # 加载基础成就数据
            self.base_achievements = self.config.load_base_achievements()
            print(f"[DEBUG] 加载了 {len(self.base_achievements)} 个基础成就")
            
            # 加载用户进度数据
            if self.current_user:
                self.user_progress = self.config.load_user_progress(self.current_user)
                print(f"[DEBUG] 加载了用户 {self.current_user} 的进度数据")
            else:
                self.user_progress = {}
            
            # 合并数据
            self.merge_data()
            
            # 更新统计
            self.update_statistics()
            
        except Exception as e:
            print(f"[ERROR] 加载数据失败: {e}")
    
    def merge_data(self):
        """合并基础成就数据和用户进度数据"""
        self.merged_achievements = []
        
        # 创建基础成就的字典副本
        merged_dict = {}
        for achievement in self.base_achievements:
            key = achievement.get('id', '')
            if key:
                merged_dict[key] = achievement.copy()
        
        # 用用户进度数据覆盖
        for key, value in self.user_progress.items():
            if key in merged_dict:
                merged_dict[key].update(value)
        
        self.merged_achievements = list(merged_dict.values())
        print(f"[DEBUG] 合并后有 {len(self.merged_achievements)} 个成就")
    
    def calculate_statistics(self, achievements, version_filter='全部'):
        """计算统计数据"""
        stats = {
            'total': 0,
            'completed': 0,
            'unavailable': 0,
            'categories': {},
            'versions': {}
        }
        
        for achievement in achievements:
            # 版本筛选
            if version_filter != '全部':
                achievement_version = achievement.get('版本', '')
                if achievement_version != version_filter:
                    # 检查大版本号
                    major_version = self._extract_major_version(achievement_version)
                    filter_major = self._extract_major_version(version_filter)
                    if major_version != filter_major:
                        continue
            
            stats['total'] += 1
            
            status = achievement.get('获取状态', '')
            if status == '已完成':
                stats['completed'] += 1
            elif status == '暂不可获取':
                stats['unavailable'] += 1
            
            # 第一分类统计
            first_cat = achievement.get('第一分类', '未知')
            if first_cat not in stats['categories']:
                stats['categories'][first_cat] = {'total': 0, 'completed': 0}
            stats['categories'][first_cat]['total'] += 1
            if status == '已完成':
                stats['categories'][first_cat]['completed'] += 1
            
            # 版本统计
            version = achievement.get('版本', '未知')
            if version not in stats['versions']:
                stats['versions'][version] = 0
            stats['versions'][version] += 1
        
        return stats
    
    def calculate_version_stats(self, achievements, version_filter):
        """计算版本统计数据（按大版本分组）"""
        version_stats = {}
        
        for achievement in achievements:
            version = achievement.get('版本', '未知')
            
            # 版本筛选
            if version_filter != '全部':
                if version != version_filter:
                    # 检查大版本号
                    major_version = self._extract_major_version(version)
                    filter_major = self._extract_major_version(version_filter)
                    if major_version != filter_major:
                        continue
            
            # 按大版本分组
            major_version = self._extract_major_version(version)
            if major_version not in version_stats:
                version_stats[major_version] = 0
            version_stats[major_version] += 1
        
        return version_stats
    
    def update_statistics(self):
        """更新统计显示"""
        if not self.merged_achievements:
            return
        
        # 获取筛选条件
        first_category = self.first_category_filter.currentText()
        second_category = self.second_category_filter.currentText()
        version_filter = self.version_filter.currentText()
        
        # 筛选成就
        filtered_achievements = []
        for achievement in self.merged_achievements:
            # 第一分类筛选
            if first_category != '全部' and achievement.get('第一分类', '') != first_category:
                continue
            
            # 第二分类筛选
            if second_category != '全部' and achievement.get('第二分类', '') != second_category:
                continue
            
            filtered_achievements.append(achievement)
        
        # 计算统计数据
        stats = self.calculate_statistics(filtered_achievements, version_filter)
        
        # 更新统计概览
        self.total_label.setText(f"总成就数: {stats['total']}")
        self.completed_label.setText(f"已完成: {stats['completed']}")
        self.unavailable_label.setText(f"暂不可获取: {stats['unavailable']}")
        
        completion_rate = int(stats['completed'] * 100 / stats['total']) if stats['total'] > 0 else 0
        self.completion_rate_label.setText(f"完成率: {completion_rate}%")
        
        # 更新图表
        self.update_charts(stats, filtered_achievements)
    
    def update_charts(self, stats, filtered_achievements):
        """更新所有图表"""
        # 1. 更新饼图 - 按指定顺序
        pie_data = {}
        order = ['未完成', '已完成', '暂不可获取']
        for key in order:
            if key == '未完成':
                pie_data[key] = stats['total'] - stats['completed'] - stats['unavailable']
            elif key == '已完成':
                pie_data[key] = stats['completed']
            elif key == '暂不可获取':
                pie_data[key] = stats['unavailable']
        
        self.pie_chart.set_data(pie_data)
        
        # 2. 更新柱状图 - 分类完成情况
        bar_data = {}
        for category, data in stats['categories'].items():
            bar_data[category] = {
                'total': data['total'],
                'completed': data['completed']
            }
        
        self.bar_chart.set_data(bar_data)
        
        # 3. 更新版本分布图
        version_stats = self.calculate_version_stats(filtered_achievements, self.version_filter)
        self.version_chart.set_data(version_stats)
    
    def on_user_changed(self, username):
        """用户切换事件"""
        if username:
            self.current_user = username
            self.load_data()
    
    def on_user_switched(self, username):
        """响应全局用户切换信号"""
        self.current_user = username
        self.load_data()
    
    def on_first_category_changed(self, category):
        """第一分类改变事件"""
        # 清空并更新第二分类选项
        self.second_category_filter.blockSignals(True)
        self.second_category_filter.clear()
        self.second_category_filter.addItem("全部")
        
        if category != '全部':
            second_categories = set()
            for achievement in self.merged_achievements:
                if achievement.get('第一分类', '') == category:
                    second_categories.add(achievement.get('第二分类', '未知'))
            
            for cat in sorted(second_categories):
                self.second_category_filter.addItem(cat)
        
        self.second_category_filter.blockSignals(False)
        
        # 更新版本选项
        self._update_version_options(category)
        
        # 更新统计
        self.update_statistics()
    
    def _update_version_options(self, first_category='全部'):
        """更新版本选项"""
        current_version = self.version_filter.currentText()
        self.version_filter.blockSignals(True)
        self.version_filter.clear()
        self.version_filter.addItem("全部")
        
        versions = set()
        for achievement in self.merged_achievements:
            if first_category == '全部' or achievement.get('第一分类', '') == first_category:
                versions.add(achievement.get('版本', '未知'))
        
        for version in sorted(versions):
            self.version_filter.addItem(version)
        
        # 恢复选择
        if current_version and current_version != '全部':
            index = self.version_filter.findText(current_version)
            if index >= 0:
                self.version_filter.setCurrentIndex(index)
        
        self.version_filter.blockSignals(False)
    
    def _update_user_list(self):
        """更新用户列表"""
        self._update_user_list_without_signal()
    
    def _update_user_list_without_signal(self):
        """更新用户列表（不触发信号）"""
        users = self.config.get_users()
        
        # 临时断开信号连接
        self.user_combo.blockSignals(True)
        
        self.user_combo.clear()
        for username in users.keys():
            self.user_combo.addItem(username)
        
        # 选择当前用户
        if self.current_user and self.current_user in users:
            index = self.user_combo.findText(self.current_user)
            if index >= 0:
                self.user_combo.setCurrentIndex(index)
        elif self.user_combo.count() > 0:
            self.current_user = self.user_combo.itemText(0)
        
        self.user_combo.blockSignals(False)
    
    def on_theme_changed(self, theme):
        """主题改变事件"""
        # 更新图表主题
        self.pie_chart.theme = theme
        self.bar_chart.theme = theme
        self.version_chart.theme = theme
        
        # 更新颜色
        self.pie_chart.colors, _, _ = ChartColors.get_theme_colors(theme)
        self.bar_chart.colors, _, _ = ChartColors.get_theme_colors(theme)
        self.version_chart.colors, _, _ = ChartColors.get_theme_colors(theme)
        
        # 更新背景
        self.pie_chart.bg_color = QColor(0, 0, 0, 0)
        self.bar_chart.bg_color = QColor(0, 0, 0, 0)
        self.version_chart.bg_color = QColor(0, 0, 0, 0)
        
        # 刷新图表
        self.pie_chart.update()
        self.bar_chart.update()
        self.version_chart.update()
        
        # 更新按钮样式
        self.refresh_btn.setStyleSheet(get_button_style(theme))
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.tooltip.hide()
        super().leaveEvent(event)