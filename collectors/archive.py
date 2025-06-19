"""
Archive.org子域名收集器模块
"""

import re
from typing import Set
import aiohttp
from bs4 import BeautifulSoup
import asyncio
import concurrent.futures
import urllib.parse
import urllib.request

from collectors.base import CollectorBase
from config.config import Config
from utils.logger import Logger


class ArchiveCollector(CollectorBase):
    """从 Archive.org 收集子域名"""
    
    def __init__(self, target_domain: str, logger: Logger):
        """
        初始化Archive收集器
        
        Args:
            target_domain: 目标域名
            logger: 日志记录器
        """
        super().__init__(target_domain, logger)
        self.api_url = (
            "https://web.archive.org/cdx/search?collapse=urlkey&fl=original"
            f"&limit=10000000&matchType=domain&output=text&url={urllib.parse.quote(target_domain, safe='')}"
        )
    
    async def collect(self) -> Set[str]:
        """
        从Archive.org收集子域名
        
        Returns:
            Set[str]: 收集到的子域名集合
        """
        self.logger.info("正在查询 Archive.org (Wayback Machine)...")
        
        # 由于这个API响应可能很大，使用线程池处理
        with concurrent.futures.ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
            try:
                future = executor.submit(self._fetch_archive_data)
                result = await asyncio.wrap_future(future)
                self.logger.info(f"从 Archive.org 获取到 {len(result)} 个域名")
                return result
            except Exception as e:
                self.logger.error(f"Archive.org 查询出错: {str(e)}")
                raise
    
    def _fetch_archive_data(self) -> Set[str]:
        """
        在线程中获取 Archive.org 数据
        
        Returns:
            Set[str]: 收集到的子域名集合
        """
        seen = set()
        count = 0
        try:
            req = urllib.request.Request(self.api_url, headers=Config.get_headers())
            with urllib.request.urlopen(req, timeout=Config.TIMEOUT) as response:
                self.logger.debug(f"Archive.org 响应已收到，开始处理数据...")
                
                for raw_line in response:
                    count += 1
                    if count % 1000 == 0:
                        self.logger.debug(f"已处理 Archive.org 数据 {count} 行, 当前发现 {len(seen)} 个唯一域名")
                    
                    line = raw_line.decode('utf-8', errors='ignore').strip()
                    if not line:
                        continue
                    
                    try:
                        parsed = urllib.parse.urlparse(line)
                        host = parsed.netloc.split(':')[0]
                        if host and self.target_domain in host.lower():
                            seen.add(host)
                    except Exception:
                        continue
                
                self.logger.debug(f"Archive.org 数据处理完成，共处理 {count} 行")
        except Exception as e:
            self.logger.error(f"获取 Archive.org 数据时出错: {str(e)}")
        
        return seen 