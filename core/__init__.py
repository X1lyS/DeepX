"""
核心模块，包含子域名收集的主要功能和命令行界面
"""

from core.core import SubdomainCollector, FofaSubdomainCollector, DomainComparator, DictBruteForcer
from core.cli import CLI, main

__all__ = [
    'SubdomainCollector', 
    'FofaSubdomainCollector', 
    'DomainComparator', 
    'DictBruteForcer',
    'CLI',
    'main'
] 