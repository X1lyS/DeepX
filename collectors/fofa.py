"""
FOFA API子域名收集器模块
"""

import asyncio
import base64
import urllib.parse
import re
import time
from typing import Set, List, Dict, Any, Optional
import aiohttp
import concurrent.futures
import os

from collectors.base import CollectorBase
from config.config import Config
from utils.logger import Logger


class FofaCollector(CollectorBase):
    """从FOFA API收集子域名"""
    
    def __init__(self, target_domain: str, logger: Logger):
        """
        初始化FOFA收集器
        
        Args:
            target_domain: 目标域名
            logger: 日志记录器
        """
        super().__init__(target_domain, logger)
        self.api_url = Config.FOFA_API_URL
        self.api_key = Config.FOFA_API_KEY  # 直接使用Config中的API密钥
        self.page_size = Config.FOFA_PAGE_SIZE
        self.max_pages = Config.FOFA_MAX_PAGES
        self.max_concurrent = Config.FOFA_MAX_CONCURRENT
        self.retry_count = Config.FOFA_RETRY_COUNT
        self.retry_delay = Config.FOFA_RETRY_DELAY
        
        # 提取域名的正则表达式
        self.domain_pattern = re.compile(r'^(?:https?://)?([^/:]+)')
        
    def _build_query(self, target_domain: str) -> str:
        """
        构建FOFA查询语句
        
        Args:
            target_domain: 目标域名
            
        Returns:
            str: 经过base64编码的查询语法
        """
        # 构建查询语法: domain="example.com"||cert="example.com"
        query = f'domain="{target_domain}"||cert="{target_domain}"'
        # Base64编码
        return base64.b64encode(query.encode()).decode()
    
    async def _fetch_page_with_retry(self, session: aiohttp.ClientSession, page: int) -> Dict[str, Any]:
        """
        带重试机制的获取指定页的FOFA API数据
        
        Args:
            session: aiohttp会话
            page: 页码
            
        Returns:
            Dict: API响应JSON
        """
        for attempt in range(self.retry_count + 1):
            try:
                if attempt > 0:
                    # 重试前等待一段时间
                    self.logger.debug(f"第 {attempt} 次重试获取FOFA API第{page}页数据，等待 {self.retry_delay} 秒...")
                    await asyncio.sleep(self.retry_delay)
                
                return await self._fetch_page(session, page)
            except Exception as e:
                if attempt < self.retry_count:
                    self.logger.debug(f"获取FOFA API第{page}页数据失败，将重试: {str(e)}")
                else:
                    self.logger.error(f"获取FOFA API第{page}页数据失败，重试次数已用完: {str(e)}")
        
        # 所有重试都失败
        return {'results': []}
    
    async def _fetch_page(self, session: aiohttp.ClientSession, page: int) -> Dict[str, Any]:
        """
        获取指定页的FOFA API数据
        
        Args:
            session: aiohttp会话
            page: 页码
            
        Returns:
            Dict: API响应JSON
        """
        self.logger.debug(f"正在获取FOFA API第{page}页数据...")
        
        params = {
            'key': self.api_key,
            'qbase64': self._build_query(self.target_domain),
            'fields': 'host,domain',  # 只获取 host 和 domain 字段
            'page': page,
            'size': self.page_size
        }
        
        try:
            async with session.get(
                self.api_url,
                params=params,
                headers=Config.get_headers(),
                timeout=Config.TIMEOUT
            ) as response:
                if response.status != 200:
                    self.logger.error(f"FOFA API返回错误状态码: {response.status}")
                    if response.status == 429:  # Too Many Requests
                        # 遇到限流时，等待更长时间
                        await asyncio.sleep(self.retry_delay * 2)
                    return {'results': []}
                
                data = await response.json()
                if data.get('error'):
                    error_msg = data.get('errmsg', '未知错误')
                    self.logger.error(f"FOFA API错误: {error_msg}")
                    return {'results': []}
                
                self.logger.debug(f"成功获取FOFA API第{page}页数据, 共{len(data.get('results', []))}条记录")
                return data
        except Exception as e:
            self.logger.error(f"获取FOFA API数据出错: {str(e)}")
            return {'results': []}
    
    def _extract_domain(self, url: str) -> Optional[str]:
        """
        从URL中提取域名
        
        Args:
            url: URL字符串
            
        Returns:
            Optional[str]: 提取的域名，如果无法提取则返回None
        """
        try:
            # 首先尝试标准提取
            match = self.domain_pattern.search(url)
            if match:
                return match.group(1).lower()
            
            return None
        except Exception:
            return None
    
    def _is_subdomain(self, domain: str, target_domain: str) -> bool:
        """
        检查域名是否为目标域名的子域名
        
        Args:
            domain: 待检查的域名
            target_domain: 目标域名
            
        Returns:
            bool: 如果是子域名则返回True
        """
        domain = domain.lower()
        target_domain = target_domain.lower()
        
        # 完全相同
        if domain == target_domain:
            return True
        
        # 子域名形式 (example.com, sub.example.com)
        if domain.endswith('.' + target_domain):
            return True
            
        return False
    
    async def _get_total_pages(self, session: aiohttp.ClientSession) -> int:
        """
        获取查询结果的总页数
        
        Args:
            session: aiohttp会话
            
        Returns:
            int: 总页数
        """
        try:
            # 获取第一页数据，以确定总记录数
            data = await self._fetch_page_with_retry(session, 1)
            total_size = data.get('size', 0)
            
            if total_size == 0:
                return 0
                
            # 计算总页数
            total_pages = (total_size + self.page_size - 1) // self.page_size
            self.logger.info(f"FOFA API搜索结果共{total_size}条记录, {total_pages}页")
            
            # 限制最大页数
            return min(total_pages, self.max_pages)
        except Exception as e:
            self.logger.error(f"获取总页数时出错: {str(e)}")
            return 0
    
    async def collect(self) -> Set[str]:
        """
        从FOFA API收集子域名
        
        Returns:
            Set[str]: 收集到的子域名集合
        """
        # 调试输出API凭证信息
        if self.api_key:
            self.logger.debug(f"使用FOFA API Key: {self.api_key[:5]}...{self.api_key[-5:] if len(self.api_key) > 10 else '(密钥太短)'}")
            
        # 检查API密钥是否配置
        if not self.api_key:
            self.logger.error("FOFA API密钥未配置，请在secrets.py文件中配置FOFA_API_KEY")
            return set()
            
        self.logger.info("正在查询FOFA API...")
        domains = set()
        
        async with aiohttp.ClientSession() as session:
            # 获取总页数
            total_pages = await self._get_total_pages(session)
            if total_pages == 0:
                self.logger.info("未从FOFA API获取到数据")
                return domains
                
            # 创建所有页的查询任务
            tasks = []
            for page in range(1, total_pages + 1):
                # 添加延迟，避免过快请求
                if page > 1:
                    await asyncio.sleep(2)  # 每页之间增加2秒延迟
                tasks.append(self._fetch_page_with_retry(session, page))
                
            # 使用信号量限制并发数量
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            async def fetch_with_semaphore(task):
                async with semaphore:
                    return await task
            
            # 并发执行所有任务
            results = await asyncio.gather(
                *[fetch_with_semaphore(task) for task in tasks],
                return_exceptions=True
            )
            
            # 处理结果
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"查询出错: {str(result)}")
                    continue
                
                # 打印原始结果详情
                if result.get('results'):
                    first_item = result.get('results')[0] if result.get('results') else None
                    if first_item:
                        self.logger.debug(f"FOFA API返回结果示例: {first_item}")
                    
                for item in result.get('results', []):
                    try:
                        # FOFA API返回结果格式为 [host, domain, ...]
                        if not isinstance(item, list) or len(item) < 2:
                            continue
                            
                        host = item[0].strip() if len(item) > 0 and item[0] else ""
                        domain = item[1].strip() if len(item) > 1 and item[1] else ""
                        
                        # 调试输出当前处理的记录
                        self.logger.debug(f"处理记录 - host: {host}, domain: {domain}")
                        
                        # 处理host值
                        if host:
                            # 提取host中的域名
                            host_domain = self._extract_domain(host)
                            if host_domain and self._is_subdomain(host_domain, self.target_domain):
                                self.logger.debug(f"从host提取到子域名: {host_domain}")
                                domains.add(host_domain)
                        
                        # 处理domain字段
                        if domain and self._is_subdomain(domain, self.target_domain):
                            self.logger.debug(f"从domain字段获取到子域名: {domain}")
                            domains.add(domain)
                            
                    except Exception as e:
                        self.logger.error(f"处理FOFA API结果出错: {str(e)}")
        
        self.logger.info(f"从FOFA API获取到 {len(domains)} 个子域名")
        
        # 保存FOFA结果到专用文件
        try:
            with open(Config.FOFA_OUTPUT_FILE, 'w', encoding='utf-8') as f:
                for domain in sorted(domains):
                    f.write(f"{domain}\n")
            self.logger.info(f"FOFA API结果已保存到 {Config.FOFA_OUTPUT_FILE}")
        except Exception as e:
            self.logger.error(f"保存FOFA API结果到文件时出错: {str(e)}")
            
        return domains 