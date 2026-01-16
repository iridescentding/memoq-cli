# -*- coding: utf-8 -*-
"""
memoQ CLI - 安装脚本
"""

from setuptools import setup, find_packages

# 读取 README 时添加错误处理，防止文件不存在导致安装失败
try:
    with open("README.md", "r", encoding="utf-8") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "memoQ Server CLI Tool"

setup(
    name="memoq-cli",
    version="1.0.0",
    author="memoQ CLI Team",
    description="memoQ Server 命令行工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/memoq-cli",
    
    # 修正 1: 明确指定包名，防止把 tests 等无关目录打包进去
    packages=find_packages(include=["memoq_cli", "memoq_cli.*"]),
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",  # 建议与 classifiers 保持一致
    install_requires=[
        "click>=8.0.0",
        "zeep>=4.0.0",
        "requests>=2.25.0",
        "lxml>=4.6.0",
        "urllib3>=1.26.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.0.0",
            "black>=21.0.0",
            "flake8>=3.9.0",
        ],
    },
    entry_points={
        "console_scripts": [
            # 修正 2: 这里必须对应 cli.py 中的函数名 'cli'
            "memoq=memoq_cli.cli:cli",
        ],
    },
)
