"""
子域名爆破模块，支持智能速率限制和自适应调整
"""

import asyncio
import aiohttp
import time
import random
import socket
from typing import Set, List, Dict, Optional, Tuple
import os
import multiprocessing
import aiodns
from collections import deque

from config.config import Config
from utils.logger import Logger
from utils.formatter import Colors
from utils.progress import ProgressBar


class SmartBruteForcer:
    """智能子域名爆破器，支持速率限制和自适应调整"""
    
    def __init__(self, target_domain: str, dictionary: List[str], logger: Logger, 
                 rate_limit: int = None, concurrency: int = None, 
                 timeout: int = None, smart_adjust: bool = True):
        """
        初始化爆破器
        
        Args:
            target_domain: 目标根域名
            dictionary: 字典列表
            logger: 日志记录器
            rate_limit: 每秒最大请求数，默认使用Config.BRUTE_RATE_LIMIT
            concurrency: 并发数，默认使用Config.MAX_BRUTE_CONCURRENCY
            timeout: 超时时间，默认使用Config.BRUTE_TIMEOUT
            smart_adjust: 是否启用智能调整
        """
        self.target_domain = target_domain
        self.dictionary = dictionary
        self.logger = logger
        self.rate_limit = rate_limit or Config.BRUTE_RATE_LIMIT
        self.concurrency = concurrency or Config.MAX_BRUTE_CONCURRENCY
        self.timeout = timeout or Config.BRUTE_TIMEOUT
        self.smart_adjust = smart_adjust
        
        # 速率限制相关
        self._request_times = deque(maxlen=100)  # 最近100次请求的时间
        self._rate_window = 1.0  # 1秒窗口
        self._target_rate = self.rate_limit
        self._current_rate = self.rate_limit
        
        # 结果统计相关
        self.found_domains = set()
        self.success_count = 0
        self.fail_count = 0
        self.error_rate = 0.0
        
        # 智能调整相关
        self.response_times = []
        self.consecutive_timeouts = 0
        self.consecutive_successes = 0
        self.adjustment_factor = 1.0
        
        # 进度回调
        self.progress_callback = None
        
        # 初始化DNS解析器
        self.resolver = None
        
    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback
    
    async def _init_resolver(self):
        """初始化DNS解析器"""
        try:
            self.resolver = aiodns.DNSResolver(timeout=self.timeout, tries=2)
            # 使用知名的公共DNS服务器
            self.resolver.nameservers = [
                '8.8.8.8', '8.8.4.4',       # Google DNS
                '1.1.1.1', '1.0.0.1',       # Cloudflare DNS
                '9.9.9.9', '149.112.112.112' # Quad9
            ]
            # 随机打乱DNS服务器顺序，避免对单个服务商压力过大
            random.shuffle(self.resolver.nameservers)
            self.logger.debug(f"DNS解析器已初始化，使用服务器: {', '.join(self.resolver.nameservers[:3])}...")
        except Exception as e:
            self.logger.error(f"初始化DNS解析器失败: {str(e)}")
            self.resolver = None
            
    async def check_subdomain(self, subdomain: str) -> Tuple[str, bool]:
        """
        检查子域名是否存在
        
        Args:
            subdomain: 子域名前缀
            
        Returns:
            Tuple[str, bool]: (完整域名, 是否存在)
        """
        if not self.resolver:
            await self._init_resolver()
            if not self.resolver:
                return f"{subdomain}.{self.target_domain}", False
                
        full_domain = f"{subdomain}.{self.target_domain}"
        
        # 执行速率限制
        await self._limit_rate()
        
        # 记录当前请求时间
        self._request_times.append(time.time())
        
        start_time = time.time()
        try:
            result = await self.resolver.query(full_domain, 'A')
            
            # 记录响应时间
            response_time = time.time() - start_time
            self.response_times.append(response_time)
            if len(self.response_times) > 20:
                self.response_times.pop(0)
                
            # 增加连续成功计数
            self.consecutive_successes += 1
            self.consecutive_timeouts = 0
            
            # 请求成功，域名存在
            self.success_count += 1
            
            # 智能调整速率
            if self.smart_adjust and self.consecutive_successes >= 10:
                self._increase_rate()
                self.consecutive_successes = 0
                
            return full_domain, True
                
        except aiodns.error.DNSError as e:
            # 域名不存在或解析错误
            response_time = time.time() - start_time
            
            if "timed out" in str(e).lower():
                # 超时错误
                self.consecutive_timeouts += 1
                self.consecutive_successes = 0
                
                # 智能调整速率
                if self.smart_adjust and self.consecutive_timeouts >= 3:
                    self._decrease_rate()
                    self.consecutive_timeouts = 0
            else:
                # 正常"不存在"错误，不减慢速率
                self.consecutive_timeouts = 0
                
            self.fail_count += 1
            return full_domain, False
            
        except Exception as e:
            # 其他错误
            self.fail_count += 1
            return full_domain, False
    
    async def _limit_rate(self):
        """限制请求速率，确保不超过设定的每秒请求数"""
        # 计算当前速率
        now = time.time()
        
        # 如果队列中有请求记录
        if self._request_times:
            # 计算当前时间窗口内的请求数量
            window_start = now - self._rate_window
            # 过滤出时间窗口内的请求
            recent_requests = [t for t in self._request_times if t > window_start]
            
            if len(recent_requests) >= self._current_rate:
                # 计算需要等待的时间
                oldest_in_window = min(recent_requests)
                wait_time = max(0, (oldest_in_window + self._rate_window) - now)
                
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
    
    def _increase_rate(self):
        """增加请求速率"""
        if self._current_rate < self._target_rate * 2:  # 不超过目标速率的2倍
            old_rate = self._current_rate
            self._current_rate = min(self._current_rate * 1.1, self._target_rate * 2)
            self.logger.debug(f"增加爆破速率: {old_rate:.1f} -> {self._current_rate:.1f} 请求/秒")
    
    def _decrease_rate(self):
        """降低请求速率以应对超时或错误"""
        if self._current_rate > self._target_rate * 0.1:  # 不低于目标速率的10%
            old_rate = self._current_rate
            self._current_rate = max(self._current_rate * 0.8, self._target_rate * 0.1)
            self.logger.debug(f"降低爆破速率: {old_rate:.1f} -> {self._current_rate:.1f} 请求/秒")
            
    def _estimate_completion(self, completed: int, total: int) -> str:
        """
        估算完成时间
        
        Args:
            completed: 已完成数量
            total: 总数量
            
        Returns:
            str: 完成时间估算字符串
        """
        if not self._request_times or completed == 0:
            return "计算中..."
            
        now = time.time()
        # 计算平均每个请求的时间
        if len(self._request_times) >= 2:
            recent_count = min(len(self._request_times), 50)
            recent_times = list(self._request_times)[-recent_count:]
            
            if len(recent_times) >= 2:
                time_span = recent_times[-1] - recent_times[0]
                requests_per_sec = (len(recent_times) - 1) / max(0.01, time_span)
                remaining = total - completed
                
                if requests_per_sec > 0:
                    remaining_seconds = remaining / requests_per_sec
                    
                    if remaining_seconds < 60:
                        return f"{int(remaining_seconds)}秒"
                    elif remaining_seconds < 3600:
                        return f"{int(remaining_seconds/60)}分钟"
                    else:
                        return f"{int(remaining_seconds/3600)}小时{int((remaining_seconds%3600)/60)}分钟"
        
        return "计算中..."
    
    async def brute_force(self) -> Set[str]:
        """
        执行子域名爆破
        
        Returns:
            Set[str]: 发现的子域名集合
        """
        self.found_domains = set()
        self.success_count = 0
        self.fail_count = 0
        
        # 显示爆破配置
        self.logger.info(f"开始爆破子域名: {self.target_domain}")
        self.logger.info(f"字典大小: {len(self.dictionary)} 条")
        self.logger.info(f"初始速率: {self.rate_limit} 请求/秒, 并发数: {self.concurrency}")
        self.logger.info(f"智能调整: {'启用' if self.smart_adjust else '禁用'}")
        
        # 创建进度条
        if Config.SHOW_PROGRESS_BAR:
            progress_bar = ProgressBar(len(self.dictionary), "子域名爆破")
            progress_bar.start()
        
        # 初始化semaphore来控制并发
        sem = asyncio.Semaphore(self.concurrency)
        
        # 定义包含semaphore的检查函数
        async def check_with_limit(subdomain, index):
            async with sem:
                full_domain, exists = await self.check_subdomain(subdomain)
                
                # 更新进度
                completed = index + 1
                
                # 更新进度条或回调
                if Config.SHOW_PROGRESS_BAR:
                    progress_bar.update(completed)
                if self.progress_callback:
                    self.progress_callback(int(completed / len(self.dictionary) * 100))
                
                # 计算当前成功率和当前速率
                total = self.success_count + self.fail_count
                success_rate = (self.success_count / max(1, total)) * 100
                current_rate = len(self._request_times) / max(0.1, self._rate_window)
                
                # 定期显示进度
                if exists:
                    self.found_domains.add(full_domain)
                    self.logger.success(f"发现子域名: {full_domain}")
                elif completed % 100 == 0:
                    eta = self._estimate_completion(completed, len(self.dictionary))
                    self.logger.info(
                        f"进度: {completed}/{len(self.dictionary)} ({completed/len(self.dictionary)*100:.1f}%), "
                        f"发现: {len(self.found_domains)}, "
                        f"速率: {current_rate:.1f}r/s, " 
                        f"预计: {eta}"
                    )
                
                return full_domain, exists
        
        # 创建所有爆破任务
        tasks = [check_with_limit(subdomain, i) for i, subdomain in enumerate(self.dictionary)]
        
        # 执行任务并等待所有任务完成
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"爆破任务出错: {str(result)}")
                elif result and isinstance(result, tuple) and result[1]:
                    # 成功的结果(full_domain, True)
                    self.found_domains.add(result[0])
        except Exception as e:
            self.logger.error(f"爆破过程中出错: {str(e)}")
            
        # 完成进度条
        if Config.SHOW_PROGRESS_BAR:
            progress_bar.finish()
        
        # 显示结果统计
        self.logger.success(f"爆破完成，共发现 {len(self.found_domains)} 个子域名")
        
        # 保存结果
        if self.found_domains:
            self._save_results()
            
        return self.found_domains
    
    def _save_results(self):
        """保存爆破结果到文件"""
        output_file = "output/brute_results.txt"
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                for domain in sorted(self.found_domains):
                    f.write(f"{domain}\n")
                    
            self.logger.success(f"爆破结果已保存到 {output_file}")
        except Exception as e:
            self.logger.error(f"保存爆破结果失败: {str(e)}")
            
            
class DictBruteForcer:
    """字典爆破管理器"""
    
    def __init__(self, target_domain: str, debug: bool = True, rate_limit: int = None, smart_adjust: bool = None):
        """
        初始化字典爆破管理器
        
        Args:
            target_domain: 目标域名
            debug: 是否启用调试模式
            rate_limit: 爆破速率限制
            smart_adjust: 智能调整
        """
        self.target_domain = target_domain
        self.logger = Logger(debug)
        self.rate_limit = rate_limit or Config.BRUTE_RATE_LIMIT
        self.smart_adjust = smart_adjust if smart_adjust is not None else Config.BRUTE_SMART_ADJUST
        
        # 加载字典
        self.dictionary = self._load_dictionary()
        
    def _load_dictionary(self) -> List[str]:
        """
        加载子域名字典
        
        Returns:
            List[str]: 子域名前缀列表
        """
        dict_path = Config.DICT_FILE
        if not os.path.exists(dict_path):
            self.logger.error(f"字典文件不存在: {dict_path}")
            return []
            
        try:
            with open(dict_path, 'r', encoding='utf-8', errors='ignore') as f:
                words = [line.strip() for line in f if line.strip()]
                
            self.logger.info(f"已加载字典文件，共 {len(words)} 个条目")
            return words
        except Exception as e:
            self.logger.error(f"加载字典文件出错: {str(e)}")
            return []
    
    async def run(self) -> Set[str]:
        """
        执行爆破
        
        Returns:
            Set[str]: 发现的子域名集合
        """
        if not self.dictionary:
            self.logger.error("字典为空，无法进行爆破")
            return set()
            
        self.logger.model(f"字典爆破模块 - 目标: {self.target_domain}")
        
        # 创建爆破器
        brute_forcer = SmartBruteForcer(
            self.target_domain,
            self.dictionary,
            self.logger,
            rate_limit=self.rate_limit,
            smart_adjust=self.smart_adjust
        )
        
        # 执行爆破
        found_domains = await brute_forcer.brute_force()
        
        return found_domains 