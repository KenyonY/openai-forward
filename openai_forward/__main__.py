import atexit
import datetime
import os
import pickle
import platform
import signal
import subprocess
from pathlib import Path

import fire
import uvicorn
import yaml


def save_yaml(path: Path, data: dict):
    with open(path, 'w') as f:
        yaml.dump(data, f)


class Cli:
    def serve(self, **kwargs):
        """ Local LLM server. """
        from openai_forward.config.settings import config
        import os

        serve_config = config['serve']
        backend = serve_config['backend']
        backend_config: dict = serve_config[backend]
        port = kwargs.get('port') or serve_config['port']
        port = str(port)

        os.environ.update({
            'PORT': port,
            'BACKEND': kwargs.get('backend') or serve_config['backend'],
            'MODEL_NAME_OR_PATH': kwargs.get('model_name_or_path') or serve_config['model_name_or_path'],
            'CALL_MODEL_NAME': kwargs.get('call_model_name') or serve_config['call_model_name'],
        })

        if backend == "transformers":
            os.environ.update({
                'MAX_CONCURRENT': kwargs.get('max_concurrent') or backend_config['max_concurrent'],
                'DEVICE': kwargs.get('device') or backend_config['device'],
                'TORCH_DTYPE': kwargs.get('dtype') or backend_config['dtype'],
                'ATTN_IMPL': kwargs.get('attn_impl') or backend_config['attn_impl'],
            })
        elif backend == "vllm":
            os.environ.update({
                'VLLM_MAX_MODEL_LEN': kwargs.get('max_model_len') or backend_config['max_model_len'],
                'VLLM_QUANTIZATION': kwargs.get('quantization') or backend_config.get('quantization') or '',
                'VLLM_ENABLE_PREFIX_CACHING': kwargs.get('enable_prefix_caching') or str(backend_config['enable_prefix_caching']),
                'VLLM_MAX_NUM_SEQS': kwargs.get('max_num_seqs') or backend_config['max_num_seqs'],
            })
        else:
            raise ValueError(f"Unknown backend: {backend}")

        uvicorn.run(
            app="openai_forward.model_serve.api.app:app",
            host="0.0.0.0",
            port=int(port),
            workers=1,
            app_dir="..",
        )

    def run_web(self, port=8001, openai_forward_host='localhost', wait=True):
        """
        Runs the web UI using the Streamlit server.

        Args:
            port (int): The port number on which to run the server.
            openai_forward_host (str): The host of the OpenAI Forward server.
            wait (bool): Whether to wait for the server to stop. Default is True.

        Returns:
            None
        """
        os.environ['OPENAI_FORWARD_HOST'] = openai_forward_host
        try:
            self._start_streamlit(port=port, wait=wait)
        except KeyboardInterrupt:
            ...
        except Exception:
            raise

    def run(self, port=8000, workers=1, webui=False, start_ui=True, ui_port=8001):
        """
        Runs the application using the Uvicorn server.

        Args:
            port (int): The port number on which to run the server.
            workers (int): The number of worker processes to run.
            webui (bool): Whether to run the web UI. Default is False.
            start_ui (bool): Whether to start the web UI.
            ui_port (int): The port number on which to run streamlit.

        Returns:
            None
        """

        if platform.system() == "Windows":
            os.environ["TZ"] = ""

        ssl_keyfile = os.environ.get("ssl_keyfile", None) or None
        ssl_certfile = os.environ.get("ssl_certfile", None) or None

        if not webui:
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
            import threading

            import zmq

            os.environ['OPENAI_FORWARD_WEBUI'] = 'true'

            context = zmq.Context()
            socket = context.socket(zmq.REP)
            restart_port = int(os.environ.get('WEBUI_RESTART_PORT', 15555))
            socket.bind(f"tcp://*:{restart_port}")
            log_socket = context.socket(zmq.ROUTER)
            log_port = int(os.environ.get("WEBUI_LOG_PORT", 15556))
            log_socket.bind(f"tcp://*:{log_port}")
            subscriber_info = {}

            def mq_worker(log_socket: zmq.Socket):

                while True:
                    identity, uid, message = log_socket.recv_multipart()
                    if uid == b"/subscribe":
                        subscriber_info[identity] = True
                        continue
                    else:
                        for subscriber, _ in subscriber_info.items():
                            log_socket.send_multipart([subscriber, uid, message])

            thread = threading.Thread(target=mq_worker, args=(log_socket,))
            thread.daemon = True
            thread.start()

            self._start_uvicorn(
                port=port,
                workers=workers,
                ssl_keyfile=ssl_keyfile,
                ssl_certfile=ssl_certfile,
            )

            if start_ui:
                self._start_streamlit(port=ui_port, wait=False)

            atexit.register(self._stop_uvicorn)

            while True:
                message = socket.recv()
                config_dict: dict = pickle.loads(message)
                config_path = Path("openai-forward-config.yaml")
                # backup
                time_str = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
                backup_path = Path(f"openai-forward-config.yaml.{time_str}.bak")
                if config_path.exists():
                    # rename openai-forward-config.yaml to openai-forward-config.yaml.bak
                    config_path.rename(backup_path)

                save_yaml(config_path, config_dict)

                self._restart_uvicorn(
                    port=port,
                    workers=workers,
                    ssl_keyfile=ssl_keyfile,
                    ssl_certfile=ssl_certfile,
                )
                socket.send(b"Restart success!")

    def _start_uvicorn(self, port, workers, app: str = 'openai_forward.app:app', ssl_keyfile=None, ssl_certfile=None):
        from openai_forward.helper import wait_for_serve_start

        self.uvicorn_proc = subprocess.Popen(
            [
                'uvicorn',
                app,
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
        suppress_exception = platform.system() == "Windows"
        wait_for_serve_start(
            f"http://localhost:{port}/healthz",
            timeout=10,
            suppress_exception=suppress_exception,
        )

    def _start_streamlit(self, port, wait=False):
        from openai_forward.helper import relp

        self.streamlit_proc = subprocess.Popen(
            [
                'streamlit',
                'run',
                f'{relp("webui/run.py")}',
                '--server.port',
                str(port),
                '--server.headless',
                'true',
                '--server.enableCORS',
                'true',
                '--server.runOnSave',
                'true',
                '--theme.base',
                'light',
                '--browser.gatherUsageStats',
                'false',
            ]
        )

        atexit.register(self._stop_streamlit)
        if wait:
            self.streamlit_proc.wait()

    def _restart_uvicorn(self, **kwargs):
        self._stop_uvicorn()
        self._start_uvicorn(**kwargs)

    def _stop_streamlit(self):
        self._stop(uvicorn=False)

    def _stop_uvicorn(self):
        self._stop(streamlit=False)

    def _stop(self, uvicorn=True, streamlit=True):
        if uvicorn and self.uvicorn_proc.poll() is None:
            self.uvicorn_proc.send_signal(signal.SIGINT)
            try:
                self.uvicorn_proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.uvicorn_proc.kill()
        if streamlit and self.streamlit_proc.poll() is None:
            self.streamlit_proc.send_signal(signal.SIGINT)
            try:
                self.streamlit_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.streamlit_proc.kill()

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
        from openai_forward.config.settings import OPENAI_ROUTE_PREFIX
        from openai_forward.helper import convert_folder_to_jsonl, route_prefix_to_str

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

    @staticmethod
    def gen_config(dir: str = "."):
        """
        Generates a .env file in the specified directory.
        """
        from pathlib import Path

        from openai_forward.config.interface import Config

        config = Config()
        env_dict = config.convert_to_env(set_env=False)
        dir = Path(dir)

        with open(dir / ".env", "w") as f:
            env_content = "\n".join(
                [f"{key}={value}" for key, value in env_dict.items()]
            )
            f.write(env_content)


def main():
    fire.Fire(Cli)
