"""
日志记录工具模块，提供统一的日志记录功能
"""

import logging
import time
import sys
from typing import Optional

from utils.formatter import get_formatter, OutputFormatter


class Logger:
    """自定义日志记录器类"""
    
    def __init__(self, debug: bool = True, name: str = 'DeepX'):
        """
        初始化日志记录器
        
        Args:
            debug: 是否启用调试模式
            name: 日志记录器名称
        """
        self.debug_mode = debug
        self.start_time = time.time()
        self.formatter = get_formatter()
        
        # 配置标准日志记录器（保留用于兼容性）
        fmt = '%(asctime)s [%(levelname)s] %(message)s'
        date_fmt = '%H:%M:%S'
        log_formatter = logging.Formatter(fmt, date_fmt)
        
        # 创建处理器
        self.console_handler = logging.StreamHandler()
        self.console_handler.setFormatter(log_formatter)
        
        # 创建日志记录器
        self.logger = logging.getLogger(name)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self.logger.addHandler(self.console_handler)
            
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    def info(self, message: str) -> None:
        """输出信息消息（青色）"""
        self.formatter.info(message)
    
    def debug(self, message: str) -> None:
        """输出调试消息（蓝色）"""
        if self.debug_mode:
            self.formatter.debug(message)
    
    def error(self, message: str) -> None:
        """输出错误消息（红色）"""
        self.formatter.error(message)
    
    def warning(self, message: str) -> None:
        """输出警告消息（使用info打印）"""
        self.formatter.info(f"警告: {message}")
    
    def success(self, message: str) -> None:
        """输出成功消息（绿色）"""
        self.formatter.success(message)
        
    def model(self, message: str) -> None:
        """输出模块消息（黄色）"""
        self.formatter.model(message)


# 创建全局日志记录器实例
_logger_instance: Optional[Logger] = None


def get_logger() -> Logger:
    """获取全局日志记录器实例"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger()
    return _logger_instance


def init_logger(debug: bool = True, name: str = 'DeepX') -> Logger:
    """初始化全局日志记录器"""
    global _logger_instance
    _logger_instance = Logger(debug=debug, name=name)
    return _logger_instance 