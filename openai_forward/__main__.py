import atexit
import os
import pickle
import platform
import signal
import subprocess
import time

import fire
import uvicorn


class Cli:
    def run(self, port=8000, workers=1, webui='false', web_port=17860, mq_port=15555):
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

        if not webui.lower() == 'true':
            uvicorn.run(
                app="openai_forward.app:app",
                host="0.0.0.0",
                port=port,
                workers=workers,
                app_dir="..",
                ssl_keyfile=ssl_keyfile,
                ssl_certfile=ssl_certfile,
            )
        else:
            import zmq

            from openai_forward.web.interface import Config

            context = zmq.Context()
            socket = context.socket(
                zmq.REP
            )  # REP (REPLY) socket for request-reply pattern
            socket.bind(f"tcp://*:{mq_port}")

            self._start_uvicorn(
                port=port,
                workers=workers,
                ssl_keyfile=ssl_keyfile,
                ssl_certfile=ssl_certfile,
            )
            self._start_streamlit(port=web_port)
            atexit.register(self._stop)

            while True:
                message = socket.recv()
                env_dict: dict = pickle.loads(message)
                print(f"{env_dict=}")
                for key, value in env_dict.items():
                    os.environ[key] = value

                self._restart_uvicorn(
                    port=port,
                    workers=workers,
                    ssl_keyfile=ssl_keyfile,
                    ssl_certfile=ssl_certfile,
                )
                socket.send(f"Restart success!".encode())

    def _start_uvicorn(self, port, workers, ssl_keyfile=None, ssl_certfile=None):
        from openai_forward.helper import wait_for_serve_start

        self.uvicorn_proc = subprocess.Popen(
            [
                'uvicorn',
                'openai_forward.app:app',
                '--host',
                '0.0.0.0',
                '--port',
                str(port),
                '--app-dir',
                '..',
                '--workers',
                str(workers),
            ]
            + (['--ssl-keyfile', ssl_keyfile] if ssl_keyfile else [])
            + (['--ssl-certfile', ssl_certfile] if ssl_certfile else [])
        )
        wait_for_serve_start(f"http://localhost:{port}/healthz")

    def _start_streamlit(self, port):
        self.streamlit_proc = subprocess.Popen(
            [
                'streamlit',
                'run',
                'openai_forward/web/run.py',
                '--server.port',
                str(port),
            ]
        )

    def _restart_uvicorn(self, **kwargs):
        self._stop(streamlit=False)
        self._start_uvicorn(**kwargs)

    def _stop(self, uvicorn=True, streamlit=True):
        if uvicorn and self.uvicorn_proc.poll() is None:
            self.uvicorn_proc.send_signal(signal.SIGINT)
            self.uvicorn_proc.wait()
        if streamlit and self.streamlit_proc.poll() is None:
            self.streamlit_proc.send_signal(signal.SIGINT)
            self.streamlit_proc.wait()

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
        from openai_forward.helper import convert_folder_to_jsonl, route_prefix_to_str
        from openai_forward.settings import OPENAI_ROUTE_PREFIX

        print(60 * '-')
        if log_folder is None:
            if target_path is not None:
                raise ValueError("target_path must be None when log_folder is None")
            _prefix_list = [route_prefix_to_str(i) for i in OPENAI_ROUTE_PREFIX]
            for prefix in _prefix_list:
                log_folder = f"./Log/{prefix}/chat"
                target_path = f"./Log/chat_{prefix}.json"
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
