from concurrent.futures import ProcessPoolExecutor
import atexit
import logging
from uprobe.http.utils.task_queue import MAX_CONCURRENT_TASKS

log = logging.getLogger(__name__)
_pool = None

def get_process_pool() -> ProcessPoolExecutor:
    global _pool
    if _pool is None:
        log.info(f"Init process pool for workflows: max_workers={MAX_CONCURRENT_TASKS}")
        _pool = ProcessPoolExecutor(max_workers=MAX_CONCURRENT_TASKS)
        atexit.register(_shutdown_pool)
    return _pool

def _shutdown_pool():
    global _pool
    if _pool is not None:
        try:
            _pool.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
        _pool = None

