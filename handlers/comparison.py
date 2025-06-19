"""
比较处理器模块，用于比较不同来源的子域名结果
"""

from typing import Set, List, Dict
import os

from handlers.base import ResultHandler
from utils.logger import Logger
from config.config import Config
from utils.formatter import Colors, get_formatter


class ComparisonHandler(ResultHandler):
    """比较处理器，分析普通收集和FOFA API结果的差异"""
    
    def __init__(self, logger: Logger, fofa_file: str = None, deep_file: str = None, result_file: str = None):
        """
        初始化比较处理器
        
        Args:
            logger: 日志记录器
            fofa_file: FOFA API结果文件路径
            deep_file: DeepX结果文件路径
            result_file: 隐藏域名结果文件路径
        """
        super().__init__(logger)
        self.fofa_file = fofa_file or Config.FOFA_OUTPUT_FILE
        self.deep_file = deep_file or Config.DEFAULT_OUTPUT_FILE
        self.result_file = result_file or Config.RESULT_OUTPUT_FILE
        self.formatter = get_formatter()
    
    def handle(self, domains: Set[str]) -> None:
        """
        处理结果的默认方法
        
        Args:
            domains: 收集到的子域名集合
        """
        # 这个方法不会直接处理传入的域名集合
        # 而是从文件中读取并比较结果
        self.compare_domains()
    
    def _read_domains_from_file(self, file_path: str) -> Set[str]:
        """
        从文件中读取域名列表
        
        Args:
            file_path: 文件路径
            
        Returns:
            Set[str]: 域名集合
        """
        domains = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    domain = line.strip()
                    if domain:
                        domains.add(domain)
            return domains
        except Exception as e:
            self.logger.error(f"读取文件 {file_path} 失败: {str(e)}")
            return set()
    
    def compare_domains(self) -> Set[str]:
        """
        比较两个数据源的域名，找出隐藏域名
        
        Returns:
            Set[str]: 隐藏域名集合
        """
        self.logger.info(f"正在对比 {self.deep_file} 和 {self.fofa_file} 中的域名...")
        
        # 读取域名
        deep_domains = self._read_domains_from_file(self.deep_file)
        fofa_domains = self._read_domains_from_file(self.fofa_file)
        
        self.logger.info(f"从 {self.deep_file} 读取到 {len(deep_domains)} 个域名")
        self.logger.info(f"从 {self.fofa_file} 读取到 {len(fofa_domains)} 个域名")
        
        # 找出在deep_domains中但不在fofa_domains中的域名
        hidden_domains = deep_domains - fofa_domains
        
        self.logger.success(f"发现 {len(hidden_domains)} 个隐藏域名")
        
        # 输出隐藏域名到控制台（绿色）
        if hidden_domains:
            print(f"\n{Colors.SUCCESS}发现的隐藏域名 ({len(hidden_domains)}):{Colors.RESET}")
            for domain in sorted(hidden_domains):
                print(f"{Colors.SUCCESS}{domain}{Colors.RESET}")
        
        # 保存结果到文件
        try:
            with open(self.result_file, 'w', encoding='utf-8') as f:
                for domain in sorted(hidden_domains):
                    f.write(f"{domain}\n")
            self.logger.success(f"隐藏域名已保存到 {self.result_file}")
        except Exception as e:
            self.logger.error(f"保存结果到文件时出错: {str(e)}")
        
        return hidden_domains 