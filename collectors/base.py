"""
子域名收集器基类模块
"""

import abc
from typing import Set

from utils.logger import Logger


class CollectorBase(abc.ABC):
    """子域名收集器抽象基类"""
    
    def __init__(self, target_domain: str, logger: Logger):
        """
        初始化收集器
        
        Args:
            target_domain: 目标域名
            logger: 日志记录器
        """
        self.target_domain = target_domain
        self.logger = logger
        self.name = self.__class__.__name__
    
    @abc.abstractmethod
    async def collect(self) -> Set[str]:
        """
        收集子域名的抽象方法，需要被子类实现
        
        Returns:
            Set[str]: 收集到的子域名集合
        """
        pass 