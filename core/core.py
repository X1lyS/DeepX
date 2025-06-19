"""
核心逻辑模块，包含子域名收集的主要功能
"""

import asyncio
from typing import Set, List, Optional

from collectors.factory import CollectorFactory
from collectors.base import CollectorBase
from config.config import Config
from handlers.base import ResultHandler
from handlers.console import ConsoleResultHandler
from handlers.file import FileResultHandler
from handlers.comparison import ComparisonHandler
from utils.logger import Logger
from utils.formatter import init_formatter
from cacher.manager import CacheManager
from cacher.dict_builder import DictBuilder


class SubdomainCollector:
    """子域名收集管理器，负责协调收集器和处理器的工作"""
    
    def __init__(self, target_domain: str, debug: bool = True, output_file: Optional[str] = None, 
                 disable_cache: bool = False, disable_brute: bool = False):
        """
        初始化子域名收集管理器
        
        Args:
            target_domain: 目标域名
            debug: 是否启用调试模式
            output_file: 输出文件路径，如果为None则使用默认路径
            disable_cache: 是否禁用缓存
            disable_brute: 是否禁用字典爆破
        """
        self.target_domain = target_domain
        
        # 设置缓存配置
        Config.DISABLE_CACHE = disable_cache
        Config.DISABLE_DICT_BRUTE = disable_brute
        
        # 初始化美化格式器
        init_formatter()
        
        # 初始化日志记录器
        self.logger = Logger(debug)
        self.collectors = CollectorFactory.create_collectors(target_domain, self.logger)
        self.result_handlers = [
            ConsoleResultHandler(self.logger),
            FileResultHandler(self.logger, output_file or Config.DEFAULT_OUTPUT_FILE)
        ]
        
        # 初始化缓存管理器
        self.cache_manager = CacheManager(self.logger)
        
        # 初始化字典构建器
        self.dict_builder = DictBuilder(self.logger)
    
    def add_collector(self, collector: CollectorBase) -> None:
        """
        添加自定义收集器
        
        Args:
            collector: 收集器实例
        """
        self.collectors.append(collector)
    
    def add_handler(self, handler: ResultHandler) -> None:
        """
        添加自定义结果处理器
        
        Args:
            handler: 结果处理器实例
        """
        self.result_handlers.append(handler)
    
    async def collect(self) -> Set[str]:
        """
        收集所有来源的子域名
        
        Returns:
            Set[str]: 收集到的子域名集合
        """
        # 检查缓存
        if self.cache_manager.has_valid_cache(self.target_domain):
            self.logger.model(f"缓存命中模块 - 使用缓存数据")
            domains = self.cache_manager.get_cached_domains(self.target_domain)
            return domains
        
        self.logger.model(f"开始模块 - 收集子域名: {self.target_domain}")
        self.logger.info(f"开始收集域名: {self.target_domain}")
        
        # 创建收集任务
        tasks = [collector.collect() for collector in self.collectors]
        
        # 异步执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        all_domains = set()
        for i, result in enumerate(results):
            collector_name = self.collectors[i].__class__.__name__
            if isinstance(result, Exception):
                self.logger.error(f"{collector_name} 收集失败: {result}")
            else:
                self.logger.success(f"{collector_name} 收集到 {len(result)} 个域名")
                all_domains.update(result)
        
        # 执行字典爆破，扩展结果
        if not Config.DISABLE_DICT_BRUTE and self.dict_builder._load_dict_words():
            brute_domains = await self.dict_builder.brute_force_subdomains(self.target_domain)
            if brute_domains:
                all_domains.update(brute_domains)
        
        self.logger.success(f"总共收集到 {len(all_domains)} 个唯一域名")
        
        # 保存到缓存
        if not Config.DISABLE_CACHE:
            self.cache_manager.save_domains_to_cache(self.target_domain, all_domains)
        
        # 更新字典
        if not Config.DISABLE_DICT_BRUTE:
            self.dict_builder.process_subdomains(self.target_domain, all_domains)
        
        return all_domains
    
    def process_results(self, domains: Set[str]) -> None:
        """
        处理收集到的结果
        
        Args:
            domains: 收集到的子域名集合
        """
        for handler in self.result_handlers:
            handler.handle(domains)
    
    async def run(self) -> Set[str]:
        """
        运行完整的收集流程
        
        Returns:
            Set[str]: 收集到的子域名集合
        """
        domains = await self.collect()
        self.process_results(domains)
        return domains


class FofaSubdomainCollector:
    """FOFA子域名收集器管理器"""
    
    def __init__(self, target_domain: str, debug: bool = True, api_key: str = None, output_file: Optional[str] = None):
        """
        初始化FOFA收集管理器
        
        Args:
            target_domain: 目标域名
            debug: 是否启用调试模式
            api_key: FOFA API密钥（优先于配置文件）
            output_file: 输出文件路径，如果为None则使用默认路径
        """
        self.target_domain = target_domain
        
        # 初始化美化格式器（如果之前未初始化）
        try:
            from utils.formatter import get_formatter
            get_formatter()
        except:
            init_formatter()
        
        # 初始化日志记录器
        self.logger = Logger(debug)
        
        # 如果提供了API密钥，临时覆盖配置文件中的密钥
        if api_key:
            # 临时保存原始配置
            original_api_key = Config.FOFA_API_KEY
            # 设置新的API密钥
            Config.FOFA_API_KEY = api_key
            
        try:
            # 创建FOFA收集器
            self.collector = CollectorFactory.create_fofa_collector(target_domain, self.logger)
        finally:
            # 如果提供了自定义API密钥，恢复原始配置
            if api_key:
                Config.FOFA_API_KEY = original_api_key
        
        # 设置输出文件（如果提供）
        if output_file:
            Config.FOFA_OUTPUT_FILE = output_file
    
    async def collect(self) -> Set[str]:
        """
        从FOFA收集子域名
        
        Returns:
            Set[str]: 收集到的子域名集合
        """
        self.logger.model(f"FOFA模块 - 收集子域名: {self.target_domain}")
        self.logger.info(f"开始从FOFA收集域名: {self.target_domain}")
        
        result = await self.collector.collect()
        self.logger.success(f"FOFA收集到 {len(result)} 个域名")
        
        return result
    
    def process_results(self, domains: Set[str]) -> None:
        """
        处理收集到的结果
        
        Args:
            domains: 收集到的子域名集合
        """
        # 创建处理器
        handlers = [
            ConsoleResultHandler(self.logger),
            FileResultHandler(self.logger, Config.FOFA_OUTPUT_FILE)
        ]
        
        # 处理结果
        for handler in handlers:
            handler.handle(domains)
    
    async def run(self) -> Set[str]:
        """
        运行完整的FOFA收集流程
        
        Returns:
            Set[str]: 收集到的子域名集合
        """
        domains = await self.collect()
        self.process_results(domains)
        return domains


class DomainComparator:
    """域名比较器，用于比较不同来源的域名结果"""
    
    def __init__(self, target_domain: str, debug: bool = True):
        """
        初始化域名比较器
        
        Args:
            target_domain: 目标域名
            debug: 是否启用调试模式
        """
        self.target_domain = target_domain
        self.logger = Logger(debug)
        self.comparator = ComparisonHandler(
            self.logger,
            Config.DEFAULT_OUTPUT_FILE,
            Config.FOFA_OUTPUT_FILE,
            Config.RESULT_OUTPUT_FILE
        )
    
    def compare(self) -> Set[str]:
        """
        比较不同来源的域名结果
        
        Returns:
            Set[str]: 隐藏域名集合
        """
        self.logger.model(f"比较模块 - 分析隐藏域名: {self.target_domain}")
        return self.comparator.compare()
    
    def run(self) -> Set[str]:
        """
        运行完整的比较流程
        
        Returns:
            Set[str]: 隐藏域名集合
        """
        return self.compare()


class DictBruteForcer:
    """字典爆破器，用于爆破子域名"""
    
    def __init__(self, target_domain: str, debug: bool = True):
        """
        初始化字典爆破器
        
        Args:
            target_domain: 目标域名
            debug: 是否启用调试模式
        """
        self.target_domain = target_domain
        self.logger = Logger(debug)
        
        # 初始化美化格式器（如果之前未初始化）
        try:
            from utils.formatter import get_formatter
            get_formatter()
        except:
            init_formatter()
            
        # 初始化字典构建器
        self.dict_builder = DictBuilder(self.logger)
    
    async def brute_force(self) -> Set[str]:
        """
        进行字典爆破
        
        Returns:
            Set[str]: 爆破成功的子域名集合
        """
        self.logger.model(f"爆破模块 - 爆破子域名: {self.target_domain}")
        return await self.dict_builder.brute_force_subdomains(self.target_domain)
    
    async def run(self) -> Set[str]:
        """
        运行完整的爆破流程
        
        Returns:
            Set[str]: 爆破成功的子域名集合
        """
        return await self.brute_force() 