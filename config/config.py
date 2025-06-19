"""
配置管理模块，用于集中管理全局配置
"""

from typing import Dict
import os

# 尝试从secrets.py中导入FOFA API密钥
try:
    from config.secrets import FOFA_API_KEY
except ImportError:
    # 如果secrets.py不存在或未配置，使用环境变量或默认值
    FOFA_API_KEY = os.environ.get("FOFA_API_KEY", "")


class Config:
    """全局配置类"""
    
    # 伪造请求头
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    # 超时设置（秒）
    TIMEOUT = 30
    
    # 默认输出文件
    DEFAULT_OUTPUT_FILE = "output/deep_subdomain.txt"
    
    # FOFA API配置
    FOFA_API_URL = "https://fofa.info/api/v1/search/all"
    FOFA_API_KEY = FOFA_API_KEY  # 使用从secrets.py导入的密钥
    FOFA_OUTPUT_FILE = "output/fofa_subdomain.txt"            # FOFA结果输出文件
    FOFA_PAGE_SIZE = 100                               # 每页查询数量，降低以避免429错误
    FOFA_MAX_PAGES = 3                                 # 最大查询页数，降低以避免429错误
    FOFA_MAX_CONCURRENT = 1                            # 最大并发请求数，降低以避免429错误
    FOFA_RETRY_COUNT = 3                               # 请求失败重试次数
    FOFA_RETRY_DELAY = 5                               # 重试间隔（秒）
    
    # 比较结果输出文件
    RESULT_OUTPUT_FILE = "output/result.txt"                  # 隐藏域名结果文件
    
    # 缓存配置
    CACHE_DIR = "cache_data"                           # 缓存目录
    CACHE_EXPIRE_DAYS = 3                              # 缓存有效期（天）
    DISABLE_CACHE = False                              # 是否禁用缓存
    
    # 字典爆破配置
    DICT_FILE = os.path.join("data", "subdomain_dict.txt")  # 子域名字典文件
    DISABLE_DICT_BRUTE = False                         # 是否禁用字典爆破
    MAX_BRUTE_CONCURRENCY = 100                        # 爆破最大并发数
    
    # 最大线程数量
    MAX_WORKERS = 5
    
    @classmethod
    def get_headers(cls) -> Dict[str, str]:
        """获取请求头"""
        return cls.DEFAULT_HEADERS.copy() 