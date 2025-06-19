"""
文件输出处理器模块
"""

from typing import Set

from handlers.base import ResultHandler
from utils.logger import Logger


class FileResultHandler(ResultHandler):
    """将结果保存到文件"""
    
    def __init__(self, logger: Logger, output_path: str):
        """
        初始化文件输出处理器
        
        Args:
            logger: 日志记录器
            output_path: 输出文件路径
        """
        super().__init__(logger)
        self.output_path = output_path
    
    def handle(self, domains: Set[str]) -> None:
        """
        将结果保存到文件
        
        Args:
            domains: 收集到的子域名集合
        """
        try:
            self.logger.info(f"正在保存结果到文件: {self.output_path}")
            
            with open(self.output_path, 'w', encoding='utf-8') as f:
                for domain in sorted(domains):
                    f.write(f"{domain}\n")
                    
            self.logger.success(f"成功保存 {len(domains)} 个域名到 {self.output_path}")
        except Exception as e:
            self.logger.error(f"保存结果到文件时出错: {str(e)}") 