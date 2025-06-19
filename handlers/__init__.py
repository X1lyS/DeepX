"""
结果处理模块，负责处理收集到的子域名
"""

from handlers.base import ResultHandler
from handlers.console import ConsoleResultHandler
from handlers.file import FileResultHandler
from handlers.comparison import ComparisonHandler

__all__ = ['ResultHandler', 'ConsoleResultHandler', 'FileResultHandler', 'ComparisonHandler'] 