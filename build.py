""" 
Nuitka 打包脚本
打包为单个可执行文件,资源文件夹外置,无控制台窗口
"""
import subprocess
import sys
import shutil
from pathlib import Path
from version import VERSION

def build():
    """执行 Nuitka 打包"""
    
    # 获取项目根目录
    project_root = Path(__file__).parent
    main_file = project_root / "main.py"
    icon_file = project_root / "resources" / "icons" / "logo.ico"
    output_filename = f"鸣潮成就管理器{VERSION}.exe"
    dist_dir = project_root / "dist"
    
    # 清理 dist 目录
    if dist_dir.exists():
        print("=" * 60)
        print("正在清理 dist 目录...")
        print("=" * 60)
        shutil.rmtree(dist_dir)
        print("dist 目录已清理")
        print("=" * 60)
    
    # Nuitka 打包命令
    cmd = [
        sys.executable,
        "-m", "nuitka",
        "--standalone",                    # 独立模式
        "--onefile",                       # 打包为单文件
        "--windows-disable-console",       # 禁用控制台窗口(调试时启用)
        "--enable-plugin=pyside6",         # 启用 PySide6 插件
        f"--windows-icon-from-ico={icon_file}",  # 设置图标
        "--lto=yes",                       # 启用链接时优化(压缩)
        "--output-dir=dist",               # 输出目录
        f"--output-filename={output_filename}",  # 输出文件名
        "--company-name=Silence",
        "--product-name=Wuthering Waves Achievement Manager",
        f"--file-version={VERSION}",
        f"--product-version={VERSION}",
        "--file-description=Wuthering Waves Achievement Tool",
        "--assume-yes-for-downloads",      # 自动确认下载
        "--show-progress",                 # 显示进度
        "--show-memory",                   # 显示内存使用
        # 排除不必要的模块以减少打包体积
        "--nofollow-import-to=numpy",
        "--nofollow-import-to=matplotlib",
        "--nofollow-import-to=PIL",
        "--nofollow-import-to=pillow",
        "--nofollow-import-to=scipy",
        "--nofollow-import-to=pandas",
        str(main_file)
    ]
    
    print("=" * 60)
    print("开始打包...")
    print("=" * 60)
    print(f"主文件: {main_file}")
    print(f"图标: {icon_file}")
    print(f"输出目录: {project_root / 'dist'}")
    print("=" * 60)
    
    try:
        # 执行打包命令
        result = subprocess.run(cmd, cwd=project_root, check=True)
        
        print("\n" + "=" * 60)
        print("打包完成!")
        print("=" * 60)
        print(f"可执行文件位于: {project_root / 'dist'}")
        print("=" * 60)

        return result.returncode
        
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 60)
        print(f"打包失败: {e}")
        print("=" * 60)
        return e.returncode
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"发生错误: {e}")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(build())
