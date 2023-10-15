import asyncio
import inspect
import random
import time
from functools import wraps
from typing import Callable

from fastapi import Request
from loguru import logger


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
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries == max_retries:
                        raise
                    logger.warning(
                        f"Error:{type(e)}\n"
                        f"Retrying `{func.__name__}` after {current_delay} seconds, retry : {retries}\n"
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff

        return wrapper

    return decorator


def async_retry(
    max_retries=3,
    delay=1,
    backoff=2,
    exceptions=(Exception,),
    raise_callback_name=None,
    raise_handler_name=None,
):
    """
    An asynchronous decorator for automatically retrying an async function upon encountering specified exceptions.

    Args:
        max_retries (int): The maximum number of times to retry the function.
        delay (float): The initial delay between retries in seconds.
        backoff (float): The multiplier by which the delay should increase after each retry.
        exceptions (tuple): A tuple of exception classes upon which to retry.
        raise_callback_name (str): A callback function to call when the maximum number of retries is reached.
        raise_handler_name (str): A error handler function to call when the maximum number of retries is reached.

    Returns:
        The return value of the wrapped function, if it succeeds.
        Raises the last encountered exception if the function never succeeds.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            while retries <= max_retries:
                try:
                    result = await func(*args, **kwargs)
                    return result
                except exceptions as e:

                    if retries == max_retries:
                        # Experimental
                        if raise_callback_name:
                            self = args[0]
                            callback: Callable = getattr(
                                self, raise_callback_name, None
                            )
                            if callback:
                                logger.warning(
                                    f"Calling raise callback {raise_callback_name}"
                                )
                                if getattr(self, 'client', None):
                                    await self.client.close()
                                callback()
                        if raise_handler_name:
                            self = args[0]
                            raise_handler: Callable = getattr(
                                self, raise_handler_name, None
                            )
                            if raise_handler:
                                logger.warning(
                                    f"Calling raise handler {raise_handler_name}"
                                )
                                raise_handler(e)
                        raise

                    retries += 1
                    logger.warning(
                        f"Error:{type(e)}\n"
                        f"Retrying `{func.__name__}` after {current_delay} seconds, retry : {retries}\n"
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

        return wrapper

    return decorator


def async_token_rate_limit(token_rate_limit: dict):
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


def async_random_sleep(min_time=0, max_time=1):
    """
    Decorator that adds a random sleep time between min_time and max_time.

    Args:
        min_time (float, optional): The minimum sleep time in seconds.
        max_time (float, optional): The maximum sleep time in seconds.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if max_time == 0:
                return await func(*args, **kwargs)
            sleep_time = random.uniform(min_time, max_time)
            await asyncio.sleep(sleep_time)
            return await func(*args, **kwargs)

        return wrapper

    return decorator
