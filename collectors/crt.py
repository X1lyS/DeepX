"""
Crt.sh证书透明度子域名收集器模块
"""

import re
from typing import Set
import aiohttp

from collectors.base import CollectorBase
from config.config import Config
from utils.logger import Logger


class CrtCollector(CollectorBase):
    """从 crt.sh 收集子域名"""
    
    def __init__(self, target_domain: str, logger: Logger):
        """
        初始化CRT收集器
        
        Args:
            target_domain: 目标域名
            logger: 日志记录器
        """
        super().__init__(target_domain, logger)
        self.api_url = f"https://crt.sh/?q={target_domain}"
    
    async def collect(self) -> Set[str]:
        """
        从crt.sh收集子域名
        
        Returns:
            Set[str]: 收集到的子域名集合
        """
        self.logger.info("正在查询 crt.sh...")
        self.logger.debug(f"CRT.sh URL: {self.api_url}")
        
        async with aiohttp.ClientSession() as session:
            try:
                self.logger.debug("发送请求到 CRT.sh...")
                async with session.get(
                    self.api_url, 
                    headers=Config.get_headers(), 
                    timeout=Config.TIMEOUT
                ) as response:
                    if response.status != 200:
                        self.logger.error(f"crt.sh 返回错误状态码: {response.status}")
                        return set()
                    
                    self.logger.debug("正在解析 CRT.sh 响应...")
                    html_content = await response.text()
                    self.logger.debug(f"获取到的HTML长度: {len(html_content)} 字符")
                    
                    # 使用正则表达式提取域名
                    self.logger.debug("开始使用正则提取域名...")
                    # 改进正则表达式以匹配更多域名类型
                    common_names = re.findall(r'<TD.*?>([^<]*\.[a-z]+)</TD>', html_content, re.S)
                    self.logger.debug(f"正则匹配到 {len(common_names)} 个潜在域名")
                    
                    # 过滤掉不相关的域名
                    relevant_domains = {name.strip() for name in common_names 
                                       if self.target_domain in name.lower() and '*' not in name}
                    
                    self.logger.info(f"从 crt.sh 获取到 {len(relevant_domains)} 个域名")
                    return relevant_domains
            except Exception as e:
                self.logger.error(f"crt.sh 查询出错: {str(e)}")
                raise 