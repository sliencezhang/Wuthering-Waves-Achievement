from PySide6.QtCore import QObject, Signal


class SignalBus(QObject):
    """全局信号总线"""
    
    # 设置相关信号
    settings_changed = Signal(dict)  # 设置变更信号
    user_switched = Signal(str)  # 用户切换信号
    theme_changed = Signal(str)  # 主题切换信号
    
    # 爬虫相关信号
    crawl_started = Signal()  # 开始爬取
    crawl_finished = Signal(object, str)  # 爬取完成 (数据, 消息)
    crawl_progress = Signal(str)  # 爬取进度
    
    # 认证相关信号
    auth_data_updated = Signal(str, str)  # 认证数据更新 (devcode, token)
    
    # 通用消息信号
    log_message = Signal(str, str, dict)  # 日志消息 (级别, 消息, 额外数据)
    
    def __init__(self):
        super().__init__()


# 创建全局信号实例
signal_bus = SignalBus()