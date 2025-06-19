"""
字典构建器模块，负责从子域名提取前缀构建爆破字典
"""

import os
import json
import asyncio
import concurrent.futures
import aiohttp
from typing import Set, List, Dict, Optional
import re
import time
import dns.resolver

from config.config import Config
from utils.logger import Logger


class DictBuilder:
    """子域名字典构建器，从子域名结果中提取前缀构建爆破字典"""
    
    def __init__(self, logger: Logger):
        """
        初始化字典构建器
        
        Args:
            logger: 日志记录器
        """
        self.logger = logger
        self.dict_file = os.path.join(os.getcwd(), Config.DICT_FILE)
        # 确保字典目录存在
        os.makedirs(os.path.dirname(self.dict_file), exist_ok=True)
        
        # 加载现有字典
        self.dict_words = self._load_dict_words()
        
    def _load_dict_words(self) -> Set[str]:
        """
        加载现有的字典词汇
        
        Returns:
            Set[str]: 字典词汇集合
        """
        if os.path.exists(self.dict_file):
            try:
                with open(self.dict_file, 'r', encoding='utf-8') as f:
                    return set(line.strip() for line in f if line.strip())
            except Exception as e:
                self.logger.error(f"加载字典文件出错: {str(e)}")
                return set()
        return set()
    
    def _save_dict_words(self) -> None:
        """保存字典词汇到文件"""
        try:
            with open(self.dict_file, 'w', encoding='utf-8') as f:
                for word in sorted(self.dict_words):
                    f.write(f"{word}\n")
            self.logger.success(f"字典已保存到 {self.dict_file}，共 {len(self.dict_words)} 个词")
        except Exception as e:
            self.logger.error(f"保存字典文件出错: {str(e)}")
    
    def extract_subdomains_prefix(self, domain: str, subdomains: Set[str]) -> Set[str]:
        """
        从子域名中提取前缀
        
        Args:
            domain: 目标域名
            subdomains: 子域名集合
            
        Returns:
            Set[str]: 提取的前缀集合
        """
        prefixes = set()
        pattern = re.compile(fr'^([\w\-]+)\.{re.escape(domain)}$', re.IGNORECASE)
        
        for subdomain in subdomains:
            match = pattern.match(subdomain)
            if match:
                prefix = match.group(1).lower()
                if prefix and len(prefix) > 1:  # 忽略过短的前缀
                    prefixes.add(prefix)
        
        self.logger.success(f"从 {len(subdomains)} 个子域名中提取了 {len(prefixes)} 个前缀")
        return prefixes
    
    def add_to_dictionary(self, prefixes: Set[str]) -> None:
        """
        将前缀添加到字典中
        
        Args:
            prefixes: 前缀集合
        """
        original_count = len(self.dict_words)
        self.dict_words.update(prefixes)
        new_count = len(self.dict_words) - original_count
        
        self.logger.info(f"添加了 {new_count} 个新前缀到字典，总计 {len(self.dict_words)} 个")
        self._save_dict_words()
    
    def process_subdomains(self, domain: str, subdomains: Set[str]) -> None:
        """
        处理子域名，提取前缀并更新字典
        
        Args:
            domain: 目标域名
            subdomains: 子域名集合
        """
        prefixes = self.extract_subdomains_prefix(domain, subdomains)
        self.add_to_dictionary(prefixes)
    
    async def brute_force_subdomains(self, domain: str) -> Set[str]:
        """
        使用字典爆破子域名
        
        Args:
            domain: 目标域名
            
        Returns:
            Set[str]: 爆破发现的子域名集合
        """
        if Config.DISABLE_DICT_BRUTE:
            self.logger.info("子域名字典爆破已禁用")
            return set()
            
        if not self.dict_words:
            self.logger.info("字典为空，无法进行爆破")
            return set()
            
        self.logger.model(f"缓存爆破模块 - 使用字典爆破 {domain}")
        self.logger.info(f"使用 {len(self.dict_words)} 个词进行子域名爆破")
        
        discovered_domains = set()
        sem = asyncio.Semaphore(Config.MAX_BRUTE_CONCURRENCY)
        
        async def check_subdomain(word):
            subdomain = f"{word}.{domain}"
            async with sem:
                try:
                    resolver = dns.resolver.Resolver()
                    resolver.timeout = 2
                    resolver.lifetime = 2
                    answers = resolver.resolve(subdomain)
                    if answers:
                        discovered_domains.add(subdomain)
                        self.logger.success(f"发现有效子域名: {subdomain}")
                except Exception:
                    pass
        
        # 使用线程池并发检查子域名
        tasks = []
        for word in self.dict_words:
            tasks.append(asyncio.create_task(check_subdomain(word)))
            
        # 分批执行任务，避免创建过多任务
        batch_size = 500
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i+batch_size]
            await asyncio.gather(*batch)
            self.logger.debug(f"完成批次 {i//batch_size + 1}/{(len(tasks)+batch_size-1)//batch_size}, 已发现 {len(discovered_domains)} 个域名")
        
        self.logger.success(f"字典爆破完成，共发现 {len(discovered_domains)} 个子域名")
        return discovered_domains 