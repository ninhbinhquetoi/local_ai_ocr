# src/ollama_service.py
# Provides functions to communicate with Ollama server.

from ollama import Client
from PySide6.QtCore import QThread, Signal
import httpx
import config


def stream_ocr_response(client: Client, model_name: str, prompt: str, image_bytes: bytes, options: dict = None):
    stream = client.chat(
        model=model_name,
        messages=[{
            'role': 'user',
            'content': prompt,
            'images': [image_bytes]  # Pass image as raw bytes
        }],
        options=options,
        stream=True  # Enable streaming - yields chunks instead of blocking
    )

    for chunk in stream:
        # Navigate the nested response structure to extract text
        content = chunk.get('message', {}).get('content', '')
        if content:
            yield content


def check_connection(client: Client) -> tuple[bool, str | None]:
    try:
        client.ps() # Quick API call to test connection
        return (True, None)
    except (ConnectionError, httpx.ConnectError, httpx.ConnectTimeout) as e:
        return (False, str(e))

def check_model_installed(client: Client, model_name: str) -> tuple[bool, str | None]:
    # Must be called after check_connection(), so connection is already verified.
    response = client.list()
    # Handle both object and dict response formats
    if hasattr(response, 'models'):
        models = response.models
    else:
        models = response.get('models', [])

    for m in models:
        name = m.model if hasattr(m, 'model') else m.get('model', '')
        if name == model_name:
            return (True, None)

    return (False, f"check_model_installed(): Model '{model_name}' is not installed")


class PreCheckWorker(QThread):
    # Background thread to check connection and model before processing.
    # Emits (success, error_type, error_msg)
    # error_type: 'connection', 'model', or None if success
    finished = Signal(bool, str, str)

    def __init__(self, client, model_name):
        super().__init__()
        self.client = client
        self.model_name = model_name

    def run(self):
        # Check connection
        success, error_msg = check_connection(self.client)
        if not success:
            self.finished.emit(False, 'connection', error_msg)
            return

        # Check model
        success, error_msg = check_model_installed(self.client, self.model_name)
        if not success:
            self.finished.emit(False, 'model', error_msg)
            return

        self.finished.emit(True, '', '')


class ModelUnloadWorker(QThread):
    # Background thread to unload the AI model from GPU memory.
    # Runs in background because checking model status can take time.
    finished = Signal(bool, str)  # (success, message_key_or_error)

    def __init__(self, client):
        super().__init__()
        self.client = client

    def run(self):
        # Check connection first
        success, error_msg = check_connection(self.client)
        if not success:
            self.finished.emit(False, error_msg)
            return

        try:
            # Check if the model is actually loaded
            response = self.client.ps()
            # Handle both object and dict response formats
            if hasattr(response, 'models'):
                models = response.models
            else:
                models = response.get('models', [])

            is_loaded = False
            for m in models:
                # Handle both attribute and dict access
                name = m.model if hasattr(m, 'model') else m.get('model')
                if name == config.OLLAMA_MODEL:
                    is_loaded = True
                    break

            if is_loaded:
                # Unload by sending empty request with keep_alive=0
                # This tells Ollama to immediately unload after this request
                self.client.chat(model=config.OLLAMA_MODEL, messages=[], keep_alive=0)
                self.finished.emit(True, "msg_model_unloaded")
            else:
                self.finished.emit(True, "msg_model_not_loaded")
        except Exception as e:
            self.finished.emit(False, str(e))
