import fire
import uvicorn
import os


class Cli:
    @staticmethod
    def run(port=8000, workers=1):
        uvicorn.run(
            app="openai_forward.app:app",
            host="0.0.0.0",
            port=port,
            workers=workers,
            app_dir='..',
            ssl_keyfile=os.environ.get("ssl_keyfile", None),
            ssl_certfile=os.environ.get("ssl_certfile", None),
        )


def main():
    fire.Fire(Cli)
