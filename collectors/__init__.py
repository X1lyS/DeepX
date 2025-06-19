"""
收集器模块，负责从各种来源收集子域名
"""

from collectors.base import CollectorBase
from collectors.otx import OTXCollector
from collectors.crt import CrtCollector
from collectors.archive import ArchiveCollector
from collectors.factory import CollectorFactory
from collectors.fofa import FofaCollector

__all__ = ['CollectorBase', 'OTXCollector', 'CrtCollector', 'ArchiveCollector', 'CollectorFactory', 'FofaCollector'] 