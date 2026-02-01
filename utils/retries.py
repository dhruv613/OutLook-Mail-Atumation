import time
import functools
from utils.logger import logger

def retry(exceptions, tries=3, delay=1, backoff=2):
    """
    Retry decorator with exponential backoff.
    
    :param exceptions: Tuple of exceptions to catch and retry on.
    :param tries: Total number of tries.
    :param delay: Initial delay between retries in seconds.
    :param backoff: Backoff multiplier.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger.warning(f"⚠️ Error in {func.__name__}: {e}. Retrying in {mdelay}s...")
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return func(*args, **kwargs)
        return wrapper
    return decorator
