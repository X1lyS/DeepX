#!/usr/bin/env python3
"""
DeepX 安装脚本
"""

import os
import sys
import platform
import subprocess
from setuptools import setup, find_packages

# 检查Python版本
REQUIRED_PYTHON_VERSION = (3, 7)
current_python = sys.version_info[:2]

if current_python < REQUIRED_PYTHON_VERSION:
    sys.stderr.write(
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

# 确保目录存在
for directory in ['output', 'cache_data', 'data']:
    os.makedirs(directory, exist_ok=True)

# 读取README文件
README_PATH = os.path.join(os.path.dirname(__file__), "README.md")
with open(README_PATH, "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 读取requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as f:
    required_packages = f.read().splitlines()

# 安装依赖
def install_dependencies():
    print("\n正在安装依赖包...\n")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("\n依赖包安装成功！\n")
    except subprocess.CalledProcessError:
        print("\n依赖包安装失败，请手动运行: pip install -r requirements.txt\n")
        return False
    return True

# 检查系统是否支持
def check_system_compatibility():
    system = platform.system()
    if system not in ['Windows', 'Linux', 'Darwin']:
        print(f"\n警告: 未经测试的操作系统 {system}，程序可能无法正常工作。\n")
        return False
    return True

# 主安装函数
def main():
    print("\n====== DeepX 安装程序 ======\n")
    
    # 检查系统兼容性
    check_system_compatibility()
    
    # 安装依赖
    install_dependencies()
    
    # 执行setuptools安装
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
    
    print("\n====== DeepX 安装完成 ======\n")
    print("您可以通过以下方式运行 DeepX:")
    print("1. python DeepX.py <命令> <参数>")
    print("2. python -m deepx <命令> <参数>")
    print("3. deepx <命令> <参数> (如果已经添加到PATH)\n")

if __name__ == "__main__":
    main() 