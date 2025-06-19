"""
命令行界面模块，处理命令行参数和用户交互
"""

import argparse
import asyncio
import sys
import os

from config.config import Config
from core import SubdomainCollector, FofaSubdomainCollector, DomainComparator, DictBruteForcer


class CLI:
    """命令行界面类"""
    
    @staticmethod
    def parse_args():
        """
        解析命令行参数
        
        Returns:
            argparse.Namespace: 解析后的参数
        """
        parser = argparse.ArgumentParser(description="DeepX - 多接口集成的子域名收集工具")
        
        # 添加子命令解析器
        subparsers = parser.add_subparsers(dest="command", help="命令")
        
        # 标准收集子命令
        collect_parser = subparsers.add_parser("collect", help="使用传统接口收集子域名")
        collect_parser.add_argument("domain", help="目标域名 (例如: example.com)")
        collect_parser.add_argument("-d", "--debug", action="store_true", default=True, 
                                  help="启用调试输出 (默认已启用)")
        collect_parser.add_argument("--no-debug", action="store_false", dest="debug",
                                  help="禁用调试输出")
        collect_parser.add_argument("-o", "--output", default=Config.DEFAULT_OUTPUT_FILE, 
                                  help="输出文件名 (默认: deep_subdomain.txt)")
        collect_parser.add_argument("--collectors", nargs="+", choices=["otx", "crt", "archive"], 
                                  help="指定要使用的收集器 (默认全部使用)")
        # 添加缓存相关参数
        collect_parser.add_argument("--no-cache", action="store_true",
                                 help="禁用域名缓存")
        collect_parser.add_argument("--cache-days", type=int, default=Config.CACHE_EXPIRE_DAYS,
                                  help=f"缓存有效期（天）(默认: {Config.CACHE_EXPIRE_DAYS}天)")
        # 添加爆破相关参数
        collect_parser.add_argument("--no-brute", action="store_true",
                                 help="禁用字典爆破")
        
        # FOFA收集子命令
        fofa_parser = subparsers.add_parser("fofa", help="使用FOFA API收集子域名")
        fofa_parser.add_argument("domain", help="目标域名 (例如: example.com)")
        fofa_parser.add_argument("-d", "--debug", action="store_true", default=True,
                               help="启用调试输出 (默认已启用)")
        fofa_parser.add_argument("--no-debug", action="store_false", dest="debug",
                               help="禁用调试输出")
        fofa_parser.add_argument("-o", "--output", default=Config.FOFA_OUTPUT_FILE,
                               help=f"输出文件名 (默认: {Config.FOFA_OUTPUT_FILE})")
        fofa_parser.add_argument("--key", help="FOFA API密钥 (优先于配置文件)")
        
        # 比较子命令
        compare_parser = subparsers.add_parser("compare", help="比较不同来源的域名结果，找出隐藏域名")
        compare_parser.add_argument("domain", help="目标域名 (仅用于日志显示)")
        compare_parser.add_argument("-d", "--debug", action="store_true", default=True,
                                  help="启用调试输出 (默认已启用)")
        compare_parser.add_argument("--deep-file", default=Config.DEFAULT_OUTPUT_FILE,
                                  help=f"DeepX结果文件 (默认: {Config.DEFAULT_OUTPUT_FILE})")
        compare_parser.add_argument("--fofa-file", default=Config.FOFA_OUTPUT_FILE,
                                  help=f"FOFA结果文件 (默认: {Config.FOFA_OUTPUT_FILE})")
        compare_parser.add_argument("-r", "--result", default=Config.RESULT_OUTPUT_FILE,
                                  help=f"隐藏域名结果文件 (默认: {Config.RESULT_OUTPUT_FILE})")
        
        # 字典爆破子命令
        brute_parser = subparsers.add_parser("brute", help="使用累积的字典对子域名进行爆破")
        brute_parser.add_argument("domain", help="目标域名 (例如: example.com)")
        brute_parser.add_argument("-d", "--debug", action="store_true", default=True,
                               help="启用调试输出 (默认已启用)")
        brute_parser.add_argument("--no-debug", action="store_false", dest="debug",
                               help="禁用调试输出")
        brute_parser.add_argument("-o", "--output", default="brute_results.txt",
                               help="输出文件名 (默认: brute_results.txt)")
        
        # 全模式 - 依次执行收集、FOFA和比较
        all_parser = subparsers.add_parser("all", help="执行完整流程：收集、FOFA和比较")
        all_parser.add_argument("domain", help="目标域名 (例如: example.com)")
        all_parser.add_argument("-d", "--debug", action="store_true", default=True,
                              help="启用调试输出 (默认已启用)")
        all_parser.add_argument("--no-debug", action="store_false", dest="debug",
                              help="禁用调试输出")
        all_parser.add_argument("--key", help="FOFA API密钥 (优先于配置文件)")
        # 添加缓存相关参数
        all_parser.add_argument("--no-cache", action="store_true",
                             help="禁用域名缓存")
        all_parser.add_argument("--no-brute", action="store_true",
                             help="禁用字典爆破")
        
        args = parser.parse_args()
        
        # 处理无参数情况 - 如果只输入deepx，需要显示帮助信息
        if len(sys.argv) == 1:
            parser.print_help()
            sys.exit(0)
            
        # 如果未指定子命令但有域名参数，默认为collect
        if args.command is None and len(sys.argv) > 1:
            # 检查是否第一个参数像是域名
            potential_domain = sys.argv[1]
            if "." in potential_domain and not potential_domain.startswith("-"):
                args.command = "collect"
                args.domain = potential_domain
                args.debug = True
                args.output = Config.DEFAULT_OUTPUT_FILE
                args.collectors = None
                args.no_cache = False
                args.no_brute = False
                
        # 应用缓存天数设置
        if hasattr(args, 'cache_days'):
            Config.CACHE_EXPIRE_DAYS = args.cache_days
            
        return args
    
    @staticmethod
    async def execute_collect(args) -> None:
        """执行标准收集命令"""
        collector = SubdomainCollector(
            args.domain, 
            debug=args.debug, 
            output_file=args.output,
            disable_cache=getattr(args, 'no_cache', False),
            disable_brute=getattr(args, 'no_brute', False)
        )
        await collector.run()
        
    @staticmethod
    async def execute_fofa(args) -> None:
        """执行FOFA收集命令"""
        collector = FofaSubdomainCollector(
            args.domain,
            debug=args.debug,
            api_key=args.key,
            output_file=args.output
        )
        await collector.run()
        
    @staticmethod
    def execute_compare(args) -> None:
        """执行域名比较命令"""
        comparator = DomainComparator(
            args.domain,
            debug=args.debug
        )
        comparator.run()
    
    @staticmethod
    async def execute_brute(args) -> None:
        """执行字典爆破命令"""
        bruter = DictBruteForcer(
            args.domain,
            debug=args.debug
        )
        result_domains = await bruter.run()
        
        # 保存结果到文件
        if result_domains:
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    for domain in sorted(result_domains):
                        f.write(f"{domain}\n")
                print(f"\n结果已保存到 {args.output}")
            except Exception as e:
                print(f"保存结果时出错: {str(e)}")
        
    @staticmethod
    async def execute_all(args) -> None:
        """执行完整流程命令"""
        # 1. 常规收集
        collector = SubdomainCollector(
            args.domain, 
            debug=args.debug,
            disable_cache=getattr(args, 'no_cache', False),
            disable_brute=getattr(args, 'no_brute', False)
        )
        await collector.run()
        
        # 2. FOFA收集
        fofa_collector = FofaSubdomainCollector(
            args.domain,
            debug=args.debug,
            api_key=args.key
        )
        await fofa_collector.run()
        
        # 3. 比较结果
        comparator = DomainComparator(
            args.domain,
            debug=args.debug
        )
        comparator.run()
        
    @staticmethod
    async def run() -> None:
        """运行命令行界面"""
        try:
            # 解析命令行参数
            args = CLI.parse_args()
            
            # 根据子命令执行相应操作
            if args.command == "collect":
                await CLI.execute_collect(args)
            elif args.command == "fofa":
                await CLI.execute_fofa(args)
            elif args.command == "compare":
                CLI.execute_compare(args)
            elif args.command == "brute":
                await CLI.execute_brute(args)
            elif args.command == "all":
                await CLI.execute_all(args)
            
        except KeyboardInterrupt:
            print("\n用户中断，退出程序")
            sys.exit(1)
        except Exception as e:
            print(f"出错: {str(e)}", file=sys.stderr)
            sys.exit(1)


def main():
    """主入口函数"""
    try:
        # 使用自定义事件循环策略，避免Windows上的ProactorEventLoop问题
        if sys.platform.startswith('win'):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        asyncio.run(CLI.run())
        
    # 捕获程序结束时可能出现的事件循环相关错误
    except RuntimeError as e:
        if "Event loop is closed" in str(e):
            # 忽略事件循环关闭的错误
            pass
        else:
            print(f"运行时错误: {str(e)}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main() 