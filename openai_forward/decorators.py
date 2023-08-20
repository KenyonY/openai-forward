import asyncio
import inspect
import time
from functools import wraps

from fastapi import Request


def retry(max_retries=3, delay=1, backoff=2, exceptions=(Exception,)):
    """
    Retry decorator.

    Parameters:
    - max_retries: Maximum number of retries.
    - delay: Initial delay in seconds.
    - backoff: Multiplier for delay after each retry.
    - exceptions: Exceptions to catch and retry on, as a tuple.

    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries >= max_retries:
                        raise
                    time.sleep(current_delay)
                    current_delay *= backoff

        return wrapper

    return decorator


def async_retry(max_retries=3, delay=1, backoff=2, exceptions=(Exception,)):
    """
    Retry decorator for asynchronous functions.

    Parameters:
    - max_retries: Maximum number of retries.
    - delay: Initial delay in seconds.
    - backoff: Multiplier for delay after each retry.
    - exceptions: Exceptions to catch and retry on, as a tuple.

    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            while retries < max_retries:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries >= max_retries:
                        raise
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

        return wrapper

    return decorator


def token_rate_limit_decorator(token_rate_limit: dict):
    def outer_wrapper(async_gen_func):
        async def inner_wrapper(*args, **kwargs):
            request: Request = kwargs.get('request')
            if not request:
                # Try to find the request argument by position
                func_argspec = inspect.getfullargspec(async_gen_func)
                request_index = func_argspec.args.index('request')
                request = args[request_index]

            route_path = f"{request.scope.get('root_path')}{request.scope.get('path')}"
            token_interval = token_rate_limit.get(route_path, 0)

            async_gen = async_gen_func(*args, **kwargs)

            start_time = time.perf_counter()
            async for value in async_gen:
                if token_interval > 0:
                    current_time = time.perf_counter()
                    delta = current_time - start_time
                    delay = token_interval - delta
                    if delay > 0:
                        await asyncio.sleep(delay)
                    start_time = time.perf_counter()
                yield value

        return inner_wrapper

    return outer_wrapper
