"""
配置管理模块，用于集中管理全局配置
"""

from typing import Dict
import os
import time
import datetime

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
    
    # 输出目录
    OUTPUT_DIR = "output"
    
    # 缓存配置
    CACHE_DIR = "cache_data"                           # 缓存目录
    
    # 时间戳格式
    TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
    
    # 当前的目标域名（运行时设置）
    TARGET_DOMAIN = ""
    
    # 当前时间戳（运行时设置）
    CURRENT_TIMESTAMP = ""
    
    # 默认输出文件
    DEFAULT_OUTPUT_FILE_TEMPLATE = os.path.join(OUTPUT_DIR, "deep_{domain}_{timestamp}.txt")
    
    # FOFA API配置
    FOFA_API_URL = "https://fofa.info/api/v1/search/all"
    FOFA_API_KEY = FOFA_API_KEY  # 使用从secrets.py导入的密钥
    FOFA_OUTPUT_FILE_TEMPLATE = os.path.join(OUTPUT_DIR, "fofa_{domain}_{timestamp}.txt")
    FOFA_PAGE_SIZE = 100                               # 每页查询数量，降低以避免429错误
    FOFA_MAX_PAGES = 50                                # 最大查询页数，增加以获取更多数据
    FOFA_MAX_CONCURRENT = 3                            # 最大并发请求数，适当增加以提高速度
    FOFA_RETRY_COUNT = 5                               # 请求失败重试次数，增加以提高成功率
    FOFA_RETRY_DELAY = 2                               # 重试间隔（秒），优化以避免频率限制
    FOFA_PAGE_INTERVAL = 1                             # 每页请求之间的间隔时间（秒），优化速度
    FOFA_BACKOFF_FACTOR = 0.5                          # 重试退避因子，用于指数级增加等待时间
    
    # 比较结果输出文件
    RESULT_OUTPUT_FILE_TEMPLATE = os.path.join(OUTPUT_DIR, "hidden_{domain}_{timestamp}.txt")
    BRUTE_OUTPUT_FILE_TEMPLATE = os.path.join(OUTPUT_DIR, "brute_{domain}_{timestamp}.txt")
    TOTAL_OUTPUT_FILE_TEMPLATE = os.path.join(OUTPUT_DIR, "total_{domain}_{timestamp}.txt")
    
    # 测活模块配置
    ALIVE_HIDDEN_OUTPUT_FILE_TEMPLATE = os.path.join(OUTPUT_DIR, "alive_hidden_{domain}_{timestamp}.txt")
    ALIVE_NORMAL_OUTPUT_FILE_TEMPLATE = os.path.join(OUTPUT_DIR, "alive_normal_{domain}_{timestamp}.txt")
    ALIVE_ALL_OUTPUT_FILE_TEMPLATE = os.path.join(OUTPUT_DIR, "alive_all_{domain}_{timestamp}.txt")
    ALIVE_TIMEOUT = 5                                  # 测活请求超时时间（秒）
    ALIVE_MAX_WORKERS = 100                            # 测活最大并发数
    ALIVE_RETRY_COUNT = 1                              # 测活请求失败重试次数
    ALIVE_RETRY_DELAY = 0.5                            # 测活重试间隔（秒）
    ALIVE_CACHE_FILE_TEMPLATE = os.path.join(CACHE_DIR, "alive_{domain}_{timestamp}.json")  # 测活缓存文件模板
    ALIVE_BATCH_SIZE = 50                              # 测活批处理大小
    ALIVE_PROTOCOLS = ["https", "http"]                # 测活协议顺序
    ALIVE_FOLLOW_REDIRECTS = True                      # 是否跟随重定向
    ALIVE_MAX_REDIRECTS = 3                            # 最大重定向次数
    ALIVE_CONNECTION_LIMIT = 200                       # 连接池限制
    ALIVE_CHECK_TITLE = True                           # 是否提取标题
    
    # 具体文件路径（运行时生成）
    DEFAULT_OUTPUT_FILE = ""
    FOFA_OUTPUT_FILE = ""
    RESULT_OUTPUT_FILE = ""
    BRUTE_OUTPUT_FILE = ""
    TOTAL_OUTPUT_FILE = ""
    ALIVE_HIDDEN_OUTPUT_FILE = ""
    ALIVE_NORMAL_OUTPUT_FILE = ""
    ALIVE_ALL_OUTPUT_FILE = ""
    
    # 缓存相关配置
    CACHE_FILE_TEMPLATE = os.path.join(CACHE_DIR, "{domain}_{timestamp}.json")  # 缓存文件模板
    CACHE_EXPIRE_DAYS = 3                              # 缓存有效期（天）
    DISABLE_CACHE = False                              # 是否禁用缓存
    AUTO_CLEAN_CACHE = True                            # 是否自动清理过期缓存
    CACHE_FOFA_RESULTS = True                          # 是否缓存FOFA结果
    
    # 字典爆破配置
    DICT_DIR = "dict"                                  # 字典目录
    DICT_FILE = os.path.join(DICT_DIR, "subdomain_dict.txt")  # 子域名字典文件
    DISABLE_DICT_BRUTE = True                          # 默认禁用字典爆破
    MAX_BRUTE_CONCURRENCY = 100                        # 爆破最大并发数
    
    # 最大线程数量
    MAX_WORKERS = 5
    
    @classmethod
    def get_headers(cls) -> Dict[str, str]:
        """获取请求头"""
        return cls.DEFAULT_HEADERS.copy()
    
    @classmethod
    def init_file_paths(cls, domain: str, timestamp: str = None) -> None:
        """
        初始化文件路径，生成带有时间戳的文件名
        
        Args:
            domain: 目标域名
            timestamp: 可选的时间戳，如果不提供则生成新的
        """
        # 设置目标域名
        cls.TARGET_DOMAIN = domain
        
        # 生成当前时间戳或使用传入的时间戳
        if timestamp is None:
            cls.CURRENT_TIMESTAMP = datetime.datetime.now().strftime(cls.TIMESTAMP_FORMAT)
        else:
            cls.CURRENT_TIMESTAMP = timestamp
        
        # 确保输出目录存在
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
        
        # 生成具体文件路径
        cls.DEFAULT_OUTPUT_FILE = cls.DEFAULT_OUTPUT_FILE_TEMPLATE.format(
            domain=domain, timestamp=cls.CURRENT_TIMESTAMP)
        cls.FOFA_OUTPUT_FILE = cls.FOFA_OUTPUT_FILE_TEMPLATE.format(
            domain=domain, timestamp=cls.CURRENT_TIMESTAMP)
        cls.RESULT_OUTPUT_FILE = cls.RESULT_OUTPUT_FILE_TEMPLATE.format(
            domain=domain, timestamp=cls.CURRENT_TIMESTAMP)
        cls.BRUTE_OUTPUT_FILE = cls.BRUTE_OUTPUT_FILE_TEMPLATE.format(
            domain=domain, timestamp=cls.CURRENT_TIMESTAMP)
        cls.TOTAL_OUTPUT_FILE = cls.TOTAL_OUTPUT_FILE_TEMPLATE.format(
            domain=domain, timestamp=cls.CURRENT_TIMESTAMP)
        
        # 生成测活模块文件路径
        cls.ALIVE_HIDDEN_OUTPUT_FILE = cls.ALIVE_HIDDEN_OUTPUT_FILE_TEMPLATE.format(
            domain=domain, timestamp=cls.CURRENT_TIMESTAMP)
        cls.ALIVE_NORMAL_OUTPUT_FILE = cls.ALIVE_NORMAL_OUTPUT_FILE_TEMPLATE.format(
            domain=domain, timestamp=cls.CURRENT_TIMESTAMP)
        cls.ALIVE_ALL_OUTPUT_FILE = cls.ALIVE_ALL_OUTPUT_FILE_TEMPLATE.format(
            domain=domain, timestamp=cls.CURRENT_TIMESTAMP)
        
        # 确保缓存目录存在
        os.makedirs(cls.CACHE_DIR, exist_ok=True) 