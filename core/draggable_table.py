from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QApplication
from PySide6.QtCore import Qt, QMimeData, QRect
from PySide6.QtGui import QDrag, QPainter, QColor


class DraggableTableWidget(QTableWidget):
    """支持行拖动的表格控件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QTableWidget.DragDropMode.InternalMove)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setDragDropOverwriteMode(False)  # 不覆盖目标行
        
        # 记录拖动起始行
        self._drag_start_row = -1
        # 记录拖动时的插入位置
        self._drop_indicator_row = -1
        
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 记录拖动起始行
            self._drag_start_row = self.rowAt(event.position().y())
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
            
        if self._drag_start_row == -1:
            return
            
        # 开始拖动
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # 设置拖动数据
        mime_data.setText(f"row:{self._drag_start_row}")
        drag.setMimeData(mime_data)
        
        # 执行拖动
        drop_action = drag.exec(Qt.DropAction.MoveAction)
        
    def dragEnterEvent(self, event):
        """拖动进入事件"""
        if event.mimeData().hasText() and event.mimeData().text().startswith("row:"):
            event.acceptProposedAction()
        else:
            event.ignore()
            self._drop_indicator_row = -1
            self.viewport().update()
            
    def dragMoveEvent(self, event):
        """拖动移动事件"""
        if event.mimeData().hasText() and event.mimeData().text().startswith("row:"):
            event.acceptProposedAction()
            
            # 获取源行
            source_row = int(event.mimeData().text().split(":")[1])
            
            # 更新插入指示线位置
            y = event.position().y()
            target_row = self.rowAt(y)
            
            if target_row == -1:
                # 如果目标行无效，显示在最后
                self._drop_indicator_row = self.rowCount()
            else:
                # 计算行的中心点
                row_top = self.rowViewportPosition(target_row)
                row_height = self.rowHeight(target_row)
                row_center = row_top + row_height / 2
                
                # 根据鼠标位置决定插入位置
                if y > row_center:
                    # 鼠标在中心下方，插入到目标行下方
                    self._drop_indicator_row = target_row + 1
                else:
                    # 鼠标在中心上方，插入到目标行上方
                    self._drop_indicator_row = target_row
                
                # 特殊处理：如果拖动到相邻行，确保插入线显示正确
                if abs(target_row - source_row) <= 1:
                    if target_row == source_row:
                        # 在同一行，根据鼠标位置决定
                        self._drop_indicator_row = source_row if y < row_center else source_row + 1
                    elif target_row == source_row - 1:
                        # 拖动到上一行
                        self._drop_indicator_row = source_row if y > row_center else target_row
                    elif target_row == source_row + 1:
                        # 拖动到下一行
                        self._drop_indicator_row = target_row + 1 if y > row_center else source_row
            
            # 触发重绘以显示指示线
            self.viewport().update()
        else:
            event.ignore()
            self._drop_indicator_row = -1
            self.viewport().update()
            
    def dropEvent(self, event):
        """放置事件"""
        if not event.mimeData().hasText() or not event.mimeData().text().startswith("row:"):
            event.ignore()
            return
            
        # 获取源行
        source_row = int(event.mimeData().text().split(":")[1])
        
        # 使用当前显示的插入线位置作为目标位置
        target_row = getattr(self, '_drop_indicator_row', -1)
        
        # 如果没有有效的插入线位置，不执行操作
        if target_row == -1:
            event.ignore()
            return
            
        # 如果源行就是目标位置，不执行操作
        if source_row == target_row or (source_row == target_row - 1):
            event.ignore()
            return
        
        # 执行行移动
        self._move_row(source_row, target_row)
        event.acceptProposedAction()
        
        # 通知父窗口行已移动
        if hasattr(self.parent(), '_on_row_moved'):
            self.parent()._on_row_moved(self, source_row, target_row)
        
        # 清理指示线
        self._drop_indicator_row = -1
        self.viewport().update()
            
    def _move_row(self, source_row, target_row):
        """移动行"""
        # 获取源行的所有项目
        items = []
        for col in range(self.columnCount()):
            item = self.takeItem(source_row, col)
            items.append(item)
            
        # 删除源行
        self.removeRow(source_row)
        
        # 调整目标行索引（因为删除源行后，目标行索引可能发生变化）
        if target_row > source_row:
            target_row -= 1
            
        # 在目标位置插入新行
        self.insertRow(target_row)
        
        # 将项目放入新行
        for col, item in enumerate(items):
            if item:
                self.setItem(target_row, col, item)
                
        # 选中新移动的行
        self.selectRow(target_row)
    
    def paintEvent(self, event):
        """重绘事件，用于绘制拖动指示线"""
        super().paintEvent(event)
        
        # 如果正在拖动且有效位置，绘制插入指示线
        if hasattr(self, '_drop_indicator_row') and self._drop_indicator_row >= 0:
            painter = QPainter(self.viewport())
            painter.setPen(QColor(64, 158, 255, 200))  # 蓝色半透明
            painter.setBrush(QColor(64, 158, 255, 100))  # 填充色
            
            # 计算指示线的位置
            if self._drop_indicator_row < self.rowCount():
                row_top = self.rowViewportPosition(self._drop_indicator_row)
            else:
                # 如果是最后一行之后
                row_top = self.rowViewportPosition(self.rowCount() - 1) + self.rowHeight(self.rowCount() - 1)
            
            # 绘制水平指示线
            indicator_rect = QRect(0, row_top - 2, self.viewport().width(), 4)
            painter.drawRect(indicator_rect)
            painter.fillRect(indicator_rect, QColor(64, 158, 255, 100))