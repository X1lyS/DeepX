#!/usr/bin/env python3
"""
DeepX 安装脚本
"""

from setuptools import setup, find_packages
import os

# 读取README文件
README_PATH = os.path.join(os.path.dirname(__file__), "README.md")
with open(README_PATH, "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="DeepX",
    version="1.0.0",
    author="DeepX Team",
    author_email="deepx@example.com",
    description="多接口集成的子域名收集工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/DeepX",
    packages=find_packages(where="."), # 从当前目录查找包
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "aiohttp>=3.8.0",
        "requests>=2.25.0",
        "typing_extensions>=4.0.0",
        "colorama>=0.4.4",
        "dnspython>=2.2.0",
        "beautifulsoup4>=4.11.0",
        "lxml>=4.9.0",
        "tqdm>=4.64.0",
        "aiodns>=3.0.0",
    ],
) 