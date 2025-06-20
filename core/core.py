"""
核心逻辑模块，包含子域名收集的主要功能
"""

import asyncio
from typing import Set, List, Optional, Dict

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
from handlers.alive import AliveHandler


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
        
        # 初始化文件路径
        Config.init_file_paths(target_domain)
        
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
    
    async def collect(self) -> Dict[str, Set[str]]:
        """
        收集所有来源的子域名
        
        Returns:
            Dict[str, Set[str]]: 收集到的子域名集合，按来源分类
        """
        # 步骤1-3: 检查缓存
        if not Config.DISABLE_CACHE and self.cache_manager.has_valid_cache(self.target_domain):
            self.logger.model(f"缓存命中模块 - 使用缓存数据")
            domains = self.cache_manager.get_cached_domains(self.target_domain)
            
            # 步骤4: 异步清理过期缓存
            if Config.AUTO_CLEAN_CACHE:
                asyncio.create_task(asyncio.to_thread(self.cache_manager.clean_expired_cache))
                
            return domains
        
        # 步骤5: 执行隐藏资产收集模块 (CRT, OTX, Archive)
        self.logger.model(f"隐藏资产收集模块 - 收集子域名: {self.target_domain}")
        self.logger.info(f"开始收集域名: {self.target_domain}")
        
        # 创建收集任务
        tasks = [collector.collect() for collector in self.collectors]
        
        # 异步执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        deep_domains = set()
        for i, result in enumerate(results):
            collector_name = self.collectors[i].__class__.__name__
            if isinstance(result, Exception):
                self.logger.error(f"{collector_name} 收集失败: {result}")
            else:
                self.logger.success(f"{collector_name} 收集到 {len(result)} 个域名")
                deep_domains.update(result)
        
        # 步骤6: 执行字典爆破模块
        brute_domains = set()
        if not Config.DISABLE_DICT_BRUTE:
            brute_domains = await self.dict_builder.brute_force_subdomains(self.target_domain)
            
        # 初始化FOFA结果集合，将在后续步骤填充
        fofa_domains = set()
            
        self.logger.success(f"隐藏资产收集完成，共收集到 {len(deep_domains)} 个隐藏域名")
        
        # 返回结果字典，包含各来源的域名集合
        return {'deep': deep_domains, 'brute': brute_domains, 'fofa': fofa_domains}
    
    def process_results(self, domains: Dict[str, Set[str]]) -> None:
        """
        处理收集到的结果
        
        Args:
            domains: 收集到的子域名集合字典
        """
        # 处理深度收集结果
        for handler in self.result_handlers:
            handler.handle(domains.get('deep', set()))
    
    async def run(self) -> Dict[str, Set[str]]:
        """
        运行完整的收集流程
        
        Returns:
            Dict[str, Set[str]]: 收集到的子域名集合，按来源分类
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
        
        # 初始化文件路径
        Config.init_file_paths(target_domain)
        
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
            
        # 初始化缓存管理器
        self.cache_manager = CacheManager(self.logger)
    
    async def collect(self) -> Set[str]:
        """
        从FOFA收集子域名
        
        Returns:
            Set[str]: 收集到的子域名集合
        """
        # 步骤7: 执行FOFA收集模块
        self.logger.model(f"FOFA收集模块 - 收集子域名: {self.target_domain}")
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
    
    def __init__(self, target_domain: str, debug: bool = True, disable_cache: bool = False):
        """
        初始化域名比较器
        
        Args:
            target_domain: 目标域名
            debug: 是否启用调试模式
            disable_cache: 是否禁用缓存
        """
        self.target_domain = target_domain
        
        # 初始化文件路径
        Config.init_file_paths(target_domain)
        
        # 初始化日志记录器
        self.logger = Logger(debug)
        
        # 输出当前配置的文件路径
        self.logger.debug(f"当前配置的文件路径:")
        self.logger.debug(f"FOFA输出文件: {Config.FOFA_OUTPUT_FILE}")
        self.logger.debug(f"深度收集输出文件: {Config.DEFAULT_OUTPUT_FILE}")
        self.logger.debug(f"隐藏域名结果文件: {Config.RESULT_OUTPUT_FILE}")
        self.logger.debug(f"爆破结果输出文件: {Config.BRUTE_OUTPUT_FILE}")
        self.logger.debug(f"总资产输出文件: {Config.TOTAL_OUTPUT_FILE}")
        
        # 创建比较处理器
        self.comparator = ComparisonHandler(
            self.logger,
            Config.FOFA_OUTPUT_FILE,
            Config.DEFAULT_OUTPUT_FILE,
            Config.RESULT_OUTPUT_FILE,
            Config.BRUTE_OUTPUT_FILE,
            Config.TOTAL_OUTPUT_FILE
        )
        
        # 创建测活处理器
        self.alive_handler = AliveHandler(self.logger, target_domain, disable_cache)
        
        # 缓存禁用状态
        self.disable_cache = disable_cache
    
    def compare(self) -> Dict[str, Set[str]]:
        """
        比较不同来源的域名结果
        
        Returns:
            Dict[str, Set[str]]: 比较结果，包含隐藏域名和总资产
        """
        # 步骤8: 执行隐藏资产比较模块
        self.logger.model(f"隐藏资产比较模块 - 分析隐藏域名: {self.target_domain}")
        return self.comparator.compare_domains()
    
    async def check_alive(self, compare_results: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
        """
        检查域名存活状态
        
        Args:
            compare_results: 比较结果，包含隐藏域名和总资产
            
        Returns:
            Dict[str, Set[str]]: 测活结果，包含存活和不存活的域名
        """
        # 获取隐藏域名和非隐藏域名（普通域名）
        hidden_domains = compare_results.get('hidden', set())
        total_domains = compare_results.get('total', set())
        normal_domains = total_domains - hidden_domains
        
        # 执行测活
        self.logger.model(f"测活模块 - 开始检测域名存活性: {self.target_domain}")
        alive_results = await self.alive_handler.handle_all_domains(hidden_domains, normal_domains)
        
        return alive_results
    
    async def run_async(self) -> Dict[str, Set[str]]:
        """
        异步运行完整的比较和测活流程
        
        Returns:
            Dict[str, Set[str]]: 完整结果，包含比较结果和测活结果
        """
        # 1. 执行比较
        compare_results = self.compare()
        
        # 2. 执行测活
        alive_results = await self.check_alive(compare_results)
        
        # 3. 合并结果
        results = {**compare_results, **alive_results}
        
        return results
    
    def run(self) -> Dict[str, Set[str]]:
        """
        运行完整的比较流程
        
        Returns:
            Dict[str, Set[str]]: 比较结果，包含隐藏域名和总资产
        """
        # 同步版本，仅执行比较，不执行测活
        # 测活需要通过异步方法run_async调用
        return self.compare()


class DomainProcessor:
    """域名后处理器，负责处理收集到的域名"""
    
    def __init__(self, target_domain: str, debug: bool = True):
        """
        初始化域名后处理器
        
        Args:
            target_domain: 目标域名
            debug: 是否启用调试模式
        """
        self.target_domain = target_domain
        
        # 初始化文件路径
        Config.init_file_paths(target_domain)
        
        self.logger = Logger(debug)
        self.cache_manager = CacheManager(self.logger)
        self.dict_builder = DictBuilder(self.logger)
        self.result_handler = FileResultHandler(self.logger, Config.TOTAL_OUTPUT_FILE)
    
    def process_domains(self, deep_domains: Set[str], fofa_domains: Set[str]) -> None:
        """
        处理收集到的域名
        
        Args:
            deep_domains: 深度收集的域名集合
            fofa_domains: FOFA收集的域名集合
        """
        # 步骤9: 执行缓存写入模块
        if not Config.DISABLE_CACHE:
            self.logger.model(f"缓存写入模块 - 保存收集结果到缓存")
            self.cache_manager.save_domains_to_cache(self.target_domain, deep_domains, fofa_domains)
        
        # 步骤10: 执行字典写入模块
        self.logger.model(f"字典更新模块 - 从结果中提取子域名前缀")
        
        # 合并所有域名，提取前缀
        all_domains = deep_domains.union(fofa_domains)
        
        # 输出所有域名到总输出文件
        self.logger.info(f"正在保存总资产到文件: {Config.TOTAL_OUTPUT_FILE}")
        self.result_handler.handle(all_domains)
        
        # 只有在未禁用字典爆破时才更新字典
        if not Config.DISABLE_DICT_BRUTE:
            self.dict_builder.process_subdomains(self.target_domain, all_domains)
    
    def run(self, deep_domains: Set[str], fofa_domains: Set[str]) -> None:
        """
        运行域名处理流程
        
        Args:
            deep_domains: 深度收集的域名集合
            fofa_domains: FOFA收集的域名集合
        """
        self.process_domains(deep_domains, fofa_domains)


class DictBruteForcer:
    """字典爆破器，负责执行子域名字典爆破"""
    
    def __init__(self, target_domain: str, debug: bool = True):
        """
        初始化字典爆破器
        
        Args:
            target_domain: 目标域名
            debug: 是否启用调试模式
        """
        self.target_domain = target_domain
        
        # 初始化文件路径
        Config.init_file_paths(target_domain)
        
        self.logger = Logger(debug)
        self.dict_builder = DictBuilder(self.logger)
        self.result_handlers = [
            ConsoleResultHandler(self.logger),
            FileResultHandler(self.logger, Config.BRUTE_OUTPUT_FILE)
        ]
    
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