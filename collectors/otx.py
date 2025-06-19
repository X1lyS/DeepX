"""
OTX子域名收集器模块
"""

from typing import Set
import aiohttp

from collectors.base import CollectorBase
from config.config import Config
from utils.logger import Logger


class OTXCollector(CollectorBase):
    """从 AlienVault OTX 收集子域名"""
    
    def __init__(self, target_domain: str, logger: Logger):
        """
        初始化OTX收集器
        
        Args:
            target_domain: 目标域名
            logger: 日志记录器
        """
        super().__init__(target_domain, logger)
        self.api_url = f"https://otx.alienvault.com/api/v1/indicators/domain/{target_domain}/url_list?limit=10000&page=1"
    
    async def collect(self) -> Set[str]:
        """
        从OTX收集子域名
        
        Returns:
            Set[str]: 收集到的子域名集合
        """
        self.logger.info("正在查询 AlienVault OTX...")
        self.logger.debug(f"OTX API URL: {self.api_url}")
        
        async with aiohttp.ClientSession() as session:
            try:
                self.logger.debug("发送请求到OTX API...")
                async with session.get(
                    self.api_url, 
                    headers=Config.get_headers(), 
                    timeout=Config.TIMEOUT
                ) as response:
                    if response.status != 200:
                        self.logger.error(f"OTX API 返回错误状态码: {response.status}")
                        return set()
                    
                    self.logger.debug("正在解析OTX响应...")
                    data = await response.json()
                    url_list = data.get('url_list', [])
                    self.logger.debug(f"从OTX获取到 {len(url_list)} 个URL记录")
                    
                    # 提取主机名
                    hostnames = {item['hostname'] for item in url_list if 'hostname' in item}
                    self.logger.info(f"从 OTX 获取到 {len(hostnames)} 个域名")
                    return hostnames
            except Exception as e:
                self.logger.error(f"OTX 查询出错: {str(e)}")
                raise 