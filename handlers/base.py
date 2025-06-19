"""
结果处理器基类模块
"""

import abc
from typing import Set

from utils.logger import Logger


class ResultHandler(abc.ABC):
    """结果处理器抽象基类，用于处理收集到的子域名"""
    
    def __init__(self, logger: Logger):
        """
        初始化结果处理器
        
        Args:
            logger: 日志记录器
        """
        self.logger = logger
    
    @abc.abstractmethod
    def handle(self, domains: Set[str]) -> None:
        """
        处理结果的抽象方法，需要被子类实现
        
        Args:
            domains: 收集到的子域名集合
        """
        pass 