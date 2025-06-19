"""
缓存管理器模块，负责处理域名收集结果的缓存
"""

import os
import json
import time
import hashlib
from typing import Set, Dict, Any, Optional
from datetime import datetime

from config.config import Config
from utils.logger import Logger


class CacheManager:
    """域名缓存管理器，管理域名收集结果的缓存"""
    
    def __init__(self, logger: Logger):
        """
        初始化缓存管理器
        
        Args:
            logger: 日志记录器
        """
        self.logger = logger
        self.cache_dir = os.path.join(os.getcwd(), Config.CACHE_DIR)
        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _generate_cache_key(self, domain: str) -> str:
        """
        生成域名的缓存键
        
        Args:
            domain: 目标域名
            
        Returns:
            str: 缓存键（哈希值）
        """
        return hashlib.md5(domain.encode()).hexdigest()
    
    def _get_cache_path(self, domain: str) -> str:
        """
        获取域名的缓存文件路径
        
        Args:
            domain: 目标域名
            
        Returns:
            str: 缓存文件路径
        """
        cache_key = self._generate_cache_key(domain)
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def has_valid_cache(self, domain: str) -> bool:
        """
        检查是否存在有效的缓存
        
        Args:
            domain: 目标域名
            
        Returns:
            bool: 如果有效缓存存在则返回True
        """
        if Config.DISABLE_CACHE:
            return False
            
        cache_path = self._get_cache_path(domain)
        
        if not os.path.exists(cache_path):
            return False
            
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                
            # 检查缓存时间是否超过有效期
            timestamp = cache_data.get('timestamp', 0)
            current_time = time.time()
            max_age = Config.CACHE_EXPIRE_DAYS * 86400  # 转换为秒
            
            if current_time - timestamp > max_age:
                self.logger.debug(f"缓存已过期: {domain}")
                return False
                
            return True
        except Exception as e:
            self.logger.error(f"检查缓存时出错: {str(e)}")
            return False
    
    def get_cached_domains(self, domain: str) -> Set[str]:
        """
        获取缓存的域名集合
        
        Args:
            domain: 目标域名
            
        Returns:
            Set[str]: 缓存的子域名集合，如果缓存无效则返回空集合
        """
        if not self.has_valid_cache(domain):
            return set()
            
        cache_path = self._get_cache_path(domain)
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                
            domains = set(cache_data.get('domains', []))
            timestamp = cache_data.get('timestamp', 0)
            cache_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            
            self.logger.model(f"缓存命中模块 - 使用 {cache_date} 的缓存数据")
            self.logger.success(f"从缓存中获取到 {len(domains)} 个子域名")
            
            return domains
        except Exception as e:
            self.logger.error(f"读取缓存时出错: {str(e)}")
            return set()
    
    def save_domains_to_cache(self, domain: str, domains: Set[str]) -> None:
        """
        将域名集合保存到缓存
        
        Args:
            domain: 目标域名
            domains: 收集到的子域名集合
        """
        if Config.DISABLE_CACHE:
            return
            
        cache_path = self._get_cache_path(domain)
        
        try:
            cache_data = {
                'domain': domain,
                'timestamp': time.time(),
                'domains': list(domains)
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
                
            self.logger.success(f"已将 {len(domains)} 个子域名保存到缓存")
        except Exception as e:
            self.logger.error(f"保存缓存时出错: {str(e)}") 