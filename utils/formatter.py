"""
美化输出模块，提供彩色日志和ASCII艺术字打印功能
"""

import os
import sys
import time
from typing import Optional

from colorama import init, Fore, Style

# 初始化colorama
init(autoreset=True)

# ASCII艺术字 - DeepX
ASCII_ART = r"""
    ____                  _  __
   / __ \___  ___  ____  | |/ /
  / / / / _ \/ _ \/ __ \ |   / 
 / /_/ /  __/  __/ /_/  /   |  
/_____/\___/\___/ .___//_/|_|  
               /_/               
"""

# 签名信息
SIGNATURE = "v1.0.5"
AUTHOR = "By:X1ly?S"

# 颜色常量
class Colors:
    """颜色常量类"""
    INFO = Fore.CYAN        # 修改为青色
    ERROR = Fore.RED
    SUCCESS = Fore.GREEN
    DEBUG = Fore.BLUE       # 修改为蓝色
    MODEL = Fore.YELLOW     # 新增模块类型的颜色为黄色
    TITLE = Fore.GREEN
    RESET = Style.RESET_ALL
    BRIGHT = Style.BRIGHT
    DIM = Style.DIM


class OutputFormatter:
    """输出美化格式器"""
    
    def __init__(self, start_time: Optional[float] = None):
        """
        初始化输出格式器
        
        Args:
            start_time: 程序开始时间，用于计算运行时长
        """
        self.start_time = start_time or time.time()
    
    def print_banner(self):
        """打印ASCII艺术字标题"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # 获取ASCII艺术字每行
        ascii_lines = ASCII_ART.splitlines()
        
        # 找出最长行的长度
        max_line_length = max(len(line) for line in ascii_lines if line)
        
        # 确保ASCII艺术字前6行的输出
        for i, line in enumerate(ascii_lines):
            if i == 0:  # 第一行是空行
                print(f"{Colors.TITLE}{line}{Colors.RESET}")
            elif i < len(ascii_lines) - 1:  # 前几行艺术字
                print(f"{Colors.TITLE}{line}{Colors.RESET}")
            else:  # 最后一行，添加签名
                # 计算签名的位置，确保其在ascii字符的右下角
                padding = max_line_length - len(ascii_lines[-1]) + 2  # +2为留一点额外空间
                print(f"{Colors.TITLE}{line}{' ' * padding}{Colors.DIM}{SIGNATURE} {Colors.TITLE}{AUTHOR}{Colors.RESET}")
        
        print()  # 额外的空行
    
    def _format_message(self, message: str, elapsed: bool = True) -> str:
        """
        格式化消息，加入时间信息
        
        Args:
            message: 要格式化的消息
            elapsed: 是否显示运行时间
            
        Returns:
            str: 格式化后的消息
        """
        if elapsed:
            elapsed_time = time.time() - self.start_time
            return f"[{elapsed_time:.2f}s] {message}"
        return message
    
    def info(self, message: str, elapsed: bool = True):
        """
        打印信息消息（青色）
        
        Args:
            message: 消息内容
            elapsed: 是否显示运行时间
        """
        formatted = self._format_message(message, elapsed)
        print(f"{Colors.INFO}[INFO] {formatted}{Colors.RESET}")
    
    def model(self, message: str, elapsed: bool = True):
        """
        打印模块消息（黄色）
        
        Args:
            message: 消息内容
            elapsed: 是否显示运行时间
        """
        formatted = self._format_message(message, elapsed)
        print(f"{Colors.MODEL}[MODEL] {formatted}{Colors.RESET}")
    
    def error(self, message: str, elapsed: bool = True):
        """
        打印错误消息（红色）
        
        Args:
            message: 消息内容
            elapsed: 是否显示运行时间
        """
        formatted = self._format_message(message, elapsed)
        print(f"{Colors.ERROR}[ERROR] {formatted}{Colors.RESET}", file=sys.stderr)
    
    def success(self, message: str, elapsed: bool = True):
        """
        打印成功消息（绿色）
        
        Args:
            message: 消息内容
            elapsed: 是否显示运行时间
        """
        formatted = self._format_message(message, elapsed)
        print(f"{Colors.SUCCESS}[SUCCESS] {formatted}{Colors.RESET}")
    
    def debug(self, message: str, elapsed: bool = True):
        """
        打印调试消息（蓝色）
        
        Args:
            message: 消息内容
            elapsed: 是否显示运行时间
        """
        formatted = self._format_message(message, elapsed)
        print(f"{Colors.DEBUG}[DEBUG] {formatted}{Colors.RESET}")


# 创建全局格式化器实例
_formatter_instance = None


def get_formatter() -> OutputFormatter:
    """
    获取全局格式化器实例
    
    Returns:
        OutputFormatter: 格式化器实例
    """
    global _formatter_instance
    if _formatter_instance is None:
        _formatter_instance = OutputFormatter()
    return _formatter_instance


def init_formatter(start_time: Optional[float] = None) -> OutputFormatter:
    """
    初始化全局格式化器
    
    Args:
        start_time: 程序开始时间
        
    Returns:
        OutputFormatter: 格式化器实例
    """
    global _formatter_instance
    _formatter_instance = OutputFormatter(start_time)
    _formatter_instance.print_banner()
    return _formatter_instance 