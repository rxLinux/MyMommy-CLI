import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from mymommy.sandbox.sandbox import Sandbox
from typing import Callable

class ProjectWatchHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        self.sandbox = Sandbox()

    def on_modified(self, event):
        if event.is_directory:
            return
        
        # Filter out .mymommy and other noise
        if ".mymommy" in event.src_path or "__pycache__" in event.src_path:
            return
            
        relative_path = str(event.src_path).replace(str(self.sandbox.base_path), "").lstrip("/")
        self.callback(relative_path)

class WatchService:
    def __init__(self, callback: Callable[[str], None]):
        self.observer = Observer()
        self.handler = ProjectWatchHandler(callback)
        self.sandbox = Sandbox()

    def start(self):
        self.observer.schedule(self.handler, str(self.sandbox.base_path), recursive=True)
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()
