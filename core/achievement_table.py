"""成就表格组件"""
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from core.styles import BaseStyles


class AchievementTable(QTableWidget):
    """成就表格（带状态管理功能）"""
    
    def __init__(self):
        super().__init__()
        self.setup_table()
        self.long_press_timer = QTimer()
        self.long_press_timer.setSingleShot(True)
        self.long_press_timer.timeout.connect(self.on_long_press)
        self.pressed_row = -1
        
    def setup_table(self):
        """设置表格"""
        # 设置列
        headers = ['状态', '名称', '描述', '奖励', '版本', '隐藏', '第一分类', '第二分类']
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # 设置表格属性
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.horizontalHeader().setStretchLastSection(True)
        
        # 设置垂直表头（序号列）样式
        self.verticalHeader().setVisible(True)
        self.verticalHeader().setDefaultSectionSize(25)
        self.verticalHeader().setMinimumWidth(40)
        
        # 去掉选中框和焦点
        self.setShowGrid(False)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setSelectionMode(QTableWidget.SelectionMode.NoSelection)  # 完全禁止选择
# 动态获取主题颜色
        from core.styles import BaseStyles, get_scrollbar_style
        from core.config import config
        table_style = BaseStyles.get_text_input_style(config.theme)
        scrollbar = get_scrollbar_style(config.theme)
        self.setStyleSheet(table_style + scrollbar)
        
        # 设置列宽
        self.setColumnWidth(0, 100)  # 状态
        self.setColumnWidth(1, 200)  # 名称
        self.setColumnWidth(2, 300)  # 描述
        self.setColumnWidth(3, 100)  # 奖励
        self.setColumnWidth(4, 100)  # 版本
        self.setColumnWidth(5, 80)   # 隐藏
        self.setColumnWidth(6, 120)  # 第一分类
        self.setColumnWidth(7, 120)  # 第二分类
        
        # 启用鼠标追踪以支持悬浮提示
        self.setMouseTracking(True)
        
    def load_data(self, achievements):
        """加载数据"""
        self.setRowCount(len(achievements))
        self.achievements = achievements  # 保存数据引用
        
        for row, achievement in enumerate(achievements):
            # 状态
            status = achievement.get('获取状态', '')
            if not status:
                status = '未完成'
            status_item = QTableWidgetItem(status)
            
            # 设置状态文字颜色
            if status == '已完成':
                status_item.setForeground(QColor(255, 140, 0))  # 橙色
            elif status == '未完成':
                status_item.setForeground(QColor(128, 128, 128))  # 灰色
            elif status == '暂不可获取':
                status_item.setForeground(QColor(255, 0, 0))  # 红色
                
            self.setItem(row, 0, status_item)

            # 名称（完整显示，但保留悬浮提示）
            name = achievement.get('名称', '')
            name_item = QTableWidgetItem(name)
            name_item.setToolTip(name)  # 悬浮显示完整名称
            
            # 设置字体加粗
            font = name_item.font()
            font.setBold(True)
            name_item.setFont(font)
            
            if achievement.get('是否隐藏') == '隐藏':
                name_item.setForeground(QColor(255, 165, 0))  # 橙黄色文字
            self.setItem(row, 1, name_item)

            # 描述（完整显示，但保留悬浮提示）
            desc = achievement.get('描述', '')
            desc_item = QTableWidgetItem(desc)
            desc_item.setToolTip(desc)  # 悬浮显示完整描述
            self.setItem(row, 2, desc_item)

            # 奖励
            reward_item = QTableWidgetItem(achievement.get('奖励', ''))
            reward_text = achievement.get('奖励', '')
            if '20' in reward_text:
                reward_item.setForeground(QColor(255, 107, 53))  # 橙色
            elif '10' in reward_text:
                reward_item.setForeground(QColor(78, 205, 196))  # 青色
            elif '5' in reward_text:
                reward_item.setForeground(QColor(69, 183, 209))  # 蓝色
            self.setItem(row, 3, reward_item)

            # 版本
            self.setItem(row, 4, QTableWidgetItem(achievement.get('版本', '')))

            # 隐藏
            hidden_item = QTableWidgetItem("是" if achievement.get('是否隐藏') == '隐藏' else "否")
            if achievement.get('是否隐藏') == '隐藏':
                hidden_item.setForeground(QColor(255, 165, 0))  # 橙黄色文字
            self.setItem(row, 5, hidden_item)

            # 第一分类
            self.setItem(row, 6, QTableWidgetItem(achievement.get('第一分类', '')))

            # 第二分类
            self.setItem(row, 7, QTableWidgetItem(achievement.get('第二分类', '')))

        # 不调整列宽，保持设定的宽度
    
    def mousePressEvent(self, event):
        """鼠标点击事件 - 处理状态切换"""
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.pos())
            if item and item.column() == 0:  # 状态列
                row = item.row()
                current_status = item.text()
                
                # 立即切换状态
                if current_status == '未完成':
                    new_status = '已完成'
                elif current_status == '已完成':
                    new_status = '未完成'
                else:
                    new_status = '未完成'
                
                # 立即更新表格和颜色
                item.setText(new_status)
                if new_status == '已完成':
                    item.setForeground(QColor(255, 140, 0))  # 橙色
                elif new_status == '未完成':
                    item.setForeground(QColor(128, 128, 128))  # 灰色
                
                # 强制重绘该单元格和viewport
                self.viewport().update()
                self.update()
                
                # 立即更新数据
                if 0 <= row < len(self.achievements):
                    self.achievements[row]['获取状态'] = new_status
                    # 立即保存数据（兼容不同的父组件）
                    parent = self.parent()
                    if hasattr(parent, 'save_local_data'):
                        parent.save_local_data()
                    elif hasattr(parent, 'save_to_json'):
                        parent.save_to_json()
                
                self.pressed_row = row
                # 启动长按定时器（1秒）
                self.long_press_timer.start(1000)
        
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 处理长按"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 停止长按定时器
            self.long_press_timer.stop()
            self.pressed_row = -1
        
        super().mouseReleaseEvent(event)
    
    def on_long_press(self):
        """长按事件处理"""
        if self.pressed_row >= 0:
            item = self.item(self.pressed_row, 0)
            if item:
                # 将状态设置为"暂不可获取"
                item.setText("暂不可获取")
                item.setForeground(QColor(255, 0, 0))  # 红色
                
                # 更新数据
                if 0 <= self.pressed_row < len(self.achievements):
                    self.achievements[self.pressed_row]['获取状态'] = '暂不可获取'
                    # 立即保存数据（兼容不同的父组件）
                    parent = self.parent()
                    if hasattr(parent, 'save_local_data'):
                        parent.save_local_data()
                    elif hasattr(parent, 'save_to_json'):
                        parent.save_to_json()
                
                # 强制重绘
                self.viewport().update()
                self.update()
    
    def apply_theme(self, theme):
        """应用主题"""
        # 更新表格样式
        table_style = BaseStyles.get_text_input_style(theme)
        self.setStyleSheet(table_style)