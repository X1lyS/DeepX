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
        # 确保字典目录存在
        os.makedirs(Config.DICT_DIR, exist_ok=True)
        self.dict_file = os.path.join(os.getcwd(), Config.DICT_FILE)
        
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
            # 确保字典目录存在
            os.makedirs(os.path.dirname(self.dict_file), exist_ok=True)
            
            with open(self.dict_file, 'w', encoding='utf-8') as f:
                for word in sorted(self.dict_words):
                    f.write(f"{word}\n")
            self.logger.success(f"字典已保存到 {self.dict_file}，共 {len(self.dict_words)} 个词")
        except Exception as e:
            self.logger.error(f"保存字典文件出错: {str(e)}")
            
    def _extract_subdomain_prefix(self, domain: str, target_domain: str) -> List[str]:
        """
        从子域名中提取所有级别的前缀
        
        Args:
            domain: 子域名
            target_domain: 目标主域名
            
        Returns:
            List[str]: 提取的前缀列表
        """
        if domain.endswith('.' + target_domain):
            # 移除目标主域名部分
            prefix = domain[:-len('.' + target_domain)]
            
            # 分割前缀的各级别
            parts = prefix.split('.')
            
            # 生成所有前缀组合
            prefixes = []
            for i in range(len(parts)):
                # 添加单个部分
                if parts[i]:
                    prefixes.append(parts[i])
                    
                # 添加组合部分
                if i > 0:
                    prefixes.append('.'.join(parts[i-1:i+1]))
            
            return prefixes
        elif domain == target_domain:
            return []
        else:
            return []
    
    def process_subdomains(self, target_domain: str, domains: Set[str]) -> None:
        """
        处理子域名集合，提取前缀并更新字典
        
        Args:
            target_domain: 目标主域名
            domains: 子域名集合
        """
        self.logger.model(f"字典写入模块 - 从子域名提取前缀")
        
        if not domains:
            self.logger.info("没有子域名可以处理，跳过字典更新")
            return
            
        # 提取所有前缀
        all_prefixes = set()
        for domain in domains:
            prefixes = self._extract_subdomain_prefix(domain, target_domain)
            all_prefixes.update(prefixes)
            
        # 更新字典集合
        original_size = len(self.dict_words)
        self.dict_words.update(all_prefixes)
        new_words = len(self.dict_words) - original_size
        
        if new_words > 0:
            self.logger.success(f"从子域名中提取了 {len(all_prefixes)} 个前缀，添加了 {new_words} 个新单词到字典")
            self._save_dict_words()
        else:
            self.logger.info("没有发现新的前缀，字典保持不变")
    
    async def _check_domain_exists(self, domain: str) -> bool:
        """
        检查域名是否存在（可解析）
        
        Args:
            domain: 待检查的域名
            
        Returns:
            bool: 如果可以解析则返回True
        """
        try:
            await asyncio.to_thread(dns.resolver.resolve, domain, 'A')
            return True
        except:
            try:
                await asyncio.to_thread(dns.resolver.resolve, domain, 'CNAME')
                return True
            except:
                return False
    
    async def brute_force_subdomains(self, target_domain: str) -> Set[str]:
        """
        使用字典爆破子域名
        
        Args:
            target_domain: 目标域名
            
        Returns:
            Set[str]: 爆破成功的子域名集合
        """
        self.logger.model(f"字典爆破模块 - 爆破目标: {target_domain}")
        
        # 首先加载字典
        dict_words = self._load_dict_words()
        if not dict_words:
            self.logger.info("字典为空，跳过爆破")
            return set()
            
        self.logger.info(f"加载了 {len(dict_words)} 个字典词汇，开始爆破...")
        
        # 构建要检查的子域名
        domains_to_check = {f"{word}.{target_domain}" for word in dict_words}
        self.logger.info(f"共有 {len(domains_to_check)} 个子域名需要检查")
        
        # 限制并发数
        semaphore = asyncio.Semaphore(Config.MAX_BRUTE_CONCURRENCY)
        
        # 创建爆破任务
        valid_domains = set()
        total = len(domains_to_check)
        completed = 0
        
        async def check_domain(domain):
            nonlocal completed
            async with semaphore:
                exists = await self._check_domain_exists(domain)
                completed += 1
                if completed % 100 == 0 or completed == total:
                    self.logger.info(f"爆破进度: {completed}/{total} ({completed/total*100:.2f}%)")
                if exists:
                    self.logger.success(f"发现子域名: {domain}")
                    valid_domains.add(domain)
                    
        # 同时检查所有域名
        tasks = [check_domain(domain) for domain in domains_to_check]
        await asyncio.gather(*tasks)
        
        # 保存爆破结果
        if valid_domains:
            try:
                os.makedirs(os.path.dirname(Config.BRUTE_OUTPUT_FILE), exist_ok=True)
                with open(Config.BRUTE_OUTPUT_FILE, 'w', encoding='utf-8') as f:
                    for domain in sorted(valid_domains):
                        f.write(f"{domain}\n")
                self.logger.success(f"爆破结果已保存到 {Config.BRUTE_OUTPUT_FILE}，共 {len(valid_domains)} 个域名")
            except Exception as e:
                self.logger.error(f"保存爆破结果时出错: {str(e)}")
                
        self.logger.info(f"字典爆破完成，共发现 {len(valid_domains)} 个有效子域名")
        return valid_domains 