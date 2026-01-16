# -*- coding: utf-8 -*-
"""
memoQ CLI - 日志配置
"""

import logging
import sys
from pathlib import Path
from typing import Optional


# 日志格式
DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
SIMPLE_FORMAT = "[%(levelname)s] %(message)s"

# 全局日志器缓存
_loggers = {}


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_str: Optional[str] = None,
    simple: bool = False
) -> logging.Logger:
    """
    配置日志系统
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径 (可选)
        format_str: 自定义日志格式
        simple: 使用简单格式
    
    Returns:
        配置好的根日志器
    """
    
    # 确定日志格式
    if format_str is None:
        format_str = SIMPLE_FORMAT if simple else DEFAULT_FORMAT
    
    # 获取或创建根日志器
    logger = logging.getLogger("memoq_cli")
    
    # 设置日志级别
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # 清除现有处理器，避免重复
    logger.handlers.clear()
    
    # 创建格式化器
    formatter = logging.Formatter(format_str, datefmt="%Y-%m-%d %H:%M:%S")
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器 (如果指定了日志文件)
    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(
                log_file, 
                encoding="utf-8",
                mode="a"
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"无法创建日志文件 {log_file}: {e}")
    
    # 防止日志传播到父日志器
    logger.propagate = False
    
    return logger


def get_logger(name: str = "memoq_cli") -> logging.Logger:
    """
    获取指定名称的日志器
    
    Args:
        name: 日志器名称，支持点号分隔的层级名称
              如 "memoq_cli.wsapi.project"
    
    Returns:
        日志器实例
    """
    # 确保名称以 memoq_cli 开头
    if not name.startswith("memoq_cli"):
        name = f"memoq_cli.{name}"
    
    # 检查缓存
    if name in _loggers:
        return _loggers[name]
    
    # 创建新日志器
    logger = logging.getLogger(name)
    _loggers[name] = logger
    
    return logger


class LoggerMixin:
    """
    日志器混入类，为类提供日志功能
    
    使用方法:
        class MyClass(LoggerMixin):
            def my_method(self):
                self.logger.info("Hello")
    """
    
    @property
    def logger(self) -> logging.Logger:
        """获取类专属的日志器"""
        if not hasattr(self, "_logger"):
            class_name = self.__class__.__name__
            self._logger = get_logger(f"memoq_cli.{class_name}")
        return self._logger
