import os

import fire
import uvicorn


class Cli:
    @staticmethod
    def run(
        port=8000,
        workers=1,
        api_key=None,
        forward_key=None,
        base_url=None,
        log_chat=None,
        route_prefix=None,
        ip_whitelist=None,
        ip_blacklist=None,
    ):
        """Run forwarding serve.

        Parameters
        ----------

        port: int, default 8000
        workers: int, 1
        api_key: str, None
        forward_key: str, None
        base_url: str, None
        log_chat: str, None
        route_prefix: str, None
        ip_whitelist: str, None
        ip_blacklist: str, None
        """
        if base_url:
            os.environ['OPENAI_BASE_URL'] = base_url
        if api_key:
            os.environ['OPENAI_API_KEY'] = api_key
        if forward_key:
            os.environ['FORWARD_KEY'] = forward_key
        if log_chat:
            os.environ['LOG_CHAT'] = log_chat
        if route_prefix:
            os.environ['ROUTE_PREFIX'] = route_prefix
        if ip_whitelist:
            os.environ['IP_WHITELIST'] = ip_whitelist
        if ip_blacklist:
            os.environ['IP_BLACKLIST'] = ip_blacklist

        ssl_keyfile = os.environ.get("ssl_keyfile", None) or None
        ssl_certfile = os.environ.get("ssl_certfile", None) or None
        uvicorn.run(
            app="openai_forward.app:app",
            host="0.0.0.0",
            port=port,
            workers=workers,
            app_dir='..',
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
        )


def main():
    fire.Fire(Cli)


if __name__ == "__main__":
    main()
