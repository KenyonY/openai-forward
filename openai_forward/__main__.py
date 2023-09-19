import os
import platform

import fire
import uvicorn


class Cli:
    @staticmethod
    def run(port=8000, workers=1):
        """
        Runs the application using the Uvicorn server.

        Args:
            port (int): The port number on which to run the server. Default is 8000.
            workers (int): The number of worker processes to run. Default is 1.

        Returns:
            None
        """

        if platform.system() == "Windows":
            os.environ["TZ"] = ""

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
        """
        Converts log files in a folder to a JSONL file.

        Args:
            log_folder (str, optional): The path to the folder containing the log files. Default is None.
            target_path (str, optional): The path to the target JSONL file. Default is None.

        Returns:
            None
        """
        from openai_forward.helper import convert_folder_to_jsonl
        from openai_forward.settings import OPENAI_ROUTE_PREFIX

        print(60 * '-')
        if log_folder is None:
            if target_path is not None:
                raise ValueError("target_path must be None when log_folder is None")
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
