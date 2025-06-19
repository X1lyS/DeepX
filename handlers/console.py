"""
控制台结果处理器模块
"""

from typing import Set

from handlers.base import ResultHandler
from utils.logger import Logger


class ConsoleResultHandler(ResultHandler):
    """控制台结果处理器，将结果输出到控制台"""
    
    def __init__(self, logger: Logger):
        """
        初始化控制台输出处理器
        
        Args:
            logger: 日志记录器
        """
        super().__init__(logger)
    
    def handle(self, domains: Set[str]) -> None:
        """
        将结果输出到控制台
        
        Args:
            domains: 收集到的子域名集合
        """
        print(f"\n发现的子域名 ({len(domains)}):")
        for domain in sorted(domains):
            print(domain) 