import os

import fire
import uvicorn


class Cli:
    @staticmethod
    def run(
        port=8000,
        workers=1,
        log_chat=None,
        api_key=None,
        forward_key=None,
        openai_base_url=None,
        openai_route_prefix=None,
        extra_base_url=None,
        extra_route_prefix=None,
        rate_limit=None,
        global_rate_limit=None,
        rate_limit_strategy=None,
        token_rate_limit=None,
        ip_whitelist=None,
        ip_blacklist=None,
        proxy=None,
    ):
        """Run forwarding serve.

        Parameters
        ----------

        port: int, default 8000
        workers: int, 1
        log_chat: str, None
        api_key: str, None
        forward_key: str, None
        openai_base_url: str, None
        openai_route_prefix: str, None
        extra_base_url: str, None
        extra_route_prefix: str, None
        ip_whitelist: str, None
        ip_blacklist: str, None
        """

        if log_chat:
            os.environ["LOG_CHAT"] = log_chat
        if openai_base_url:
            os.environ["OPENAI_BASE_URL"] = openai_base_url
        if openai_route_prefix:
            os.environ["OPENAI_ROUTE_PREFIX"] = openai_route_prefix
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        if extra_base_url:
            os.environ["EXTRA_BASE_URL"] = extra_base_url
        if extra_route_prefix:
            os.environ["EXTRA_ROUTE_PREFIX"] = extra_route_prefix
        if forward_key:
            os.environ["FORWARD_KEY"] = forward_key
        if rate_limit:
            import json

            assert isinstance(rate_limit, dict)
            os.environ["RATE_LIMIT"] = json.dumps(rate_limit)
        if global_rate_limit:
            os.environ["GLOBAL_RATE_LIMIT"] = global_rate_limit
        if rate_limit_strategy:
            os.environ["RATE_LIMIT_STRATEGY"] = rate_limit_strategy
        if token_rate_limit:
            os.environ["TOKEN_RATE_LIMIT"] = token_rate_limit
        if ip_whitelist:
            os.environ["IP_WHITELIST"] = ip_whitelist
        if ip_blacklist:
            os.environ["IP_BLACKLIST"] = ip_blacklist
        if proxy:
            os.environ["PROXY"] = proxy

        ssl_keyfile = os.environ.get("ssl_keyfile", None) or None
        ssl_certfile = os.environ.get("ssl_certfile", None) or None
        uvicorn.run(
            app="openai_forward.app:app",
            host="0.0.0.0",
            port=port,
            workers=workers,
            app_dir="..",
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
        )

    @staticmethod
    def convert(log_folder: str = None, target_path: str = None):
        """Convert log folder to jsonl file"""
        from openai_forward.forwarding.settings import OPENAI_ROUTE_PREFIX
        from openai_forward.helper import convert_folder_to_jsonl

        print(60 * '-')
        if log_folder is None:
            _prefix_list = [i.replace("/", "_") for i in OPENAI_ROUTE_PREFIX]
            for _prefix in _prefix_list:
                log_folder = f"./Log/chat/{_prefix}"
                target_path = f"./Log/chat{_prefix}.json"
                print(f"Convert {log_folder}/*.log to {target_path}")
                convert_folder_to_jsonl(log_folder, target_path)
                print(60 * '-')
        else:
            print(f"Convert {log_folder}/*.log to {target_path}")
            convert_folder_to_jsonl(log_folder, target_path)
            print(60 * '-')


def main():
    fire.Fire(Cli)


if __name__ == "__main__":
    main()
