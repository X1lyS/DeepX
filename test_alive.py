#!/usr/bin/env python3
"""
测活模块测试脚本
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import platform
import os
import sys
from utils.formatter import Colors

# 在Windows平台上配置事件循环策略
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

def get_status_color(status_code: int) -> str:
    """根据状态码获取颜色"""
    if 100 <= status_code < 200:  # 信息响应
        return Colors.INFO
    elif 200 <= status_code < 300:  # 成功响应
        return Colors.SUCCESS
    elif 300 <= status_code < 400:  # 重定向
        return Colors.WARNING
    elif 400 <= status_code < 500:  # 客户端错误
        return Colors.ERROR
    elif 500 <= status_code < 600:  # 服务器错误
        return Colors.CRITICAL
    else:
        return Colors.RESET

async def check_domain(domain):
    """检查单个域名是否存活"""
    print(f"测试域名: {domain}")
    url = f"https://{domain}"
    
    # 禁用DNS缓存，避免aiodns的问题
    connector = aiohttp.TCPConnector(ssl=False, use_dns_cache=False, limit=100)
    timeout = aiohttp.ClientTimeout(total=5)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
        "Connection": "keep-alive"
    }
    
    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout, headers=headers) as session:
            try:
                async with session.get(url, allow_redirects=True) as response:
                    status_code = response.status
                    status_color = get_status_color(status_code)
                    
                    content_type = response.headers.get('Content-Type', '')
                    content_length = int(response.headers.get('Content-Length', 0))
                    title = "N/A"
                    
                    if 'text/html' in content_type:
                        try:
                            text = await response.text(errors='ignore')
                            soup = BeautifulSoup(text, 'lxml')
                            title_tag = soup.find('title')
                            if title_tag:
                                title = title_tag.text.strip()
                            
                            if content_length == 0:
                                content_length = len(text)
                        except Exception as e:
                            print(f"提取标题时出错: {str(e)}")
                    
                    # 按照新格式输出
                    status_str = f"{status_color}[{status_code}]{Colors.RESET}"
                    title_str = f"[{title}]"
                    size_str = f"[{content_length}]"
                    print(f"{status_color}{url}{Colors.RESET} {status_str} {title_str} {size_str}")
                    
                    return True, status_code, title, content_length
            except Exception as e:
                print(f"{Colors.ERROR}{url} [失活]{Colors.RESET}")
                print(f"错误: {str(e)}")
                return False, None, None, None
    except Exception as e:
        print(f"{Colors.ERROR}{url} [失活]{Colors.RESET}")
        print(f"会话错误: {str(e)}")
        return False, None, None, None

async def main():
    """主函数"""
    # 从命令行参数或默认列表获取域名
    if len(sys.argv) > 1:
        domains = sys.argv[1:]
    else:
        domains = ["www.baidu.com", "www.github.com", "example1.notexistdomain12345.com"]
    
    print(f"开始测试 {len(domains)} 个域名...")
    
    # 创建任务
    tasks = []
    for domain in domains:
        task = asyncio.create_task(check_domain(domain))
        tasks.append(task)
    
    # 等待所有任务完成
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 处理结果
    alive_count = 0
    for result in results:
        if isinstance(result, tuple) and result[0]:
            alive_count += 1
    
    print(f"测试完成: 总计 {len(domains)} 个域名, 存活 {alive_count} 个, 不存活 {len(domains) - alive_count} 个")

if __name__ == "__main__":
    # 创建新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # 直接执行任务
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"错误: {str(e)}")
    finally:
        # 关闭事件循环
        loop.close() 