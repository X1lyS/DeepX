"""
命令行接口模块，用于处理命令行参数和启动相应的功能
"""

import sys
import asyncio
import argparse
import os
import datetime
from typing import Dict, Set

from config.config import Config
from core.core import SubdomainCollector, FofaSubdomainCollector, DomainComparator, DictBruteForcer, DomainProcessor
from utils.logger import Logger
from handlers.comparison import ComparisonHandler
from handlers.alive import AliveHandler


class CLI:
    """命令行接口类，处理命令行参数和启动相应的功能"""

    @staticmethod
    def parse_args():
        """解析命令行参数"""
        parser = argparse.ArgumentParser(
            description="DeepX - 多接口集成的子域名收集工具",
            epilog="示例: python DeepX.py collect example.com"
        )
        
        subparsers = parser.add_subparsers(dest="command", help="命令")
        
        collect_parser = subparsers.add_parser("collect", help="使用传统方法收集子域名")
        collect_parser.add_argument("domain", help="目标域名 (例如: example.com)")
        collect_parser.add_argument("-d", "--debug", action="store_true", default=True,
                                  help="启用调试输出 (默认已启用)")
        collect_parser.add_argument("--no-debug", action="store_false", dest="debug",
                                   help="禁用调试输出")
        collect_parser.add_argument("-o", "--output", default=Config.DEFAULT_OUTPUT_FILE,
                                  help=f"输出文件名 (默认: {Config.DEFAULT_OUTPUT_FILE})")
        collect_parser.add_argument("--collectors", nargs="+", choices=["otx", "crt", "archive"],
                                  help="指定要使用的收集器 (可选: otx, crt, archive)")
        collect_parser.add_argument("--no-cache", action="store_true",
                                  help="禁用域名缓存")
        collect_parser.add_argument("--cache-days", type=int, default=Config.CACHE_EXPIRE_DAYS,
                                  help=f"缓存有效期 (天，默认: {Config.CACHE_EXPIRE_DAYS})")
        collect_parser.add_argument("--no-brute", action="store_true",
                                  help="禁用字典爆破")
        
        fofa_parser = subparsers.add_parser("fofa", help="使用FOFA API收集子域名")
        fofa_parser.add_argument("domain", help="目标域名 (例如: example.com)")
        fofa_parser.add_argument("-d", "--debug", action="store_true", default=True,
                               help="启用调试输出 (默认已启用)")
        fofa_parser.add_argument("--no-debug", action="store_false", dest="debug",
                               help="禁用调试输出")
        fofa_parser.add_argument("-o", "--output", default=Config.FOFA_OUTPUT_FILE,
                               help=f"输出文件名 (默认: {Config.FOFA_OUTPUT_FILE})")
        fofa_parser.add_argument("--key", help="FOFA API密钥 (优先于配置文件)")
        
        compare_parser = subparsers.add_parser("compare", help="比较不同来源的域名结果，找出隐藏域名")
        compare_parser.add_argument("domain", help="目标域名 (仅用于日志显示)")
        compare_parser.add_argument("-d", "--debug", action="store_true", default=True,
                                  help="启用调试输出 (默认已启用)")
        compare_parser.add_argument("--deep-file", default=Config.DEFAULT_OUTPUT_FILE,
                                  help=f"DeepX结果文件 (默认: {Config.DEFAULT_OUTPUT_FILE})")
        compare_parser.add_argument("--fofa-file", default=Config.FOFA_OUTPUT_FILE,
                                  help=f"FOFA结果文件 (默认: {Config.FOFA_OUTPUT_FILE})")
        compare_parser.add_argument("--brute-file", default=Config.BRUTE_OUTPUT_FILE,
                                  help=f"爆破结果文件 (默认: {Config.BRUTE_OUTPUT_FILE})")
        compare_parser.add_argument("-r", "--result", default=Config.RESULT_OUTPUT_FILE,
                                  help=f"隐藏域名结果文件 (默认: {Config.RESULT_OUTPUT_FILE})")
        compare_parser.add_argument("-t", "--total", default=Config.TOTAL_OUTPUT_FILE,
                                  help=f"总资产域名结果文件 (默认: {Config.TOTAL_OUTPUT_FILE})")
        compare_parser.add_argument("--alive", action="store_true",
                                  help="启用测活 (检查域名是否存活)")
        compare_parser.add_argument("--no-cache", action="store_true",
                                  help="禁用域名缓存")
        
        alive_parser = subparsers.add_parser("alive", help="测试域名是否存活")
        alive_parser.add_argument("domain", help="目标域名 (例如: example.com)")
        alive_parser.add_argument("-d", "--debug", action="store_true", default=True,
                               help="启用调试输出 (默认已启用)")
        alive_parser.add_argument("--no-debug", action="store_false", dest="debug",
                               help="禁用调试输出")
        alive_parser.add_argument("--input-file", 
                               help="输入文件，包含要测活的域名列表 (每行一个域名)")
        alive_parser.add_argument("--hidden-file", default=Config.RESULT_OUTPUT_FILE,
                               help=f"隐藏域名结果文件 (默认: {Config.RESULT_OUTPUT_FILE})")
        alive_parser.add_argument("--normal-file", default=Config.FOFA_OUTPUT_FILE,
                               help=f"普通域名结果文件 (默认: {Config.FOFA_OUTPUT_FILE})")
        alive_parser.add_argument("--no-cache", action="store_true",
                               help="禁用域名缓存")
        
        brute_parser = subparsers.add_parser("brute", help="使用累积的字典对子域名进行爆破")
        brute_parser.add_argument("domain", help="目标域名 (例如: example.com)")
        brute_parser.add_argument("-d", "--debug", action="store_true", default=True,
                               help="启用调试输出 (默认已启用)")
        brute_parser.add_argument("--no-debug", action="store_false", dest="debug",
                               help="禁用调试输出")
        brute_parser.add_argument("-o", "--output", default=Config.BRUTE_OUTPUT_FILE,
                               help=f"输出文件名 (默认: {Config.BRUTE_OUTPUT_FILE})")
        
        all_parser = subparsers.add_parser("all", help="执行完整流程：收集、FOFA、比较和测活")
        all_parser.add_argument("domain", help="目标域名 (例如: example.com)")
        all_parser.add_argument("-d", "--debug", action="store_true", default=True,
                              help="启用调试输出 (默认已启用)")
        all_parser.add_argument("--no-debug", action="store_false", dest="debug",
                              help="禁用调试输出")
        all_parser.add_argument("--key", help="FOFA API密钥 (优先于配置文件)")
        all_parser.add_argument("--no-cache", action="store_true",
                              help="禁用域名缓存")
        all_parser.add_argument("--cache-days", type=int, default=Config.CACHE_EXPIRE_DAYS,
                              help=f"缓存有效期 (天，默认: {Config.CACHE_EXPIRE_DAYS})")
        all_parser.add_argument("--enable-brute", action="store_false", dest="no_brute",
                              help="启用字典爆破 (默认禁用)")
        all_parser.add_argument("--no-alive", action="store_true",
                              help="禁用测活 (默认启用)")
        
        args = parser.parse_args()
        
        if len(sys.argv) == 1:
            parser.print_help()
            sys.exit(0)
            
        if args.command is None and len(sys.argv) > 1:
            potential_domain = sys.argv[1]
            if "." in potential_domain and not potential_domain.startswith("-"):
                args.command = "collect"
                args.domain = potential_domain
                args.debug = True
                args.output = Config.DEFAULT_OUTPUT_FILE
                args.collectors = None
                args.no_cache = False
                args.no_brute = True  # 默认禁用爆破
                
        if hasattr(args, 'cache_days'):
            Config.CACHE_EXPIRE_DAYS = args.cache_days
            
        return args

    @staticmethod
    async def execute_alive(args) -> None:
        """执行测活命令"""
        logger = Logger(args.debug)
        
        # 初始化文件路径
        Config.init_file_paths(args.domain)
        
        # 创建测活处理器
        alive_handler = AliveHandler(logger, args.domain, getattr(args, 'no_cache', False))
        
        domains = set()
        
        # 如果提供了输入文件，从文件读取域名
        if hasattr(args, 'input_file') and args.input_file:
            try:
                with open(args.input_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        domain = line.strip()
                        if domain:
                            domains.add(domain)
                logger.info(f"从文件 {args.input_file} 读取到 {len(domains)} 个域名")
            except Exception as e:
                logger.error(f"读取文件 {args.input_file} 失败: {str(e)}")
                return
        else:
            # 从隐藏域名文件和普通域名文件读取域名
            hidden_domains = set()
            normal_domains = set()
            
            # 读取隐藏域名
            if os.path.exists(args.hidden_file):
                try:
                    with open(args.hidden_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            domain = line.strip()
                            if domain:
                                hidden_domains.add(domain)
                    logger.info(f"从文件 {args.hidden_file} 读取到 {len(hidden_domains)} 个隐藏域名")
                except Exception as e:
                    logger.error(f"读取文件 {args.hidden_file} 失败: {str(e)}")
            
            # 读取普通域名
            if os.path.exists(args.normal_file):
                try:
                    with open(args.normal_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            domain = line.strip()
                            if domain:
                                normal_domains.add(domain)
                    logger.info(f"从文件 {args.normal_file} 读取到 {len(normal_domains)} 个普通域名")
                except Exception as e:
                    logger.error(f"读取文件 {args.normal_file} 失败: {str(e)}")
            
            # 如果两个文件都存在，则分别测活
            if hidden_domains and normal_domains:
                await alive_handler.handle_all_domains(hidden_domains, normal_domains)
                return
            
            # 合并域名
            domains = hidden_domains.union(normal_domains)
        
        # 如果有域名，则测活
        if domains:
            await alive_handler.handle_async(domains)
        else:
            logger.error(f"没有找到需要测活的域名")
    
    @staticmethod
    async def execute_collect(args) -> Dict[str, Set[str]]:
        """执行标准收集命令"""
        collector = SubdomainCollector(
            args.domain, 
            debug=args.debug, 
            output_file=args.output,
            disable_cache=getattr(args, 'no_cache', False),
            disable_brute=getattr(args, 'no_brute', True)
        )
        return await collector.run()
        
    @staticmethod
    async def execute_fofa(args) -> Set[str]:
        """执行FOFA收集命令"""
        collector = FofaSubdomainCollector(
            args.domain,
            debug=args.debug,
            api_key=args.key,
            output_file=args.output
        )
        return await collector.run()
        
    @staticmethod
    async def execute_compare(args) -> Dict[str, Set[str]]:
        """执行域名比较命令"""
        logger = Logger(args.debug)
        
        # 如果是从execute_all调用，则已经有正确的文件路径
        if hasattr(args, 'from_all') and args.from_all:
            logger.debug(f"从完整流程调用，使用传入的文件路径")
        else:
            # 如果使用命令行参数提供的文件路径，则不初始化文件路径
            # 这样可以使用已有的文件进行比较
            if args.deep_file != Config.DEFAULT_OUTPUT_FILE or args.fofa_file != Config.FOFA_OUTPUT_FILE:
                logger.debug(f"使用指定的文件路径进行比较")
            else:
                # 如果没有指定文件路径，则初始化新的文件路径
                timestamp = datetime.datetime.now().strftime(Config.TIMESTAMP_FORMAT)
                Config.init_file_paths(args.domain, timestamp)
                args.deep_file = Config.DEFAULT_OUTPUT_FILE
                args.fofa_file = Config.FOFA_OUTPUT_FILE
                args.brute_file = Config.BRUTE_OUTPUT_FILE
                args.result = Config.RESULT_OUTPUT_FILE
                args.total = Config.TOTAL_OUTPUT_FILE
        
        # 确保结果文件和总资产文件路径正确
        if not args.result:
            # 使用与deep_file相同的时间戳格式
            timestamp = datetime.datetime.now().strftime(Config.TIMESTAMP_FORMAT)
            if '\\' in args.deep_file:
                args.result = f"output\\hidden_{args.domain}_{timestamp}.txt"
            else:
                args.result = f"output/hidden_{args.domain}_{timestamp}.txt"
            logger.debug(f"使用生成的隐藏域名结果文件路径: {args.result}")
            
        if not args.total:
            timestamp = datetime.datetime.now().strftime(Config.TIMESTAMP_FORMAT)
            if '\\' in args.deep_file:
                args.total = f"output\\total_{args.domain}_{timestamp}.txt"
            else:
                args.total = f"output/total_{args.domain}_{timestamp}.txt"
            logger.debug(f"使用生成的总资产文件路径: {args.total}")
            
        # 确保输出目录存在
        os.makedirs(os.path.dirname(args.result), exist_ok=True)
        os.makedirs(os.path.dirname(args.total), exist_ok=True)
        
        # 确保爆破文件路径不为None
        if not args.brute_file:
            args.brute_file = ""
            
        comparator = ComparisonHandler(
            logger,
            args.fofa_file,
            args.deep_file,
            args.result,
            args.brute_file,
            args.total
        )
        
        compare_results = comparator.compare_domains()
        
        # 如果启用了测活，则对比较结果进行测活
        if getattr(args, 'alive', False):
            logger.info(f"开始测活...")
            domain_comparator = DomainComparator(
                args.domain,
                debug=args.debug,
                disable_cache=getattr(args, 'no_cache', False)
            )
            alive_results = await domain_comparator.check_alive(compare_results)
            # 合并结果
            compare_results.update(alive_results)
        
        return compare_results
    
    @staticmethod
    async def execute_brute(args) -> Set[str]:
        """执行字典爆破命令"""
        bruter = DictBruteForcer(
            args.domain,
            debug=args.debug
        )
        result_domains = await bruter.run()
        
        if result_domains:
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    for domain in sorted(result_domains):
                        f.write(f"{domain}\n")
                print(f"\n结果已保存到 {args.output}")
            except Exception as e:
                print(f"保存结果时出错: {str(e)}")
                
        return result_domains
        
    @staticmethod
    async def execute_all(args) -> None:
        """执行完整流程命令"""
        logger = Logger(args.debug)
        
        # 初始化文件路径，使用相同的时间戳
        timestamp = datetime.datetime.now().strftime(Config.TIMESTAMP_FORMAT)
        Config.init_file_paths(args.domain, timestamp)
        
        # 记录当前使用的文件路径
        deep_file = Config.DEFAULT_OUTPUT_FILE
        fofa_file = Config.FOFA_OUTPUT_FILE
        brute_file = Config.BRUTE_OUTPUT_FILE
        result_file = Config.RESULT_OUTPUT_FILE
        total_file = Config.TOTAL_OUTPUT_FILE
        
        logger.debug(f"初始化文件路径，使用时间戳: {timestamp}")
        logger.debug(f"深度收集文件: {deep_file}")
        logger.debug(f"FOFA收集文件: {fofa_file}")
        logger.debug(f"爆破结果文件: {brute_file}")
        logger.debug(f"隐藏域名文件: {result_file}")
        logger.debug(f"总资产文件: {total_file}")
        
        # 1. 执行隐藏资产收集（包括缓存检查和字典爆破）
        logger.info(f"开始执行完整流程: {args.domain}")
        collector = SubdomainCollector(
            args.domain, 
            debug=args.debug,
            output_file=deep_file,
            disable_cache=getattr(args, 'no_cache', False),
            disable_brute=getattr(args, 'no_brute', True)
        )
        deep_results = await collector.run()
        
        # 2. 执行FOFA收集
        fofa_collector = FofaSubdomainCollector(
            args.domain,
            debug=args.debug,
            api_key=args.key,
            output_file=fofa_file
        )
        fofa_domains = await fofa_collector.run()
        
        # 更新结果字典
        deep_results['fofa'] = fofa_domains
        
        # 4. 执行后处理（缓存写入和字典更新）
        processor = DomainProcessor(
            args.domain,
            debug=args.debug
        )
        processor.run(deep_results['deep'], fofa_domains)
        
        # 3. 执行比较分析 (在处理完成后进行比较)
        logger.info(f"开始比较分析结果...")
        
        # 创建一个临时参数对象，用于传递给execute_compare
        class TempArgs:
            pass
            
        temp_args = TempArgs()
        temp_args.domain = args.domain
        temp_args.debug = args.debug
        temp_args.deep_file = deep_file
        temp_args.fofa_file = fofa_file
        temp_args.brute_file = brute_file or ""
        temp_args.result = result_file
        temp_args.total = total_file
        temp_args.from_all = True  # 标记为从完整流程调用
        temp_args.no_cache = getattr(args, 'no_cache', False)
        
        # 执行比较
        compare_results = await CLI.execute_compare(temp_args)
        
        # 5. 执行测活 (除非明确禁用)
        if not getattr(args, 'no_alive', False):
            logger.info(f"开始测试域名存活性...")
            domain_comparator = DomainComparator(
                args.domain,
                debug=args.debug,
                disable_cache=getattr(args, 'no_cache', False)
            )
            await domain_comparator.check_alive(compare_results)
        
        logger.success(f"完整流程执行完成: {args.domain}")
        
    async def run(self) -> None:
        args = self.parse_args()
        
        if args.command == "collect":
            await self.execute_collect(args)
        elif args.command == "fofa":
            await self.execute_fofa(args)
        elif args.command == "compare":
            await self.execute_compare(args)
        elif args.command == "brute":
            await self.execute_brute(args)
        elif args.command == "alive":
            await self.execute_alive(args)
        elif args.command == "all":
            await self.execute_all(args)


def main():
    cli = CLI()
    
    # Windows的事件循环策略已在DeepX.py中设置
    
    # 创建新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # 运行CLI
        loop.run_until_complete(cli.run())
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {str(e)}")
    finally:
        # 关闭所有未完成的任务
        try:
            # 获取所有正在运行的任务
            pending = asyncio.all_tasks(loop)
            
            # 取消所有任务
            if pending:
                for task in pending:
                    task.cancel()
                
                # 等待任务取消完成
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            
            # 关闭事件循环
            loop.run_until_complete(loop.shutdown_asyncgens())
            if hasattr(loop, 'shutdown_default_executor'):
                loop.run_until_complete(loop.shutdown_default_executor())
        except Exception as e:
            print(f"关闭事件循环时出错: {str(e)}")
        finally:
            # 关闭事件循环
            loop.close()


if __name__ == "__main__":
    main() 