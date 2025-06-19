"""
收集器工厂模块，负责创建和管理不同类型的收集器
"""

from typing import List

from utils.logger import Logger
from collectors.base import CollectorBase
from collectors.otx import OTXCollector
from collectors.crt import CrtCollector
from collectors.archive import ArchiveCollector
from collectors.fofa import FofaCollector


class CollectorFactory:
    """收集器工厂类，用于创建各种收集器实例"""
    
    @classmethod
    def create_collectors(cls, target_domain: str, logger: Logger) -> List[CollectorBase]:
        """
        创建所有默认收集器
        
        Args:
            target_domain: 目标域名
            logger: 日志记录器
        
        Returns:
            List[CollectorBase]: 收集器实例列表
        """
        return [
            OTXCollector(target_domain, logger),
            CrtCollector(target_domain, logger),
            ArchiveCollector(target_domain, logger)
        ]
    
    @classmethod
    def create_fofa_collector(cls, target_domain: str, logger: Logger) -> FofaCollector:
        """
        创建FOFA收集器实例
        
        Args:
            target_domain: 目标域名
            logger: 日志记录器
            
        Returns:
            FofaCollector: FOFA收集器实例
        """
        return FofaCollector(target_domain, logger)
    
    @staticmethod
    def get_collector(collector_type: str, target_domain: str, logger: Logger) -> CollectorBase:
        """
        根据类型创建特定的收集器实例
        
        Args:
            collector_type: 收集器类型 ('otx', 'crt', 'archive', 'fofa')
            target_domain: 目标域名
            logger: 日志记录器
            
        Returns:
            CollectorBase: 收集器实例
            
        Raises:
            ValueError: 如果收集器类型无效
        """
        if collector_type.lower() == 'otx':
            return OTXCollector(target_domain, logger)
        elif collector_type.lower() == 'crt':
            return CrtCollector(target_domain, logger)
        elif collector_type.lower() == 'archive':
            return ArchiveCollector(target_domain, logger)
        elif collector_type.lower() == 'fofa':
            return FofaCollector(target_domain, logger)
        else:
            raise ValueError(f"未知的收集器类型: {collector_type}") 