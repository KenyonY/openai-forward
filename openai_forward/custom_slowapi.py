import inspect
from typing import List

from slowapi.extension import Limit, LimitGroup, RateLimitItem
from slowapi.wrappers import parse_many


def __iter__(self):
    if callable(self._LimitGroup__limit_provider):
        if (
            "key"
            in inspect.signature(self._LimitGroup__limit_provider).parameters.keys()
        ):
            assert (
                "request" in inspect.signature(self.key_function).parameters.keys()
            ), f"Limit provider function {self.key_function.__name__} needs a `request` argument"
            if self.request is None:
                raise Exception("`request` object can't be None")
            limit_raw = self._LimitGroup__limit_provider(
                self.key_function(self.request)
            )
        else:
            limit_raw = self._LimitGroup__limit_provider
    else:
        limit_raw = self._LimitGroup__limit_provider
    if limit_raw.lower().startswith("inf"):
        # limit_items = [RateLimitItem(0, 0, "second")]
        limit_items = ['-.-']
        self.exempt_when = lambda: True
    else:
        limit_items: List[RateLimitItem] = parse_many(limit_raw)
    for limit in limit_items:
        yield Limit(
            limit,
            self.key_function,
            self._LimitGroup__scope,
            self.per_method,
            self.methods,
            self.error_message,
            self.exempt_when,
            self.cost,
            self.override_defaults,
        )


LimitGroup.__iter__ = __iter__
