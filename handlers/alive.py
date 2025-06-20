"""
测活处理器模块，用于处理域名测活
"""

from typing import Set, Dict, List, Tuple
import asyncio
import platform

from handlers.base import ResultHandler
from utils.logger import Logger
from utils.alivecheck import AliveChecker
from config.config import Config


class AliveHandler(ResultHandler):
    """测活处理器，用于检测域名是否存活"""
    
    def __init__(self, logger: Logger, target_domain: str, disable_cache: bool = False):
        """
        初始化测活处理器
        
        Args:
            logger: 日志记录器
            target_domain: 目标域名
            disable_cache: 是否禁用缓存
        """
        super().__init__(logger)
        self.target_domain = target_domain
        self.disable_cache = disable_cache
        self.alive_checker = AliveChecker(logger, disable_cache)
    
    def handle(self, domains: Set[str]) -> None:
        """
        处理域名集合（同步版本，实际调用异步方法）
        
        Args:
            domains: 域名集合
        """
        # 使用事件循环执行异步方法
        try:
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 运行异步方法
            loop.run_until_complete(self.handle_async(domains))
        except Exception as e:
            self.logger.error(f"执行测活任务时出错: {str(e)}")
        finally:
            # 确保关闭事件循环
            try:
                loop.close()
            except:
                pass
    
    async def handle_async(self, domains: Set[str]) -> None:
        """
        异步处理域名集合
        
        Args:
            domains: 域名集合
        """
        await self.alive_checker.check_and_save(domains, Config.ALIVE_ALL_OUTPUT_FILE, self.target_domain)
    
    async def handle_hidden_domains(self, domains: Set[str]) -> Tuple[Set[str], Set[str]]:
        """
        处理隐藏域名
        
        Args:
            domains: 隐藏域名集合
            
        Returns:
            Tuple[Set[str], Set[str]]: 存活域名集合和不存活域名集合
        """
        self.logger.model(f"测活模块 - 检测隐藏域名存活性")
        return await self.alive_checker.check_and_save(domains, Config.ALIVE_HIDDEN_OUTPUT_FILE, self.target_domain)
    
    async def handle_normal_domains(self, domains: Set[str]) -> Tuple[Set[str], Set[str]]:
        """
        处理普通域名
        
        Args:
            domains: 普通域名集合
            
        Returns:
            Tuple[Set[str], Set[str]]: 存活域名集合和不存活域名集合
        """
        self.logger.model(f"测活模块 - 检测普通域名存活性")
        return await self.alive_checker.check_and_save(domains, Config.ALIVE_NORMAL_OUTPUT_FILE, self.target_domain)
    
    async def handle_all_domains(self, hidden_domains: Set[str], normal_domains: Set[str]) -> Dict[str, Set[str]]:
        """
        处理所有域名
        
        Args:
            hidden_domains: 隐藏域名集合
            normal_domains: 普通域名集合
            
        Returns:
            Dict[str, Set[str]]: 结果字典，包含各类域名的存活和不存活情况
        """
        self.logger.model(f"测活模块 - 分别检测隐藏域名和普通域名存活性")
        
        # 先处理隐藏域名
        hidden_alive, hidden_dead = await self.handle_hidden_domains(hidden_domains)
        
        # 再处理普通域名
        normal_alive, normal_dead = await self.handle_normal_domains(normal_domains)
        
        # 返回结果字典
        return {
            'hidden_alive': hidden_alive,
            'hidden_dead': hidden_dead,
            'normal_alive': normal_alive,
            'normal_dead': normal_dead
        } 