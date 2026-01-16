# -*- coding: utf-8 -*-
"""
memoQ CLI - 文件过滤工具
"""

import os
import re
from pathlib import Path
from typing import List, Callable, Optional, Set


# ============================================================
# macOS 系统文件模式
# ============================================================
MACOS_JUNK_PATTERNS = [
    ".DS_Store",           # Finder 元数据
    "._.DS_Store",         # AppleDouble 资源分支
    "__MACOSX",            # ZIP 中的 macOS 元数据目录
    "._",                  # AppleDouble 前缀
    ".Spotlight-V100",     # Spotlight 索引
    ".Trashes",            # 回收站
    ".fseventsd",          # 文件系统事件
    ".TemporaryItems",     # 临时文件
    ".VolumeIcon.icns",    # 卷图标
    ".AppleDouble",        # AppleDouble 目录
    ".LSOverride",         # Launch Services 覆盖
    ".DocumentRevisions-V100",  # 文档版本
    ".PKInstallSandboxManager", # 安装沙盒
    ".PKInstallSandboxManager-SystemSoftware",
]

# ============================================================
# Windows 系统文件模式
# ============================================================
WINDOWS_JUNK_PATTERNS = [
    "Thumbs.db",           # 缩略图缓存
    "ehthumbs.db",         # 视频缩略图
    "ehthumbs_vista.db",   # Vista 视频缩略图
    "Desktop.ini",         # 文件夹设置
    "desktop.ini",         # 文件夹设置 (小写)
    "$RECYCLE.BIN",        # 回收站
    "System Volume Information",  # 系统卷信息
]

# ============================================================
# 通用忽略模式
# ============================================================
COMMON_IGNORE_PATTERNS = [
    ".git",                # Git 目录
    ".svn",                # SVN 目录
    ".hg",                 # Mercurial 目录
    ".idea",               # IntelliJ IDEA
    ".vscode",             # VS Code
    "__pycache__",         # Python 缓存
    "*.pyc",               # Python 编译文件
    "*.pyo",               # Python 优化文件
    ".env",                # 环境变量文件
    "node_modules",        # Node.js 模块
    ".sass-cache",         # Sass 缓存
]

# 编译所有模式为集合，便于快速查找
ALL_JUNK_PATTERNS: Set[str] = set(
    MACOS_JUNK_PATTERNS + 
    WINDOWS_JUNK_PATTERNS + 
    COMMON_IGNORE_PATTERNS
)


def is_system_file(filename: str) -> bool:
    """
    检查文件是否为系统文件或垃圾文件
    
    Args:
        filename: 文件名或文件路径
    
    Returns:
        True 如果是系统文件，否则 False
    """
    # 获取文件名
    name = os.path.basename(filename)
    
    # 精确匹配
    if name in ALL_JUNK_PATTERNS:
        return True
    
    # 检查 macOS AppleDouble 前缀
    if name.startswith("._"):
        return True
    
    # 检查隐藏文件 (以点开头，但排除 . 和 ..)
    if name.startswith(".") and name not in [".", ".."]:
        # 检查是否在忽略列表中
        for pattern in ALL_JUNK_PATTERNS:
            if name == pattern or name.startswith(pattern):
                return True
    
    # 检查 Windows 系统文件 (不区分大小写)
    name_lower = name.lower()
    for pattern in WINDOWS_JUNK_PATTERNS:
        if name_lower == pattern.lower():
            return True
    
    # 检查通配符模式
    for pattern in COMMON_IGNORE_PATTERNS:
        if "*" in pattern:
            # 简单通配符匹配
            regex = pattern.replace(".", r"\.").replace("*", ".*")
            if re.match(regex, name):
                return True
    
    return False


def is_hidden_file(filename: str) -> bool:
    """
    检查文件是否为隐藏文件
    
    Args:
        filename: 文件名或文件路径
    
    Returns:
        True 如果是隐藏文件
    """
    name = os.path.basename(filename)
    return name.startswith(".") and name not in [".", ".."]


def filter_files(
    file_list: List[str],
    filter_system: bool = True,
    filter_hidden: bool = False,
    include_extensions: Optional[List[str]] = None,
    exclude_extensions: Optional[List[str]] = None,
    custom_filter: Optional[Callable[[str], bool]] = None
) -> List[str]:
    """
    过滤文件列表
    
    Args:
        file_list: 文件路径列表
        filter_system: 是否过滤系统文件
        filter_hidden: 是否过滤隐藏文件
        include_extensions: 只包含这些扩展名的文件 (如 [".docx", ".xlsx"])
        exclude_extensions: 排除这些扩展名的文件
        custom_filter: 自定义过滤函数，返回 True 表示保留
    
    Returns:
        过滤后的文件列表
    """
    result = []
    
    for f in file_list:
        name = os.path.basename(f)
        
        # 系统文件过滤
        if filter_system and is_system_file(f):
            continue
        
        # 隐藏文件过滤
        if filter_hidden and is_hidden_file(f):
            continue
        
        # 扩展名包含过滤
        if include_extensions:
            ext = os.path.splitext(name)[1].lower()
            if ext not in [e.lower() for e in include_extensions]:
                continue
        
        # 扩展名排除过滤
        if exclude_extensions:
            ext = os.path.splitext(name)[1].lower()
            if ext in [e.lower() for e in exclude_extensions]:
                continue
        
        # 自定义过滤
        if custom_filter and not custom_filter(f):
            continue
        
        result.append(f)
    
    return result


def get_files_from_directory(
    directory: str,
    recursive: bool = True,
    filter_system: bool = True,
    filter_hidden: bool = False,
    include_extensions: Optional[List[str]] = None,
    exclude_extensions: Optional[List[str]] = None
) -> List[str]:
    """
    从目录获取文件列表
    
    Args:
        directory: 目录路径
        recursive: 是否递归子目录
        filter_system: 是否过滤系统文件
        filter_hidden: 是否过滤隐藏文件
        include_extensions: 只包含这些扩展名
        exclude_extensions: 排除这些扩展名
    
    Returns:
        文件路径列表
    """
    files = []
    dir_path = Path(directory)
    
    if not dir_path.is_dir():
        raise NotADirectoryError(f"目录不存在: {directory}")
    
    # 收集文件
    if recursive:
        for f in dir_path.rglob("*"):
            if f.is_file():
                # 检查路径中是否包含系统目录
                if filter_system:
                    skip = False
                    for part in f.parts:
                        if is_system_file(part):
                            skip = True
                            break
                    if skip:
                        continue
                
                files.append(str(f))
    else:
        for f in dir_path.iterdir():
            if f.is_file():
                files.append(str(f))
    
    # 应用过滤
    files = filter_files(
        files,
        filter_system=filter_system,
        filter_hidden=filter_hidden,
        include_extensions=include_extensions,
        exclude_extensions=exclude_extensions
    )
    
    return files


def get_relative_path(file_path: str, base_dir: str) -> str:
    """
    获取相对路径
    
    Args:
        file_path: 文件完整路径
        base_dir: 基础目录
    
    Returns:
        相对路径
    """
    return str(Path(file_path).relative_to(base_dir))


def ensure_directory(path: str) -> Path:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        path: 目录路径
    
    Returns:
        Path 对象
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path
