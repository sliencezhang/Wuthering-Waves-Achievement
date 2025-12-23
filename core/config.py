import json
import sys
import os
from pathlib import Path


def get_resource_path(relative_path):
    """获取资源文件的绝对路径，支持开发环境和打包后的环境"""
    # Nuitka 打包后 sys.executable 指向临时目录的 python.exe
    # 判断是否打包：检查 __file__ 是否存在（打包后不存在）或 sys.argv[0] 是否为 .exe
    if getattr(sys, 'frozen', False) or not hasattr(sys.modules[__name__], '__file__') or sys.argv[0].endswith('.exe'):
        # 打包后：使用 argv[0] 的绝对路径获取 exe 实际位置
        base_path = Path(os.path.abspath(sys.argv[0])).parent
    else:
        # 开发环境：当前文件的父目录的父目录
        base_path = Path(__file__).parent.parent
    
    return base_path / relative_path


class Config:
    """配置管理类"""
    
    def __init__(self):
        self.config_file = get_resource_path("resources/config.json")
        
        # 直接定义属性，与模板保持一致
        self.current_user = ""
        self.users = {}
        self.devcode = ""
        self.token = ""
        self.theme = "light"
        self.auto_save = True
        self.use_background = True
        self.custom_background_light = ""
        self.custom_background_dark = ""
        self.current_profile = ""
        self.user_avatars = {}  # 存储用户头像路径
        self.user_character_names = {}  # 存储用户选择的角色名
        self.crawl_settings = {
            "default_output_file": "鸣潮成就数据.json",
            "default_version_filter": "",
            "save_logs": True
        }
        
        # GitHub仓库配置（用于更新检查）
        self.github_owner = "sliencezhang"  # GitHub用户名
        self.github_repo = "Wuthering-Waves-Achievement"  # 仓库名
        
        # 更新下载链接配置
        self.update_download_url = "https://wwbml.lanzoum.com/b01880knob"  # 蓝奏云下载链接
        self.update_download_password = "1234"  # 下载密码
        
        # 使用 QSettings 存储认证信息
        from PySide6.QtCore import QSettings
        self.settings = QSettings("WutheringWavesAchievement", "AuthData")
        
        self.load_config()
        self._load_auth_from_settings()
    
    def load_config(self):
        """加载配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    # 更新属性
                    for key, value in loaded_data.items():
                        if hasattr(self, key):
                            setattr(self, key, value)
        except Exception as e:
            print(f"加载配置失败: {e}")
    
    def save_config(self):
        """保存配置"""
        try:
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 收集所有属性（不包括认证信息）
            data = {
                "current_user": self.current_user,
                "users": self.users,
                "theme": self.theme,
                "auto_save": self.auto_save,
                "use_background": self.use_background,
                "custom_background_light": self.custom_background_light,
                "custom_background_dark": self.custom_background_dark,
                "current_profile": self.current_profile,
                "crawl_settings": self.crawl_settings,
                "user_avatars": self.user_avatars,
                "user_character_names": self.user_character_names,
                "github_owner": self.github_owner,
                "github_repo": self.github_repo,
                "update_download_url": self.update_download_url,
                "update_download_password": self.update_download_password
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 保存认证信息到 QSettings
            self._save_auth_to_settings()
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def save_to_settings(self):
        """保存配置到设置文件（与模板保持一致的方法名）"""
        self.save_config()
    
    def add_user(self, username, user_data=None):
        """添加用户"""
        if user_data is None:
            user_data = {}
        self.users[username] = user_data
        self.current_user = username
        self.save_config()
    
    def switch_user(self, username):
        """切换用户"""
        if username in self.users:
            self.current_user = username
            self.save_config()
            # 发送用户切换信号
            from core.signal_bus import signal_bus
            signal_bus.user_switched.emit(username)
            return True
        return False
    
    def get_current_user(self):
        """获取当前用户"""
        return self.current_user
    
    def get_users(self):
        """获取所有用户"""
        return self.users
    
    def get_auth_data(self):
        """获取当前认证数据"""
        return self.devcode or "", self.token or ""
    
    def _load_auth_from_settings(self):
        """从 QSettings 加载认证信息"""
        self.devcode = self.settings.value("devcode", "", str)
        self.token = self.settings.value("token", "", str)
    
    def _save_auth_to_settings(self):
        """保存认证信息到 QSettings"""
        self.settings.setValue("devcode", self.devcode)
        self.settings.setValue("token", self.token)
        self.settings.sync()  # 立即保存
    
    def set_user_avatar(self, username, avatar_path):
        """设置用户头像"""
        self.user_avatars[username] = avatar_path
        self.save_config()
    
    def get_user_avatar(self, username):
        """获取用户头像"""
        return self.user_avatars.get(username, "")
    
    def get_current_user_avatar(self):
        """获取当前用户头像"""
        current_user = self.get_current_user()
        return self.get_user_avatar(current_user)
    
    def set_user_character_name(self, username, character_name):
        """设置用户角色名"""
        self.user_character_names[username] = character_name
        self.save_config()
    
    def get_user_character_name(self, username):
        """获取用户角色名"""
        character_name = self.user_character_names.get(username)
        if not character_name:
            avatar_path = self.get_user_avatar(username)
            if avatar_path:
                character_name = Path(avatar_path).stem
            else:
                character_name = "男漂泊者"
        return character_name
    
    def get_current_user_character_name(self):
        """获取当前用户角色名"""
        current_user = self.get_current_user()
        return self.get_user_character_name(current_user)
    
    def save_base_achievements(self, achievements):
        """保存基础成就数据"""
        base_file = get_resource_path("resources/base_achievements.json")
        try:
            # 只保存基础信息，排除用户相关的字段
            base_data = []
            for achievement in achievements:
                base_achievement = {
                    "绝对编号": achievement.get("绝对编号", ""),  # 仅用于排序
                    "版本": achievement.get("版本", ""),
                    "第一分类": achievement.get("第一分类", ""),
                    "第二分类": achievement.get("第二分类", ""),
                    "编号": achievement.get("编号", ""),  # 作为主键
                    "名称": achievement.get("名称", ""),
                    "描述": achievement.get("描述", ""),
                    "奖励": achievement.get("奖励", ""),
                    "是否隐藏": achievement.get("是否隐藏", "")
                }
                base_data.append(base_achievement)
            
            with open(base_file, 'w', encoding='utf-8') as f:
                json.dump(base_data, f, ensure_ascii=False, indent=2)
            print(f"[INFO] 基础成就数据已保存到: {base_file}")
            return True
        except Exception as e:
            print(f"[ERROR] 保存基础成就数据失败: {str(e)}")
            return False
    
    def load_base_achievements(self):
        """加载基础成就数据"""
        base_file = get_resource_path("resources/base_achievements.json")
        try:
            if base_file.exists():
                with open(base_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print("[WARNING] 基础成就数据文件不存在")
                return []
        except Exception as e:
            print(f"[ERROR] 加载基础成就数据失败: {str(e)}")
            return []
    
    def save_user_progress(self, username, progress_data):
        """保存用户进度数据"""
        # 获取用户的UID
        users = self.get_users()
        user_data = users.get(username, {})
        uid = user_data.get('uid', username) if isinstance(user_data, dict) else username
        
        progress_file = get_resource_path(f"resources/user_progress_{uid}.json")
        try:
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[ERROR] 保存用户进度数据失败: {str(e)}")
            return False
    
    def load_user_progress(self, username):
        """加载用户进度数据"""
        # 获取用户的UID
        users = self.get_users()
        user_data = users.get(username, {})
        uid = user_data.get('uid', username) if isinstance(user_data, dict) else username
        
        progress_file = get_resource_path(f"resources/user_progress_{uid}.json")
        try:
            if progress_file.exists():
                with open(progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"[INFO] 用户 {username} (UID: {uid}) 的进度数据文件不存在，创建空数据文件")
                # 创建空的进度数据文件
                empty_progress = {}
                with open(progress_file, 'w', encoding='utf-8') as f:
                    json.dump(empty_progress, f, ensure_ascii=False, indent=2)
                return empty_progress
        except Exception as e:
            print(f"[ERROR] 加载用户进度数据失败: {str(e)}")
            return {}
    
    def save_category_config(self, category_config):
        """保存分类配置"""
        config_file = get_resource_path("resources/category_config.json")
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(category_config, f, ensure_ascii=False, indent=2)
            print(f"[INFO] 分类配置已保存到: {config_file}")
            return True
        except Exception as e:
            print(f"[ERROR] 保存分类配置失败: {str(e)}")
            return False
    
    def load_category_config(self):
        """加载分类配置"""
        config_file = get_resource_path("resources/category_config.json")
        try:
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print("[INFO] 分类配置文件不存在，创建默认配置文件")
                default_config = self.get_default_category_config()
                # 创建默认配置文件
                self.save_category_config(default_config)
                return default_config
        except Exception as e:
            print(f"[ERROR] 加载分类配置失败: {str(e)}")
            return self.get_default_category_config()
    
    def get_default_category_config(self):
        """获取默认分类配置"""
        return {
            "first_categories": {
                "索拉漫行": 1,
                "长路留迹": 2,
                "铿锵刃鸣": 3,
                "诸音声轨": 4
            },
            "second_categories": {
                "索拉漫行": {
                    "索拉的大地·瑝珑": "10",
                    "瑝珑的足迹·一": "20",
                    "瑝珑的足迹·二": "30",
                    "黑海岸的足迹·一": "40",
                    "索拉的大地·黎那汐塔": "50",
                    "黎那汐塔的足迹·一": "60",
                    "黎那汐塔的足迹·二": "70",
                    "黎那汐塔的足迹·三": "80",
                    "荒野的呼唤": "90"
                },
                "长路留迹": {
                    "漂泊之旅": "10",
                    "漂泊之旅·一": "10",
                    "漂泊之旅·二": "20",
                    "与你的印迹": "30",
                    "世间百态": "40",
                    "世间百态·一": "40"
                },
                "铿锵刃鸣": {
                    "战斗的记忆": "10",
                    "战斗的技巧·一": "20",
                    "战斗的技巧·二": "30",
                    "战斗的技巧·三": "40",
                    "战斗的技巧·四": "50",
                    "战斗的回响": "60",
                    "意外体验": "70",
                    "来自深塔·一": "80",
                    "来自深塔·二": "90"
                },
                "诸音声轨": {
                    "成长之路": "10",
                    "别域的友谊": "20",
                    "声骸数据": "30"
                }
            }
        }


# 创建全局配置实例
config = Config()