import fire
import uvicorn


class Cli:
    def run(self, port=8000, workers=1):
        uvicorn.run(
            app="openai_forward.app:app",
            host="0.0.0.0",
            port=port,
            workers=workers,
            app_dir='..'
        )

def main():
    fire.Fire(Cli)
