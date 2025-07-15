"""Progress tracking utilities"""

from typing import Optional, Callable, Any, Dict
from contextlib import contextmanager
from datetime import datetime, timedelta
import sys
import time
import logging

logger = logging.getLogger(__name__)

# Try to import rich for better progress display
try:
    from rich.progress import (
        Progress, SpinnerColumn, TextColumn, BarColumn, 
        TimeElapsedColumn, TimeRemainingColumn, MofNCompleteColumn
    )
    from rich.console import Console
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    logger.debug("Rich library not available, using simple progress display")


class ProgressTracker:
    """Progress tracking with fallback to simple display"""
    
    def __init__(self, use_rich: bool = True):
        """
        Initialize progress tracker
        
        Args:
            use_rich: Whether to use rich library if available
        """
        self.use_rich = use_rich and RICH_AVAILABLE
        
        if self.use_rich:
            self.console = Console()
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                console=self.console
            )
        else:
            self.tasks = {}
            self.start_times = {}
    
    @contextmanager
    def track_task(self, description: str, total: Optional[int] = None):
        """
        Context manager for tracking a task
        
        Args:
            description: Task description
            total: Total number of items (None for indeterminate)
            
        Yields:
            Update function that accepts (current, description)
        """
        if self.use_rich:
            with self.progress:
                task_id = self.progress.add_task(description, total=total)
                
                def update(current: int, description: Optional[str] = None):
                    updates = {'completed': current}
                    if description:
                        updates['description'] = description
                    self.progress.update(task_id, **updates)
                
                yield update
        else:
            # Simple progress tracking
            task_id = len(self.tasks)
            self.tasks[task_id] = {
                'description': description,
                'total': total,
                'current': 0
            }
            self.start_times[task_id] = time.time()
            
            def update(current: int, description: Optional[str] = None):
                self.tasks[task_id]['current'] = current
                if description:
                    self.tasks[task_id]['description'] = description
                self._print_simple_progress(task_id)
            
            yield update
            
            # Final update
            self._print_simple_progress(task_id, final=True)
    
    def _print_simple_progress(self, task_id: int, final: bool = False):
        """Print simple progress bar"""
        task = self.tasks[task_id]
        description = task['description']
        current = task['current']
        total = task['total']
        
        if total:
            # Calculate percentage
            percentage = (current / total) * 100
            
            # Calculate elapsed time
            elapsed = time.time() - self.start_times[task_id]
            
            # Estimate remaining time
            if current > 0:
                rate = current / elapsed
                remaining = (total - current) / rate if rate > 0 else 0
                remaining_str = str(timedelta(seconds=int(remaining)))
            else:
                remaining_str = "?"
            
            # Create progress bar
            bar_width = 30
            filled = int(bar_width * current / total)
            bar = '█' * filled + '░' * (bar_width - filled)
            
            # Print progress
            if final:
                print(f"\r{description}: [{bar}] {current}/{total} (100%) - {timedelta(seconds=int(elapsed))}")
            else:
                print(f"\r{description}: [{bar}] {current}/{total} ({percentage:.1f}%) - ETA: {remaining_str}", end='')
                sys.stdout.flush()
        else:
            # Indeterminate progress
            spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            spin_char = spinner[int(time.time() * 10) % len(spinner)]
            
            if final:
                print(f"\r{description}: ✓ Complete")
            else:
                print(f"\r{spin_char} {description}: {current} items processed", end='')
                sys.stdout.flush()
    
    def display_stats(self, stats: Dict[str, Any], title: str = "Processing Statistics"):
        """
        Display statistics table
        
        Args:
            stats: Dictionary of statistics
            title: Table title
        """
        if self.use_rich:
            table = Table(title=title)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            for key, value in stats.items():
                # Format value
                if isinstance(value, float):
                    value_str = f"{value:.2f}"
                elif isinstance(value, dict):
                    # Nested stats
                    value_str = "\n".join(f"{k}: {v}" for k, v in value.items())
                else:
                    value_str = str(value)
                
                table.add_row(key.replace('_', ' ').title(), value_str)
            
            self.console.print(table)
        else:
            # Simple display
            print(f"\n{title}")
            print("=" * len(title))
            
            for key, value in stats.items():
                key_display = key.replace('_', ' ').title()
                if isinstance(value, dict):
                    print(f"{key_display}:")
                    for k, v in value.items():
                        print(f"  {k}: {v}")
                else:
                    print(f"{key_display}: {value}")
            print()
    
    def log_info(self, message: str, style: str = "info"):
        """
        Log informational message
        
        Args:
            message: Message to log
            style: Message style (info, success, warning, error)
        """
        if self.use_rich:
            styles = {
                'info': 'blue',
                'success': 'green',
                'warning': 'yellow',
                'error': 'red'
            }
            self.console.print(message, style=styles.get(style, 'white'))
        else:
            prefixes = {
                'info': '[INFO]',
                'success': '[OK]',
                'warning': '[WARN]',
                'error': '[ERROR]'
            }
            print(f"{prefixes.get(style, '')} {message}")


class BatchProgressTracker:
    """Track progress across multiple batches"""
    
    def __init__(self, total_batches: int, items_per_batch: Optional[int] = None):
        """
        Initialize batch progress tracker
        
        Args:
            total_batches: Total number of batches
            items_per_batch: Items per batch (if known)
        """
        self.total_batches = total_batches
        self.items_per_batch = items_per_batch
        self.current_batch = 0
        self.current_items = 0
        self.total_items = 0
        self.start_time = time.time()
        
        self.tracker = ProgressTracker()
    
    def start_batch(self, batch_num: int, batch_size: int):
        """Start processing a new batch"""
        self.current_batch = batch_num
        self.current_items = 0
        
        description = f"Batch {batch_num}/{self.total_batches}"
        return self.tracker.track_task(description, batch_size)
    
    def update_totals(self, items_processed: int):
        """Update total items processed"""
        self.total_items += items_processed
    
    def get_summary(self) -> Dict[str, Any]:
        """Get processing summary"""
        elapsed = time.time() - self.start_time
        
        return {
            'batches_processed': self.current_batch,
            'total_batches': self.total_batches,
            'items_processed': self.total_items,
            'elapsed_time': elapsed,
            'avg_time_per_batch': elapsed / max(1, self.current_batch),
            'avg_time_per_item': elapsed / max(1, self.total_items)
        }