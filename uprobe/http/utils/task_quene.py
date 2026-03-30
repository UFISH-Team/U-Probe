import asyncio
import multiprocessing
import os
import logging
from uprobe.http.utils.paths import get_config

log = logging.getLogger(__name__)

def _load_queue_config():
    config = get_config()
    
    # Default threads per task
    threads = 10
    if config.has_section("TaskQueue") and config.has_option("TaskQueue", "task_threads"):
        threads = config.getint("TaskQueue", "task_threads")
    
    # Allow environment variable override
    threads = int(os.getenv("UPROBE_TASK_THREADS", str(threads)))
    
    total_cores = multiprocessing.cpu_count()
    
    # Calculate max concurrent tasks to ensure at least 1 task runs
    max_tasks = max(1, total_cores // threads)
    
    if config.has_section("TaskQueue") and config.has_option("TaskQueue", "max_concurrent_tasks"):
        val = config.get("TaskQueue", "max_concurrent_tasks").strip().lower()
        if val != "auto":
            try:
                max_tasks = int(val)
            except ValueError:
                log.warning(f"Invalid max_concurrent_tasks value '{val}' in config, falling back to auto ({max_tasks})")
                
    return threads, max_tasks

TASK_THREADS, MAX_CONCURRENT_TASKS = _load_queue_config()

_task_semaphore = None

def get_task_semaphore() -> asyncio.Semaphore:
    """
    Get the global task concurrency semaphore.
    Must be initialized within an active asyncio event loop.
    """
    global _task_semaphore
    if _task_semaphore is None:
        log.info(f"Init task queue: total_cores={multiprocessing.cpu_count()}, threads_per_task={TASK_THREADS}, max_concurrent_tasks={MAX_CONCURRENT_TASKS}")
        _task_semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)
    return _task_semaphore
