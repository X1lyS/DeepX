"""
测活模块，用于检测域名是否存活
"""

import asyncio
import aiohttp
import json
import time
import re
import os
from typing import Set, Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from bs4 import BeautifulSoup
import datetime
from concurrent.futures import ThreadPoolExecutor

from config.config import Config
from utils.logger import Logger
from utils.formatter import Colors, get_formatter


@dataclass
class AliveResult:
    """测活结果数据类"""
    domain: str
    url: str
    is_alive: bool
    status_code: Optional[int] = None
    title: Optional[str] = None
    content_length: Optional[int] = None
    response_time: Optional[float] = None
    final_url: Optional[str] = None
    protocol: str = "https"
    error: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AliveResult':
        """从字典创建实例"""
        return cls(**data)


class AliveChecker:
    """测活检查器，用于检测域名是否存活"""
    
    def __init__(self, logger: Logger, disable_cache: bool = False):
        """
        初始化测活检查器
        
        Args:
            logger: 日志记录器
            disable_cache: 是否禁用缓存
        """
        self.logger = logger
        self.disable_cache = disable_cache
        self.formatter = get_formatter()
        self.headers = Config.get_headers()
        self.connector = None  # 连接器在异步方法中初始化
        self.total_count = 0
        self.alive_count = 0
        self.dead_count = 0
        
    async def check_domain_alive(self, domain: str, session: aiohttp.ClientSession) -> AliveResult:
        """
        检查单个域名是否存活
        
        Args:
            domain: 目标域名
            session: aiohttp会话对象
            
        Returns:
            AliveResult: 测活结果
        """
        for protocol in Config.ALIVE_PROTOCOLS:
            url = f"{protocol}://{domain}"
            start_time = time.time()
            
            try:
                # 发起请求，并可能跟随重定向
                async with session.get(
                    url,
                    allow_redirects=Config.ALIVE_FOLLOW_REDIRECTS,
                    max_redirects=Config.ALIVE_MAX_REDIRECTS,
                    timeout=Config.ALIVE_TIMEOUT
                ) as response:
                    response_time = time.time() - start_time
                    
                    # 提取响应头部
                    headers = dict(response.headers)
                    
                    # 获取最终URL
                    final_url = str(response.url)
                    
                    # 获取状态码
                    status_code = response.status
                    
                    # 获取响应大小
                    content_length = int(headers.get('Content-Length', 0))
                    
                    # 如果需要提取标题
                    title = None
                    if Config.ALIVE_CHECK_TITLE:
                        # 只对HTML内容提取标题
                        content_type = headers.get('Content-Type', '')
                        if 'text/html' in content_type:
                            try:
                                # 读取响应体并提取标题
                                html_content = await response.text(errors='ignore')
                                if html_content:
                                    soup = BeautifulSoup(html_content, 'lxml')
                                    title_tag = soup.find('title')
                                    if title_tag:
                                        title = title_tag.text.strip()
                                    
                                    # 如果响应头没有Content-Length，则计算响应体大小
                                    if content_length == 0:
                                        content_length = len(html_content)
                            except Exception as e:
                                self.logger.debug(f"提取标题时出错: {str(e)}")
                    
                    # 如果响应码正常，则认为域名存活
                    is_alive = 100 <= status_code < 600
                    
                    # 如果存活，则不需要尝试其他协议
                    if is_alive:
                        return AliveResult(
                            domain=domain,
                            url=url,
                            is_alive=True,
                            status_code=status_code,
                            title=title,
                            content_length=content_length,
                            response_time=response_time,
                            final_url=final_url,
                            protocol=protocol,
                            headers=headers
                        )
            
            except aiohttp.ClientError as e:
                # 特定连接错误，可能需要尝试其他协议
                continue
            except asyncio.TimeoutError:
                # 超时错误，可能需要尝试其他协议
                continue
            except Exception as e:
                # 其他错误，记录但继续尝试其他协议
                self.logger.debug(f"检查域名 {domain} 时出错: {str(e)}")
                continue
        
        # 所有协议都尝试过，但都失败了
        return AliveResult(
            domain=domain,
            url=f"{Config.ALIVE_PROTOCOLS[0]}://{domain}",
            is_alive=False,
            error="所有协议尝试均失败",
            protocol=Config.ALIVE_PROTOCOLS[0]
        )
    
    async def check_batch(self, domains: Set[str]) -> List[AliveResult]:
        """
        批量检查域名是否存活
        
        Args:
            domains: 域名集合
            
        Returns:
            List[AliveResult]: 测活结果列表
        """
        connector = aiohttp.TCPConnector(
            limit=Config.ALIVE_CONNECTION_LIMIT,
            ssl=False,
            use_dns_cache=False  # 禁用DNS缓存，避免aiodns的问题
        )
        
        timeout = aiohttp.ClientTimeout(total=Config.ALIVE_TIMEOUT)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.headers
        ) as session:
            # 创建任务
            tasks = [self.check_domain_alive(domain, session) for domain in domains]
            
            # 并发执行任务
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            alive_results = []
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"执行测活任务时出错: {str(result)}")
                else:
                    alive_results.append(result)
            
            return alive_results
    
    def get_status_color(self, status_code: int) -> str:
        """
        根据状态码获取颜色
        
        Args:
            status_code: HTTP状态码
            
        Returns:
            str: 颜色代码
        """
        if 100 <= status_code < 200:  # 信息响应
            return Colors.INFO
        elif 200 <= status_code < 300:  # 成功响应
            return Colors.SUCCESS
        elif 300 <= status_code < 400:  # 重定向
            return Colors.WARNING
        elif 400 <= status_code < 500:  # 客户端错误
            return Colors.ERROR
        elif 500 <= status_code < 600:  # 服务器错误
            return Colors.ERROR  # 使用ERROR替代CRITICAL
        else:
            return Colors.RESET
    
    async def check_domains_alive(self, domains: Set[str], batch_size: int = Config.ALIVE_BATCH_SIZE) -> List[AliveResult]:
        """
        分批检查域名是否存活
        
        Args:
            domains: 域名集合
            batch_size: 批处理大小
            
        Returns:
            List[AliveResult]: 测活结果列表
        """
        self.logger.model(f"测活模块 - 检测域名存活性: {len(domains)} 个域名")
        
        # 优化批处理大小，提高性能
        optimized_batch_size = min(max(batch_size, 20), 50)
        
        # 初始化统计数据
        self.total_count = len(domains)
        self.alive_count = 0
        self.dead_count = 0
        
        # 分批处理
        all_results = []
        domains_list = list(domains)
        
        for i in range(0, len(domains_list), optimized_batch_size):
            batch = domains_list[i:i+optimized_batch_size]
            self.logger.info(f"测活进度: {i}/{len(domains_list)} ({i/len(domains_list)*100:.1f}%)")
            
            # 检查当前批次
            batch_results = await self.check_batch(set(batch))
            
            # 更新统计数据
            for result in batch_results:
                if result.is_alive:
                    self.alive_count += 1
                    # 根据状态码获取颜色
                    status_color = self.get_status_color(result.status_code)
                    # 输出存活域名（使用对应状态码的颜色）
                    status_str = f"{status_color}[{result.status_code}]{Colors.RESET}"
                    title_str = f"{Colors.INFO}[{result.title or 'N/A'}]{Colors.RESET}"
                    size_str = f"{Colors.MODEL}[{result.content_length or 0}]{Colors.RESET}"
                    
                    print(f"{status_color}{result.url}{Colors.RESET} {status_str} {title_str} {size_str}")
                else:
                    self.dead_count += 1
                    # 输出不存活域名（红色）
                    print(f"{Colors.ERROR}{result.url} [失活]{Colors.RESET}")
            
            # 添加到总结果
            all_results.extend(batch_results)
            
            # 短暂暂停，避免请求过于频繁
            await asyncio.sleep(0.05)  # 减少暂停时间，提高性能
        
        self.logger.success(f"测活完成: 总计 {self.total_count} 个域名, 存活 {self.alive_count} 个, 不存活 {self.dead_count} 个")
        
        return all_results
    
    async def save_results(self, results: List[AliveResult], output_file: str) -> None:
        """
        保存测活结果到文件
        
        Args:
            results: 测活结果列表
            output_file: 输出文件路径
        """
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                for result in results:
                    if result.is_alive:
                        f.write(f"{result.url} [{result.status_code}] [{result.title or 'N/A'}] [{result.content_length or 0}]\n")
                    else:
                        f.write(f"{result.url} [失活]\n")
                        
            self.logger.success(f"测活结果已保存到 {output_file}")
        except Exception as e:
            self.logger.error(f"保存测活结果到文件时出错: {str(e)}")
    
    async def cache_results(self, results: List[AliveResult], domain: str) -> None:
        """
        缓存测活结果
        
        Args:
            results: 测活结果列表
            domain: 目标域名
        """
        if self.disable_cache:
            return
            
        try:
            timestamp = datetime.datetime.now().strftime(Config.TIMESTAMP_FORMAT)
            cache_path = Config.ALIVE_CACHE_FILE_TEMPLATE.format(domain=domain, timestamp=timestamp)
            
            # 确保缓存目录存在
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            
            # 转换结果为可序列化的字典
            cache_data = {
                'domain': domain,
                'timestamp': time.time(),
                'results': [result.to_dict() for result in results]
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
                
            self.logger.success(f"测活结果已缓存到 {cache_path}")
        except Exception as e:
            self.logger.error(f"缓存测活结果时出错: {str(e)}")
    
    def get_alive_domains(self, results: List[AliveResult]) -> Set[str]:
        """
        获取存活的域名集合
        
        Args:
            results: 测活结果列表
            
        Returns:
            Set[str]: 存活的域名集合
        """
        return {result.domain for result in results if result.is_alive}
    
    def get_dead_domains(self, results: List[AliveResult]) -> Set[str]:
        """
        获取不存活的域名集合
        
        Args:
            results: 测活结果列表
            
        Returns:
            Set[str]: 不存活的域名集合
        """
        return {result.domain for result in results if not result.is_alive}
    
    async def check_and_save(self, domains: Set[str], output_file: str, domain: str) -> Tuple[Set[str], Set[str]]:
        """
        检查域名存活并保存结果
        
        Args:
            domains: 域名集合
            output_file: 输出文件路径
            domain: 目标域名
            
        Returns:
            Tuple[Set[str], Set[str]]: 存活域名集合和不存活域名集合
        """
        if not domains:
            self.logger.info(f"没有域名需要测活")
            return set(), set()
            
        # 检查域名存活
        results = await self.check_domains_alive(domains)
        
        # 保存结果到文件
        await self.save_results(results, output_file)
        
        # 缓存结果
        await self.cache_results(results, domain)
        
        # 获取存活和不存活的域名集合
        alive_domains = self.get_alive_domains(results)
        dead_domains = self.get_dead_domains(results)
        
        return alive_domains, dead_domains 