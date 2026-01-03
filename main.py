import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from core.styles import get_icon
from version import VERSION


import sys


def setup_resources_structure():
    """检查并创建resources文件夹结构"""
    try:
        # 获取resources目录路径 - 兼容打包后的路径
        import sys
        if getattr(sys, 'frozen', False):
            # 打包后的可执行文件
            resources_dir = Path(sys.executable).parent / "resources"
        else:
            # 开发环境
            resources_dir = Path(__file__).parent / "resources"
        
        # 创建resources目录（如果不存在）
        if not resources_dir.exists():
            print(f"[INFO] 创建resources目录: {resources_dir}")
            resources_dir.mkdir(exist_ok=True)
        
        # 定义子文件夹和对应的说明内容
        subdirs = {
            "characters": "角色肖像图文件夹\n\n此文件夹用于存放游戏角色的全身肖像图文件。\n\n获取方式：\n1. 访问库街区Wiki-角色列表页面\n   链接：https://wiki.kurobbs.com/mc/catalogue/list?fid=1099&sid=1105\n2. 点击每个角色进入详情页\n3. 拖动角色的全身肖像图到此文件夹\n4. 将图片重命名为角色名(如：今汐.webp)\n\n支持的格式：.webp\n\n重要提示：\n• 肖像图文件名必须与profile文件夹中的头像文件名完全一致\n• 这样切换头像时才能自动联动显示对应的肖像图\n\n请勿删除此文件夹。",
            "img": "界面背景图片文件夹\n\n此文件夹用于存放应用程序的背景图片文件。\n\n默认背景图片：\n• background-light.png - 浅色主题背景\n• background-dark.png - 深色主题背景\n\n支持的格式：.png, .jpg\n\n使用说明：\n• 替换这些文件可以自定义应用背景\n• 文件名必须保持一致才能被正确识别\n\n请勿删除此文件夹。",
            "profile": "用户头像文件夹\n\n此文件夹用于存放用户选择的头像图片文件。\n\n获取方式：\n1. 访问库街区Wiki-角色头像页面\n   链接：https://wiki.kurobbs.com/mc/catalogue/list?fid=1099&sid=1363\n2. 直接拖动每个角色的头像图片到此文件夹\n3. 将图片重命名为角色名(如：今汐.png)\n\n支持的格式：.png\n\n重要提示：\n• 头像文件名必须与characters文件夹中的肖像图文件名完全一致\n• 在主窗口点击头像切换头像，会自动更新同角色肖像图\n\n请勿删除此文件夹。"
        }
        
        # 检查并创建子文件夹和说明文件
        for subdir_name, description in subdirs.items():
            subdir_path = resources_dir / subdir_name
            
            # 创建子文件夹（如果不存在）
            if not subdir_path.exists():
                print(f"[INFO] 创建子目录: {subdir_path}")
                subdir_path.mkdir(exist_ok=True)
            
            # 创建说明文件（如果不存在）
            readme_file = subdir_path / "文件夹说明.txt"
            if not readme_file.exists():
                print(f"[INFO] 创建说明文件: {readme_file}")
                with open(readme_file, 'w', encoding='utf-8') as f:
                    f.write(description)
        
        print("[SUCCESS] Resources文件夹结构检查完成")
        
    except Exception as e:
        print(f"[ERROR] 创建resources文件夹结构失败: {str(e)}")
        import traceback
        traceback.print_exc()


print(f"sys.frozen: {getattr(sys, 'frozen', False)}")

print(f"sys.argv[0]: {sys.argv[0]}")

print(f"sys.executable: {sys.executable}")


def setup_application():
    """设置应用程序基本属性"""
    app = QApplication(sys.argv)
    app.setApplicationName("鸣潮成就管理器")
    app.setApplicationVersion(VERSION)
    app.setOrganizationName("鸣潮成就工具")
    
    # 设置全局默认字体为微软雅黑
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)
    
    # 设置窗口图标
    icon = get_icon("logo")
    if not icon.isNull():
        app.setWindowIcon(icon)
    
    return app


def main():
    """主函数"""
    try:
        # 检查并创建resources文件夹结构
        setup_resources_structure()
        
        print("正在创建应用实例...")
        # 创建应用实例
        app = setup_application()
        print("应用实例创建完成")
        
        print("正在导入TemplateMainWindow...")
        from core.main_window import TemplateMainWindow
        print("TemplateMainWindow导入完成")
        
        print("正在创建主窗口...")
        # 创建主窗口
        main_window = TemplateMainWindow()
        print("主窗口创建完成")
        
        print("正在显示主窗口...")
        # 直接显示窗口（不使用延迟）
        main_window.show()
        print("主窗口显示完成")
        
        print("应用启动成功！")
        # 运行应用
        sys.exit(app.exec())
    except Exception as e:
        print(f"启动应用时发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()