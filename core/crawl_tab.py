from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QTableWidget, QTableWidgetItem, QLineEdit,
                               QGroupBox, QFileDialog)
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor
import json

import requests
from bs4 import BeautifulSoup
import re
import html
import os

from core.config import config
from core.signal_bus import signal_bus
from core.styles import (get_button_style, get_font_gray_style)


class AchievementCrawler(QObject):
    """成就爬虫类"""
    progress = Signal(str)
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, target_version=None):
        super().__init__()
        self.target_version = target_version
        self.devcode = ""
        self.token = ""
        
        # 从配置文件加载分类配置
        self.category_config = config.load_category_config()
        self.first_categories = self.category_config.get("first_categories", {})
        self.second_categories = self.category_config.get("second_categories", {})
        
        # 创建第二分类到第一分类的映射
        self.first_category_map = {}
        for first_cat, second_cats in self.second_categories.items():
            for second_cat in second_cats:
                self.first_category_map[second_cat] = first_cat
    
    def _load_auth_config(self):
        """从配置中加载认证信息"""
        self.devcode, self.token = config.get_auth_data()

    def crawl(self):
        try:
            # 加载认证信息
            self._load_auth_config()
            self.progress.emit("正在获取成就数据...")
            data = self.get_achievement_data()
            if data:
                self.progress.emit("解析成就数据...")
                achievements = self.parse_achievements_data(data, self.target_version)
                self.finished.emit(achievements)
            else:
                self.error.emit("获取数据失败")
        except Exception as e:
            self.error.emit(str(e))

    def get_achievement_data(self):
        from core.config import get_resource_path
        import json
        
        cache_file = get_resource_path("resources") / "achievement_cache.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                self.progress.emit("使用本地缓存数据...")
                print("[INFO] 使用本地缓存数据")
                return cached_data
            except Exception as e:
                print(f"[WARNING] 读取缓存失败: {str(e)}，将重新请求")
        
        url = "https://api.kurobbs.com/wiki/core/catalogue/item/getEntryDetail"
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'Origin': 'https://wiki.kurobbs.com',
            'Referer': 'https://wiki.kurobbs.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'devcode': self.devcode,
            'token': self.token,
            'wiki_type': '9'
        }
        data = {'id': '1220879855033786368'}

        try:
            response = requests.post(url, headers=headers, data=data, timeout=30)
            response.encoding = 'utf-8'
            response_data = response.json()
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, ensure_ascii=False, indent=2)
            print(f"[INFO] 已保存缓存到: {cache_file}")
            
            return response_data
        except Exception as e:
            raise Exception(f"网络请求失败: {str(e)}")

    def clean_text(self, text):
        if text is None:
            return ""
        text = re.sub(r'\s+', ' ', text).strip()
        text = html.unescape(text)
        return text

    def parse_html_table(self, html_content):
        achievements = []
        soup = BeautifulSoup(html_content, 'html.parser')
        rows = soup.find_all('tr')

        for row in rows[1:]:
            cells = row.find_all('td')
            if len(cells) >= 5:
                name_text = self.clean_text(cells[0].get_text(strip=True))
                is_hidden = '隐藏成就' in name_text

                if '「隐藏成就」' in name_text:
                    name_text = name_text.replace('「隐藏成就」', '').strip()

                achievement = {
                    '名称': name_text,
                    '版本': self.clean_text(cells[1].get_text(strip=True)),
                    '第二分类': self.clean_text(cells[2].get_text(strip=True)),
                    '描述': self.clean_text(cells[3].get_text(strip=True)),
                    '奖励': self.clean_text(cells[4].get_text(strip=True)),
                    '是否隐藏': '隐藏' if is_hidden else ''
                }
                achievements.append(achievement)
        return achievements

    def parse_achievements_data(self, api_data, target_version=None):
        achievements = []
        try:
            content = api_data.get('data', {}).get('content', {})
            modules = content.get('modules', [])

            for module in modules:
                components = module.get('components', [])
                for component in components:
                    if component.get('type') == 'filter-component':
                        html_content = component.get('content', '')
                        parsed = self.parse_html_table(html_content)
                        achievements.extend(parsed)

            # 添加分类信息和其他字段
            for achievement in achievements:
                second_category = achievement.get('第二分类', '')
                first_category = self.first_category_map.get(second_category, "未知分类")
                achievement['第一分类'] = first_category

            # 再次过滤掉未知分类的数据（双重保险）
            achievements = [a for a in achievements if a.get('第一分类') != '未知分类']
            
            # 填充编号（内部已包含排序）
            achievements = self.fill_serial_numbers(achievements)

            # 再次过滤掉未知分类的数据（双重保险）
            achievements = [a for a in achievements if a.get('第一分类') != '未知分类']
            
            print(f"[DEBUG] 过滤后剩余 {len(achievements)} 条成就数据")

            # 必须有target_version才进行筛选
            if not target_version:
                raise Exception("必须指定版本号才能爬取数据")
                
            version_filtered = [ach for ach in achievements if ach.get('版本') == target_version]
            print(f"[DEBUG] 版本 {target_version} 筛选后剩余 {len(version_filtered)} 条成就数据")
            
            if not version_filtered:
                raise Exception(f"版本 {target_version} 没有找到任何成就数据")
                
            achievements = version_filtered
                
        except Exception as e:
            raise Exception(f"解析数据失败: {str(e)}")

        return achievements
    
    
    
    def fill_serial_numbers(self, achievements):
            """根据分类自动填充绝对编号和编号"""
            # 获取分类配置
            first_categories = self.first_categories
            second_categories = self.second_categories
            
            def get_sort_key(achievement):
                """获取排序键"""
                # 第一分类排序
                first_cat = achievement.get('第一分类', '')
                first_order = first_categories.get(first_cat, 999)

                # 第二分类排序
                second_cat = achievement.get('第二分类', '')
                first_cat_second = second_categories.get(first_cat, {})
                second_order = int(first_cat_second.get(second_cat, 999)) if second_cat in first_cat_second else 999

                # 版本号排序（浮点型正序）
                version_str = achievement.get('version', '0.0')
                try:
                    version = float(version_str)
                except ValueError:
                    version = 0.0

                # 原编号（用于保持相对稳定）
                original_id = achievement.get('serial_number', '99999999')

                return (first_order, second_order, version, original_id)
            
            # 按新规则排序
            sorted_achievements = sorted(achievements, key=get_sort_key)
            # 用于跟踪每个分类组合的当前序号
            current_numbers = {}
            
            # 为每个成就分配编号
            for achievement in sorted_achievements:
                first_cat = achievement.get('第一分类', '')
                second_cat = achievement.get('第二分类', '')
                
                if not first_cat or not second_cat:
                    achievement['serial_number'] = ''
                    continue
                
                # 获取第一分类
                first_category_detail = first_cat
                first_category = self.get_first_category(first_category_detail)
                
                # 获取第二分类后缀
                suffix = self.get_second_category_suffix(first_category, second_cat)
                
                # 获取第一分类排序号
                first_category_order = self.first_categories.get(first_category, 1)
                
                # 生成完整前缀：第一分类(1位) + 第二分类后缀(补齐到3位)
                # 确保第二分类后缀至少3位，不足前面补0
                suffix_padded = f"{int(suffix):03d}"
                full_prefix = f"{first_category_order}{suffix_padded}"
                
                # 获取当前序号
                category_key = (first_cat, second_cat)
                current_num = current_numbers.get(category_key, 1)
                
                # 生成编号：4位分类码 + 4位序号
                achievement['serial_number'] = f"{full_prefix}{current_num:04d}"
                
                # 更新序号
                current_numbers[category_key] = current_num + 1
            
            return sorted_achievements
    
    def get_first_category(self, first_category_detail):
        """获取第一分类，如果不存在则智能分配并添加到配置"""
        # 如果分类已存在，直接返回
        if first_category_detail in self.first_categories:
            return first_category_detail
        
        # 为新分类分配排序号（当前最大排序号+1）
        max_order = max(self.first_categories.values()) if self.first_categories else 0
        new_order = max_order + 1
        
        # 添加新分类到配置
        self.first_categories[first_category_detail] = new_order
        self.second_categories[first_category_detail] = {}
        
        # 保存配置
        self.save_category_config()
        
        return first_category_detail
    
    def get_second_category_suffix(self, first_category, second_category):
        """获取第二分类后缀，如果不存在则智能分配"""
        # 获取该第一分类下的第二分类配置
        category_config = self.second_categories.get(first_category, {})
        
        # 如果已存在，返回现有后缀
        if second_category in category_config:
            return category_config[second_category]
        
        # 智能分配新后缀
        existing_suffixes = set()
        for suffix in category_config.values():
            try:
                existing_suffixes.add(int(suffix))
            except (ValueError, TypeError):
                pass
        
        # 找到最小的未使用后缀
        new_suffix = 10
        while new_suffix in existing_suffixes:
            new_suffix += 10
        
        # 保存新配置
        category_config[second_category] = str(new_suffix)
        self.second_categories[first_category] = category_config
        
        # 保存到配置文件
        self.save_category_config()
        
        return str(new_suffix)
    
    def save_category_config(self):
        """保存分类配置到文件"""
        updated_config = {
            "first_categories": self.first_categories,
            "second_categories": self.second_categories
        }
        from core.config import config
        config.save_category_config(updated_config)
        print("[INFO] 分类配置已保存")


class CrawlerThread(QThread):
    """爬虫线程"""
    
    def __init__(self, crawler):
        super().__init__()
        self.crawler = crawler
    
    def run(self):
        self.crawler.crawl()


class AchievementTable(QTableWidget):
    """成就表格（爬虫专用，不带状态功能）"""
    
    def __init__(self):
        super().__init__()
        self.setup_table()
        
    def setup_table(self):
        """设置表格"""
        # 设置列
        headers = ['名称', '描述', '奖励', '版本', '隐藏', '第一分类', '第二分类']
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
        from core.styles import BaseStyles
        from core.config import config
        table_style = BaseStyles.get_text_input_style(config.theme)
        self.setStyleSheet(table_style)
        
        # 设置列宽
        self.setColumnWidth(0, 200)  # 名称
        self.setColumnWidth(1, 300)  # 描述
        self.setColumnWidth(2, 100)  # 奖励
        self.setColumnWidth(3, 100)  # 版本
        self.setColumnWidth(4, 80)   # 隐藏
        self.setColumnWidth(5, 120)  # 第一分类
        self.setColumnWidth(6, 120)  # 第二分类
        
        # 启用鼠标追踪以支持悬浮提示
        self.setMouseTracking(True)
        
    def load_data(self, achievements):
        """加载数据"""
        self.setRowCount(len(achievements))
        self.achievements = achievements  # 保存数据引用
        
        for row, achievement in enumerate(achievements):
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
            self.setItem(row, 0, name_item)

            # 描述（完整显示，但保留悬浮提示）
            desc = achievement.get('描述', '')
            desc_item = QTableWidgetItem(desc)
            desc_item.setToolTip(desc)  # 悬浮显示完整描述
            self.setItem(row, 1, desc_item)

            # 奖励
            reward_item = QTableWidgetItem(achievement.get('奖励', ''))
            reward_text = achievement.get('奖励', '')
            if '20' in reward_text:
                reward_item.setForeground(QColor(255, 107, 53))  # 橙色
            elif '10' in reward_text:
                reward_item.setForeground(QColor(78, 205, 196))  # 青色
            elif '5' in reward_text:
                reward_item.setForeground(QColor(69, 183, 209))  # 蓝色
            self.setItem(row, 2, reward_item)

            # 版本
            self.setItem(row, 3, QTableWidgetItem(achievement.get('版本', '')))

            # 隐藏
            hidden_item = QTableWidgetItem("是" if achievement.get('是否隐藏') == '隐藏' else "否")
            if achievement.get('是否隐藏') == '隐藏':
                hidden_item.setForeground(QColor(255, 165, 0))  # 橙黄色文字
            self.setItem(row, 4, hidden_item)

            # 第一分类
            self.setItem(row, 5, QTableWidgetItem(achievement.get('第一分类', '')))

            # 第二分类
            self.setItem(row, 6, QTableWidgetItem(achievement.get('第二分类', '')))

        # 不调整列宽，保持设定的宽度
    



class CrawlTab(QWidget):
    """数据爬取标签页"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.achievements = []
        self.crawler_thread = None
        # 本地数据文件路径
        # 保存数据到JSON文件
        from core.config import get_resource_path
        data_dir = get_resource_path("resources")
        data_dir.mkdir(exist_ok=True)
        self.data_file = str(data_dir / "wuthering_waves_achievements.json")
        self.init_ui()
        
        # 配置信息
        # 从配置中读取认证信息
        self._load_auth_config()
        
        # 监听配置变化信号
        signal_bus.settings_changed.connect(self._on_settings_changed)
        
        # 监听主题切换信号
        signal_bus.theme_changed.connect(self._on_theme_changed)
        
        # 不再自动加载本地数据,避免显示旧数据
        # self.load_local_data()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 控制面板
        control_group = QGroupBox("控制面板")
        control_layout = QHBoxLayout(control_group)
        
        self.version_input = QLineEdit()
        self.version_input.setPlaceholderText("输入版本号（如：1.0, 1.1, 2.0）")
        self.version_input.setMaximumWidth(150)
        # 添加输入验证器，只允许数字和小数点
        from PySide6.QtGui import QRegularExpressionValidator
        from PySide6.QtCore import QRegularExpression
        version_validator = QRegularExpressionValidator(QRegularExpression(r"^\d*\.?\d*$"))
        self.version_input.setValidator(version_validator)
        # 连接焦点失去信号，用于自动格式化
        self.version_input.editingFinished.connect(self.format_version_input)
        control_layout.addWidget(QLabel("版本:"))
        control_layout.addWidget(self.version_input)
        
        self.crawl_btn = QPushButton("开始爬取")
        self.crawl_btn.setStyleSheet(get_button_style(config.theme))
        self.crawl_btn.clicked.connect(self.start_crawling)
        self.crawl_btn.setMaximumWidth(100)
        control_layout.addWidget(self.crawl_btn)
        
        self.merge_btn = QPushButton("确认覆盖")
        self.merge_btn.setStyleSheet(get_button_style(config.theme))
        self.merge_btn.clicked.connect(self.merge_to_manage)
        self.merge_btn.setEnabled(False)
        self.merge_btn.setMaximumWidth(100)
        control_layout.addWidget(self.merge_btn)
        
        self.wiki_btn = QPushButton("打开WIKI")
        self.wiki_btn.setStyleSheet(get_button_style(config.theme))
        self.wiki_btn.clicked.connect(self.open_wiki)
        self.wiki_btn.setMaximumWidth(100)
        control_layout.addWidget(self.wiki_btn)
        
        self.clear_cache_btn = QPushButton("清除缓存")
        self.clear_cache_btn.setStyleSheet(get_button_style(config.theme))
        self.clear_cache_btn.clicked.connect(self.clear_cache)
        self.clear_cache_btn.setMaximumWidth(100)
        control_layout.addWidget(self.clear_cache_btn)
        
        self.export_btn = QPushButton("导出JSON")
        self.export_btn.setStyleSheet(get_button_style(config.theme))
        self.export_btn.clicked.connect(self.export_json)
        self.export_btn.setEnabled(False)
        self.export_btn.setMaximumWidth(100)
        control_layout.addWidget(self.export_btn)
        
        control_layout.addStretch()
        layout.addWidget(control_group)
        
        # 数据表格
        self.table = AchievementTable()
        layout.addWidget(self.table)
        
        # 初始日志
        print("[INFO] 数据爬取标签页已初始化")
    
    def _load_auth_config(self):
        """从配置中加载认证信息"""
        self.devcode, self.token = config.get_auth_data()
    
    def _on_settings_changed(self, settings_data):
        """配置变化时的处理"""
        if 'devcode' in settings_data or 'token' in settings_data:
            self._load_auth_config()
            print("[INFO] 认证配置已更新")
    
    def _on_theme_changed(self, theme):
        """主题切换时更新样式"""
        # 更新按钮样式
        if hasattr(self, 'crawl_btn'):
            self.crawl_btn.setStyleSheet(get_button_style(theme))
        if hasattr(self, 'merge_btn'):
            self.merge_btn.setStyleSheet(get_button_style(theme))
        if hasattr(self, 'wiki_btn'):
            self.wiki_btn.setStyleSheet(get_button_style(theme))
        if hasattr(self, 'clear_cache_btn'):
            self.clear_cache_btn.setStyleSheet(get_button_style(theme))
        if hasattr(self, 'export_btn'):
            self.export_btn.setStyleSheet(get_button_style(theme))
    
    def format_version_input(self):
        """自动格式化版本号输入"""
        text = self.version_input.text().strip()
        
        # 如果输入的是整数，自动添加.0
        if text and text.isdigit():
            self.version_input.setText(f"{text}.0")
    
    def start_crawling(self):
        """开始爬取"""
        target_version = self.version_input.text().strip()
        
        # 检查是否输入了版本号
        if not target_version:
            self.show_notification("请输入版本号")
            return
        
        self.crawl_btn.setEnabled(False)
        
        # 检查认证信息是否完整
        if not self.devcode or not self.token:
            self.crawl_btn.setEnabled(True)
            self.show_notification("请先在设置中配置认证信息")
            return
        
        # 创建爬虫对象和线程
        crawler = AchievementCrawler(target_version)
        crawler.progress.connect(self.update_progress)
        crawler.finished.connect(self.on_crawl_finished)
        crawler.error.connect(self.on_crawl_error)
        
        self.crawler_thread = CrawlerThread(crawler)
        self.crawler_thread.start()
        
        print(f"[INFO] 开始爬取成就数据，版本: {target_version or '全部'}")
    
    def update_progress(self, message):
        """更新进度"""
        print(f"[INFO] {message}")
    
    def on_crawl_finished(self, achievements):
        """爬取完成"""
        self.achievements = achievements
        self.table.load_data(achievements)
        self.export_btn.setEnabled(True)
        self.crawl_btn.setEnabled(True)
        
        self.show_notification(f"爬取完成，共获取 {len(achievements)} 条成就数据")
        
        # 更新配置中的默认输出文件名（包含版本）
        target_version = self.version_input.text().strip()
        if target_version:
            from core.config import config
            config.crawl_settings["default_output_file"] = f"鸣潮成就数据_v{target_version}.json"
            config.save_config()
            print(f"[INFO] 已更新默认输出文件名为: 鸣潮成就数据_v{target_version}.json")
        
        print(f"[SUCCESS] 爬取完成，共 {len(achievements)} 条数据")
        
        # 启用确认覆盖按钮
        self.merge_btn.setEnabled(True)
    
    def on_crawl_error(self, error_message):
        """爬取出错"""
        self.crawl_btn.setEnabled(True)
        self.show_notification(f"爬取失败: {error_message}")
        print(f"[ERROR] 爬取失败: {error_message}")
    
    def merge_to_manage(self):
        """确认覆盖到成就管理"""
        if not self.achievements:
            print("[WARNING] 没有数据可以覆盖")
            return
        
        # 添加确认对话框
        from core.custom_message_box import CustomMessageBox
        reply = CustomMessageBox.question(
            self, 
            "确认添加", 
            f"确定要将新爬取的 {len(self.achievements)} 条成就数据添加到现有数据中吗？\n仅添加不存在的成就，已存在的成就将保持不变！",
            ("确定", "取消")
        )
        
        if reply != CustomMessageBox.Yes:
            print("[INFO] 用户取消了覆盖操作")
            return
        
        # 获取当前管理标签页的数据
        # 尝试多种方式获取main_window
        main_window = None
        
        # 方法1: 通过parent链
        try:
            parent = self.parent()
            if parent:
                tab_widget = parent.parent()
                if tab_widget:
                    main_window = tab_widget.parent()
        except:
            pass
        
        # 方法2: 通过全局查找
        if not main_window or not hasattr(main_window, 'manage_tab'):
            try:
                from core.main_window import TemplateMainWindow
                for widget in QApplication.topLevelWidgets():
                    if isinstance(widget, TemplateMainWindow):
                        main_window = widget
                        break
                    # 即使不是TemplateMainWindow类型，如果有manage_tab属性也尝试使用
                    elif hasattr(widget, 'manage_tab'):
                        main_window = widget
                        break
            except:
                pass
        
        if not main_window or not hasattr(main_window, 'manage_tab'):
            print("[ERROR] 找不到管理标签页")
            return
        
        manage_tab = main_window.manage_tab
        if not manage_tab:
            print("[ERROR] 管理标签页为空")
            return
        
        current_achievements = manage_tab.manager.achievements
        current_names = {a.get('名称', '') for a in current_achievements}
        
        # 创建名称到成就的映射，用于快速查找
        current_name_map = {a.get('名称', ''): a for a in current_achievements}
        
        # 仅筛选出不存在的成就进行添加
        to_add = []     # 需要新增的成就
        
        for achievement in self.achievements:
            name = achievement.get('名称', '')
            if name not in current_names:
                # 新成就
                to_add.append(achievement)
        
        if not to_add:
            print("[INFO] 所有成就已存在，无需添加")
            self.show_notification("所有成就已存在，无需添加")
            return
        
        # 获取分类配置
        from core.config import config
        category_config = config.load_category_config()
        first_categories = category_config.get("first_categories", {})
        second_categories = category_config.get("second_categories", {})
        
        # 为新成就按规则生成编号
        # 先统计每个分类下已有的最大序号
        category_max_nums = {}
        for achievement in current_achievements:
            first_cat = achievement.get('第一分类', '')
            second_cat = achievement.get('第二分类', '')
            serial_num = achievement.get('编号', '')
            
            if first_cat and second_cat and serial_num and len(serial_num) >= 8:
                # 提取序号部分（后4位）
                try:
                    seq_num = int(serial_num[-4:])
                    category_key = (first_cat, second_cat)
                    category_max_nums[category_key] = max(category_max_nums.get(category_key, 0), seq_num)
                except:
                    pass
        
            # 为新成就生成编号
            for achievement in to_add:
                first_cat = achievement.get('第一分类', '')
                second_cat = achievement.get('第二分类', '')
                
                if not first_cat or not second_cat:
                    achievement['serial_number'] = ''
                    continue
                
                # 获取第一分类排序号
                first_category_order = first_categories.get(first_cat, 1)
                
                # 获取第二分类后缀
                suffix = second_categories.get(first_cat, {}).get(second_cat, '10')
                
                # 生成完整前缀：第一分类(1位) + 第二分类后缀(补齐到3位)
                suffix_padded = f"{int(suffix):03d}"
                full_prefix = f"{first_category_order}{suffix_padded}"
                
                # 获取当前分类的下一个序号
                category_key = (first_cat, second_cat)
                next_num = category_max_nums.get(category_key, 0) + 1
                
                # 生成编号：4位分类码 + 4位序号
                achievement['serial_number'] = f"{full_prefix}{next_num:04d}"
                
                # 更新最大序号
                category_max_nums[category_key] = next_num        
        # 合并数据：现有成就 + 新增的成就
        all_achievements = current_achievements + to_add
        
        # 按照规则排序
        def get_sort_key(achievement):
            """获取排序键"""
            # 第一分类排序
            first_cat = achievement.get('第一分类', '')
            first_order = first_categories.get(first_cat, 999)
            
            # 第二分类排序
            second_cat = achievement.get('第二分类', '')
            first_cat_second = second_categories.get(first_cat, {})
            second_order = int(first_cat_second.get(second_cat, 999)) if second_cat in first_cat_second else 999
            
            # 版本号排序（浮点型正序）
            version_str = achievement.get('版本', '0.0')
            try:
                version = float(version_str)
            except ValueError:
                version = 0.0
            
            # 编号（用于保持相对稳定）
            serial_number = achievement.get('serial_number', '99999999')
            
            return (first_order, second_order, version, serial_number)
        
        # 排序
        all_achievements = sorted(all_achievements, key=get_sort_key)
        
        # 重新生成绝对编号（按最终排序顺序从1开始递增）
        for index, achievement in enumerate(all_achievements, start=1):
            achievement['绝对编号'] = str(index)
        
        # 直接更新管理器的数据，而不是调用load_data
        manage_tab.manager.achievements = all_achievements
        manage_tab.manager.filtered_achievements = all_achievements.copy()
        
        print(f"[SUCCESS] 已新增 {len(to_add)} 条成就，总计 {len(all_achievements)} 条成就数据")
        
        # 添加右上角自动关闭的提示
        self.show_notification(f"成功新增 {len(to_add)} 条成就，总计 {len(all_achievements)} 条成就数据")
        
        # 更新表格显示
        manage_tab.manager_table.load_data(all_achievements)
        
        # 更新筛选器
        manage_tab.update_filters()
        
        # 更新统计
        manage_tab.update_statistics()
        
        # 保存到JSON
        manage_tab.save_to_json()
        
        # 禁用确认覆盖按钮
        self.merge_btn.setEnabled(False)
        
        # 切换到管理标签页
        if hasattr(main_window, 'tab_widget'):
            main_window.tab_widget.setCurrentIndex(0)  # 成就管理现在是第一个标签页
    
    def show_notification(self, message):
        """显示右上角自动关闭的提示"""
        from PySide6.QtWidgets import QLabel, QVBoxLayout
        from PySide6.QtCore import QTimer, Qt
        
        # 创建提示窗口
        notification = QWidget()
        notification.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        notification.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        notification.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        layout = QVBoxLayout(notification)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel(message)
        
        # 使用统一的通知样式
        from core.styles import get_notification_style
        label.setStyleSheet(get_notification_style(config.theme))
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        # 获取主窗口位置
        main_window = None
        try:
            from core.main_window import TemplateMainWindow
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, TemplateMainWindow):
                    main_window = widget
                    break
        except:
            pass
        
        # 设置提示大小和位置
        notification_width = 300
        notification_height = 60
        notification.setFixedSize(notification_width, notification_height)
        
        if main_window:
            # 相对于主窗口右上角
            main_pos = main_window.pos()
            main_size = main_window.size()
            x = main_pos.x() + main_size.width() - notification_width - 20
            y = main_pos.y() + 60
        else:
            # 屏幕右上角
            from PySide6.QtGui import QGuiApplication
            screen = QGuiApplication.primaryScreen().geometry()
            x = screen.width() - notification_width - 20
            y = 60
        
        notification.move(x, y)
        notification.show()
        
        # 创建淡出定时器
        fade_timer = QTimer()
        fade_timer.setSingleShot(True)
        fade_timer.timeout.connect(lambda: self.fade_out_notification(notification))
        fade_timer.start(3000)  # 3秒后开始淡出
        
        # 存储引用以避免被垃圾回收
        if not hasattr(self, 'active_notifications'):
            self.active_notifications = []
        self.active_notifications.append((notification, fade_timer))
    
    def fade_out_notification(self, notification):
        """淡出提示"""
        from PySide6.QtCore import QPropertyAnimation, QEasingCurve
        
        # 检查对象是否还存在
        try:
            if notification is None or not notification.isVisible():
                self._remove_notification_from_list(notification)
                return
        except RuntimeError:
            # 对象已被删除
            self._remove_notification_from_list(notification)
            return
        
        # 创建透明度动画
        fade_animation = QPropertyAnimation(notification, b"windowOpacity")
        fade_animation.setDuration(500)
        fade_animation.setStartValue(1.0)
        fade_animation.setEndValue(0.0)
        fade_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        # 动画完成后删除提示
        fade_animation.finished.connect(lambda: self._cleanup_notification(notification))
        fade_animation.start()
        
        # 保存动画引用防止被垃圾回收
        if not hasattr(self, 'active_animations'):
            self.active_animations = []
        self.active_animations.append(fade_animation)
        
        # 从活动通知列表中移除
        self._remove_notification_from_list(notification)
    
    def _remove_notification_from_list(self, notification):
        """从活动通知列表中移除通知"""
        if hasattr(self, 'active_notifications'):
            self.active_notifications = [(n, t) for n, t in self.active_notifications if n != notification]
    
    def open_wiki(self):
        """打开库街区Wiki成就页面"""
        import webbrowser
        wiki_url = "https://wiki.kurobbs.com/mc/item/1220879855033786368?wkFrom=home&wkFromLabel=%E9%A6%96%E9%A1%B5%E5%BF%AB%E6%8D%B7%E5%AF%BC%E8%88%AA"
        webbrowser.open(wiki_url)
        print(f"[INFO] 已打开Wiki页面: {wiki_url}")
    
    def clear_cache(self):
        """清除本地缓存的网页文件"""
        from core.custom_message_box import CustomMessageBox
        from core.config import get_resource_path
        
        cache_file = get_resource_path("resources") / "achievement_cache.json"
        
        if cache_file.exists():
            reply = CustomMessageBox.question(
                self, 
                "确认清除", 
                "确定要清除本地缓存的网页文件吗？",
                ("确定", "取消")
            )
            
            if reply == CustomMessageBox.Yes:
                try:
                    cache_file.unlink()
                    print("[INFO] 缓存文件已删除")
                    self.show_notification("缓存已清除")
                except Exception as e:
                    print(f"[ERROR] 清除缓存失败: {str(e)}")
                    self.show_notification(f"清除缓存失败: {str(e)}")
        else:
            print("[INFO] 没有找到缓存文件")
            self.show_notification("没有缓存文件")
    
    def _cleanup_notification(self, notification):
        """清理通知"""
        try:
            if notification and hasattr(notification, 'close'):
                notification.close()
            if notification and hasattr(notification, 'deleteLater'):
                notification.deleteLater()
            # 清理动画引用
            if hasattr(self, 'active_animations'):
                self.active_animations = [anim for anim in self.active_animations if anim and anim.state() != anim.State.Stopped]
        except:
            pass
    
        def on_crawl_error(self, error_msg):
    
            """爬取错误"""
    
            self.crawl_btn.setEnabled(True)
    
            print(f"[ERROR] 爬取失败: {error_msg}")
    
            self.show_notification(f"爬取失败: {error_msg}")
    
    
    
    def export_json(self):
        """导出数据"""
        if not self.achievements:
            print("[WARNING] 没有数据可导出")
            return
        
        # 获取配置中的默认文件名
        from core.config import config
        default_filename = config.crawl_settings.get("default_output_file", "鸣潮成就数据.json")
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出JSON文件", default_filename, "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                self.export_to_json(file_path)
            except Exception as e:
                print(f"[ERROR] 导出失败: {str(e)}")
    
    def export_to_json(self, json_path):
        """导出为全字段 JSON 格式"""
        try:
            export_data = []
            for achievement in self.achievements:
                export_data.append({
                    '绝对编号': achievement.get('绝对编号', ''),
                    '版本': achievement.get('版本', ''),
                    '第一分类': achievement.get('第一分类', ''),
                    '第二分类': achievement.get('第二分类', ''),
                    '编号': achievement.get('编号', ''),
                    '名称': achievement.get('名称', ''),
                    '描述': achievement.get('描述', ''),
                    '奖励': achievement.get('奖励', ''),
                    '是否隐藏': achievement.get('是否隐藏', ''),
                    '获取状态': achievement.get('获取状态', '')
                })
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            print(f"[SUCCESS] 全字段数据已导出到: {json_path}")
            print(f"[INFO] 包含 {len(export_data)} 条成就数据")
        except Exception as e:
            print(f"[ERROR] 导出 JSON 失败: {str(e)}")
    
    def load_local_data(self):
        """加载本地保存的数据"""
        try:
            print(f"[DEBUG] 检查文件: {self.data_file}")
            print(f"[DEBUG] 文件是否存在: {os.path.exists(self.data_file)}")
            
            if os.path.exists(self.data_file):
                print(f"[INFO] 正在从 {self.data_file} 加载数据...")
                
                # 检查是否有 JSON 备份文件
                json_file = self.data_file.replace('.xlsx', '.json')
                if os.path.exists(json_file):
                    print(f"[INFO] 找到 JSON 备份文件，优先加载: {json_file}")
                    self.load_from_json(json_file)
                    return
                
                # 现在只支持JSON格式，Excel文件已不再使用
                print(f"[INFO] 本地数据文件不存在或格式不支持: {self.data_file}")
                print(f"[INFO] 请使用JSON格式的数据文件")
                
                print(f"[DEBUG] 转换后的数据条数: {len(self.achievements)}")
                
                self.table.load_data(self.achievements)
                self.export_btn.setEnabled(True)
                print(f"[INFO] 已加载本地数据: {len(self.achievements)} 条")
            else:
                print(f"[INFO] 本地数据文件不存在: {self.data_file}")
        except Exception as e:
            print(f"[WARNING] 加载本地数据失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def load_from_json(self, json_file):
        """从 JSON 文件加载数据"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.achievements = []
                
                # 直接使用中文键名,不需要映射
                for item in data:
                    achievement = {}
                    for key, value in item.items():
                        achievement[key] = value
                    
                    self.achievements.append(achievement)
                
                print(f"[INFO] 从 JSON 加载了 {len(self.achievements)} 条数据")
        except Exception as e:
            print(f"[ERROR] 加载 JSON 文件失败: {str(e)}")
    

    
    
    
    
    
    def save_local_data(self):
            """保存数据到本地文件（JSON）"""
            if not self.achievements:
                print("[WARNING] 没有数据可保存")
                return

            try:
                print(f"[DEBUG] 准备保存数据到: {self.data_file}")
                print(f"[DEBUG] 文件路径类型: {type(self.data_file)}")
                print(f"[DEBUG] 文件是否存在: {os.path.exists(self.data_file)}")

                # 确保目录存在
                data_dir = os.path.dirname(self.data_file)
                if not os.path.exists(data_dir):
                    print(f"[INFO] 创建目录: {data_dir}")
                    os.makedirs(data_dir, exist_ok=True)

                # 保存为 JSON 格式
                self.save_to_json(self.data_file)
                print("[INFO] 数据已保存为 JSON 格式")

            except Exception as e:
                print(f"[ERROR] 保存数据失败: {str(e)}")
                import traceback
                traceback.print_exc()
    
    def save_to_json(self, json_file):
        """保存为 JSON 格式"""
        try:
            # 准备数据，使用中文键名
            json_data = []
            for achievement in self.achievements:
                # 创建副本，确保数据可序列化
                item = {}
                
                # 按照指定顺序处理字段
                field_order = [
                    '版本',
                    '第一分类',
                    '第二分类',
                    '编号',
                    '名称',
                    '描述',
                    '奖励',
                    '是否隐藏'
                ]
                
                for chinese_key in field_order:
                    # 获取原始值
                    value = achievement.get(chinese_key, '')
                    
                    # 确保所有值都是字符串
                    if value is None:
                        item[chinese_key] = ''
                    else:
                        item[chinese_key] = str(value)
                
                json_data.append(item)
            
            # 保存到 JSON
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            file_size = os.path.getsize(json_file)
            print(f"[SUCCESS] JSON 数据已保存到: {json_file}")
            print(f"[SUCCESS] JSON 文件大小: {file_size} 字节")
            print(f"[INFO] 保存了 {len(json_data)} 条成就数据")
            
        except Exception as e:
            print(f"[ERROR] 保存 JSON 失败: {str(e)}")
    
    
    
    def apply_theme(self, theme):
        """应用主题"""
        # 更新按钮样式
        if hasattr(self, 'crawl_btn'):
            self.crawl_btn.setStyleSheet(get_button_style(theme))
        if hasattr(self, 'merge_btn'):
            self.merge_btn.setStyleSheet(get_button_style(theme))
        if hasattr(self, 'export_btn'):
            self.export_btn.setStyleSheet(get_button_style(theme))
        
        # 更新输入框样式
        if hasattr(self, 'search_input'):
            from core.styles import BaseStyles
            input_style = BaseStyles.get_text_input_style(theme)
            self.search_input.setStyleSheet(input_style)
        
        # 更新下拉框样式
        if hasattr(self, 'version_filter'):
            from core.styles import BaseStyles
            combo_style = BaseStyles.get_combobox_style(theme)
            self.version_filter.setStyleSheet(combo_style)
        if hasattr(self, 'first_category_filter'):
            from core.styles import BaseStyles
            combo_style = BaseStyles.get_combobox_style(theme)
            self.first_category_filter.setStyleSheet(combo_style)
        if hasattr(self, 'second_category_filter'):
            from core.styles import BaseStyles
            combo_style = BaseStyles.get_combobox_style(theme)
            self.second_category_filter.setStyleSheet(combo_style)
        if hasattr(self, 'priority_filter'):
            from core.styles import BaseStyles
            combo_style = BaseStyles.get_combobox_style(theme)
            self.priority_filter.setStyleSheet(combo_style)
        if hasattr(self, 'hidden_filter'):
            from core.styles import BaseStyles
            combo_style = BaseStyles.get_combobox_style(theme)
            self.hidden_filter.setStyleSheet(combo_style)
        if hasattr(self, 'obtainable_filter'):
            from core.styles import BaseStyles
            combo_style = BaseStyles.get_combobox_style(theme)
            self.obtainable_filter.setStyleSheet(combo_style)
        
        # 更新表格样式
        if hasattr(self, 'table'):
            from core.styles import BaseStyles
            table_style = BaseStyles.get_text_input_style(theme)
            self.table.setStyleSheet(table_style)
    
    