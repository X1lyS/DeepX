#!/usr/bin/env python3
"""
DeepX 安装脚本
"""

import os
import sys
import platform
import subprocess
import argparse
from setuptools import setup, find_packages

# 导入日志美化模块
try:
    from utils.logger import init_logger, get_logger
    # 初始化日志记录器
    logger = init_logger(debug=True, name='DeepX-Setup')
except ImportError:
    # 如果导入失败，创建简易的日志记录器
    class SimpleLogger:
        def info(self, msg): print(f"[INFO] {msg}")
        def debug(self, msg): print(f"[DEBUG] {msg}")
        def error(self, msg): print(f"[ERROR] {msg}", file=sys.stderr)
        def warning(self, msg): print(f"[WARNING] {msg}")
        def success(self, msg): print(f"[SUCCESS] {msg}")
        def model(self, msg): print(f"[MODEL] {msg}")
    
    logger = SimpleLogger()
    logger.debug("未能导入日志模块，使用简易日志记录器替代")

# 检查Python版本
REQUIRED_PYTHON_VERSION = (3, 7)
current_python = sys.version_info[:2]

if current_python < REQUIRED_PYTHON_VERSION:
    logger.error(
        f"""
==========================
错误: 不兼容的Python版本
==========================
DeepX需要Python {REQUIRED_PYTHON_VERSION[0]}.{REQUIRED_PYTHON_VERSION[1]}或更高版本，
但您正在使用Python {current_python[0]}.{current_python[1]}。

请安装兼容的Python版本，然后重试。
"""
    )
    sys.exit(1)

# 解析命令行参数
def parse_arguments():
    parser = argparse.ArgumentParser(description="DeepX 安装配置工具")
    parser.add_argument("--skip-deps", action="store_true", 
                      help="跳过安装依赖包")
    parser.add_argument("--offline", action="store_true", 
                      help="离线模式，跳过所有需要网络的操作")
    parser.add_argument("--no-proxy", action="store_true", 
                      help="禁用代理设置，直接连接")
    parser.add_argument("command", nargs="?", default="develop",
                      help="setuptools命令 (默认: develop)")
    
    # 如果没有参数，不解析，返回默认值
    if len(sys.argv) == 1:
        return parser.parse_args(["develop"])
    return parser.parse_args()

# 确保目录存在
def create_directories():
    logger.info("正在创建必要的目录...")
    for directory in ['output', 'cache_data', 'data']:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            logger.success(f"创建目录: {directory}")
        else:
            logger.debug(f"目录已存在: {directory}")

# 读取README文件
README_PATH = os.path.join(os.path.dirname(__file__), "README.md")
with open(README_PATH, "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 读取requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as f:
    required_packages = f.read().splitlines()

# 安装依赖
def install_dependencies(args):
    if args.skip_deps or args.offline:
        logger.info("跳过依赖安装...")
        return True
    
    logger.info("正在安装依赖包...")
    try:
        cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        
        # 如果指定了禁用代理，添加--no-proxy选项
        if args.no_proxy:
            cmd.extend(["--no-proxy"])
            logger.debug("启用--no-proxy选项")
        
        # 详细记录执行的命令
        logger.debug(f"执行命令: {' '.join(cmd)}")
        
        # 尝试安装
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 检查是否成功
        if result.returncode == 0:
            logger.success("依赖包安装成功！")
            # 输出安装的包信息
            logger.debug("已安装的依赖包:")
            for pkg in required_packages:
                logger.debug(f"  - {pkg}")
            return True
        else:
            logger.error("依赖包安装失败，错误信息：")
            for line in result.stderr.split('\n'):
                if line.strip():
                    logger.debug(f"  {line}")
            
            logger.info("尝试显示可能的解决方法...")
            
            if "ProxyError" in result.stderr:
                logger.error("检测到代理错误，您可以尝试以下方法：")
                logger.info("1. 使用 --no-proxy 参数重新运行安装：python setup.py --no-proxy")
                logger.info("2. 手动设置HTTP代理环境变量：")
                logger.info("   - Windows: set HTTP_PROXY=http://your_proxy:port")
                logger.info("   - Linux/Mac: export HTTP_PROXY=http://your_proxy:port")
                logger.info("3. 或者完全跳过依赖安装：python setup.py --skip-deps")
            else:
                logger.info("请尝试手动运行: pip install -r requirements.txt")
            
            logger.info("是否要继续安装过程(依赖安装失败)？(y/n)")
            response = input().strip().lower()
            return response == 'y' or response == 'yes'
            
    except Exception as e:
        logger.error(f"安装依赖包时出错: {str(e)}")
        logger.debug(f"异常类型: {type(e).__name__}")
        logger.debug(f"异常详情: {str(e)}")
        logger.info("请尝试手动运行: pip install -r requirements.txt")
        logger.info("是否要继续安装过程(依赖安装失败)？(y/n)")
        response = input().strip().lower()
        return response == 'y' or response == 'yes'

# 检查系统是否支持
def check_system_compatibility():
    system = platform.system()
    logger.debug(f"检测到操作系统: {system}")
    logger.debug(f"Python版本: {platform.python_version()}")
    logger.debug(f"系统平台: {platform.platform()}")
    
    if system not in ['Windows', 'Linux', 'Darwin']:
        logger.warning(f"未经测试的操作系统 {system}，程序可能无法正常工作。")
        logger.info("是否要继续？(y/n)")
        response = input().strip().lower()
        return response == 'y' or response == 'yes'
    else:
        logger.success(f"系统兼容性检查通过: {system}")
    return True

# 执行setup
def run_setup(args):
    setup_args = {
        'name': "DeepX",
        'version': "1.0",
        'author': "DeepX Team",
        'author_email': "deepx@example.com",
        'description': "多接口集成的子域名收集工具",
        'long_description': long_description,
        'long_description_content_type': "text/markdown",
        'url': "https://github.com/yourusername/DeepX",
        'packages': find_packages(where="."),
        'include_package_data': True,
        'classifiers': [
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
        ],
        'python_requires': f">={REQUIRED_PYTHON_VERSION[0]}.{REQUIRED_PYTHON_VERSION[1]}",
        'install_requires': required_packages,
        'entry_points': {
            'console_scripts': [
                'deepx=core.cli:main',
            ],
        },
    }

    # 当使用develop模式但未传递其他参数时，仅创建必要文件而不运行setup
    if args.command == "develop" and len(sys.argv) == 1:
        logger.info("跳过setuptools安装过程，仅创建必要的目录和文件。")
        return True
    
    # 重新构建命令行参数，添加setup.py和用户指定的命令
    setup_args = []
    for arg in sys.argv[1:]:
        if not arg.startswith("--skip-deps") and not arg.startswith("--offline") and not arg.startswith("--no-proxy"):
            setup_args.append(arg)
    
    # 如果没有命令，添加默认命令
    if not setup_args:
        setup_args.append(args.command)
    
    # 输出详细的安装信息
    logger.debug("安装详情:")
    logger.debug(f"  命令: {' '.join(setup_args)}")
    logger.debug(f"  包数量: {len(required_packages)}")
    logger.debug(f"  入口点: deepx=core.cli:main")
    
    # 执行setup
    sys.argv = [sys.argv[0]] + setup_args
    try:
        logger.info("开始执行setuptools安装...")
        setup(
            name="DeepX",
            version="1.0.0",
            author="DeepX Team",
            author_email="deepx@example.com",
            description="多接口集成的子域名收集工具",
            long_description=long_description,
            long_description_content_type="text/markdown",
            url="https://github.com/yourusername/DeepX",
            packages=find_packages(where="."),
            include_package_data=True,
            classifiers=[
                "Programming Language :: Python :: 3",
                "License :: OSI Approved :: MIT License",
                "Operating System :: OS Independent",
            ],
            python_requires=f">={REQUIRED_PYTHON_VERSION[0]}.{REQUIRED_PYTHON_VERSION[1]}",
            install_requires=required_packages,
            entry_points={
                'console_scripts': [
                    'deepx=core.cli:main',
                ],
            },
        )
        logger.success("setuptools安装完成")
        return True
    except Exception as e:
        logger.error(f"执行setuptools安装时出错: {str(e)}")
        logger.debug(f"异常类型: {type(e).__name__}")
        logger.debug(f"异常详情: {str(e)}")
        return False

# 主安装函数
def main():
    logger.model("====== DeepX 安装程序 ======")
    
    # 解析命令行参数
    args = parse_arguments()
    logger.debug(f"命令行参数: {args}")
    
    # 检查系统兼容性
    if not check_system_compatibility():
        logger.error("安装已取消。")
        return
    
    # 创建必要目录
    create_directories()
    
    # 安装依赖
    if not install_dependencies(args):
        logger.error("安装已中断。")
        return
    
    # 执行setup安装
    success = run_setup(args)
    
    if success:
        logger.model("====== DeepX 安装完成 ======")
        logger.success("您可以通过以下方式运行 DeepX:")
        logger.info("1. python DeepX.py <命令> <参数>")
        logger.info("2. python -m deepx <命令> <参数>")
        logger.info("3. deepx <命令> <参数> (如果已经添加到PATH)")
    else:
        logger.model("====== DeepX 安装未完成 ======")
        logger.error("请检查上述错误信息，修复后重试。")

if __name__ == "__main__":
    main() 