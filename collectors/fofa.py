"""
FOFA API子域名收集器模块
"""

import asyncio
import base64
import urllib.parse
import re
import time
import random
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
        self.page_interval = Config.FOFA_PAGE_INTERVAL
        self.backoff_factor = Config.FOFA_BACKOFF_FACTOR
        
        # 记录429错误次数，用于自适应调整请求间隔
        self.rate_limit_count = 0
        
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
        # 计算当前页的初始等待时间（考虑页码，越后面的页码等待越长）
        base_wait = self.page_interval * (1 + (page - 1) * 0.2)  # 随页码递增
        
        for attempt in range(self.retry_count + 1):
            try:
                if attempt > 0:
                    # 使用指数退避策略计算等待时间
                    wait_time = base_wait + (self.retry_delay * (self.backoff_factor ** (attempt - 1)))
                    # 添加随机抖动以避免同步请求
                    jitter = random.uniform(0.5, 1.5)
                    actual_wait = wait_time * jitter
                    
                    self.logger.debug(f"第 {attempt} 次重试获取FOFA API第{page}页数据，等待 {actual_wait:.2f} 秒...")
                    await asyncio.sleep(actual_wait)
                else:
                    # 首次请求也需要一定延迟，避免触发限流
                    initial_wait = base_wait * random.uniform(0.8, 1.2)
                    self.logger.debug(f"准备获取FOFA API第{page}页数据，预先等待 {initial_wait:.2f} 秒...")
                    await asyncio.sleep(initial_wait)
                
                # 执行实际查询
                result = await self._fetch_page(session, page)
                
                # 如果成功获取数据，重置rate_limit_count
                if result and result.get('results') and len(result.get('results', [])) > 0:
                    if self.rate_limit_count > 0:
                        self.rate_limit_count -= 1
                    return result
                
                # 如果没有数据但没有报错，可能是到达了数据末尾
                if result and not result.get('error') and not result.get('results'):
                    self.logger.info(f"FOFA API第{page}页没有数据，可能已到达结果末尾")
                    return result
                
                # 其他情况视为请求失败，继续重试
                self.logger.debug(f"获取FOFA API第{page}页数据不完整，将重试")
                
            except Exception as e:
                self.logger.debug(f"获取FOFA API第{page}页数据出错: {str(e)}，将重试")
        
        # 所有重试都失败
        self.logger.error(f"获取FOFA API第{page}页数据失败，重试{self.retry_count}次后放弃")
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
            # 添加随机User-Agent，减少被识别为爬虫的可能性
            headers = Config.get_headers()
            
            async with session.get(
                self.api_url,
                params=params,
                headers=headers,
                timeout=Config.TIMEOUT
            ) as response:
                if response.status != 200:
                    self.logger.error(f"FOFA API返回错误状态码: {response.status} (第{page}页)")
                    
                    if response.status == 429:  # Too Many Requests
                        # 遇到限流，增加计数器
                        self.rate_limit_count += 1
                        # 根据限流情况动态调整等待时间
                        wait_time = self.retry_delay * (2 ** self.rate_limit_count)
                        wait_time = min(wait_time, 300)  # 最多等待5分钟
                        self.logger.warning(f"遇到FOFA API频率限制，将等待{wait_time}秒后继续...")
                        await asyncio.sleep(wait_time)
                    
                    # 尝试读取错误响应内容
                    try:
                        error_text = await response.text()
                        self.logger.debug(f"错误响应内容: {error_text[:200]}...")
                    except:
                        pass
                        
                    return {'results': []}
                
                data = await response.json()
                if data.get('error'):
                    error_msg = data.get('errmsg', '未知错误')
                    self.logger.error(f"FOFA API错误: {error_msg} (第{page}页)")
                    return {'results': []}
                
                # 检查返回的数据是否包含预期的字段
                if 'results' not in data:
                    self.logger.error(f"FOFA API返回数据格式异常，缺少'results'字段 (第{page}页)")
                    return {'results': []}
                
                result_count = len(data.get('results', []))
                self.logger.success(f"成功获取FOFA API第{page}页数据, 共{result_count}条记录")
                
                # 如果获取的记录数少于请求的页大小，可能已到达结果末尾
                if result_count < self.page_size:
                    self.logger.info(f"FOFA API第{page}页返回{result_count}条记录，少于页大小{self.page_size}，可能已到达结果末尾")
                
                return data
        except aiohttp.ClientError as e:
            self.logger.error(f"FOFA API请求出错 (第{page}页): {str(e)}")
            return {'results': []}
        except asyncio.TimeoutError:
            self.logger.error(f"FOFA API请求超时 (第{page}页)")
            return {'results': []}
        except Exception as e:
            self.logger.error(f"获取FOFA API数据出错 (第{page}页): {str(e)}")
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
                self.logger.warning("FOFA API返回的结果数量为0，请检查查询条件或API密钥是否正确")
                return 0
                
            # 计算总页数
            total_pages = (total_size + self.page_size - 1) // self.page_size
            
            # 显示预计的查询时间
            estimated_time = total_pages * (self.page_interval + 2)  # 粗略估计
            self.logger.info(f"FOFA API搜索结果共{total_size}条记录, {total_pages}页 (预计耗时约{estimated_time}秒)")
            
            # 限制最大页数
            capped_pages = min(total_pages, self.max_pages)
            if capped_pages < total_pages:
                self.logger.warning(f"由于配置限制，将只获取前{capped_pages}页数据，共{capped_pages * self.page_size}条记录")
            
            return capped_pages
        except Exception as e:
            self.logger.error(f"获取FOFA API总页数时出错: {str(e)}")
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
            
        self.logger.info(f"正在查询FOFA API (目标域名: {self.target_domain})...")
        domains = set()
        
        # 自定义客户端session，使用连接池限制
        conn = aiohttp.TCPConnector(limit=self.max_concurrent, limit_per_host=self.max_concurrent)
        timeout = aiohttp.ClientTimeout(total=Config.TIMEOUT)
        
        async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
            # 获取总页数
            total_pages = await self._get_total_pages(session)
            if total_pages == 0:
                self.logger.info("未从FOFA API获取到数据，任务结束")
                return domains
                
            # 创建进度计数器
            processed_pages = 0
            
            # 批量处理页面，按顺序处理以减轻服务器负担
            for page in range(1, total_pages + 1):
                # 记录开始时间
                start_time = time.time()
                
                # 获取当前页数据
                try:
                    self.logger.info(f"获取FOFA API第{page}/{total_pages}页数据 (进度: {processed_pages/total_pages*100:.1f}%)...")
                    data = await self._fetch_page_with_retry(session, page)
                    
                    # 处理返回的数据
                    page_domains = set()
                    for item in data.get('results', []):
                        try:
                            # FOFA API返回结果格式为 [host, domain, ...]
                            if not isinstance(item, list) or len(item) < 2:
                                continue
                                
                            host = item[0].strip() if len(item) > 0 and item[0] else ""
                            domain = item[1].strip() if len(item) > 1 and item[1] else ""
                            
                            # 处理host值
                            if host:
                                # 提取host中的域名
                                host_domain = self._extract_domain(host)
                                if host_domain and self._is_subdomain(host_domain, self.target_domain):
                                    page_domains.add(host_domain)
                            
                            # 处理domain字段
                            if domain and self._is_subdomain(domain, self.target_domain):
                                page_domains.add(domain)
                                
                        except Exception as e:
                            self.logger.error(f"处理FOFA API结果条目出错: {str(e)}")
                    
                    # 更新总域名集合
                    domains.update(page_domains)
                    
                    # 更新进度计数器
                    processed_pages += 1
                    
                    # 记录当前页获取结果
                    elapsed = time.time() - start_time
                    self.logger.success(f"第{page}页处理完成，获取到{len(page_domains)}个域名，耗时{elapsed:.2f}秒，总计{len(domains)}个域名")
                    
                    # 如果当前页没有数据，可能已到达结果末尾，提前结束
                    if not data.get('results'):
                        self.logger.info(f"第{page}页没有数据，提前结束查询")
                        break
                        
                except Exception as e:
                    self.logger.error(f"处理第{page}页时出错: {str(e)}")
            
        self.logger.info(f"FOFA API查询完成，共获取到{len(domains)}个子域名")
        
        # 保存FOFA结果到专用文件
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(Config.FOFA_OUTPUT_FILE), exist_ok=True)
            
            with open(Config.FOFA_OUTPUT_FILE, 'w', encoding='utf-8') as f:
                for domain in sorted(domains):
                    f.write(f"{domain}\n")
            self.logger.success(f"FOFA API结果已保存到 {Config.FOFA_OUTPUT_FILE}")
        except Exception as e:
            self.logger.error(f"保存FOFA API结果到文件时出错: {str(e)}")
            
        return domains 