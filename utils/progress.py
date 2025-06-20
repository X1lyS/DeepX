"""
进度条模块，用于显示各种任务的进度
"""

import sys
import time
from typing import Optional, Callable

from utils.formatter import Colors


class ProgressBar:
    """简单的命令行进度条"""
    
    def __init__(self, total: int, description: str = "", bar_length: int = 50):
        """
        初始化进度条
        
        Args:
            total: 总任务数
            description: 进度条描述
            bar_length: 进度条长度
        """
        self.total = max(1, total)  # 避免除0错误
        self.description = description
        self.bar_length = bar_length
        self.start_time = None
        self.current = 0
        self.last_update_time = 0
        self.update_interval = 0.1  # 更新间隔，秒
    
    def start(self) -> None:
        """开始进度条"""
        self.start_time = time.time()
        self.current = 0
        self._update_progress(0)
    
    def update(self, current: int) -> None:
        """
        更新进度条
        
        Args:
            current: 当前完成的任务数
        """
        self.current = min(current, self.total)
        
        # 限制更新频率，避免刷新太快
        current_time = time.time()
        if current_time - self.last_update_time < self.update_interval and self.current < self.total:
            return
            
        self.last_update_time = current_time
        self._update_progress(self.current)
    
    def finish(self) -> None:
        """完成进度条"""
        self._update_progress(self.total)
        print()  # 添加一个换行
    
    def increment(self, step: int = 1) -> None:
        """
        增加进度
        
        Args:
            step: 增加的步数
        """
        self.update(self.current + step)
    
    def _update_progress(self, current: int) -> None:
        """
        实际更新进度条显示
        
        Args:
            current: 当前任务数
        """
        percent = min(100, int(current / self.total * 100))
        filled_length = int(self.bar_length * current // self.total)
        bar = f"{Colors.SUCCESS}{'█' * filled_length}{Colors.DIM}{'-' * (self.bar_length - filled_length)}{Colors.RESET}"
        
        # 计算已用时间
        elapsed = time.time() - self.start_time if self.start_time else 0
        elapsed_str = f"{int(elapsed)}s" if elapsed < 60 else f"{int(elapsed / 60)}m {int(elapsed % 60)}s"
        
        # 计算剩余时间
        if current > 0:
            avg_time_per_task = elapsed / current
            remaining_tasks = self.total - current
            estimated_remaining = avg_time_per_task * remaining_tasks
            remaining_str = f"{int(estimated_remaining)}s" if estimated_remaining < 60 else f"{int(estimated_remaining / 60)}m {int(estimated_remaining % 60)}s"
        else:
            remaining_str = "计算中..."
            
        # 构建进度信息
        if self.description:
            progress_str = f"\r{self.description}: {Colors.BRIGHT}[{bar}] {percent}%{Colors.RESET} ({current}/{self.total}) 用时: {elapsed_str} 剩余: {remaining_str}"
        else:
            progress_str = f"\r{Colors.BRIGHT}[{bar}] {percent}%{Colors.RESET} ({current}/{self.total}) 用时: {elapsed_str} 剩余: {remaining_str}"
            
        # 确保进度条不超过终端宽度
        term_width = 120  # 假设终端宽度为120
        if len(progress_str) > term_width:
            # 保留最重要的部分，截断中间部分
            progress_str = progress_str[:term_width-3] + "..."
            
        sys.stdout.write(progress_str)
        sys.stdout.flush()


class TaskProgress:
    """任务进度追踪器，支持嵌套任务"""
    
    def __init__(self, total_tasks: int, description: str = ""):
        """
        初始化任务进度追踪器
        
        Args:
            total_tasks: 总任务数
            description: 任务描述
        """
        self.total_tasks = total_tasks
        self.description = description
        self.completed_tasks = 0
        self.progress_bar = ProgressBar(total_tasks, description)
        self.start_time = None
        self.subtasks = []
    
    def start(self) -> None:
        """开始任务进度追踪"""
        self.start_time = time.time()
        self.progress_bar.start()
    
    def update(self, completed: int) -> None:
        """
        更新任务完成数
        
        Args:
            completed: 已完成的任务数
        """
        self.completed_tasks = min(completed, self.total_tasks)
        self.progress_bar.update(self.completed_tasks)
    
    def increment(self, step: int = 1) -> None:
        """
        增加完成的任务数
        
        Args:
            step: 增加的任务数
        """
        self.update(self.completed_tasks + step)
    
    def add_subtask(self, subtask_weight: float = 1.0) -> 'SubTaskProgress':
        """
        添加子任务
        
        Args:
            subtask_weight: 子任务权重
            
        Returns:
            SubTaskProgress: 子任务进度追踪器
        """
        subtask = SubTaskProgress(self, subtask_weight)
        self.subtasks.append(subtask)
        return subtask
    
    def finish(self) -> None:
        """完成任务"""
        self.progress_bar.finish()


class SubTaskProgress:
    """子任务进度追踪器"""
    
    def __init__(self, parent: TaskProgress, weight: float = 1.0):
        """
        初始化子任务进度追踪器
        
        Args:
            parent: 父任务
            weight: 任务权重
        """
        self.parent = parent
        self.weight = weight
        self.progress = 0.0
    
    def update(self, progress: float) -> None:
        """
        更新进度
        
        Args:
            progress: 当前进度 (0.0-1.0)
        """
        self.progress = min(1.0, max(0.0, progress))
        # 更新父任务进度
        total_weight = sum(subtask.weight for subtask in self.parent.subtasks)
        if total_weight > 0:
            weighted_progress = sum(subtask.progress * (subtask.weight / total_weight) 
                                   for subtask in self.parent.subtasks)
            self.parent.update(int(weighted_progress * self.parent.total_tasks))
    
    def increment(self, step: float) -> None:
        """
        增加进度
        
        Args:
            step: 增加的进度 (0.0-1.0)
        """
        self.update(self.progress + step) 