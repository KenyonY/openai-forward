import asyncio
import inspect
import time
from functools import wraps

from fastapi import Request


def retry(max_retries=3, delay=1, backoff=2, exceptions=(Exception,)):
    """
    A decorator for automatically retrying a function upon encountering specified exceptions.

    Args:
        max_retries (int): The maximum number of times to retry the function.
        delay (float): The initial delay between retries in seconds.
        backoff (float): The multiplier by which the delay should increase after each retry.
        exceptions (tuple): A tuple of exception classes upon which to retry.

    Returns:
        The return value of the wrapped function, if it succeeds.
        Raises the last encountered exception if the function never succeeds.
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
    An asynchronous decorator for automatically retrying an async function upon encountering specified exceptions.

    Args:
        max_retries (int): The maximum number of times to retry the function.
        delay (float): The initial delay between retries in seconds.
        backoff (float): The multiplier by which the delay should increase after each retry.
        exceptions (tuple): A tuple of exception classes upon which to retry.

    Returns:
        The return value of the wrapped function, if it succeeds.
        Raises the last encountered exception if the function never succeeds.
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
    """
    A decorator for rate-limiting requests based on tokens. It limits the rate at which tokens can be consumed
    for a particular route path.

    Args:
        token_rate_limit (dict): A dictionary mapping route paths to their respective token intervals (in seconds).

    Yields:
        value: The value from the wrapped asynchronous generator.

    Note:
        The 'request' object should be passed either as a keyword argument or as a positional argument to the
        decorated function.
    """

    def decorator(async_gen_func):
        @wraps(async_gen_func)
        async def wrapper(*args, **kwargs):
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

        return wrapper

    return decorator
