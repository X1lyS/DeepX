"""
缓存管理器模块，负责处理域名收集结果的缓存
"""

import os
import json
import time
import hashlib
import datetime
from typing import Set, Dict, Any, Optional, List
import glob

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
        timestamp = datetime.datetime.now().strftime(Config.TIMESTAMP_FORMAT)
        return os.path.join(self.cache_dir, f"{domain}_{timestamp}.json")
    
    def _get_cache_files(self, domain: str) -> List[str]:
        """
        获取域名对应的所有缓存文件
        
        Args:
            domain: 目标域名
            
        Returns:
            List[str]: 缓存文件列表，按时间戳排序
        """
        pattern = os.path.join(self.cache_dir, f"{domain}_*.json")
        files = glob.glob(pattern)
        
        # 添加安全的排序函数，防止文件名格式错误导致转换异常
        def safe_get_timestamp(filename):
            try:
                # 尝试从文件名中提取时间戳
                base_name = os.path.basename(filename)
                if '_' in base_name:
                    # 尝试提取格式为 domain_timestamp.json 的时间戳部分
                    parts = base_name.split('_', 1)
                    if len(parts) > 1:
                        timestamp_part = parts[1].split('.')[0]
                        # 尝试解析时间戳字符串为datetime对象
                        try:
                            dt = datetime.datetime.strptime(timestamp_part, Config.TIMESTAMP_FORMAT)
                            return dt.timestamp()
                        except ValueError:
                            pass
                # 如果提取或解析失败，使用文件的修改时间作为备选
                return os.path.getmtime(filename)
            except (ValueError, IndexError, OSError):
                # 出现任何错误，返回文件修改时间作为备选
                try:
                    return os.path.getmtime(filename)
                except OSError:
                    # 如果连文件修改时间都无法获取，返回0（最低优先级）
                    return 0
        
        # 按时间戳排序，最新的在前
        files.sort(key=safe_get_timestamp, reverse=True)
        return files
    
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
            
        cache_files = self._get_cache_files(domain)
        if not cache_files:
            return False
            
        # 使用最新的缓存文件
        cache_path = cache_files[0]
        
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
    
    def clean_expired_cache(self) -> None:
        """
        清理过期的缓存文件
        """
        if not Config.AUTO_CLEAN_CACHE:
            return
            
        self.logger.model(f"缓存过期清理模块 - 开始清理过期缓存")
        
        try:
            # 获取所有缓存文件
            cache_files = glob.glob(os.path.join(self.cache_dir, "*.json"))
            current_time = time.time()
            max_age = Config.CACHE_EXPIRE_DAYS * 86400  # 转换为秒
            cleaned_count = 0
            
            for cache_path in cache_files:
                try:
                    # 尝试读取和解析缓存文件
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    # 安全地获取时间戳，如果不存在则使用文件修改时间
                    try:
                        timestamp = cache_data.get('timestamp', 0)
                        if timestamp == 0:
                            # 使用文件修改时间作为备选
                            timestamp = os.path.getmtime(cache_path)
                    except (KeyError, TypeError):
                        timestamp = os.path.getmtime(cache_path)
                    
                    # 检查是否过期
                    if current_time - timestamp > max_age:
                        os.remove(cache_path)
                        cleaned_count += 1
                        self.logger.debug(f"已清理过期缓存: {cache_path}")
                except (json.JSONDecodeError, IOError, OSError) as e:
                    self.logger.error(f"清理缓存文件 {cache_path} 时出错: {str(e)}")
                    # 尝试删除无法解析的文件（可能已损坏）
                    try:
                        os.remove(cache_path)
                        cleaned_count += 1
                        self.logger.debug(f"已删除损坏的缓存文件: {cache_path}")
                    except OSError:
                        pass
                    continue
                    
            self.logger.success(f"缓存清理完成，共清理 {cleaned_count} 个过期缓存文件")
        except Exception as e:
            self.logger.error(f"清理缓存时出错: {str(e)}")
    
    def get_cached_domains(self, domain: str) -> Dict[str, Set[str]]:
        """
        获取缓存的域名集合
        
        Args:
            domain: 目标域名
            
        Returns:
            Dict[str, Set[str]]: 缓存的子域名集合，按来源分类，如果缓存无效则返回空字典
        """
        if not self.has_valid_cache(domain):
            return {'deep': set(), 'fofa': set()}
            
        cache_files = self._get_cache_files(domain)
        if not cache_files:
            return {'deep': set(), 'fofa': set()}
            
        # 使用最新的缓存文件
        cache_path = cache_files[0]
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                
            deep_domains = set(cache_data.get('deep_domains', []))
            fofa_domains = set(cache_data.get('fofa_domains', []))
            timestamp = cache_data.get('timestamp', 0)
            cache_date = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            
            self.logger.model(f"缓存命中模块 - 使用 {cache_date} 的缓存数据")
            self.logger.success(f"从缓存中获取到 {len(deep_domains)} 个深度子域名和 {len(fofa_domains)} 个FOFA子域名")
            
            return {'deep': deep_domains, 'fofa': fofa_domains}
        except Exception as e:
            self.logger.error(f"读取缓存时出错: {str(e)}")
            return {'deep': set(), 'fofa': set()}
    
    def save_domains_to_cache(self, domain: str, deep_domains: Set[str], fofa_domains: Set[str]) -> None:
        """
        将域名集合保存到缓存
        
        Args:
            domain: 目标域名
            deep_domains: 收集到的隐藏子域名集合
            fofa_domains: 收集到的FOFA子域名集合
        """
        if Config.DISABLE_CACHE:
            return
            
        cache_path = self._get_cache_path(domain)
        
        try:
            cache_data = {
                'domain': domain,
                'timestamp': time.time(),
                'deep_domains': list(deep_domains),
                'fofa_domains': list(fofa_domains)
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
                
            self.logger.success(f"已将 {len(deep_domains)} 个隐藏子域名和 {len(fofa_domains)} 个FOFA子域名保存到缓存")
        except Exception as e:
            self.logger.error(f"保存缓存时出错: {str(e)}") 