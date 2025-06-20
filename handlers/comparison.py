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
    
    def __init__(self, logger: Logger, fofa_file: str = None, deep_file: str = None, result_file: str = None, brute_file: str = None, total_file: str = None):
        """
        初始化比较处理器
        
        Args:
            logger: 日志记录器
            fofa_file: FOFA API结果文件路径
            deep_file: DeepX结果文件路径
            result_file: 隐藏域名结果文件路径
            brute_file: 爆破结果文件路径
            total_file: 总资产结果文件路径
        """
        super().__init__(logger)
        # 使用传入的路径或Config中的最新路径
        self.fofa_file = fofa_file or Config.FOFA_OUTPUT_FILE
        self.deep_file = deep_file or Config.DEFAULT_OUTPUT_FILE
        self.result_file = result_file or Config.RESULT_OUTPUT_FILE
        self.brute_file = brute_file or Config.BRUTE_OUTPUT_FILE
        self.total_file = total_file or Config.TOTAL_OUTPUT_FILE
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
            # 调试输出文件路径和是否存在
            self.logger.debug(f"尝试读取文件: {file_path}, 文件是否存在: {os.path.exists(file_path)}")
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 调试输出文件大小
                    self.logger.debug(f"文件大小: {len(content)} 字节")
                    
                    # 按行处理文件内容
                    for line in content.splitlines():
                        domain = line.strip()
                        if domain:
                            domains.add(domain)
            else:
                self.logger.warning(f"文件不存在: {file_path}")
                
            return domains
        except Exception as e:
            self.logger.error(f"读取文件 {file_path} 失败: {str(e)}")
            return set()
    
    def compare_domains(self) -> Dict[str, Set[str]]:
        """
        比较三个数据源的域名，找出隐藏域名和总资产
        
        Returns:
            Dict[str, Set[str]]: 隐藏域名和总资产集合
        """
        self.logger.model(f"隐藏资产比较模块 - 对比不同来源的域名数据")
        
        # 输出当前使用的文件路径
        self.logger.debug(f"比较使用的文件路径:")
        self.logger.debug(f"深度收集文件: {self.deep_file}")
        self.logger.debug(f"FOFA收集文件: {self.fofa_file}")
        self.logger.debug(f"爆破结果文件: {self.brute_file}")
        self.logger.debug(f"隐藏域名结果文件: {self.result_file}")
        self.logger.debug(f"总资产文件: {self.total_file}")
        
        # 读取域名
        deep_domains = self._read_domains_from_file(self.deep_file)
        fofa_domains = self._read_domains_from_file(self.fofa_file)
        brute_domains = self._read_domains_from_file(self.brute_file)
        
        self.logger.info(f"从 {self.deep_file} 读取到 {len(deep_domains)} 个深度收集域名")
        self.logger.info(f"从 {self.fofa_file} 读取到 {len(fofa_domains)} 个FOFA收集域名")
        self.logger.info(f"从 {self.brute_file} 读取到 {len(brute_domains)} 个爆破成功域名")
        
        # 找出在deep_domains或brute_domains中但不在fofa_domains中的域名（即隐藏域名）
        hidden_domains = (deep_domains.union(brute_domains)) - fofa_domains
        
        # 所有来源域名的合并（总资产）
        total_domains = deep_domains.union(fofa_domains).union(brute_domains)
        
        self.logger.success(f"发现 {len(hidden_domains)} 个隐藏域名，总计 {len(total_domains)} 个总资产域名")
        
        # 输出隐藏域名到控制台（绿色）
        if hidden_domains:
            print(f"\n{Colors.SUCCESS}发现的隐藏域名 ({len(hidden_domains)}):{Colors.RESET}")
            for domain in sorted(hidden_domains):
                print(f"{Colors.SUCCESS}{domain}{Colors.RESET}")
        
        # 保存隐藏域名结果到文件
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(self.result_file), exist_ok=True)
            
            with open(self.result_file, 'w', encoding='utf-8') as f:
                for domain in sorted(hidden_domains):
                    f.write(f"{domain}\n")
            self.logger.success(f"隐藏域名已保存到 {self.result_file}")
        except Exception as e:
            self.logger.error(f"保存隐藏域名到文件时出错: {str(e)}")
            
        # 保存总资产到文件
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(self.total_file), exist_ok=True)
            
            with open(self.total_file, 'w', encoding='utf-8') as f:
                for domain in sorted(total_domains):
                    f.write(f"{domain}\n")
            self.logger.success(f"总资产已保存到 {self.total_file}")
        except Exception as e:
            self.logger.error(f"保存总资产到文件时出错: {str(e)}")
        
        return {'hidden': hidden_domains, 'total': total_domains} 